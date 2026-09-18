package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// providerInfo is one entry in the assistant's provider registry: what the app
// offers the owner to pick. Models and effort levels are lists so the Settings
// UI can drill provider -> model -> effort. A new provider is added by dropping
// a providers.json next to the config, not by changing code.
type providerInfo struct {
	ID      string   `json:"id"`
	Label   string   `json:"label"`
	Models  []string `json:"models"`
	Efforts []string `json:"efforts"`
	KeyFile string   `json:"keyFile"`
}

// assistConfig is the owner's current selection.
type assistConfig struct {
	Provider string `json:"provider"`
	Model    string `json:"model"`
	Effort   string `json:"effort"`
}

func builtinProviders() []providerInfo {
	return []providerInfo{
		{
			ID: "gemini", Label: "Gemini", KeyFile: "gemini.key",
			Models:  []string{"gemini-3.8-flash", "gemini-3.5-flash", "gemini-flash-latest", "gemini-2.5-flash"},
			Efforts: []string{"off", "low", "medium", "high"},
		},
		{
			ID: "claude", Label: "Claude", KeyFile: "claude.key",
			Models:  []string{"claude-opus-4-8", "claude-sonnet-5", "claude-haiku-4-5"},
			Efforts: []string{"off", "low", "medium", "high"},
		},
	}
}

// loadProviders returns the registry, letting an optional providers.json extend
// or replace the built-in list so a new provider needs no code change.
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
