package main

import (
	"encoding/json"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"time"
)

// The owner's phone sends a "what slows this phone" report whenever its process monitor runs
// one. The Pi keeps only the latest, so the assistant can answer questions about phone lag from
// the same facts the owner saw, and say how old they are.

func phoneDiagnosticsPath() string {
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".local", "state", "csync", "phone-diagnostics.json")
}

func phoneRoutes(mux *http.ServeMux, token string) {
	mux.HandleFunc("/phone/diagnostics", func(w http.ResponseWriter, r *http.Request) {
		if !authed(w, r, token) {
			return
		}
		if r.Method == http.MethodGet {
			writeJSON(w, phoneDiagnostics())
			return
		}
		if r.Method != http.MethodPost {
			http.Error(w, "GET or POST", http.StatusMethodNotAllowed)
			return
		}
		body, err := io.ReadAll(io.LimitReader(r.Body, 256<<10))
		var report map[string]any
		if err != nil || json.Unmarshal(body, &report) != nil {
			http.Error(w, "need the report as JSON", http.StatusBadRequest)
			return
		}
		report["received_at"] = time.Now().UTC().Format(time.RFC3339)
		encoded, _ := json.MarshalIndent(report, "", "  ")
		path := phoneDiagnosticsPath()
		_ = os.MkdirAll(filepath.Dir(path), 0o700)
		if err := os.WriteFile(path, encoded, 0o600); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		writeJSON(w, map[string]any{"ok": true})
	})
}

// phoneDiagnostics returns the latest report with its age, or says how to get one.
func phoneDiagnostics() map[string]any {
	data, err := os.ReadFile(phoneDiagnosticsPath())
	if err != nil {
		return map[string]any{"code": "NO_REPORT", "error": "the phone has not sent a report yet",
			"how": "ask the owner to open More > Process monitor in the csync app and tap Find what slows this phone"}
	}
	var report map[string]any
	if json.Unmarshal(data, &report) != nil {
		return map[string]any{"code": "REPORT_INVALID", "error": "the saved report could not be read"}
	}
	if at, err := time.Parse(time.RFC3339, str(report["received_at"])); err == nil {
		age := time.Since(at).Round(time.Minute)
		report["age_minutes"] = int(age.Minutes())
		if age > 30*time.Minute {
			report["stale"] = "older than 30 minutes; ask the owner to tap Find what slows this phone again for fresh readings"
		}
	}
	return report
}
