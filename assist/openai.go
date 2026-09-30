package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"regexp"
	"strings"
	"time"
)

// OpenAI as a chat provider, through the Responses API. This is what the app
// calls Codex: the GPT and Codex model families behind one OpenAI key.
//
// The first call of a turn sends the whole conversation. Each follow-up after a
// tool call sends only the tool results and names the previous response, so
// OpenAI keeps the model's reasoning between steps.

type oaRequest struct {
	Model              string       `json:"model"`
	Instructions       string       `json:"instructions,omitempty"`
	Input              []any        `json:"input"`
	Tools              []any        `json:"tools,omitempty"`
	Reasoning          *oaReasoning `json:"reasoning,omitempty"`
	PreviousResponseID string       `json:"previous_response_id,omitempty"`
}

type oaReasoning struct {
	Effort string `json:"effort"`
}

type oaResponse struct {
	ID     string `json:"id"`
	Output []struct {
		Type      string `json:"type"` // reasoning | function_call | message
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
	} `json:"output"`
	Error *struct {
		Message string `json:"message"`
	} `json:"error"`
}

// Models that accept a reasoning effort. Sending one to a model that does not is an error.
var oaReasoningModel = regexp.MustCompile(`^(gpt-5|o[0-9]|codex)`)

func runOpenAI(key, model, effort, system string, history []gContent, emit func(turn)) ([]turn, error) {
	req := oaRequest{Model: model, Instructions: system, Input: openAIInput(history), Tools: openAITools()}
	if oaReasoningModel.MatchString(model) {
		req.Reasoning = &oaReasoning{Effort: openAIEffort(effort)}
	}
	var turns []turn
	add := func(t turn) {
		turns = append(turns, t)
		if emit != nil {
			emit(t)
		}
	}
	for step := 0; step < maxToolSteps; step++ {
		resp, err := openAICall(key, req)
		if err != nil {
			return turns, err
		}
		var answer strings.Builder
		var results []any
		for _, item := range resp.Output {
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
				args := map[string]any{}
				_ = json.Unmarshal([]byte(item.Arguments), &args)
				result := executeTool(item.Name, args)
				add(turn{Type: "tool_call", Name: item.Name, Args: args, Result: result})
				encoded, _ := json.Marshal(result)
				results = append(results, map[string]any{"type": "function_call_output", "call_id": item.CallID, "output": string(encoded)})
			}
		}
		if len(results) == 0 {
			add(turn{Type: "text", Text: answer.String()})
			return turns, nil
		}
		req.Input = results
		req.PreviousResponseID = resp.ID
	}
	return turns, fmt.Errorf("stopped after %d tool steps (safety ceiling) without a final answer", maxToolSteps)
}

func openAICall(key string, req oaRequest) (oaResponse, error) {
	body, err := json.Marshal(req)
	if err != nil {
		return oaResponse{}, err
	}
	httpReq, err := http.NewRequest(http.MethodPost, "https://api.openai.com/v1/responses", bytes.NewReader(body))
	if err != nil {
		return oaResponse{}, err
	}
	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Authorization", "Bearer "+key)
	resp, err := (&http.Client{Timeout: 5 * time.Minute}).Do(httpReq)
	if err != nil {
		return oaResponse{}, err
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(resp.Body)
	var out oaResponse
	if err := json.Unmarshal(raw, &out); err != nil {
		return oaResponse{}, fmt.Errorf("openai unparseable (%d): %s", resp.StatusCode, truncate(string(raw), 300))
	}
	if out.Error != nil {
		return oaResponse{}, fmt.Errorf("openai error: %s", out.Error.Message)
	}
	if resp.StatusCode >= 300 {
		return oaResponse{}, fmt.Errorf("openai returned %d: %s", resp.StatusCode, truncate(string(raw), 300))
	}
	return out, nil
}

// openAIEffort maps the app's effort words to OpenAI's. There is no "off" that every model accepts, so it becomes low.
func openAIEffort(effort string) string {
	switch strings.ToLower(effort) {
	case "high", "medium":
		return strings.ToLower(effort)
	default:
		return "low"
	}
}

func openAIInput(history []gContent) []any {
	var out []any
	for _, c := range history {
		assistant := c.Role == "model"
		var content []any
		for _, p := range c.Parts {
			switch {
			case p.InlineData != nil && p.InlineData.MimeType == "application/pdf":
				content = append(content, map[string]any{"type": "input_file", "filename": "attachment.pdf",
					"file_data": "data:application/pdf;base64," + p.InlineData.Data})
			case p.InlineData != nil:
				content = append(content, map[string]any{"type": "input_image",
					"image_url": "data:" + p.InlineData.MimeType + ";base64," + p.InlineData.Data})
			case p.Text != "" && !p.Thought && assistant:
				content = append(content, map[string]any{"type": "output_text", "text": p.Text})
			case p.Text != "" && !p.Thought:
				content = append(content, map[string]any{"type": "input_text", "text": p.Text})
			}
		}
		if len(content) == 0 {
			continue
		}
		role := "user"
		if assistant {
			role = "assistant"
		}
		out = append(out, map[string]any{"role": role, "content": content})
	}
	return out
}

func openAITools() []any {
	var out []any
	for _, d := range allFunctionDeclarations() {
		out = append(out, map[string]any{
			"type": "function", "name": d.Name, "description": d.Description,
			"parameters": map[string]any{"type": "object", "properties": schemaProperties(d.Parameters), "required": nonNil(d.Parameters.Required)},
		})
	}
	return out
}

var (
	oaChatModel    = regexp.MustCompile(`^(gpt-5|gpt-4\.1|o[0-9]|codex)`)
	oaNotChatModel = regexp.MustCompile(`audio|realtime|image|tts|transcribe|search|embedding|moderation`)
)

// listOpenAIModels names the models this key can chat with, leaving out the speech, image and embedding ones.
func listOpenAIModels(key string) ([]string, error) {
	req, _ := http.NewRequest(http.MethodGet, "https://api.openai.com/v1/models", nil)
	req.Header.Set("Authorization", "Bearer "+key)
	resp, err := (&http.Client{Timeout: 15 * time.Second}).Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode == 401 || resp.StatusCode == 403 {
		return nil, errKeyRejected
	}
	var list struct {
		Data []struct {
			ID string `json:"id"`
		} `json:"data"`
		Error *struct {
			Message string `json:"message"`
		} `json:"error"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&list); err != nil {
		return nil, err
	}
	if list.Error != nil {
		return nil, fmt.Errorf("openai error: %s", list.Error.Message)
	}
	var ids []string
	for _, m := range list.Data {
		if oaChatModel.MatchString(m.ID) && !oaNotChatModel.MatchString(m.ID) {
			ids = append(ids, m.ID)
		}
	}
	return ids, nil
}
