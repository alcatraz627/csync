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
// ("user" or "model") and text parts; the whole conversation is replayed each
// call, with the persona carried separately as a system instruction.

type gPart struct {
	Text string `json:"text"`
}

type gContent struct {
	Role  string  `json:"role,omitempty"`
	Parts []gPart `json:"parts"`
}

type gRequest struct {
	SystemInstruction *gContent  `json:"system_instruction,omitempty"`
	Contents          []gContent `json:"contents"`
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

// callGemini sends the persona plus the full conversation and returns the
// model's reply text.
func callGemini(key, model, system string, history []gContent) (string, error) {
	reqBody := gRequest{Contents: history}
	if system != "" {
		reqBody.SystemInstruction = &gContent{Parts: []gPart{{Text: system}}}
	}
	body, err := json.Marshal(reqBody)
	if err != nil {
		return "", err
	}

	url := fmt.Sprintf("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent", model)
	req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("x-goog-api-key", key)

	client := &http.Client{Timeout: 60 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(resp.Body)

	var gr gResponse
	if err := json.Unmarshal(raw, &gr); err != nil {
		return "", fmt.Errorf("gemini returned unparseable response (%d): %s", resp.StatusCode, truncate(string(raw), 300))
	}
	if gr.Error != nil {
		return "", fmt.Errorf("gemini error: %s", gr.Error.Message)
	}
	if len(gr.Candidates) == 0 || len(gr.Candidates[0].Content.Parts) == 0 {
		return "", fmt.Errorf("gemini returned no answer (%d): %s", resp.StatusCode, truncate(string(raw), 300))
	}
	return gr.Candidates[0].Content.Parts[0].Text, nil
}

// listModels names the models the key can reach, used to verify the configured
// model id and to surface the right one when the configured id is wrong.
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
