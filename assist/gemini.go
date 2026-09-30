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

// The Gemini Generative Language API. A turn is one content with a role
// ("user" or "model") and parts; the whole conversation is replayed each call,
// with the persona carried separately as a system instruction. When tools are
// offered, the model may answer with a functionCall part instead of text; the
// caller runs the tool and replays a functionResponse part.

type gPart struct {
	Text             string             `json:"text,omitempty"`
	FunctionCall     *gFunctionCall     `json:"functionCall,omitempty"`
	FunctionResponse *gFunctionResponse `json:"functionResponse,omitempty"`
	// Gemini 3.x returns an opaque thought signature on functionCall parts that
	// must be echoed back verbatim when the tool-call turn is replayed.
	ThoughtSignature string `json:"thoughtSignature,omitempty"`
	// A part marked Thought is the model's reasoning, surfaced separately from
	// its answer when thinking output is requested.
	Thought bool `json:"thought,omitempty"`
	// An image or PDF the owner attached, sent to the model as raw bytes.
	InlineData *gBlob `json:"inlineData,omitempty"`
}

type gBlob struct {
	MimeType string `json:"mimeType"`
	Data     string `json:"data"`
}

type gFunctionCall struct {
	Name string         `json:"name"`
	Args map[string]any `json:"args"`
}

type gFunctionResponse struct {
	Name     string         `json:"name"`
	Response map[string]any `json:"response"`
}

type gContent struct {
	Role  string  `json:"role,omitempty"`
	Parts []gPart `json:"parts"`
}

type gSchema struct {
	Type       string             `json:"type"`
	Properties map[string]gSchema `json:"properties,omitempty"`
	Description string            `json:"description,omitempty"`
	Required   []string           `json:"required,omitempty"`
}

type gFuncDecl struct {
	Name        string  `json:"name"`
	Description string  `json:"description"`
	Parameters  gSchema `json:"parameters"`
}

type gTool struct {
	FunctionDeclarations []gFuncDecl `json:"function_declarations"`
}

type gThinkingConfig struct {
	IncludeThoughts bool `json:"includeThoughts"`
}

type gGenerationConfig struct {
	ThinkingConfig *gThinkingConfig `json:"thinkingConfig,omitempty"`
}

type gRequest struct {
	SystemInstruction *gContent          `json:"system_instruction,omitempty"`
	Contents          []gContent         `json:"contents"`
	Tools             []gTool            `json:"tools,omitempty"`
	GenerationConfig  *gGenerationConfig `json:"generationConfig,omitempty"`
}

type gResponse struct {
	Candidates []struct {
		Content      gContent `json:"content"`
		FinishReason string   `json:"finishReason"`
	} `json:"candidates"`
	Error *struct {
		Message string `json:"message"`
		Status  string `json:"status"`
	} `json:"error"`
}

// generate makes one API call and returns the model's content (which may hold a
// text part, a functionCall part, or both).
func generate(key, model string, req gRequest) (gContent, error) {
	body, err := json.Marshal(req)
	if err != nil {
		return gContent{}, err
	}
	url := fmt.Sprintf("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent", model)
	httpReq, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return gContent{}, err
	}
	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("x-goog-api-key", key)

	client := &http.Client{Timeout: 90 * time.Second}
	resp, err := client.Do(httpReq)
	if err != nil {
		return gContent{}, err
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(resp.Body)

	var gr gResponse
	if err := json.Unmarshal(raw, &gr); err != nil {
		return gContent{}, fmt.Errorf("gemini unparseable (%d): %s", resp.StatusCode, truncate(string(raw), 300))
	}
	if gr.Error != nil {
		return gContent{}, fmt.Errorf("gemini error: %s", gr.Error.Message)
	}
	if len(gr.Candidates) == 0 {
		return gContent{}, fmt.Errorf("gemini returned no candidate (%d): %s", resp.StatusCode, truncate(string(raw), 300))
	}
	return gr.Candidates[0].Content, nil
}

// callGemini is the no-tools path: send the persona plus history, return the text.
func callGemini(key, model, system string, history []gContent) (string, error) {
	req := gRequest{Contents: history}
	if system != "" {
		req.SystemInstruction = &gContent{Parts: []gPart{{Text: system}}}
	}
	content, err := generate(key, model, req)
	if err != nil {
		return "", err
	}
	return firstText(content), nil
}

func firstText(c gContent) string {
	for _, p := range c.Parts {
		if p.Text != "" {
			return p.Text
		}
	}
	return ""
}

// firstAnswerText returns the model's answer, skipping thought parts.
func firstAnswerText(c gContent) string {
	for _, p := range c.Parts {
		if p.Text != "" && !p.Thought {
			return p.Text
		}
	}
	return ""
}

// thoughts returns the model's reasoning parts as plain strings.
func thoughts(c gContent) []string {
	var out []string
	for _, p := range c.Parts {
		if p.Text != "" && p.Thought {
			out = append(out, p.Text)
		}
	}
	return out
}

func functionCalls(c gContent) []gFunctionCall {
	var calls []gFunctionCall
	for _, p := range c.Parts {
		if p.FunctionCall != nil {
			calls = append(calls, *p.FunctionCall)
		}
	}
	return calls
}

// listModels names the models the key can reach, used to verify the model id.
func listModels(key string) (string, error) {
	req, _ := http.NewRequest(http.MethodGet,
		"https://generativelanguage.googleapis.com/v1beta/models", nil)
	req.Header.Set("x-goog-api-key", key)
	client := &http.Client{Timeout: 20 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	// Gemini answers a bad key with 400 on this plain list call, not only 401 or 403.
	if resp.StatusCode == 400 || resp.StatusCode == 401 || resp.StatusCode == 403 {
		return "", errKeyRejected
	}
	raw, _ := io.ReadAll(resp.Body)
	return string(raw), nil
}

// listGeminiChatModels names the Gemini models this key can chat with, leaving
// out the embedding, speech, image and live-audio ones.
func listGeminiChatModels(key string) ([]string, error) {
	raw, err := listModels(key)
	if err != nil {
		return nil, err
	}
	var list struct {
		Models []struct {
			Name    string   `json:"name"`
			Methods []string `json:"supportedGenerationMethods"`
		} `json:"models"`
	}
	if err := json.Unmarshal([]byte(raw), &list); err != nil {
		return nil, err
	}
	var ids []string
	for _, m := range list.Models {
		id := strings.TrimPrefix(m.Name, "models/")
		if !strings.HasPrefix(id, "gemini") || geminiNotChat.MatchString(id) {
			continue
		}
		for _, method := range m.Methods {
			if method == "generateContent" {
				ids = append(ids, id)
				break
			}
		}
	}
	return ids, nil
}

var geminiNotChat = regexp.MustCompile(`embedding|tts|image|audio|live|robotics|computer-use|transcribe|customtools`)

func truncate(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n] + "..."
}
