package main

import (
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

// mediaDir is the single place captures and shared files live, created on demand.
// The /media endpoint serves files from here so the app can show them inline.
func mediaDir() string {
	home, _ := os.UserHomeDir()
	d := filepath.Join(home, "csync-media")
	_ = os.MkdirAll(d, 0o755)
	return d
}

// argStr reads a tool argument as a string even when the model sent a number.
func argStr(args map[string]any, key string) string {
	v, ok := args[key]
	if !ok || v == nil {
		return ""
	}
	if s, ok := v.(string); ok {
		return s
	}
	if f, ok := v.(float64); ok {
		return strconv.FormatFloat(f, 'f', -1, 64)
	}
	return fmt.Sprintf("%v", v)
}

func cameraBin(still bool) string {
	names := []string{"rpicam-still", "libcamera-still"}
	if !still {
		names = []string{"rpicam-vid", "libcamera-vid"}
	}
	for _, n := range names {
		if p, err := exec.LookPath(n); err == nil {
			return p
		}
	}
	return ""
}

// cameraPresent asks the still tool to list cameras and reads whether one is wired.
func cameraPresent() bool {
	bin := cameraBin(true)
	if bin == "" {
		return false
	}
	out, _ := exec.Command(bin, "--list-cameras").CombinedOutput()
	s := strings.ToLower(string(out))
	return !strings.Contains(s, "no cameras available")
}

// cameraTool detects the camera, reports status, or captures a still or a clip.
// Captures land in mediaDir and return a media_url the app renders inline.
func cameraTool(action, durationSec string) map[string]any {
	switch strings.ToLower(strings.TrimSpace(action)) {
	case "", "status", "detect":
		result := mediaGet("/v1/camera/status")
		result["present"] = cameraPresent()
		return result
	case "capture", "photo", "image":
		result := mediaRequest(http.MethodPost, "/v1/camera/photo", map[string]any{}, 15*time.Second)
		if name, ok := result["name"].(string); ok {
			result["media_url"] = "/media/" + name
			result["media_type"] = "image"
		}
		return result
	case "record", "video":
		secs := 5
		if d, err := strconv.Atoi(strings.TrimSpace(durationSec)); err == nil && d > 0 && d <= 120 {
			secs = d
		}
		result := mediaRequest(http.MethodPost, "/v1/camera/record/clip",
			map[string]any{"durationSeconds": secs}, time.Duration(secs+125)*time.Second)
		if name, ok := result["name"].(string); ok {
			result["media_url"] = "/media/" + name
			result["media_type"] = "video"
			result["seconds"] = secs
		}
		return result
	default:
		return map[string]any{"error": "unknown camera action " + action + " (use status, capture, or record)"}
	}
}

// sendFile shares any existing file into the chat by staging it in mediaDir and
// returning a media_url and a media_type the app renders or offers to open.
func sendFile(path string) map[string]any {
	if strings.TrimSpace(path) == "" {
		return map[string]any{"error": "path is required"}
	}
	info, err := os.Stat(path)
	if err != nil || info.IsDir() {
		return map[string]any{"error": "no such file: " + path}
	}
	ext := strings.ToLower(filepath.Ext(path))
	name := time.Now().Format("150405") + "-" + filepath.Base(path)
	b, err := os.ReadFile(path)
	if err != nil {
		return map[string]any{"error": "could not read file: " + err.Error()}
	}
	if err := os.WriteFile(filepath.Join(mediaDir(), name), b, 0o644); err != nil {
		return map[string]any{"error": "could not stage file: " + err.Error()}
	}
	return map[string]any{"ok": true, "media_url": "/media/" + name, "media_type": fileType(ext), "filename": filepath.Base(path)}
}

func fileType(ext string) string {
	switch strings.TrimPrefix(strings.ToLower(ext), ".") {
	case "jpg", "jpeg", "png", "gif", "webp", "bmp":
		return "image"
	case "mp4", "mov", "h264", "webm", "mkv":
		return "video"
	case "pdf":
		return "pdf"
	case "md", "markdown":
		return "markdown"
	case "txt", "log", "json", "yaml", "yml", "toml", "xml", "csv", "conf", "ini", "env",
		"sh", "bash", "py", "js", "ts", "java", "kt", "go", "c", "h", "cpp", "rs", "html", "css":
		return "text"
	default:
		return "file"
	}
}

// skillsDir holds simple reusable prompts the model can list and load. The model
// creates a skill by writing a .md file here (via run_command) and uses it by
// loading its text back.
func skillsDir() string {
	d := filepath.Join(configDir(), "skills")
	_ = os.MkdirAll(d, 0o755)
	return d
}

func firstNonEmptyLine(s string) string {
	for _, l := range strings.Split(s, "\n") {
		l = strings.TrimSpace(strings.TrimLeft(l, "# "))
		if l != "" {
			return l
		}
	}
	return ""
}

func listSkills() map[string]any {
	entries, err := os.ReadDir(skillsDir())
	if err != nil {
		return map[string]any{"skills": []any{}, "dir": skillsDir()}
	}
	skills := []map[string]any{}
	for _, e := range entries {
		if e.IsDir() || !strings.HasSuffix(e.Name(), ".md") {
			continue
		}
		desc := ""
		if b, err := os.ReadFile(filepath.Join(skillsDir(), e.Name())); err == nil {
			desc = firstNonEmptyLine(string(b))
		}
		skills = append(skills, map[string]any{"name": strings.TrimSuffix(e.Name(), ".md"), "summary": truncate(desc, 200)})
	}
	return map[string]any{"skills": skills, "dir": skillsDir()}
}

func loadSkill(name string) map[string]any {
	name = strings.TrimSuffix(strings.TrimSpace(name), ".md")
	if name == "" || strings.ContainsAny(name, "/\\") {
		return map[string]any{"error": "give a plain skill name"}
	}
	b, err := os.ReadFile(filepath.Join(skillsDir(), name+".md"))
	if err != nil {
		return map[string]any{"error": "no skill named " + name + " (create one by writing " + filepath.Join(skillsDir(), name+".md") + ")"}
	}
	return map[string]any{"name": name, "content": string(b)}
}

// topProcesses lists the heaviest processes by cpu or memory.
func topProcesses(by string) map[string]any {
	sortKey := "-%cpu"
	if strings.HasPrefix(strings.ToLower(by), "mem") {
		sortKey = "-%mem"
	}
	out := sh("ps -eo pid,comm,%cpu,%mem --sort=" + sortKey + " | head -n 11")
	return map[string]any{"processes": out, "sorted_by": strings.TrimPrefix(sortKey, "-")}
}

// piVitals reports the Pi's temperature, throttling, clock, and voltage.
func piVitals() map[string]any {
	return map[string]any{
		"temperature": strings.TrimPrefix(sh("vcgencmd measure_temp"), "temp="),
		"throttled":   sh("vcgencmd get_throttled"),
		"arm_clock":   sh("vcgencmd measure_clock arm | awk -F= '{if($2)print $2/1000000\" MHz\"}'"),
		"core_volt":   strings.TrimPrefix(sh("vcgencmd measure_volts core"), "volt="),
		"cpu_temp_c":  sh("awk '{printf \"%.1f C\", $1/1000}' /sys/class/thermal/thermal_zone0/temp 2>/dev/null"),
	}
}
