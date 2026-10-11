package main

// The phone's window into Switchboard on this Mac: GET /switchboard/<tab> runs the
// installed app's headless --json export and passes it through, so a phone page shows
// exactly the rows the Mac panel draws.

import (
	"bytes"
	"context"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// The list tabs Switchboard can export; anything else is refused before running it.
var switchboardTabs = map[string]bool{"library": true, "rules": true, "ledger": true, "plugins": true, "queue": true}

func switchboardBinary() string {
	if p := os.Getenv("CSYNC_SWITCHBOARD"); p != "" {
		return p
	}
	home, _ := os.UserHomeDir()
	return filepath.Join(home, "Applications", "Switchboard.app", "Contents", "MacOS", "Switchboard")
}

func handleSwitchboard(w http.ResponseWriter, r *http.Request) {
	tab := strings.TrimPrefix(r.URL.Path, "/switchboard/")
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
	// a Switchboard built before --json ignores the flag and launches as a second app,
	// which displaced the owner's running one once; look for the export in the binary first
	if bin, err := os.ReadFile(switchboardBinary()); err != nil || !bytes.Contains(bin, []byte("no list tab named")) {
		http.Error(w, `{"error":"Switchboard on this Mac is too old to share its tabs; update it"}`, http.StatusConflict)
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
