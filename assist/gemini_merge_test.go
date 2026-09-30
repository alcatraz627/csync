package main

import (
	"encoding/json"
	"strings"
	"testing"
)

// A real Gemini stream ends a tool-calling step with a part that holds nothing.
// Replaying that part made the next request fail, so it must never be kept.
func TestAnEmptyStreamedPartIsNotReplayed(t *testing.T) {
	var parts []gPart
	parts = mergePart(parts, gPart{FunctionCall: &gFunctionCall{Name: "pi_vitals"}, ThoughtSignature: "sig-1"})
	parts = mergePart(parts, gPart{FunctionCall: &gFunctionCall{Name: "media_drives"}})
	parts = mergePart(parts, gPart{})

	if len(parts) != 2 {
		t.Fatalf("kept %d parts, want the 2 tool calls only", len(parts))
	}
	for i, p := range parts {
		raw, _ := json.Marshal(p)
		if !strings.Contains(string(raw), "functionCall") {
			t.Fatalf("part %d would be sent with no data: %s", i, raw)
		}
	}
	if parts[0].ThoughtSignature != "sig-1" {
		t.Fatalf("the first tool call lost its signature")
	}
}

func TestASignatureOnAnEmptyPartMovesToThePartBefore(t *testing.T) {
	parts := mergePart(nil, gPart{FunctionCall: &gFunctionCall{Name: "pi_vitals"}})
	parts = mergePart(parts, gPart{ThoughtSignature: "sig-late"})

	if len(parts) != 1 || parts[0].ThoughtSignature != "sig-late" {
		t.Fatalf("got %+v, want one tool call carrying the late signature", parts)
	}

	// A signature the part already has is the one Gemini expects back.
	parts = mergePart(parts, gPart{ThoughtSignature: "sig-other"})
	if parts[0].ThoughtSignature != "sig-late" {
		t.Fatalf("an existing signature was replaced by %q", parts[0].ThoughtSignature)
	}
}
