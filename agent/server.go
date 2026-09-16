package main

import (
	"crypto/subtle"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"
	"time"
)

// whoAmI is the identity + capability record a peer returns from /whoami. It is
// both the "who is this" answer and the liveness probe used by peer scanning.
type whoAmI struct {
	Name     string   `json:"name"`
	Platform string   `json:"platform"`
	Version  string   `json:"version"`
	Caps     []string `json:"caps"`
}

func localWhoAmI() whoAmI {
	return whoAmI{
		Name:     selfName(),
		Platform: platform(),
		Version:  AgentVersion,
		Caps:     []string{"text", "file", "image"},
	}
}

var safeName = regexp.MustCompile(`[^A-Za-z0-9._-]`)

// sanitize reduces an untrusted header value to a single safe path segment, so a
// sender cannot write outside the inbox via "../" or an absolute path.
func sanitize(s, fallback string) string {
	s = filepath.Base(strings.TrimSpace(s))
	s = safeName.ReplaceAllString(s, "_")
	if s == "" || s == "." || s == ".." {
		return fallback
	}
	return s
}

// serve starts the receiver bound to the tailnet IP. Binding to that address
// (not 0.0.0.0) is the first gate: the port exists only on the tailnet. The
// token check in each handler is the second.
func serve() error {
	token, err := loadOrCreateToken()
	if err != nil {
		return err
	}
	ip, err := tailscaleIP()
	if err != nil {
		return err
	}
	if err := os.MkdirAll(inboxRoot(), 0o755); err != nil {
		return err
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/whoami", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, localWhoAmI())
	})
	mux.HandleFunc("/peers", func(w http.ResponseWriter, r *http.Request) {
		if !authed(w, r, token) {
			return
		}
		peers, err := scanPeers(token)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadGateway)
			return
		}
		writeJSON(w, peers)
	})
	mux.HandleFunc("/send", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "POST only", http.StatusMethodNotAllowed)
			return
		}
		if !authed(w, r, token) {
			return
		}
		handleSend(w, r)
	})

	addr := fmt.Sprintf("%s:%d", ip, AgentPort)
	srv := &http.Server{
		Addr:              addr,
		Handler:           mux,
		ReadHeaderTimeout: 10 * time.Second,
	}
	log.Printf("csync-agent %s (%s/%s) listening on http://%s  inbox=%s",
		AgentVersion, selfName(), platform(), addr, inboxRoot())
	return srv.ListenAndServe()
}

// authed rejects a request whose token header does not match, in constant time.
func authed(w http.ResponseWriter, r *http.Request, token string) bool {
	got := r.Header.Get("X-Csync-Token")
	if subtle.ConstantTimeCompare([]byte(got), []byte(token)) == 1 {
		return true
	}
	http.Error(w, "unauthorized", http.StatusUnauthorized)
	return false
}

func handleSend(w http.ResponseWriter, r *http.Request) {
	from := sanitize(r.Header.Get("X-Csync-From"), "unknown")
	kind := strings.ToLower(strings.TrimSpace(r.Header.Get("X-Csync-Kind")))
	if kind == "" {
		kind = "file"
	}
	ts := time.Now().Format("20060102-150405")

	var name string
	switch kind {
	case "text":
		name = sanitize(r.Header.Get("X-Csync-Name"), "text-"+ts+".txt")
	default:
		name = sanitize(r.Header.Get("X-Csync-Name"), "item-"+ts)
	}

	dir := filepath.Join(inboxRoot(), from)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	dest := filepath.Join(dir, name)

	f, err := os.Create(dest)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	n, err := io.Copy(f, r.Body)
	f.Close()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Make a shared item instantly usable, not just filed: text lands on the
	// clipboard, and every arrival raises a desktop notification.
	if kind == "text" && runtime.GOOS == "darwin" {
		copyToClipboard(dest)
	}
	notify(fmt.Sprintf("csync: %s from %s", kind, from), name)

	log.Printf("received %s %q from %s (%d bytes) -> %s", kind, name, from, n, dest)
	writeJSON(w, map[string]any{"ok": true, "saved": dest, "bytes": n})
}

func writeJSON(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(v)
}

// copyToClipboard pipes a received text file to pbcopy (macOS only).
func copyToClipboard(path string) {
	b, err := os.ReadFile(path)
	if err != nil {
		return
	}
	cmd := exec.Command("pbcopy")
	in, err := cmd.StdinPipe()
	if err != nil {
		return
	}
	if err := cmd.Start(); err != nil {
		return
	}
	in.Write(b)
	in.Close()
	_ = cmd.Wait()
}

// notify raises a native desktop notification, best-effort per platform.
func notify(title, body string) {
	switch runtime.GOOS {
	case "darwin":
		script := fmt.Sprintf("display notification %q with title %q", body, title)
		_ = exec.Command("osascript", "-e", script).Run()
	case "linux":
		_ = exec.Command("notify-send", title, body).Run()
	}
}
