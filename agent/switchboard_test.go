package main

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
	"time"
)

// An old Switchboard (no --json) must be refused, never run: it would launch as a second app.
func TestSwitchboardRefusesOldBinary(t *testing.T) {
	t.Setenv("CSYNC_SWITCHBOARD", "/bin/echo")
	rec := httptest.NewRecorder()
	handleSwitchboard(rec, httptest.NewRequest(http.MethodGet, "/switchboard/ledger", nil))
	if rec.Code != http.StatusConflict {
		t.Fatalf("an old binary must get 409, got %d %s", rec.Code, rec.Body.String())
	}
}

func actRequest(method, body string) *http.Request {
	return httptest.NewRequest(method, "/switchboard/act", strings.NewReader(body))
}

// Pressing a button is a POST of a known tab, and an old Switchboard is never run for it.
func TestSwitchboardActRefusals(t *testing.T) {
	t.Setenv("CSYNC_SWITCHBOARD", "/bin/echo")
	cases := []struct {
		name string
		req  *http.Request
		want int
	}{
		{"GET", actRequest(http.MethodGet, ""), http.StatusMethodNotAllowed},
		{"no key", actRequest(http.MethodPost, `{"tab":"plugins"}`), http.StatusBadRequest},
		{"unknown tab", actRequest(http.MethodPost, `{"tab":"../x","key":"k"}`), http.StatusNotFound},
		{"old binary", actRequest(http.MethodPost, `{"tab":"plugins","key":"k","button":"Enable"}`), http.StatusConflict},
		{"bulbs is a known tab", actRequest(http.MethodPost, `{"tab":"bulbs","key":"k","button":"On"}`), http.StatusConflict},
		{"value too long", actRequest(http.MethodPost, `{"tab":"bulbs","key":"k","button":"Colour","value":"`+strings.Repeat("a", 65)+`"}`), http.StatusBadRequest},
		{"old binary with a value", actRequest(http.MethodPost, `{"tab":"bulbs","key":"k","button":"Brightness","value":"50"}`), http.StatusConflict},
	}
	for _, c := range cases {
		rec := httptest.NewRecorder()
		handleSwitchboard(rec, c.req)
		if rec.Code != c.want {
			t.Errorf("%s: want %d, got %d %s", c.name, c.want, rec.Code, rec.Body.String())
		}
	}
}

// Runs only where a Switchboard binary is named, since it shells out to the real app.
// A stale key reaches Switchboard and its refusal comes back as JSON; nothing is pressed.
func TestSwitchboardActStaleKey(t *testing.T) {
	if os.Getenv("CSYNC_SWITCHBOARD") == "" {
		t.Skip("set CSYNC_SWITCHBOARD to a Switchboard binary")
	}
	rec := httptest.NewRecorder()
	handleSwitchboard(rec, actRequest(http.MethodPost, `{"tab":"plugins","key":"Plugins::gone","button":"Enable"}`))
	var got struct{ Error string }
	if rec.Code != http.StatusOK || json.Unmarshal(rec.Body.Bytes(), &got) != nil || !strings.Contains(got.Error, "refresh the list") {
		t.Fatalf("want Switchboard's refusal passed through, got %d %s", rec.Code, rec.Body.String())
	}
}

// Runs only where a Switchboard binary is named, since it shells out to the real app.
func TestSwitchboardRoute(t *testing.T) {
	if os.Getenv("CSYNC_SWITCHBOARD") == "" {
		t.Skip("set CSYNC_SWITCHBOARD to a Switchboard binary")
	}
	rec := httptest.NewRecorder()
	handleSwitchboard(rec, httptest.NewRequest(http.MethodGet, "/switchboard/ledger?group=Closed%20proposals&limit=3", nil))
	if rec.Code != http.StatusOK {
		t.Fatalf("ledger: status %d %s", rec.Code, rec.Body.String())
	}
	var got struct {
		Tab    string `json:"tab"`
		Groups []struct {
			Title string            `json:"title"`
			Total int               `json:"total"`
			Rows  []json.RawMessage `json:"rows"`
		} `json:"groups"`
	}
	if err := json.Unmarshal(rec.Body.Bytes(), &got); err != nil {
		t.Fatalf("not JSON: %v", err)
	}
	if got.Tab != "ledger" || len(got.Groups) != 1 || got.Groups[0].Title != "Closed proposals" || len(got.Groups[0].Rows) != 3 || got.Groups[0].Total < 3 {
		t.Fatalf("unexpected page: %+v", got)
	}
	rec = httptest.NewRecorder()
	handleSwitchboard(rec, httptest.NewRequest(http.MethodGet, "/switchboard/../../etc", nil))
	if rec.Code != http.StatusNotFound {
		t.Fatalf("an unknown tab must be refused, got %d", rec.Code)
	}
}

// The three tabs added for the phone are on the allow-list, and an old binary is still refused.
func TestSwitchboardNewTabsAllowed(t *testing.T) {
	t.Setenv("CSYNC_SWITCHBOARD", "/bin/echo")
	for _, tab := range []string{"usage", "bulbs", "agents"} {
		rec := httptest.NewRecorder()
		handleSwitchboard(rec, httptest.NewRequest(http.MethodGet, "/switchboard/"+tab, nil))
		if rec.Code != http.StatusConflict {
			t.Errorf("%s: an old binary must get 409 (not 404), got %d", tab, rec.Code)
		}
	}
}

// Runs only where a Switchboard binary is named. Usage and agents are read only; the bulbs
// press uses a key no bulb has, so Switchboard refuses it and no real bulb is touched.
func TestSwitchboardNewTabsLive(t *testing.T) {
	if os.Getenv("CSYNC_SWITCHBOARD") == "" {
		t.Skip("set CSYNC_SWITCHBOARD to a Switchboard binary")
	}
	for _, tab := range []string{"usage", "agents"} {
		rec := httptest.NewRecorder()
		handleSwitchboard(rec, httptest.NewRequest(http.MethodGet, "/switchboard/"+tab, nil))
		var got struct {
			Tab    string `json:"tab"`
			Groups []struct {
				Rows []map[string]any `json:"rows"`
			} `json:"groups"`
		}
		if rec.Code != http.StatusOK || json.Unmarshal(rec.Body.Bytes(), &got) != nil || got.Tab != tab || len(got.Groups) == 0 {
			t.Fatalf("%s: unexpected answer %d %s", tab, rec.Code, rec.Body.String())
		}
		if tab == "usage" && len(got.Groups[0].Rows) > 0 {
			if _, ok := got.Groups[0].Rows[0]["percent"]; !ok {
				t.Errorf("usage rows must carry a percent: %v", got.Groups[0].Rows[0])
			}
		}
	}
	rec := httptest.NewRecorder()
	handleSwitchboard(rec, actRequest(http.MethodPost, `{"tab":"bulbs","key":"no-such-bulb","button":"Brightness","value":"50"}`))
	var got struct{ Error string }
	if rec.Code != http.StatusOK || json.Unmarshal(rec.Body.Bytes(), &got) != nil || !strings.Contains(got.Error, "refresh the list") {
		t.Fatalf("want Switchboard's refusal for an unknown bulb, got %d %s", rec.Code, rec.Body.String())
	}
}

// A phone that hangs up mid-press must not kill the action: the run is detached from the request.
func TestSwitchboardActSurvivesDroppedConnection(t *testing.T) {
	fake := t.TempDir() + "/Switchboard"
	script := "#!/bin/sh\n# no longer on the Mac; refresh the list\nsleep 0.3\necho '{\"ok\":true}'\n"
	if err := os.WriteFile(fake, []byte(script), 0o755); err != nil {
		t.Fatal(err)
	}
	t.Setenv("CSYNC_SWITCHBOARD", fake)
	ctx, cancel := context.WithCancel(context.Background())
	req := actRequest(http.MethodPost, `{"tab":"ledger","key":"k","button":"Kill"}`).WithContext(ctx)
	go func() {
		time.Sleep(50 * time.Millisecond)
		cancel()
	}()
	rec := httptest.NewRecorder()
	handleSwitchboardAct(rec, req)
	if rec.Code != http.StatusOK || !strings.Contains(rec.Body.String(), `"ok":true`) {
		t.Fatalf("a dropped connection must not cancel the act, got %d %s", rec.Code, rec.Body.String())
	}
}

// The binary is scanned once per version; a changed file is scanned again.
func TestSwitchboardCurrentCachesByVersion(t *testing.T) {
	fake := t.TempDir() + "/Switchboard"
	if err := os.WriteFile(fake, []byte("has marker-x"), 0o755); err != nil {
		t.Fatal(err)
	}
	t.Setenv("CSYNC_SWITCHBOARD", fake)
	if !switchboardCurrent("marker-x") {
		t.Fatal("marker should be found")
	}
	// Same size and mtime but different bytes: the cached answer stands, proving no re-read.
	info, _ := os.Stat(fake)
	if err := os.WriteFile(fake, []byte("has marker-y"), 0o755); err != nil {
		t.Fatal(err)
	}
	_ = os.Chtimes(fake, info.ModTime(), info.ModTime())
	if !switchboardCurrent("marker-x") {
		t.Fatal("same mtime and size should answer from the cache")
	}
	// A different size is a new version and is scanned again.
	if err := os.WriteFile(fake, []byte("has marker-y!"), 0o755); err != nil {
		t.Fatal(err)
	}
	if switchboardCurrent("marker-x") {
		t.Fatal("a changed file must be scanned again")
	}
}
