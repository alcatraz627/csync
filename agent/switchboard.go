package main

// The phone's window into Switchboard on this Mac: GET /switchboard/<tab> runs the
// installed app's headless --json export and passes it through, so a phone page shows
// exactly the rows the Mac panel draws.

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

// The list tabs Switchboard can export; anything else is refused before running it.
var switchboardTabs = map[string]bool{"library": true, "rules": true, "ledger": true, "plugins": true, "queue": true,
	"usage": true, "bulbs": true, "agents": true}

func switchboardBinary() string {
	if p := os.Getenv("CSYNC_SWITCHBOARD"); p != "" {
		return p
	}
	home, _ := os.UserHomeDir()
	return filepath.Join(home, "Applications", "Switchboard.app", "Contents", "MacOS", "Switchboard")
}

// switchboardCurrent reports whether the installed Switchboard knows the headless exports.
// A build from before them ignores the flags and launches as a second app, which once
// displaced the owner's running one, so look for the export in the binary first.
func switchboardCurrent(marker string) bool {
	path := switchboardBinary()
	info, err := os.Stat(path)
	if err != nil {
		return false
	}
	key := markerKey{path, info.ModTime().UnixNano(), info.Size(), marker}
	markerMu.Lock()
	found, seen := markerSeen[key]
	markerMu.Unlock()
	if seen {
		return found
	}
	bin, err := os.ReadFile(path)
	if err != nil {
		return false
	}
	found = bytes.Contains(bin, []byte(marker))
	markerMu.Lock()
	markerSeen[key] = found
	markerMu.Unlock()
	return found
}

// The binary is scanned once per version (path, mtime, size, marker), not once per request.
type markerKey struct {
	path   string
	mtime  int64
	size   int64
	marker string
}

var (
	markerMu   sync.Mutex
	markerSeen = map[markerKey]bool{}
)

func handleSwitchboard(w http.ResponseWriter, r *http.Request) {
	tab := strings.TrimPrefix(r.URL.Path, "/switchboard/")
	if tab == "act" {
		handleSwitchboardAct(w, r)
		return
	}
	if !switchboardTabs[tab] {
		http.Error(w, `{"error":"no such Switchboard tab"}`, http.StatusNotFound)
		return
	}
	args := []string{"--json", tab}
	q := r.URL.Query()
	for _, k := range []string{"group", "offset", "limit"} {
		if v := q.Get(k); v != "" {
			args = append(args, "--"+k, v)
		}
	}
	// the phone's own tabs came later than --json, so they need a build that has them
	marker := "no list tab named"
	if tab == "usage" || tab == "bulbs" || tab == "agents" {
		marker = "needs a --value"
	}
	if !switchboardCurrent(marker) {
		http.Error(w, `{"error":"Switchboard on this Mac is too old to share this tab; update it"}`, http.StatusConflict)
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 20*time.Second)
	defer cancel()
	out, err := exec.CommandContext(ctx, switchboardBinary(), args...).Output()
	if err != nil {
		http.Error(w, `{"error":"Switchboard did not answer on this Mac"}`, http.StatusBadGateway)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	_, _ = w.Write(out)
}

// handleSwitchboardAct presses one row's button on the Mac, for the phone: POST {tab, key,
// button, confirmed}. Switchboard's own answer (ok, a failure line, or a question to confirm)
// goes back as is, so the phone shows the Mac's words.
func handleSwitchboardAct(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, `{"error":"POST only"}`, http.StatusMethodNotAllowed)
		return
	}
	var ask struct {
		Tab, Key, Button string
		Value            string // the line a brightness or colour button asks for
		Confirmed        bool
	}
	if err := json.NewDecoder(io.LimitReader(r.Body, 64<<10)).Decode(&ask); err != nil || ask.Key == "" {
		http.Error(w, `{"error":"send tab, key and button"}`, http.StatusBadRequest)
		return
	}
	if len(ask.Value) > 64 {
		http.Error(w, `{"error":"value is too long"}`, http.StatusBadRequest)
		return
	}
	if !switchboardTabs[ask.Tab] {
		http.Error(w, `{"error":"no such Switchboard tab"}`, http.StatusNotFound)
		return
	}
	if !switchboardCurrent("no longer on the Mac; refresh the list") {
		http.Error(w, `{"error":"Switchboard on this Mac is too old to act from the phone; update it"}`, http.StatusConflict)
		return
	}
	if ask.Value != "" && !switchboardCurrent("needs a --value") {
		http.Error(w, `{"error":"Switchboard on this Mac is too old to take a value from the phone; update it"}`, http.StatusConflict)
		return
	}
	args := []string{"--act", ask.Tab, "--key", ask.Key}
	if ask.Button != "" {
		args = append(args, "--button", ask.Button)
	}
	if ask.Value != "" {
		args = append(args, "--value", ask.Value)
	}
	if ask.Confirmed {
		args = append(args, "--confirmed")
	}
	// A phone that drops the connection must not kill the action half way: the parent keeps
	// the request's values but not its cancellation; the timeout still bounds the run.
	ctx, cancel := context.WithTimeout(context.WithoutCancel(r.Context()), 30*time.Second)
	defer cancel()
	// Switchboard exits non-zero for a refusal or a failed button but still prints its answer.
	out, _ := exec.CommandContext(ctx, switchboardBinary(), args...).Output()
	if !json.Valid(out) {
		http.Error(w, `{"error":"Switchboard did not answer on this Mac"}`, http.StatusBadGateway)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	_, _ = w.Write(out)
}
