package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"
)

// providerInfo is one entry in the assistant's provider registry: what the app
// offers the owner to pick. Models and effort levels are lists so the Settings
// UI can drill provider -> model -> effort.
type providerInfo struct {
	ID      string   `json:"id"`
	Label   string   `json:"label"`
	Models  []string `json:"models"`
	Efforts []string `json:"efforts"`
	KeyFile string   `json:"keyFile"`
	// ChatSupported is true when this Pi can chat through the provider right now:
	// the code path exists and its key file is present.
	ChatSupported bool `json:"chatSupported"`
	// Reason says why not, in words the app can show as they are.
	Reason string `json:"reason,omitempty"`
}

// A chat runner drives one user turn to a final answer through one provider.
// emit gets each thinking, tool-call and answer turn as it happens, and delta
// gets the answer's words as they are written; either may be nil. Cancelling
// ctx stops the run and ends it with the answer so far, marked stopped.
type chatRunner func(ctx context.Context, key, model, effort, system string, history []gContent, emit func(turn), delta func(string)) ([]turn, tokenCount, error)

var chatRunners = map[string]chatRunner{"gemini": runChat, "claude": runClaude, "openai": runOpenAI}

// assistConfig is the owner's current selection.
type assistConfig struct {
	Provider string `json:"provider"`
	Model    string `json:"model"`
	Effort   string `json:"effort"`
}

// builtinProviders is the registry, with the model lists used when a provider's
// own model list cannot be fetched.
func builtinProviders() []providerInfo {
	return []providerInfo{
		{
			ID: "gemini", Label: "Gemini", KeyFile: "gemini.key",
			Models:  []string{"gemini-3.8-flash", "gemini-3.5-flash", "gemini-flash-latest", "gemini-2.5-flash"},
			Efforts: []string{"off", "low", "medium", "high"},
		},
		{
			ID: "claude", Label: "Claude", KeyFile: "claude.key",
			Models:  []string{"claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-4-5", "claude-fable-5-1"},
			Efforts: []string{"low", "medium", "high"},
		},
		{
			ID: "openai", Label: "Codex", KeyFile: "openai.key",
			Models:  chatGPTModels,
			Efforts: []string{"low", "medium", "high"},
		},
	}
}

// loadProviders returns the registry, letting an optional providers.json replace
// the built-in list.
func loadProviders() []providerInfo {
	p := filepath.Join(configDir(), "providers.json")
	if b, err := os.ReadFile(p); err == nil {
		var extra []providerInfo
		if json.Unmarshal(b, &extra) == nil && len(extra) > 0 {
			return extra
		}
	}
	return builtinProviders()
}

// providersForApp is the registry as the phone sees it: whether each provider
// can chat on this Pi, and the models its key can reach right now.
func providersForApp() []providerInfo {
	providers := loadProviders()
	var wait sync.WaitGroup
	for i := range providers {
		p := &providers[i]
		if _, ok := chatRunners[p.ID]; !ok {
			p.Reason = p.Label + " is not built into this Pi's assistant"
			continue
		}
		// A ChatGPT sign-in comes before an API key: it uses the plan the owner already pays for.
		if p.ID == "openai" && chatGPTSignedIn() {
			p.ChatSupported, p.Models = true, chatGPTModels
			continue
		}
		key, err := readKeyFile(filepath.Join(configDir(), p.KeyFile))
		if err != nil {
			p.Reason = "No " + p.Label + " key on this Pi"
			continue
		}
		p.ChatSupported = true
		wait.Add(1)
		go func() {
			defer wait.Done()
			live, err := liveModels(p.ID, key)
			if errors.Is(err, errKeyRejected) {
				p.ChatSupported = false
				p.Reason = "The " + p.Label + " key on this Pi was rejected"
			} else if len(live) > 0 {
				p.Models = live
			}
		}()
	}
	wait.Wait()
	return providers
}

func chatProviderSupported(id string) bool {
	for _, p := range loadProviders() {
		if p.ID == id {
			_, implemented := chatRunners[id]
			_, err := providerKey(id)
			return implemented && err == nil
		}
	}
	return false
}

// providerForModel names the provider a model id belongs to, so a conversation
// can pin a model from any provider and the right key and API are used.
func providerForModel(model, fallback string) string {
	m := strings.ToLower(model)
	switch {
	case strings.HasPrefix(m, "claude"):
		return "claude"
	case strings.HasPrefix(m, "gemini"):
		return "gemini"
	case strings.HasPrefix(m, "gpt"), strings.HasPrefix(m, "codex"), oaChatModel.MatchString(m):
		return "openai"
	}
	return fallback
}

var modelCache = struct {
	sync.Mutex
	at     map[string]time.Time
	models map[string][]string
}{at: map[string]time.Time{}, models: map[string][]string{}}

// errKeyRejected means the provider answered and refused the key itself, as
// opposed to being unreachable. A list function wraps it so the app can say so.
var errKeyRejected = errors.New("the provider rejected this key")

// liveModels asks the provider which chat models this key can use, newest first,
// and remembers the answer for six hours. On an error the caller keeps the
// built-in list, unless the error is errKeyRejected.
func liveModels(id, key string) ([]string, error) {
	modelCache.Lock()
	if cached, ok := modelCache.models[id]; ok && time.Since(modelCache.at[id]) < 6*time.Hour {
		modelCache.Unlock()
		return cached, nil
	}
	modelCache.Unlock()

	var ids []string
	var err error
	switch id {
	case "gemini":
		ids, err = listGeminiChatModels(key)
	case "claude":
		ids, err = listClaudeModels(key) // already newest first
	case "openai":
		ids, err = listOpenAIModels(key)
	}
	if err != nil || len(ids) == 0 {
		return nil, err
	}
	if id != "claude" {
		sort.Sort(sort.Reverse(sort.StringSlice(ids)))
	}
	modelCache.Lock()
	modelCache.models[id], modelCache.at[id] = ids, time.Now()
	modelCache.Unlock()
	return ids, nil
}

// loadAssistConfig reads the current selection, falling back to the older
// single-value files and finally to sensible defaults, so an existing install
// keeps working.
func loadAssistConfig() assistConfig {
	c := assistConfig{Provider: "gemini", Model: model(), Effort: "medium"}
	p := filepath.Join(configDir(), "assist.config.json")
	if b, err := os.ReadFile(p); err == nil {
		var got assistConfig
		if json.Unmarshal(b, &got) == nil {
			if got.Provider != "" {
				c.Provider = got.Provider
			}
			if got.Model != "" {
				c.Model = got.Model
			}
			if got.Effort != "" {
				c.Effort = got.Effort
			}
		}
	}
	return c
}

func saveAssistConfig(c assistConfig) error {
	if err := os.MkdirAll(configDir(), 0o700); err != nil {
		return err
	}
	b, _ := json.MarshalIndent(c, "", "  ")
	return os.WriteFile(filepath.Join(configDir(), "assist.config.json"), b, 0o600)
}

// providerKey reads the API key for a provider from its registered key file.
func providerKey(id string) (string, error) {
	if id == "openai" && chatGPTSignedIn() {
		return chatGPTKey, nil
	}
	for _, p := range loadProviders() {
		if p.ID == id {
			return readKeyFile(filepath.Join(configDir(), p.KeyFile))
		}
	}
	return "", fmt.Errorf("unknown provider %q", id)
}

// effortToThinking maps an effort level to Gemini's thinking config; off means
// no thinking output, the rest raise the budget.
func effortToThinking(effort string) *gGenerationConfig {
	switch strings.ToLower(effort) {
	case "", "off":
		return &gGenerationConfig{ThinkingConfig: &gThinkingConfig{IncludeThoughts: false}}
	default:
		return &gGenerationConfig{ThinkingConfig: &gThinkingConfig{IncludeThoughts: true}}
	}
}

// The tools are declared once, in Gemini's shape. These turn that one list into
// the JSON schema the other providers take.

func allFunctionDeclarations() []gFuncDecl {
	var out []gFuncDecl
	for _, t := range toolDeclarations() {
		out = append(out, t.FunctionDeclarations...)
	}
	return out
}

func schemaProperties(s gSchema) map[string]any {
	props := map[string]any{}
	for name, p := range s.Properties {
		one := map[string]any{"type": strings.ToLower(p.Type)}
		if p.Description != "" {
			one["description"] = p.Description
		}
		if len(p.Properties) > 0 {
			one["properties"] = schemaProperties(p)
		}
		props[name] = one
	}
	return props
}

func nonNil(list []string) []string {
	if list == nil {
		return []string{}
	}
	return list
}
