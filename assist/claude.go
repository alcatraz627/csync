package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/anthropics/anthropic-sdk-go"
	"github.com/anthropics/anthropic-sdk-go/option"
)

// Claude as a chat provider. The conversation history is kept in the same shape
// for every provider and converted to Claude's messages here, so switching model
// mid-conversation keeps the thread.

// runClaude drives one user turn to a final answer through the Messages API,
// running each tool Claude asks for and replaying the result, and reporting the
// thinking and tool calls through emit as they happen.
func runClaude(key, model, effort, system string, history []gContent, emit func(turn)) ([]turn, error) {
	client := anthropic.NewClient(option.WithAPIKey(key))
	params := anthropic.MessageNewParams{
		Model:     anthropic.Model(model),
		MaxTokens: 16000,
		System:    []anthropic.TextBlockParam{{Text: system}},
		Tools:     claudeTools(),
	}
	// Haiku 4.5 takes neither adaptive thinking nor an effort level; every newer model takes both.
	if !strings.Contains(model, "haiku") {
		adaptive := anthropic.ThinkingConfigAdaptiveParam{Display: anthropic.ThinkingConfigAdaptiveDisplaySummarized}
		params.Thinking = anthropic.ThinkingConfigParamUnion{OfAdaptive: &adaptive}
		params.OutputConfig = anthropic.OutputConfigParam{Effort: claudeEffort(effort)}
	}
	messages := claudeMessages(history)

	var turns []turn
	add := func(t turn) {
		turns = append(turns, t)
		if emit != nil {
			emit(t)
		}
	}
	for step := 0; step < maxToolSteps; step++ {
		params.Messages = messages
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
		resp, err := client.Messages.New(ctx, params)
		cancel()
		if err != nil {
			return turns, fmt.Errorf("claude: %w", err)
		}
		if resp.StopReason == anthropic.StopReasonRefusal {
			add(turn{Type: "text", Text: "Claude declined this request. Try rephrasing it, or switch to another model for this conversation."})
			return turns, nil
		}
		// The whole reply, thinking included, goes back unchanged so the next call can continue from it.
		messages = append(messages, resp.ToParam())

		var answer strings.Builder
		var results []anthropic.ContentBlockParamUnion
		for _, block := range resp.Content {
			switch b := block.AsAny().(type) {
			case anthropic.ThinkingBlock:
				if strings.TrimSpace(b.Thinking) != "" {
					add(turn{Type: "thinking", Text: b.Thinking})
				}
			case anthropic.TextBlock:
				answer.WriteString(b.Text)
			case anthropic.ToolUseBlock:
				args := map[string]any{}
				_ = json.Unmarshal([]byte(b.JSON.Input.Raw()), &args)
				result := executeTool(b.Name, args)
				add(turn{Type: "tool_call", Name: b.Name, Args: args, Result: result})
				encoded, _ := json.Marshal(result)
				results = append(results, anthropic.NewToolResultBlock(b.ID, string(encoded), false))
			}
		}
		if resp.StopReason != anthropic.StopReasonToolUse {
			text := answer.String()
			if resp.StopReason == anthropic.StopReasonMaxTokens {
				text += "\n\n(The answer was cut off at the length limit.)"
			}
			add(turn{Type: "text", Text: text})
			return turns, nil
		}
		messages = append(messages, anthropic.NewUserMessage(results...))
	}
	return turns, fmt.Errorf("stopped after %d tool steps (safety ceiling) without a final answer", maxToolSteps)
}

// claudeEffort maps the app's effort words to Claude's. Thinking cannot be turned
// off on current models, so "off" becomes the lowest level.
func claudeEffort(effort string) anthropic.OutputConfigEffort {
	switch strings.ToLower(effort) {
	case "high":
		return anthropic.OutputConfigEffortHigh
	case "medium":
		return anthropic.OutputConfigEffortMedium
	default:
		return anthropic.OutputConfigEffortLow
	}
}

func claudeMessages(history []gContent) []anthropic.MessageParam {
	var out []anthropic.MessageParam
	for _, c := range history {
		var blocks []anthropic.ContentBlockParamUnion
		for _, p := range c.Parts {
			switch {
			case p.InlineData != nil && p.InlineData.MimeType == "application/pdf":
				blocks = append(blocks, anthropic.NewDocumentBlock(anthropic.Base64PDFSourceParam{Data: p.InlineData.Data}))
			case p.InlineData != nil:
				blocks = append(blocks, anthropic.NewImageBlockBase64(p.InlineData.MimeType, p.InlineData.Data))
			case p.Text != "" && !p.Thought:
				blocks = append(blocks, anthropic.NewTextBlock(p.Text))
			}
		}
		if len(blocks) == 0 {
			continue
		}
		if c.Role == "model" {
			out = append(out, anthropic.NewAssistantMessage(blocks...))
		} else {
			out = append(out, anthropic.NewUserMessage(blocks...))
		}
	}
	return out
}

// claudeTools offers Claude the same tools Gemini gets, from the one declaration list.
func claudeTools() []anthropic.ToolUnionParam {
	var out []anthropic.ToolUnionParam
	for _, d := range allFunctionDeclarations() {
		tool := anthropic.ToolParam{
			Name:        d.Name,
			Description: anthropic.String(d.Description),
			InputSchema: anthropic.ToolInputSchemaParam{
				Properties: schemaProperties(d.Parameters),
				Required:   d.Parameters.Required,
			},
		}
		out = append(out, anthropic.ToolUnionParam{OfTool: &tool})
	}
	return out
}

func listClaudeModels(key string) ([]string, error) {
	client := anthropic.NewClient(option.WithAPIKey(key))
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	var ids []string
	pager := client.Models.ListAutoPaging(ctx, anthropic.ModelListParams{})
	for pager.Next() {
		ids = append(ids, pager.Current().ID)
	}
	var apiErr *anthropic.Error
	if err := pager.Err(); errors.As(err, &apiErr) && (apiErr.StatusCode == 401 || apiErr.StatusCode == 403) {
		return nil, fmt.Errorf("%w: %v", errKeyRejected, err)
	}
	return ids, pager.Err()
}
