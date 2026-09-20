package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// functionResponseRole is the role a tool result is replayed under. Gemini's
// valid content roles are "user" and "model"; a tool result rides as "user".
const functionResponseRole = "user"

// toolDeclarations is the toolset offered to the model. Read-only tools plus a
// mesh send; run_command is declared but gated (see runCommand).
func toolDeclarations() []gTool {
	return []gTool{{FunctionDeclarations: []gFuncDecl{
		{
			Name:        "home_health",
			Description: "Report this home server's health: disk, memory, uptime, load, and whether key services (tailscale, jellyfin, ssh) are running. No arguments.",
			Parameters:  gSchema{Type: "object", Properties: map[string]gSchema{}},
		},
		{
			Name:        "list_peers",
			Description: "List the owner's devices on the Tailscale network and whether each is online. No arguments.",
			Parameters:  gSchema{Type: "object", Properties: map[string]gSchema{}},
		},
		{
			Name:        "send_to_peer",
			Description: "Send a short text message to one of the owner's devices, delivered to its csync inbox and clipboard.",
			Parameters: gSchema{
				Type: "object",
				Properties: map[string]gSchema{
					"peer": {Type: "string", Description: "device name, e.g. aakarshs-m5-pro"},
					"text": {Type: "string", Description: "the message to deliver"},
				},
				Required: []string{"peer", "text"},
			},
		},
		{
			Name:        "run_command",
			Description: "Run a shell command on this home server and return its output. May be disabled by the owner; if so it returns an error saying so.",
			Parameters: gSchema{
				Type: "object",
				Properties: map[string]gSchema{
					"command": {Type: "string", Description: "the shell command to run"},
				},
				Required: []string{"command"},
			},
		},
		{
			Name:        "camera",
			Description: "Use this home server's camera. action=status detects the camera and reports whether one is attached; action=capture takes a photo; action=record films a short clip (duration_seconds, default 5). Photos and clips are saved and returned with a media_url the app shows inline.",
			Parameters: gSchema{
				Type: "object",
				Properties: map[string]gSchema{
					"action":           {Type: "string", Description: "status, capture, or record"},
					"duration_seconds": {Type: "integer", Description: "clip length for record, 1 to 120"},
				},
				Required: []string{"action"},
			},
		},
		{
			Name:        "send_image",
			Description: "Share an image or video file that already exists on this home server into the chat, returned as a media_url the app shows inline.",
			Parameters: gSchema{
				Type: "object",
				Properties: map[string]gSchema{
					"path": {Type: "string", Description: "absolute path to the image or video file"},
				},
				Required: []string{"path"},
			},
		},
		{
			Name:        "top_processes",
			Description: "List the heaviest processes on this home server. by=cpu (default) or by=mem.",
			Parameters: gSchema{
				Type: "object",
				Properties: map[string]gSchema{
					"by": {Type: "string", Description: "cpu or mem"},
				},
			},
		},
		{
			Name:        "pi_vitals",
			Description: "Report this Raspberry Pi's temperature, throttling state, CPU clock, and core voltage. No arguments.",
			Parameters:  gSchema{Type: "object", Properties: map[string]gSchema{}},
		},
	}}}
}

// executeTool runs one tool and returns a response map. It never throws; a
// failure comes back as {"error": ...} so the model can react.
func executeTool(name string, args map[string]any) map[string]any {
	log.Printf("tool %s args=%v", name, args)
	switch name {
	case "home_health":
		return map[string]any{"report": homeHealth()}
	case "list_peers":
		return map[string]any{"peers": peerList()}
	case "send_to_peer":
		return sendToPeer(str(args["peer"]), str(args["text"]))
	case "run_command":
		return runCommand(str(args["command"]))
	case "camera":
		return cameraTool(str(args["action"]), argStr(args, "duration_seconds"))
	case "send_image":
		return sendImage(str(args["path"]))
	case "top_processes":
		return topProcesses(str(args["by"]))
	case "pi_vitals":
		return piVitals()
	default:
		return map[string]any{"error": "unknown tool " + name}
	}
}

func str(v any) string {
	if s, ok := v.(string); ok {
		return s
	}
	return ""
}

func sh(cmd string) string {
	out, err := exec.Command("sh", "-c", cmd).CombinedOutput()
	s := strings.TrimSpace(string(out))
	if err != nil && s == "" {
		return "(" + err.Error() + ")"
	}
	return s
}

func homeHealth() string {
	var b strings.Builder
	b.WriteString("disk /: " + sh("df -h / | awk 'NR==2{print $3\" used of \"$2\" (\"$5\")\"}'") + "\n")
	b.WriteString("memory: " + sh("free -h | awk 'NR==2{print $3\" used of \"$2}'") + "\n")
	b.WriteString("uptime: " + sh("uptime -p") + "\n")
	b.WriteString("load: " + sh("cut -d' ' -f1-3 /proc/loadavg") + "\n")
	for _, svc := range []string{"tailscaled", "ssh", "jellyfin"} {
		b.WriteString(svc + ": " + sh("systemctl is-active "+svc+" 2>/dev/null || echo unknown") + "\n")
	}
	return strings.TrimSpace(b.String())
}

func peerList() string {
	st, err := tailscaleStatusForTools()
	if err != nil {
		return "error: " + err.Error()
	}
	var b strings.Builder
	for _, p := range st {
		state := "offline"
		if p.online {
			state = "online"
		}
		b.WriteString(p.name + " (" + state + ")\n")
	}
	if b.Len() == 0 {
		return "no peers"
	}
	return strings.TrimSpace(b.String())
}

type toolPeer struct {
	name   string
	online bool
}

func tailscaleStatusForTools() ([]toolPeer, error) {
	out, err := exec.Command(tailscaleBin(), "status", "--json").Output()
	if err != nil {
		return nil, err
	}
	var st struct {
		Peer map[string]struct {
			DNSName string `json:"DNSName"`
			Online  bool   `json:"Online"`
		} `json:"Peer"`
	}
	if err := json.Unmarshal(out, &st); err != nil {
		return nil, err
	}
	var peers []toolPeer
	for _, p := range st.Peer {
		name := strings.TrimSuffix(p.DNSName, ".")
		if i := strings.Index(name, "."); i > 0 {
			name = name[:i]
		}
		if name != "" {
			peers = append(peers, toolPeer{name: name, online: p.Online})
		}
	}
	return peers, nil
}

// sendToPeer delivers text to a peer's mesh agent by MagicDNS name.
func sendToPeer(peer, text string) map[string]any {
	if peer == "" || text == "" {
		return map[string]any{"error": "peer and text are required"}
	}
	token, err := meshToken()
	if err != nil {
		return map[string]any{"error": err.Error()}
	}
	url := fmt.Sprintf("http://%s:8790/send", peer)
	req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader([]byte(text)))
	if err != nil {
		return map[string]any{"error": err.Error()}
	}
	req.Header.Set("X-Csync-Token", token)
	req.Header.Set("X-Csync-From", selfName())
	req.Header.Set("X-Csync-Kind", "text")
	req.Header.Set("X-Csync-Name", "from-assistant.txt")
	client := &http.Client{Timeout: 15 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return map[string]any{"error": "could not reach " + peer + ": " + err.Error()}
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return map[string]any{"error": fmt.Sprintf("%s refused (%d)", peer, resp.StatusCode)}
	}
	return map[string]any{"ok": true, "delivered_to": peer}
}

// runCommand executes a shell command, but only when the owner has enabled it by
// creating the flag file. This keeps phone-triggered shell off by default.
func runCommand(command string) map[string]any {
	if command == "" {
		return map[string]any{"error": "command is required"}
	}
	flag := filepath.Join(configDir(), "assist.allow_exec")
	if _, err := os.Stat(flag); err != nil {
		return map[string]any{"error": "run_command is disabled. The owner can enable it by creating " + flag + " on this device."}
	}
	out, err := exec.Command("sh", "-c", command).CombinedOutput()
	res := map[string]any{"output": truncate(strings.TrimSpace(string(out)), 4000)}
	if err != nil {
		res["exit_error"] = err.Error()
	}
	return res
}
