package main

import (
	"reflect"
	"testing"
)

// The list offered for chat holds only models this assistant can actually talk to.
func TestGeminiChatModelsLeaveOutWhatCannotChatHere(t *testing.T) {
	raw := `{"models":[
		{"name":"models/gemini-3.8-flash","supportedGenerationMethods":["generateContent","countTokens"]},
		{"name":"models/gemini-omni-1.1-flash","supportedGenerationMethods":["generateContent"]},
		{"name":"models/gemini-omni-flash-preview","supportedGenerationMethods":["generateContent"]},
		{"name":"models/gemini-embedding-001","supportedGenerationMethods":["embedContent"]},
		{"name":"models/gemini-2.5-flash-preview-tts","supportedGenerationMethods":["generateContent"]},
		{"name":"models/gemini-pro-latest","supportedGenerationMethods":["generateContent"]},
		{"name":"models/gemini-batch-only","supportedGenerationMethods":["batchGenerateContent"]},
		{"name":"models/gemma-3-27b-it","supportedGenerationMethods":["generateContent"]}
	]}`
	got, err := geminiChatModels(raw)
	if err != nil {
		t.Fatal(err)
	}
	want := []string{"gemini-3.8-flash", "gemini-pro-latest"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("chat models = %v, want %v", got, want)
	}
	if _, err := geminiChatModels("not json"); err == nil {
		t.Fatal("a reply that is not a model list should be an error")
	}
}
