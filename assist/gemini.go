package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
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

type gRequest struct {
	SystemInstruction *gContent  `json:"system_instruction,omitempty"`
	Contents          []gContent `json:"contents"`
	Tools             []gTool    `json:"tools,omitempty"`
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
	raw, _ := io.ReadAll(resp.Body)
	return string(raw), nil
}

func truncate(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n] + "..."
}
