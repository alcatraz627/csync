package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os/exec"
	"strings"
	"time"
)

var mediaBaseURL = "http://127.0.0.1:8792"

func mediaRequest(method, path string, body map[string]any, timeout ...time.Duration) map[string]any {
	token, err := meshToken()
	if err != nil {
		return map[string]any{"code": "AUTH_REQUIRED", "error": "mesh token unavailable"}
	}
	var input io.Reader
	if body != nil {
		encoded, err := json.Marshal(body)
		if err != nil {
			return map[string]any{"code": "REQUEST_INVALID", "error": err.Error()}
		}
		input = bytes.NewReader(encoded)
	}
	request, err := http.NewRequest(method, mediaBaseURL+path, input)
	if err != nil {
		return map[string]any{"code": "REQUEST_INVALID", "error": err.Error()}
	}
	request.Header.Set("X-Csync-Token", token)
	if body != nil {
		request.Header.Set("Content-Type", "application/json")
	}
	limit := 5 * time.Second
	if len(timeout) > 0 {
		limit = timeout[0]
	}
	client := &http.Client{Timeout: limit}
	response, err := client.Do(request)
	if err != nil {
		return map[string]any{"code": "MEDIA_SERVICE_UNAVAILABLE", "error": "media service did not answer", "retryable": true}
	}
	defer response.Body.Close()
	limited := io.LimitReader(response.Body, 1<<20)
	var result map[string]any
	if err := json.NewDecoder(limited).Decode(&result); err != nil {
		return map[string]any{"code": "MEDIA_RESPONSE_INVALID", "error": "media service returned an invalid response"}
	}
	if response.StatusCode >= 400 {
		result["ok"] = false
	}
	return result
}

func mediaGet(path string) map[string]any { return mediaRequest(http.MethodGet, path, nil) }

func mediaSearch(query string) map[string]any {
	if strings.TrimSpace(query) == "" {
		return map[string]any{"code": "SEARCH_INVALID", "error": "query is required"}
	}
	return mediaGet("/v1/search?q=" + url.QueryEscape(query))
}

func mediaCastYouTube(videoURL string) map[string]any {
	if strings.TrimSpace(videoURL) == "" {
		return map[string]any{"code": "URL_INVALID", "error": "YouTube video URL is required"}
	}
	return mediaRequest(http.MethodPost, "/v1/cast/youtube",
		map[string]any{"url": videoURL}, 40*time.Second)
}

func mediaStatus(target string) map[string]any {
	if target != "pi" && target != "phone" {
		return map[string]any{"code": "TARGET_INVALID", "error": "target must be pi or phone"}
	}
	return mediaGet("/v1/player/" + target)
}

func mediaCommand(target, action, itemID string, position any) map[string]any {
	state := mediaStatus(target)
	revision, ok := state["revision"]
	if !ok {
		return state
	}
	body := map[string]any{"action": action, "expectedRevision": revision}
	if action == "play" {
		if itemID == "" {
			return map[string]any{"code": "ITEM_INVALID", "error": "item_id is required"}
		}
		body["itemId"] = itemID
	}
	if action == "seek" {
		value, ok := position.(float64)
		if !ok || value < 0 {
			return map[string]any{"code": "COMMAND_INVALID", "error": "position_ms must be nonnegative"}
		}
		body["positionMs"] = value
	}
	if action == "volume" || action == "speed" {
		value, ok := position.(float64)
		if !ok || (action == "volume" && (value < 0 || value > 100)) ||
			(action == "speed" && (value < 0.25 || value > 4)) {
			return map[string]any{"code": "COMMAND_INVALID", "error": "choose a valid playback setting"}
		}
		body["value"] = value
	}
	if target == "phone" {
		body["commandId"] = fmt.Sprintf("assist-%d", time.Now().UnixNano())
		body["expectedSessionId"] = state["id"]
		body["expectedGeneration"] = state["generation"]
	}
	if target == "pi" && action == "play" && strings.HasPrefix(itemID, "youtube:") {
		return mediaRequest(http.MethodPost, "/v1/player/pi/commands", body, 40*time.Second)
	}
	return mediaRequest(http.MethodPost, "/v1/player/"+target+"/commands", body)
}

func boundedCommand(name string, args ...string) string {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	out, err := exec.CommandContext(ctx, name, args...).CombinedOutput()
	if err != nil {
		return "unavailable: " + err.Error()
	}
	return truncate(strings.TrimSpace(string(out)), 500)
}

func mediaDiagnose() map[string]any {
	result := map[string]any{
		"observedAt": time.Now().UTC().Format(time.RFC3339),
		"service":    boundedCommand("systemctl", "--user", "is-active", "csync-media.service"),
		"power":      boundedCommand("vcgencmd", "get_throttled"),
		"mounts":     boundedCommand("findmnt", "-n", "-o", "TARGET,UUID,FSTYPE", "/srv/media"),
		"hdmi1":      boundedCommand("cat", "/sys/class/drm/card1-HDMI-A-1/status"),
		"hdmi2":      boundedCommand("cat", "/sys/class/drm/card1-HDMI-A-2/status"),
	}
	result["media"] = mediaGet("/v1/diagnostics")
	return result
}
