package main

import (
	"fmt"
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
		bin := cameraBin(true)
		if bin == "" {
			return map[string]any{"present": false, "detail": "no libcamera/rpicam tools installed"}
		}
		out, _ := exec.Command(bin, "--list-cameras").CombinedOutput()
		return map[string]any{"present": cameraPresent(), "detail": truncate(strings.TrimSpace(string(out)), 1000)}
	case "capture", "photo", "image":
		bin := cameraBin(true)
		if bin == "" {
			return map[string]any{"error": "no camera tool installed"}
		}
		if !cameraPresent() {
			return map[string]any{"error": "no camera detected on this device"}
		}
		name := "cap-" + time.Now().Format("20060102-150405") + ".jpg"
		path := filepath.Join(mediaDir(), name)
		if out, err := exec.Command(bin, "-n", "-t", "800", "-o", path).CombinedOutput(); err != nil {
			return map[string]any{"error": "capture failed: " + strings.TrimSpace(string(out))}
		}
		return map[string]any{"ok": true, "path": path, "media_url": "/media/" + name, "media_type": "image"}
	case "record", "video":
		bin := cameraBin(false)
		if bin == "" {
			return map[string]any{"error": "no camera video tool installed"}
		}
		if !cameraPresent() {
			return map[string]any{"error": "no camera detected on this device"}
		}
		secs := 5
		if d, err := strconv.Atoi(strings.TrimSpace(durationSec)); err == nil && d > 0 && d <= 120 {
			secs = d
		}
		name := "vid-" + time.Now().Format("20060102-150405") + ".mp4"
		path := filepath.Join(mediaDir(), name)
		if out, err := exec.Command(bin, "-n", "-t", fmt.Sprintf("%d", secs*1000), "--codec", "libav", "-o", path).CombinedOutput(); err != nil {
			return map[string]any{"error": "record failed: " + strings.TrimSpace(string(out))}
		}
		return map[string]any{"ok": true, "path": path, "media_url": "/media/" + name, "media_type": "video", "seconds": secs}
	default:
		return map[string]any{"error": "unknown camera action " + action + " (use status, capture, or record)"}
	}
}

// sendImage shares an existing image or video file into the chat by staging it in
// mediaDir and returning a media_url the app renders inline.
func sendImage(path string) map[string]any {
	if strings.TrimSpace(path) == "" {
		return map[string]any{"error": "path is required"}
	}
	info, err := os.Stat(path)
	if err != nil || info.IsDir() {
		return map[string]any{"error": "no such file: " + path}
	}
	ext := strings.ToLower(filepath.Ext(path))
	var mt string
	switch ext {
	case ".jpg", ".jpeg", ".png", ".gif", ".webp":
		mt = "image"
	case ".mp4", ".mov", ".h264", ".webm":
		mt = "video"
	default:
		return map[string]any{"error": "not an image or video file: " + ext}
	}
	name := "share-" + time.Now().Format("20060102-150405") + ext
	b, err := os.ReadFile(path)
	if err != nil {
		return map[string]any{"error": "could not read file: " + err.Error()}
	}
	if err := os.WriteFile(filepath.Join(mediaDir(), name), b, 0o644); err != nil {
		return map[string]any{"error": "could not stage file: " + err.Error()}
	}
	return map[string]any{"ok": true, "media_url": "/media/" + name, "media_type": mt}
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
