package main

import (
	"bufio"
	"bytes"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

// OpenAI through a ChatGPT subscription instead of an API key.
//
// The owner signs in once on this device with the Codex CLI (`codex login`),
// which writes ~/.codex/auth.json. The assistant reads that file, keeps the
// access token fresh, and sends chat to the same endpoint the Codex CLI uses,
// so usage comes out of the ChatGPT plan and no API credit is needed.
//
// Two things differ from the API-key path in openai.go: the reply is always a
// stream, and nothing is stored on OpenAI's side, so every follow-up after a
// tool call resends the whole turn, including the model's own output items.

// chatGPTKey is what providerKey returns for OpenAI when a ChatGPT sign-in is
// present. It is a marker, not a secret: the real token is read at call time.
const chatGPTKey = "chatgpt-subscription"

// The models a ChatGPT plan can use on this endpoint, newest first. There is no
// list call for it; each was accepted by the endpoint on 2026-09-30, and the
// API-only ids (gpt-5.4, the -codex names) were refused.
var chatGPTModels = []string{"gpt-6.1-sol", "gpt-5.6-sol", "gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.5"}

const (
	chatGPTEndpoint = "https://chatgpt.com/backend-api/codex/responses"
	chatGPTTokenURL = "https://auth.openai.com/oauth/token"
	// The Codex CLI's public OAuth client id. A refresh must name the client that signed in.
	chatGPTClientID = "app_EMoamEEZ73f0CkXaXp7hrann"
)

var chatGPTAuthLock sync.Mutex

func codexAuthPath() string {
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".codex", "auth.json")
}

// chatGPTSignedIn reports whether the Codex CLI has a ChatGPT sign-in on this device.
func chatGPTSignedIn() bool {
	_, tokens, err := readCodexAuth()
	return err == nil && tokens["refresh_token"] != nil && tokens["access_token"] != nil
}

// readCodexAuth loads the Codex CLI's auth file as loose JSON, so fields this
// code does not know about survive when the file is written back.
func readCodexAuth() (map[string]any, map[string]any, error) {
	raw, err := os.ReadFile(codexAuthPath())
	if err != nil {
		return nil, nil, fmt.Errorf("no ChatGPT sign-in on this device: run codex login")
	}
	var file map[string]any
	if err := json.Unmarshal(raw, &file); err != nil {
		return nil, nil, fmt.Errorf("the Codex sign-in file is not readable: %v", err)
	}
	tokens, _ := file["tokens"].(map[string]any)
	if tokens == nil {
		return nil, nil, fmt.Errorf("the Codex CLI is not signed in with ChatGPT on this device")
	}
	return file, tokens, nil
}

// chatGPTToken returns a usable access token and the account it belongs to,
// refreshing it first when it has under five minutes left.
func chatGPTToken() (access, account string, err error) {
	chatGPTAuthLock.Lock()
	defer chatGPTAuthLock.Unlock()
	file, tokens, err := readCodexAuth()
	if err != nil {
		return "", "", err
	}
	access, _ = tokens["access_token"].(string)
	account, _ = tokens["account_id"].(string)
	if time.Until(jwtExpiry(access)) > 5*time.Minute {
		return access, account, nil
	}
	refresh, _ := tokens["refresh_token"].(string)
	body, _ := json.Marshal(map[string]string{
		"client_id": chatGPTClientID, "grant_type": "refresh_token",
		"refresh_token": refresh, "scope": "openid profile email",
	})
	resp, err := (&http.Client{Timeout: 30 * time.Second}).Post(chatGPTTokenURL, "application/json", bytes.NewReader(body))
	if err != nil {
		return "", "", fmt.Errorf("could not refresh the ChatGPT sign-in: %v", err)
	}
	defer resp.Body.Close()
	var fresh map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&fresh); err != nil || resp.StatusCode != http.StatusOK {
		return "", "", fmt.Errorf("the ChatGPT sign-in has expired (%d): run codex login on this device again", resp.StatusCode)
	}
	for _, name := range []string{"access_token", "refresh_token", "id_token"} {
		if v, ok := fresh[name].(string); ok && v != "" {
			tokens[name] = v
		}
	}
	file["tokens"] = tokens
	file["last_refresh"] = time.Now().UTC().Format(time.RFC3339Nano)
	if out, err := json.MarshalIndent(file, "", "  "); err == nil {
		_ = os.WriteFile(codexAuthPath(), out, 0o600)
	}
	access, _ = tokens["access_token"].(string)
	return access, account, nil
}

// jwtExpiry reads the expiry time out of a token without verifying it. A token
// that cannot be read counts as already expired, so it gets refreshed.
func jwtExpiry(token string) time.Time {
	parts := strings.Split(token, ".")
	if len(parts) < 2 {
		return time.Time{}
	}
	payload, err := base64.RawURLEncoding.DecodeString(parts[1])
	if err != nil {
		return time.Time{}
	}
	var claims struct {
		Exp int64 `json:"exp"`
	}
	if json.Unmarshal(payload, &claims) != nil {
		return time.Time{}
	}
	return time.Unix(claims.Exp, 0)
}

// runChatGPT drives one user turn to a final answer on the subscription endpoint.
func runChatGPT(model, effort, system string, history []gContent, emit func(turn)) ([]turn, error) {
	input := openAIInput(history)
	var turns []turn
	add := func(t turn) {
		turns = append(turns, t)
		if emit != nil {
			emit(t)
		}
	}
	for step := 0; step < maxToolSteps; step++ {
		items, err := chatGPTStream(map[string]any{
			"model": model, "instructions": system, "input": input, "tools": openAITools(),
			"tool_choice": "auto", "parallel_tool_calls": false,
			"reasoning": map[string]any{"effort": openAIEffort(effort), "summary": "auto"},
			"store": false, "stream": true, "include": []string{"reasoning.encrypted_content"},
		})
		if err != nil {
			return turns, err
		}
		var answer strings.Builder
		called := false
		for _, raw := range items {
			var item struct {
				Type      string `json:"type"`
				CallID    string `json:"call_id"`
				Name      string `json:"name"`
				Arguments string `json:"arguments"`
				Content   []struct {
					Type string `json:"type"`
					Text string `json:"text"`
				} `json:"content"`
				Summary []struct {
					Text string `json:"text"`
				} `json:"summary"`
			}
			if json.Unmarshal(raw, &item) != nil {
				continue
			}
			// The model's own items go back as they came, so the next call has its reasoning and its tool calls.
			input = append(input, raw)
			switch item.Type {
			case "reasoning":
				for _, s := range item.Summary {
					if strings.TrimSpace(s.Text) != "" {
						add(turn{Type: "thinking", Text: s.Text})
					}
				}
			case "message":
				for _, c := range item.Content {
					if c.Type == "output_text" {
						answer.WriteString(c.Text)
					}
				}
			case "function_call":
				called = true
				args := map[string]any{}
				_ = json.Unmarshal([]byte(item.Arguments), &args)
				result := executeTool(item.Name, args)
				add(turn{Type: "tool_call", Name: item.Name, Args: args, Result: result})
				encoded, _ := json.Marshal(result)
				input = append(input, map[string]any{"type": "function_call_output", "call_id": item.CallID, "output": string(encoded)})
			}
		}
		if !called {
			add(turn{Type: "text", Text: answer.String()})
			return turns, nil
		}
	}
	return turns, fmt.Errorf("stopped after %d tool steps (safety ceiling) without a final answer", maxToolSteps)
}

// chatGPTStream sends one request and returns the finished output items, in order, as raw JSON.
func chatGPTStream(body map[string]any) ([]json.RawMessage, error) {
	access, account, err := chatGPTToken()
	if err != nil {
		return nil, err
	}
	encoded, err := json.Marshal(body)
	if err != nil {
		return nil, err
	}
	req, err := http.NewRequest(http.MethodPost, chatGPTEndpoint, bytes.NewReader(encoded))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+access)
	req.Header.Set("chatgpt-account-id", account)
	req.Header.Set("OpenAI-Beta", "responses=experimental")
	req.Header.Set("originator", "codex_cli_rs")
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "text/event-stream")
	resp, err := (&http.Client{Timeout: 10 * time.Minute}).Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		raw, _ := io.ReadAll(io.LimitReader(resp.Body, 2000))
		var problem struct {
			Detail string `json:"detail"`
		}
		if json.Unmarshal(raw, &problem) == nil && problem.Detail != "" {
			return nil, fmt.Errorf("openai: %s", problem.Detail)
		}
		return nil, fmt.Errorf("openai returned %d: %s", resp.StatusCode, truncate(string(raw), 300))
	}
	var items []json.RawMessage
	lines := bufio.NewScanner(resp.Body)
	lines.Buffer(make([]byte, 0, 1<<20), 32<<20)
	for lines.Scan() {
		data, ok := strings.CutPrefix(lines.Text(), "data:")
		if !ok {
			continue
		}
		var event struct {
			Type     string          `json:"type"`
			Item     json.RawMessage `json:"item"`
			Response struct {
				Error *struct {
					Message string `json:"message"`
				} `json:"error"`
			} `json:"response"`
		}
		if json.Unmarshal([]byte(strings.TrimSpace(data)), &event) != nil {
			continue
		}
		switch event.Type {
		case "response.output_item.done":
			items = append(items, event.Item)
		case "response.failed":
			if event.Response.Error != nil {
				return items, fmt.Errorf("openai: %s", event.Response.Error.Message)
			}
			return items, fmt.Errorf("openai: the response failed")
		case "response.completed":
			return items, nil
		}
	}
	if err := lines.Err(); err != nil {
		return items, err
	}
	return items, nil
}
