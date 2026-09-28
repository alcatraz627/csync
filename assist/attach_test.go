package main

import (
	"encoding/base64"
	"os"
	"strings"
	"testing"
)

func TestUserPartsKinds(t *testing.T) {
	dir := t.TempDir()
	img := base64.StdEncoding.EncodeToString([]byte{0x89, 'P', 'N', 'G'})
	txt := base64.StdEncoding.EncodeToString([]byte("hello notes"))
	bin := base64.StdEncoding.EncodeToString([]byte{0, 1, 2})
	parts, err := userParts("look", []attachment{
		{Name: "a.png", Mime: "image/png", Data: img},
		{Name: "../n.txt", Mime: "text/plain", Data: txt},
		{Name: "b.bin", Mime: "application/octet-stream", Data: bin},
	}, dir)
	if err != nil {
		t.Fatal(err)
	}
	if parts[0].Text != "look" {
		t.Fatalf("message first, got %+v", parts[0])
	}
	if parts[1].InlineData == nil || parts[1].InlineData.MimeType != "image/png" {
		t.Fatalf("image should be inline data, got %+v", parts[1])
	}
	if !strings.Contains(parts[3].Text, "hello notes") {
		t.Fatalf("text file should be pasted, got %q", parts[3].Text)
	}
	if !strings.Contains(parts[4].Text, "b.bin") {
		t.Fatalf("binary should be named, got %q", parts[4].Text)
	}
	entries, _ := os.ReadDir(dir)
	if len(entries) != 3 {
		t.Fatalf("all three saved, got %d", len(entries))
	}
	for _, e := range entries {
		if strings.Contains(e.Name(), "..") {
			t.Fatalf("path escaped: %s", e.Name())
		}
	}
}

func TestUserPartsRejectsEmptyAndBadData(t *testing.T) {
	if _, err := userParts("  ", nil, ""); err == nil {
		t.Fatal("empty turn should fail")
	}
	if _, err := userParts("", []attachment{{Name: "x", Mime: "text/plain", Data: "%%%"}}, ""); err == nil {
		t.Fatal("bad base64 should fail")
	}
}
