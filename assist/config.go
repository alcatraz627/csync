package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
)

// AssistPort is the fixed tailnet port the assistant listens on, one above the
// mesh agent's 8790 so both can run on the same device.
const AssistPort = 8791

const defaultModel = "gemini-flash-latest"

func configDir() string {
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".config", "csync")
}

// geminiKey is the API key, kept on this device only (never on the phone). The
// file may hold the raw key or a KEY=value line (e.g. GEMINI_API_KEY=...); both
// are accepted, and surrounding quotes are stripped.
func geminiKey() (string, error) {
	p := filepath.Join(configDir(), "gemini.key")
	b, err := os.ReadFile(p)
	if err != nil {
		return "", fmt.Errorf("no Gemini key at %s: write your key there, then restart", p)
	}
	k := strings.TrimSpace(string(b))
	if i := strings.Index(k, "="); i >= 0 && !strings.Contains(k[:i], " ") {
		k = strings.TrimSpace(k[i+1:]) // drop a leading GEMINI_API_KEY= style prefix
	}
	k = strings.Trim(k, "\"'")
	if k == "" {
		return "", fmt.Errorf("Gemini key at %s is empty", p)
	}
	return k, nil
}

// model resolves the Gemini model id: a gemini.model file, then env, then default.
func model() string {
	if b, err := os.ReadFile(filepath.Join(configDir(), "gemini.model")); err == nil {
		if m := strings.TrimSpace(string(b)); m != "" {
			return m
		}
	}
	if m := strings.TrimSpace(os.Getenv("CSYNC_GEMINI_MODEL")); m != "" {
		return m
	}
	return defaultModel
}

// systemPrompt is the assistant's persona, overridable via assist.prompt.
func systemPrompt() string {
	if b, err := os.ReadFile(filepath.Join(configDir(), "assist.prompt")); err == nil {
		if s := strings.TrimSpace(string(b)); s != "" {
			return s
		}
	}
	return "You are csync, a personal assistant running on " + selfName() +
		", a home server reachable over the owner's private Tailscale network. " +
		"Be concise, direct, and practical. When you are unsure, say so."
}

// meshToken is the shared secret, the same file the mesh agent uses, so a phone
// already on the mesh needs no new credential to chat.
func meshToken() (string, error) {
	b, err := os.ReadFile(filepath.Join(configDir(), "mesh.token"))
	if err != nil {
		return "", fmt.Errorf("no mesh token at %s", filepath.Join(configDir(), "mesh.token"))
	}
	t := strings.TrimSpace(string(b))
	if t == "" {
		return "", fmt.Errorf("mesh token is empty")
	}
	return t, nil
}

func tailscaleBin() string {
	if p, err := exec.LookPath("tailscale"); err == nil {
		return p
	}
	home, _ := os.UserHomeDir()
	for _, c := range []string{
		filepath.Join(home, ".local", "bin", "tailscale"),
		"/Applications/Tailscale.app/Contents/MacOS/Tailscale",
		"/usr/local/bin/tailscale", "/opt/homebrew/bin/tailscale", "/usr/bin/tailscale",
	} {
		if _, err := os.Stat(c); err == nil {
			return c
		}
	}
	return "tailscale"
}

func tailscaleIP() (string, error) {
	out, err := exec.Command(tailscaleBin(), "ip", "-4").Output()
	if err != nil {
		return "", fmt.Errorf("tailscale ip -4 failed (is Tailscale up?): %w", err)
	}
	ip := strings.TrimSpace(string(out))
	if ip == "" {
		return "", fmt.Errorf("tailscale returned no IPv4 address")
	}
	return ip, nil
}

func selfName() string {
	out, err := exec.Command(tailscaleBin(), "status", "--json").Output()
	if err == nil {
		var st struct {
			Self struct {
				DNSName string `json:"DNSName"`
			} `json:"Self"`
		}
		if err := json.Unmarshal(out, &st); err == nil && st.Self.DNSName != "" {
			s := strings.TrimSuffix(st.Self.DNSName, ".")
			if i := strings.Index(s, "."); i > 0 {
				return s[:i]
			}
			return s
		}
	}
	if h, err := os.Hostname(); err == nil {
		return h
	}
	return "assist"
}

func platform() string { return runtime.GOOS }
