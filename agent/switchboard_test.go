package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
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
