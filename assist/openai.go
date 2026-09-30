package main

import (
	"bytes"
	"context"
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
	Stream             bool         `json:"stream"`
}

type oaReasoning struct {
	Effort string `json:"effort"`
}

// oaItem is one finished output item of a response: reasoning, a message, or a function call.
type oaItem struct {
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

// openAIBaseURL is where the OpenAI API lives; tests point it at a local fake.
var openAIBaseURL = "https://api.openai.com"

// Models that accept a reasoning effort. Sending one to a model that does not is an error.
var oaReasoningModel = regexp.MustCompile(`^(gpt-5|o[0-9]|codex)`)

func runOpenAI(ctx context.Context, key, model, effort, system string, history []gContent, emit func(turn), delta func(string)) ([]turn, tokenCount, error) {
	if key == chatGPTKey {
		return runChatGPT(ctx, model, effort, system, history, emit, delta)
	}
	req := oaRequest{Model: model, Instructions: system, Input: openAIInput(history), Tools: openAITools(), Stream: true}
	if oaReasoningModel.MatchString(model) {
		req.Reasoning = &oaReasoning{Effort: openAIEffort(effort)}
	}
	st := newRunState(ctx, emit, delta)
	for step := 0; step < maxToolSteps; step++ {
		if st.stopped() {
			return st.stop()
		}
		st.step()
		body, err := json.Marshal(req)
		if err != nil {
			return st.fail(err)
		}
		httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, openAIBaseURL+"/v1/responses", bytes.NewReader(body))
		if err != nil {
			return st.fail(err)
		}
		httpReq.Header.Set("Content-Type", "application/json")
		httpReq.Header.Set("Authorization", "Bearer "+key)
		raws, id, tokens, err := responsesStream(httpReq, st.text)
		if tokens.Reported {
			st.count(tokens.In, tokens.Out)
		}
		if err != nil {
			return st.fail(err)
		}
		var answer strings.Builder
		var results []any
		for _, raw := range raws {
			var item oaItem
			if json.Unmarshal(raw, &item) != nil {
				continue
			}
			switch item.Type {
			case "reasoning":
				for _, s := range item.Summary {
					if strings.TrimSpace(s.Text) != "" {
						st.add(turn{Type: "thinking", Text: s.Text})
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
				st.add(turn{Type: "tool_call", Name: item.Name, Args: args, Result: result})
				encoded, _ := json.Marshal(result)
				results = append(results, map[string]any{"type": "function_call_output", "call_id": item.CallID, "output": string(encoded)})
			}
		}
		if len(results) == 0 {
			return st.answer(answer.String())
		}
		req.Input = results
		req.PreviousResponseID = id
	}
	return st.turns, st.tokens, fmt.Errorf("stopped after %d tool steps (safety ceiling) without a final answer", maxToolSteps)
}

// responsesStream sends one streaming Responses request, the shape both the API
// and the ChatGPT endpoint speak. It hands each piece of answer text to onText
// as it arrives and returns the finished output items in order, the response id
// and the tokens it used.
func responsesStream(req *http.Request, onText func(string)) ([]json.RawMessage, string, tokenCount, error) {
	var tokens tokenCount
	req.Header.Set("Accept", "text/event-stream")
	resp, err := (&http.Client{Timeout: 10 * time.Minute}).Do(req)
	if err != nil {
		return nil, "", tokens, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		raw, _ := io.ReadAll(io.LimitReader(resp.Body, 4000))
		var problem struct {
			Detail string `json:"detail"`
			Error  *struct {
				Message string `json:"message"`
			} `json:"error"`
		}
		if json.Unmarshal(raw, &problem) == nil && problem.Detail != "" {
			return nil, "", tokens, fmt.Errorf("openai: %s", problem.Detail)
		}
		if problem.Error != nil {
			return nil, "", tokens, fmt.Errorf("openai error: %s", problem.Error.Message)
		}
		return nil, "", tokens, fmt.Errorf("openai returned %d: %s", resp.StatusCode, truncate(string(raw), 300))
	}
	var items []json.RawMessage
	id := ""
	completed := false
	err = readSSE(resp.Body, func(data []byte) (bool, error) {
		var event struct {
			Type     string          `json:"type"`
			Delta    string          `json:"delta"`
			Item     json.RawMessage `json:"item"`
			Message  string          `json:"message"`
			Response struct {
				ID    string `json:"id"`
				Usage *struct {
					InputTokens  int64 `json:"input_tokens"`
					OutputTokens int64 `json:"output_tokens"`
				} `json:"usage"`
				Error *struct {
					Message string `json:"message"`
				} `json:"error"`
			} `json:"response"`
		}
		if json.Unmarshal(data, &event) != nil {
			return false, nil
		}
		switch event.Type {
		case "response.output_text.delta":
			onText(event.Delta)
		case "response.output_item.done":
			items = append(items, event.Item)
		case "response.failed":
			if event.Response.Error != nil {
				return true, fmt.Errorf("openai: %s", event.Response.Error.Message)
			}
			return true, fmt.Errorf("openai: the response failed")
		case "error":
			return true, fmt.Errorf("openai: %s", event.Message)
		case "response.completed", "response.incomplete":
			id, completed = event.Response.ID, true
			if u := event.Response.Usage; u != nil {
				tokens = tokenCount{In: u.InputTokens, Out: u.OutputTokens, Reported: true}
			}
			return true, nil
		}
		return false, nil
	})
	if err == nil && !completed {
		err = fmt.Errorf("openai: the reply ended before it was complete")
	}
	return items, id, tokens, err
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
		out = append(out, map[string]any{"type": "message", "role": role, "content": content})
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
