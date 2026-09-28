package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
)

func mediaFixture(t *testing.T, handler http.HandlerFunc) {
	t.Helper()
	home := t.TempDir()
	t.Setenv("HOME", home)
	config := filepath.Join(home, ".config", "csync")
	if err := os.MkdirAll(config, 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(config, "mesh.token"), []byte("fixture-token\n"), 0600); err != nil {
		t.Fatal(err)
	}
	server := httptest.NewServer(handler)
	t.Cleanup(server.Close)
	previous := mediaBaseURL
	mediaBaseURL = server.URL
	t.Cleanup(func() { mediaBaseURL = previous })
}

func TestMediaPhoneCommandReportsQueued(t *testing.T) {
	mediaFixture(t, func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("X-Csync-Token") != "fixture-token" {
			t.Errorf("missing token")
		}
		if r.Method == http.MethodGet && r.URL.Path == "/v1/player/phone" {
			json.NewEncoder(w).Encode(map[string]any{"revision": 3, "state": "playing", "id": "phone-a", "generation": 4})
			return
		}
		if r.Method == http.MethodPost && r.URL.Path == "/v1/player/phone/commands" {
			var body map[string]any
			if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
				t.Error(err)
			}
			if body["expectedRevision"] != float64(3) || body["action"] != "pause" || body["commandId"] == "" ||
				body["expectedSessionId"] != "phone-a" || body["expectedGeneration"] != float64(4) {
				t.Errorf("wrong command: %#v", body)
			}
			json.NewEncoder(w).Encode(map[string]any{"status": "queued"})
			return
		}
		http.NotFound(w, r)
	})
	result := executeTool("media_pause", map[string]any{"target": "phone"})
	if result["status"] != "queued" {
		t.Fatalf("phone command was not reported queued: %#v", result)
	}
}

func TestMediaCastYouTubeUsesSharedPlayer(t *testing.T) {
	mediaFixture(t, func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("X-Csync-Token") != "fixture-token" ||
			r.Method != http.MethodPost || r.URL.Path != "/v1/cast/youtube" {
			t.Errorf("wrong media request: %s %s", r.Method, r.URL.Path)
		}
		var body map[string]any
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil ||
			body["url"] != "https://youtu.be/aqz-KE-bpKQ" {
			t.Errorf("wrong video URL: %#v %v", body, err)
		}
		json.NewEncoder(w).Encode(map[string]any{"status": "applied", "player": map[string]any{"state": "playing", "volume": 0}})
	})
	result := executeTool("media_cast_youtube", map[string]any{"url": "https://youtu.be/aqz-KE-bpKQ"})
	if result["status"] != "applied" {
		t.Fatalf("cast was not reported applied: %#v", result)
	}
}

func TestMediaRejectsInvalidTargetAndServiceDown(t *testing.T) {
	if result := mediaStatus("other"); result["code"] != "TARGET_INVALID" {
		t.Fatalf("wrong target accepted: %#v", result)
	}
	home := t.TempDir()
	t.Setenv("HOME", home)
	config := filepath.Join(home, ".config", "csync")
	if err := os.MkdirAll(config, 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(config, "mesh.token"), []byte("fixture-token"), 0600); err != nil {
		t.Fatal(err)
	}
	previous := mediaBaseURL
	mediaBaseURL = "http://127.0.0.1:1"
	defer func() { mediaBaseURL = previous }()
	if result := mediaGet("/v1/drives"); result["code"] != "MEDIA_SERVICE_UNAVAILABLE" {
		t.Fatalf("service failure not classified: %#v", result)
	}
}

func TestCameraUsesSharedMediaService(t *testing.T) {
	mediaFixture(t, func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/v1/camera/photo" && r.Method == http.MethodPost {
			json.NewEncoder(w).Encode(map[string]any{"name": "photo.jpg", "path": "/captures/photo.jpg"})
			return
		}
		if r.URL.Path == "/v1/camera/record/clip" && r.Method == http.MethodPost {
			var body map[string]any
			json.NewDecoder(r.Body).Decode(&body)
			if body["durationSeconds"] != float64(2) {
				t.Errorf("wrong duration: %#v", body)
			}
			json.NewEncoder(w).Encode(map[string]any{"name": "clip.mp4", "path": "/captures/clip.mp4"})
			return
		}
		http.NotFound(w, r)
	})
	if result := executeTool("camera", map[string]any{"action": "capture"}); result["media_url"] != "/media/photo.jpg" {
		t.Fatalf("photo did not use camera service: %#v", result)
	}
	if result := executeTool("camera", map[string]any{"action": "record", "duration_seconds": float64(2)}); result["media_url"] != "/media/clip.mp4" {
		t.Fatalf("clip did not use camera service: %#v", result)
	}
}

func TestNotesToolUsesMediaAuthorityAndRevision(t *testing.T) {
	requests := 0
	mediaFixture(t, func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("X-Csync-Token") != "fixture-token" {
			t.Error("note request missing mesh token")
		}
		requests++
		switch {
		case r.Method == http.MethodGet && r.URL.Path == "/v1/notes":
			json.NewEncoder(w).Encode(map[string]any{"notes": []any{}})
		case r.Method == http.MethodPost && r.URL.Path == "/v1/notes":
			var body map[string]any
			json.NewDecoder(r.Body).Decode(&body)
			if body["title"] != "Trip" || body["body"] != "# List" {
				t.Errorf("wrong create body: %#v", body)
			}
			json.NewEncoder(w).Encode(map[string]any{"id": "n1", "revision": 1})
		case r.Method == http.MethodPut && r.URL.Path == "/v1/notes/n1":
			var body map[string]any
			json.NewDecoder(r.Body).Decode(&body)
			if body["expectedRevision"] != float64(1) {
				t.Errorf("lost revision: %#v", body)
			}
			w.WriteHeader(http.StatusConflict)
			json.NewEncoder(w).Encode(map[string]any{"code": "NOTE_CONFLICT"})
		case r.Method == http.MethodDelete && r.URL.Path == "/v1/notes/n1":
			var body map[string]any
			json.NewDecoder(r.Body).Decode(&body)
			if body["expectedRevision"] != float64(2) {
				t.Errorf("lost delete revision: %#v", body)
			}
			json.NewEncoder(w).Encode(map[string]any{"deleted": true})
		default:
			http.NotFound(w, r)
		}
	})
	if result := executeTool("notes", map[string]any{"action": "list"}); result["notes"] == nil {
		t.Fatalf("list failed: %#v", result)
	}
	if result := executeTool("notes", map[string]any{"action": "create", "title": "Trip", "body": "# List"}); result["id"] != "n1" {
		t.Fatalf("create failed: %#v", result)
	}
	if result := executeTool("notes", map[string]any{"action": "update", "id": "n1", "title": "Trip", "body": "# List", "expected_revision": float64(1)}); result["code"] != "NOTE_CONFLICT" || result["ok"] != false {
		t.Fatalf("conflict was lost: %#v", result)
	}
	if result := executeTool("notes", map[string]any{"action": "delete", "id": "n1", "expected_revision": float64(2)}); result["deleted"] != true {
		t.Fatalf("delete failed: %#v", result)
	}
	if result := executeTool("notes", map[string]any{"action": "delete", "id": "n1", "expected_revision": float64(1.5)}); result["code"] != "NOTE_INVALID" {
		t.Fatalf("fractional revision accepted: %#v", result)
	}
	if requests != 4 {
		t.Fatalf("unexpected network requests: %d", requests)
	}
}
