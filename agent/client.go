package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// peerInfo is one row of a peer scan: what Tailscale knows (name, ip, online)
// joined with what the agent probe found (reachable, its /whoami).
type peerInfo struct {
	Name      string   `json:"name"`
	IP        string   `json:"ip"`
	Online    bool     `json:"online"`
	Reachable bool     `json:"reachable"`
	Platform  string   `json:"platform,omitempty"`
	Version   string   `json:"version,omitempty"`
	Caps      []string `json:"caps,omitempty"`
}

// scanPeers is the real peer discovery: tailscale reports who is up, then each
// peer's /whoami is probed to learn who actually runs an agent and what it takes.
func scanPeers(token string) ([]peerInfo, error) {
	st, err := tailscaleStatus()
	if err != nil {
		return nil, err
	}
	var out []peerInfo
	client := &http.Client{Timeout: 2 * time.Second}
	for _, p := range st.Peer {
		name := shortName(p.DNSName)
		ip := firstIPv4(p.TailscaleIPs)
		if name == "" || ip == "" {
			continue // tagged/shared nodes with no name or no IPv4 are not send targets
		}
		info := peerInfo{Name: name, IP: ip, Online: p.Online}
		if p.Online {
			if who, err := probeWhoAmI(client, ip); err == nil {
				info.Reachable = true
				info.Platform = who.Platform
				info.Version = who.Version
				info.Caps = who.Caps
			}
		}
		out = append(out, info)
	}
	return out, nil
}

// firstIPv4 returns the IPv4 address from a Tailscale node's IP list, which
// pairs an IPv4 and an IPv6; the agent talks IPv4.
func firstIPv4(ips []string) string {
	for _, ip := range ips {
		if !strings.Contains(ip, ":") {
			return ip
		}
	}
	return ""
}

func probeWhoAmI(client *http.Client, ip string) (*whoAmI, error) {
	url := fmt.Sprintf("http://%s:%d/whoami", ip, AgentPort)
	resp, err := client.Get(url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("whoami returned %d", resp.StatusCode)
	}
	var who whoAmI
	if err := json.NewDecoder(resp.Body).Decode(&who); err != nil {
		return nil, err
	}
	return &who, nil
}

// resolvePeer turns a device name into its tailnet IP. An IP passed straight
// through is accepted so a device that Tailscale has not surfaced still works.
func resolvePeer(name string) (string, error) {
	if strings.Count(name, ".") == 3 && !strings.ContainsAny(name, "abcdefghijklmnopqrstuvwxyz") {
		return name, nil // already an IPv4 literal
	}
	st, err := tailscaleStatus()
	if err != nil {
		return "", err
	}
	want := strings.ToLower(name)
	for _, p := range st.Peer {
		if strings.ToLower(shortName(p.DNSName)) == want || strings.EqualFold(p.HostName, name) {
			if ip := firstIPv4(p.TailscaleIPs); ip != "" {
				return ip, nil
			}
		}
	}
	return "", fmt.Errorf("no tailnet peer named %q (try `csync-agent peers`)", name)
}

// sendItem posts one payload to a peer's /send. kind is text|file|image; for
// text, payload is the literal text; otherwise it is a file path.
func sendItem(peerIP, token, from, kind, payload string) error {
	var body io.Reader
	var name string
	switch kind {
	case "text":
		body = strings.NewReader(payload)
		name = "text-" + time.Now().Format("20060102-150405") + ".txt"
	default:
		b, err := os.ReadFile(payload)
		if err != nil {
			return err
		}
		body = bytes.NewReader(b)
		name = filepath.Base(payload)
	}

	url := fmt.Sprintf("http://%s:%d/send", peerIP, AgentPort)
	req, err := http.NewRequest(http.MethodPost, url, body)
	if err != nil {
		return err
	}
	req.Header.Set("X-Csync-Token", token)
	req.Header.Set("X-Csync-From", from)
	req.Header.Set("X-Csync-Kind", kind)
	req.Header.Set("X-Csync-Name", name)
	req.Header.Set("Content-Type", "application/octet-stream")

	client := &http.Client{Timeout: 60 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	msg, _ := io.ReadAll(resp.Body)
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("peer refused (%d): %s", resp.StatusCode, strings.TrimSpace(string(msg)))
	}
	fmt.Printf("sent %s to %s: %s", kind, peerIP, msg)
	return nil
}
