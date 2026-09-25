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
			Description: "Use the same Pi camera service as the app's Camera tab. action=status reports live viewing and recording; action=capture saves a photo; action=record films a short clip (duration_seconds, default 5). Photos and clips appear in the app and return a media_url here.",
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
			Name:        "send_file",
			Description: "Share any file on this home server into the chat (image, video, pdf, code, markdown, text, or other), returned as a media_url the app shows or opens.",
			Parameters: gSchema{
				Type: "object",
				Properties: map[string]gSchema{
					"path": {Type: "string", Description: "absolute path to the file"},
				},
				Required: []string{"path"},
			},
		},
		{
			Name:        "list_skills",
			Description: "List the saved skills (reusable prompts) on this home server. No arguments.",
			Parameters:  gSchema{Type: "object", Properties: map[string]gSchema{}},
		},
		{
			Name:        "load_skill",
			Description: "Load a saved skill's text by name so you can follow it. Create a skill by writing a .md file into the skills dir with run_command.",
			Parameters: gSchema{
				Type: "object",
				Properties: map[string]gSchema{
					"name": {Type: "string", Description: "the skill name (filename without .md)"},
				},
				Required: []string{"name"},
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
		{
			Name: "media_drives", Description: "List connected and absent media drives, with their observed status.",
			Parameters: gSchema{Type: "object", Properties: map[string]gSchema{}},
		},
		{
			Name: "media_search", Description: "Find media by file name across connected drives.",
			Parameters: gSchema{Type: "object", Properties: map[string]gSchema{
				"query": {Type: "string", Description: "part of a file name"},
			}, Required: []string{"query"}},
		},
		{
			Name: "media_status", Description: "Read observed playback state for the Pi or active phone player.",
			Parameters: gSchema{Type: "object", Properties: map[string]gSchema{
				"target": {Type: "string", Description: "pi or phone"},
			}, Required: []string{"target"}},
		},
		{
			Name: "media_play", Description: "Play a media_search item on the Pi projector. Reports applied only after the Pi player accepts the command.",
			Parameters: gSchema{Type: "object", Properties: map[string]gSchema{
				"item_id": {Type: "string", Description: "opaque item ID from media_search"},
			}, Required: []string{"item_id"}},
		},
		{
			Name: "media_cast_youtube", Description: "Play one YouTube video on the Pi projector, starting muted. Uses the same player and controls as the Media screen.",
			Parameters: gSchema{Type: "object", Properties: map[string]gSchema{
				"url": {Type: "string", Description: "HTTPS YouTube watch, Shorts, live, or youtu.be video URL"},
			}, Required: []string{"url"}},
		},
		{
			Name: "media_pause", Description: "Pause playback on the Pi or active phone. Phone commands may remain queued until the app acknowledges them.",
			Parameters: gSchema{Type: "object", Properties: map[string]gSchema{
				"target": {Type: "string", Description: "pi or phone"},
			}, Required: []string{"target"}},
		},
		{
			Name: "media_seek", Description: "Seek in the Pi or active phone player; phone application is acknowledged asynchronously.",
			Parameters: gSchema{Type: "object", Properties: map[string]gSchema{
				"target":      {Type: "string", Description: "pi or phone"},
				"position_ms": {Type: "integer", Description: "absolute position in milliseconds"},
			}, Required: []string{"target", "position_ms"}},
		},
		{
			Name: "media_resume", Description: "Resume the Pi or active phone player.",
			Parameters: gSchema{Type: "object", Properties: map[string]gSchema{
				"target": {Type: "string", Description: "pi or phone"},
			}, Required: []string{"target"}},
		},
		{
			Name: "media_stop", Description: "Stop playback on the Pi or active phone.",
			Parameters: gSchema{Type: "object", Properties: map[string]gSchema{
				"target": {Type: "string", Description: "pi or phone"},
			}, Required: []string{"target"}},
		},
		{
			Name: "media_volume", Description: "Set player volume from 0 to 100 on the Pi or active phone.",
			Parameters: gSchema{Type: "object", Properties: map[string]gSchema{
				"target": {Type: "string", Description: "pi or phone"},
				"value":  {Type: "number", Description: "volume from 0 to 100"},
			}, Required: []string{"target", "value"}},
		},
		{
			Name: "media_speed", Description: "Set player speed from 0.25 to 4 on the Pi or active phone.",
			Parameters: gSchema{Type: "object", Properties: map[string]gSchema{
				"target": {Type: "string", Description: "pi or phone"},
				"value":  {Type: "number", Description: "speed from 0.25 to 4"},
			}, Required: []string{"target", "value"}},
		},
		{
			Name: "media_diagnose", Description: "Check media service, drives, Pi power, and HDMI observations even if the media service is down.",
			Parameters: gSchema{Type: "object", Properties: map[string]gSchema{}},
		},
	}}}
}

// executeTool runs one tool and returns a response map. It never throws; a
// failure comes back as {"error": ...} so the model can react.
func executeTool(name string, args map[string]any) map[string]any {
	if name == "media_cast_youtube" {
		log.Printf("tool %s", name)
	} else {
		log.Printf("tool %s args=%v", name, args)
	}
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
	case "send_file", "send_image":
		return sendFile(str(args["path"]))
	case "list_skills":
		return listSkills()
	case "load_skill":
		return loadSkill(str(args["name"]))
	case "top_processes":
		return topProcesses(str(args["by"]))
	case "pi_vitals":
		return piVitals()
	case "media_drives":
		return mediaGet("/v1/drives")
	case "media_search":
		return mediaSearch(str(args["query"]))
	case "media_status":
		return mediaStatus(str(args["target"]))
	case "media_play":
		return mediaCommand("pi", "play", str(args["item_id"]), 0)
	case "media_cast_youtube":
		return mediaCastYouTube(str(args["url"]))
	case "media_pause":
		return mediaCommand(str(args["target"]), "pause", "", 0)
	case "media_seek":
		return mediaCommand(str(args["target"]), "seek", "", args["position_ms"])
	case "media_resume":
		return mediaCommand(str(args["target"]), "resume", "", 0)
	case "media_stop":
		return mediaCommand(str(args["target"]), "stop", "", 0)
	case "media_volume":
		return mediaCommand(str(args["target"]), "volume", "", args["value"])
	case "media_speed":
		return mediaCommand(str(args["target"]), "speed", "", args["value"])
	case "media_diagnose":
		return mediaDiagnose()
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
