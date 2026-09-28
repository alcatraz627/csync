package main

import (
	"encoding/base64"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// An attachment is a file the phone sends along with a chat message: a photo,
// a document, anything the owner picked from the + drawer.
type attachment struct {
	Name string `json:"name"`
	Mime string `json:"mime"`
	Data string `json:"data"` // base64
}

const (
	maxInlineBytes = 8 << 20   // images and PDFs the model reads directly
	maxTextBytes   = 200 << 10 // text files pasted into the prompt
)

// userParts turns a message and its attachments into the parts of one user
// turn. Images and PDFs go to the model as inline data, small text files as
// text, and anything else as a note naming the saved copy. Every attachment is
// also saved to the media folder so tools can find it later.
func userParts(message string, atts []attachment, saveDir string) ([]gPart, error) {
	var parts []gPart
	if strings.TrimSpace(message) != "" {
		parts = append(parts, gPart{Text: message})
	}
	for _, a := range atts {
		raw, err := base64.StdEncoding.DecodeString(a.Data)
		if err != nil {
			return nil, fmt.Errorf("attachment %q is not valid base64", a.Name)
		}
		name := filepath.Base(a.Name)
		if name == "." || name == "/" || name == "" {
			name = "attachment"
		}
		saved := time.Now().Format("20060102-150405") + "-" + name
		if saveDir != "" {
			if err := os.WriteFile(filepath.Join(saveDir, saved), raw, 0o644); err != nil {
				return nil, fmt.Errorf("could not save %q: %v", name, err)
			}
		}
		mime := strings.ToLower(a.Mime)
		switch {
		case strings.HasPrefix(mime, "image/") || mime == "application/pdf":
			if len(raw) > maxInlineBytes {
				parts = append(parts, gPart{Text: fmt.Sprintf("[%s is too large to show the model; saved as %s]", name, saved)})
				continue
			}
			parts = append(parts, gPart{InlineData: &gBlob{MimeType: mime, Data: a.Data}})
			parts = append(parts, gPart{Text: fmt.Sprintf("[attached %s, saved as %s]", name, saved)})
		case strings.HasPrefix(mime, "text/") || mime == "application/json":
			body := string(raw)
			if len(raw) > maxTextBytes {
				body = string(raw[:maxTextBytes]) + "\n[truncated]"
			}
			parts = append(parts, gPart{Text: fmt.Sprintf("File %s (saved as %s):\n%s", name, saved, body)})
		default:
			parts = append(parts, gPart{Text: fmt.Sprintf("[attached %s (%s), saved as %s]", name, mime, saved)})
		}
	}
	if len(parts) == 0 {
		return nil, fmt.Errorf("need a message or an attachment")
	}
	return parts, nil
}
