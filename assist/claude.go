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

// claudeBaseURL overrides where the Messages API lives; tests point it at a local fake.
var claudeBaseURL = ""

// runClaude drives one user turn to a final answer through the Messages API,
// running each tool Claude asks for and replaying the result. Thinking and tool
// calls go to emit as they happen; the answer's words go to delta as they stream.
func runClaude(ctx context.Context, key, model, effort, system string, history []gContent, emit func(turn), delta func(string)) ([]turn, tokenCount, error) {
	opts := []option.RequestOption{option.WithAPIKey(key)}
	if claudeBaseURL != "" {
		opts = append(opts, option.WithBaseURL(claudeBaseURL))
	}
	client := anthropic.NewClient(opts...)
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

	st := newRunState(ctx, emit, delta)
	for step := 0; step < maxToolSteps; step++ {
		if st.stopped() {
			return st.stop()
		}
		st.step()
		params.Messages = messages
		resp, err := claudeStream(ctx, client, params, st.text)
		if resp.JSON.Usage.Valid() {
			u := resp.Usage
			st.count(u.InputTokens+u.CacheCreationInputTokens+u.CacheReadInputTokens, u.OutputTokens)
		}
		if err != nil {
			return st.fail(fmt.Errorf("claude: %w", err))
		}
		if resp.StopReason == anthropic.StopReasonRefusal {
			return st.answer("Claude declined this request. Try rephrasing it, or switch to another model for this conversation.")
		}
		// The whole reply, thinking included, goes back unchanged so the next call can continue from it.
		messages = append(messages, resp.ToParam())

		var answer strings.Builder
		var results []anthropic.ContentBlockParamUnion
		for _, block := range resp.Content {
			switch b := block.AsAny().(type) {
			case anthropic.ThinkingBlock:
				if strings.TrimSpace(b.Thinking) != "" {
					st.add(turn{Type: "thinking", Text: b.Thinking})
				}
			case anthropic.TextBlock:
				answer.WriteString(b.Text)
			case anthropic.ToolUseBlock:
				args := map[string]any{}
				_ = json.Unmarshal([]byte(b.JSON.Input.Raw()), &args)
				result := executeTool(b.Name, args)
				st.add(turn{Type: "tool_call", Name: b.Name, Args: args, Result: result})
				encoded, _ := json.Marshal(result)
				results = append(results, anthropic.NewToolResultBlock(b.ID, string(encoded), false))
			}
		}
		if resp.StopReason != anthropic.StopReasonToolUse {
			text := answer.String()
			if resp.StopReason == anthropic.StopReasonMaxTokens {
				const cut = "\n\n(The answer was cut off at the length limit.)"
				st.text(cut)
				text += cut
			}
			return st.answer(text)
		}
		messages = append(messages, anthropic.NewUserMessage(results...))
	}
	return st.turns, st.tokens, fmt.Errorf("stopped after %d tool steps (safety ceiling) without a final answer", maxToolSteps)
}

// claudeStream makes one streaming Messages call and returns the whole message
// once it is complete, handing each piece of answer text to onText as it arrives.
func claudeStream(ctx context.Context, client anthropic.Client, params anthropic.MessageNewParams, onText func(string)) (anthropic.Message, error) {
	ctx, cancel := context.WithTimeout(ctx, 10*time.Minute)
	defer cancel()
	stream := client.Messages.NewStreaming(ctx, params)
	defer stream.Close()
	var msg anthropic.Message
	for stream.Next() {
		event := stream.Current()
		if err := msg.Accumulate(event); err != nil {
			return msg, err
		}
		if event.Type == "content_block_delta" && event.Delta.Type == "text_delta" {
			onText(event.Delta.Text)
		}
	}
	return msg, stream.Err()
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
