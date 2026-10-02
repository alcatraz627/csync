package main

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestPhoneDiagnosticsRoundTrip(t *testing.T) {
	t.Setenv("HOME", t.TempDir())
	if got := phoneDiagnostics(); got["code"] != "NO_REPORT" {
		t.Fatalf("before any report: %v", got)
	}
	mux := http.NewServeMux()
	phoneRoutes(mux, "tok")

	post := httptest.NewRequest(http.MethodPost, "/phone/diagnostics",
		strings.NewReader(`{"findings":[{"name":"Truecaller","level":"Some","score":75}]}`))
	post.Header.Set("X-Csync-Token", "tok")
	rec := httptest.NewRecorder()
	mux.ServeHTTP(rec, post)
	if rec.Code != http.StatusOK {
		t.Fatalf("post: %d %s", rec.Code, rec.Body.String())
	}

	got := phoneDiagnostics()
	rows, _ := got["findings"].([]any)
	if len(rows) != 1 || got["age_minutes"] != 0 || got["stale"] != nil {
		t.Fatalf("after report: %v", got)
	}

	bad := httptest.NewRequest(http.MethodPost, "/phone/diagnostics", strings.NewReader("not json"))
	bad.Header.Set("X-Csync-Token", "tok")
	rec = httptest.NewRecorder()
	mux.ServeHTTP(rec, bad)
	if rec.Code != http.StatusBadRequest {
		t.Fatalf("bad body: %d", rec.Code)
	}

	noToken := httptest.NewRequest(http.MethodGet, "/phone/diagnostics", nil)
	rec = httptest.NewRecorder()
	mux.ServeHTTP(rec, noToken)
	if rec.Code == http.StatusOK {
		t.Fatalf("read without the token was allowed")
	}
}
