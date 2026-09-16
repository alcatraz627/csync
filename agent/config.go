package main

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
)

// AgentPort is the fixed port every csync agent listens on across the tailnet.
// One well-known port keeps peer discovery a simple probe rather than a registry.
const AgentPort = 8790

// AgentVersion travels in /whoami so a peer can tell what contract it is talking to.
const AgentVersion = "0.1.0"

// configDir is where the shared mesh token lives, alongside csync's own state.
func configDir() string {
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".config", "csync")
}

func tokenPath() string { return filepath.Join(configDir(), "mesh.token") }

// inboxRoot is where received items land, one sub-folder per sending device.
func inboxRoot() string {
	if v := os.Getenv("CSYNC_INBOX"); v != "" {
		return v
	}
	home, _ := os.UserHomeDir()
	return filepath.Join(home, "csync", "inbox")
}

// loadOrCreateToken returns the shared secret, minting one on first run so a
// fresh device is usable without a manual step. The same value must be copied to
// every device you trust; that is the second gate on top of the tailnet.
func loadOrCreateToken() (string, error) {
	if b, err := os.ReadFile(tokenPath()); err == nil {
		t := strings.TrimSpace(string(b))
		if t != "" {
			return t, nil
		}
	}
	if err := os.MkdirAll(configDir(), 0o700); err != nil {
		return "", err
	}
	raw := make([]byte, 32)
	if _, err := rand.Read(raw); err != nil {
		return "", err
	}
	t := hex.EncodeToString(raw)
	if err := os.WriteFile(tokenPath(), []byte(t+"\n"), 0o600); err != nil {
		return "", err
	}
	return t, nil
}

// loadToken reads an existing token without creating one; senders must already
// share the receiver's secret, so a missing file here is a real error.
func loadToken() (string, error) {
	b, err := os.ReadFile(tokenPath())
	if err != nil {
		return "", fmt.Errorf("no mesh token at %s: run `csync-agent token` or copy it from another device", tokenPath())
	}
	t := strings.TrimSpace(string(b))
	if t == "" {
		return "", fmt.Errorf("mesh token at %s is empty", tokenPath())
	}
	return t, nil
}

// --- Tailscale is the source of truth for identity and reachability. ---

type tsPeer struct {
	DNSName      string   `json:"DNSName"`
	HostName     string   `json:"HostName"`
	TailscaleIPs []string `json:"TailscaleIPs"`
	Online       bool     `json:"Online"`
	OS           string   `json:"OS"`
}

type tsStatus struct {
	Self *tsPeer            `json:"Self"`
	Peer map[string]*tsPeer `json:"Peer"`
}

// tailscaleBin locates the Tailscale CLI, which is not always on a service's
// PATH (a macOS LaunchAgent, for one, gets a minimal PATH). PATH is tried first,
// then the usual install locations across platforms.
func tailscaleBin() string {
	if p, err := exec.LookPath("tailscale"); err == nil {
		return p
	}
	home, _ := os.UserHomeDir()
	for _, c := range []string{
		filepath.Join(home, ".local", "bin", "tailscale"),
		"/Applications/Tailscale.app/Contents/MacOS/Tailscale",
		"/usr/local/bin/tailscale",
		"/opt/homebrew/bin/tailscale",
		"/usr/bin/tailscale",
	} {
		if _, err := os.Stat(c); err == nil {
			return c
		}
	}
	return "tailscale"
}

func tailscaleStatus() (*tsStatus, error) {
	out, err := exec.Command(tailscaleBin(), "status", "--json").Output()
	if err != nil {
		return nil, fmt.Errorf("tailscale status failed (is Tailscale up?): %w", err)
	}
	var st tsStatus
	if err := json.Unmarshal(out, &st); err != nil {
		return nil, fmt.Errorf("parsing tailscale status: %w", err)
	}
	return &st, nil
}

// tailscaleIP returns this device's tailnet IPv4, the address the receiver binds
// to so it is reachable only over the tailnet, never on the LAN or the internet.
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

// shortName turns a MagicDNS name like "raspberrypi.tail905820.ts.net." into the
// bare device label a person recognises.
func shortName(dnsName string) string {
	s := strings.TrimSuffix(dnsName, ".")
	if i := strings.Index(s, "."); i > 0 {
		return s[:i]
	}
	return s
}

// selfName is this device's identity on the mesh: its tailnet label when we can
// read it, otherwise the OS hostname.
func selfName() string {
	if st, err := tailscaleStatus(); err == nil && st.Self != nil && st.Self.DNSName != "" {
		return shortName(st.Self.DNSName)
	}
	if h, err := os.Hostname(); err == nil {
		return h
	}
	return "unknown"
}

func platform() string { return runtime.GOOS }
