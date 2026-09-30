package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"sync"
	"time"
)

// runRegistry knows which conversations are answering right now, so a second
// message waits its turn and the owner can stop a reply that is under way.
type runRegistry struct {
	mu      sync.Mutex
	running map[string]context.CancelFunc
}

func newRunRegistry() *runRegistry {
	return &runRegistry{running: map[string]context.CancelFunc{}}
}

// start claims a conversation for one run. It returns false when a run is
// already in flight there. The run's context is not tied to the request, so a
// phone that loses its connection does not cut the answer short; call finish
// when the run ends.
func (r *runRegistry) start(id string) (ctx context.Context, finish func(), ok bool) {
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, busy := r.running[id]; busy {
		return nil, nil, false
	}
	ctx, cancel := context.WithCancel(context.Background())
	r.running[id] = cancel
	return ctx, func() {
		r.mu.Lock()
		delete(r.running, id)
		r.mu.Unlock()
		cancel()
	}, true
}

// stop asks the run in a conversation to end, reporting whether one was running.
func (r *runRegistry) stop(id string) bool {
	r.mu.Lock()
	defer r.mu.Unlock()
	cancel, ok := r.running[id]
	if ok {
		cancel()
	}
	return ok
}

// chatRoutes serves chat to the owner's devices: POST /chat answers a message,
// POST /chat/stop ends the answer under way, and GET /skills lists the saved
// skills for the app's slash menu. The wire format is in docs/architecture.md.
func chatRoutes(mux *http.ServeMux, token string, sessions *convStore) {
	runs := newRunRegistry()
	mux.HandleFunc("/chat", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "POST only", http.StatusMethodNotAllowed)
			return
		}
		if !authed(w, r, token) {
			return
		}
		var req struct {
			Session string `json:"session"`
			Message string `json:"message"`
			Model   string `json:"model"`
			Effort  string `json:"effort"`
			// Files picked from the phone's + drawer, sent with this turn.
			Attachments []attachment `json:"attachments"`
		}
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil || (req.Message == "" && len(req.Attachments) == 0) {
			http.Error(w, "need JSON {session, message}", http.StatusBadRequest)
			return
		}
		parts, err := userParts(req.Message, req.Attachments, mediaDir())
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		if req.Session == "" {
			req.Session = "default"
		}
		cfg := loadAssistConfig()
		// A conversation can pin its own model and effort, overriding the saved default.
		if req.Model != "" {
			cfg.Model = req.Model
		}
		if req.Effort != "" {
			cfg.Effort = req.Effort
		}
		// The model decides the provider, so a conversation can use any provider's model.
		cfg.Provider = providerForModel(cfg.Model, cfg.Provider)
		if !chatProviderSupported(cfg.Provider) {
			http.Error(w, cfg.Provider+" has no key on this Pi, so "+cfg.Model+" cannot be used yet", http.StatusNotImplemented)
			return
		}
		run := chatRunners[cfg.Provider]
		key, err := providerKey(cfg.Provider)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadGateway)
			return
		}
		ctx, finish, ok := runs.start(req.Session)
		if !ok {
			http.Error(w, "This conversation is still answering the last message. Wait for it to finish or stop it, then send again.", http.StatusConflict)
			return
		}
		defer finish()
		history, err := sessions.userTurn(req.Session, req.Message, gContent{Role: "user", Parts: parts})
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		// Thinking and tool calls are saved the moment they happen. The answer is
		// saved once the run ends, because only then is its cost known.
		save := func(t turn) {
			if t.Type != "text" {
				sessions.assistantTurn(req.Session, t)
			}
		}
		finishRun := func(turns []turn, tokens tokenCount, started time.Time) (string, bool, *usage) {
			spent := newUsage(tokens, time.Since(started).Milliseconds(), cfg.Model)
			last := -1
			for i, t := range turns {
				if t.Type == "text" {
					last = i
				}
			}
			stopped := false
			if last >= 0 {
				turns[last].Usage = spent
				stopped = turns[last].Stopped
				sessions.assistantTurn(req.Session, turns[last])
			}
			reply := finalText(turns)
			sessions.answered(req.Session, reply)
			return reply, stopped, spent
		}
		started := time.Now()

		// Streaming mode (?stream=1): send each turn as newline-delimited JSON,
		// flushed the moment it happens, with the answer's words as delta lines
		// while it is written. A usage line and a done line close the stream.
		if r.URL.Query().Get("stream") == "1" {
			w.Header().Set("Content-Type", "application/x-ndjson")
			w.Header().Set("X-Accel-Buffering", "no")
			flusher, _ := w.(http.Flusher)
			enc := json.NewEncoder(w)
			send := func(v any) {
				_ = enc.Encode(v)
				if flusher != nil {
					flusher.Flush()
				}
			}
			emit := func(t turn) {
				save(t)
				send(map[string]any{"turn": t})
			}
			delta := func(text string) { send(map[string]any{"delta": map[string]string{"text": text}}) }
			turns, tokens, err := run(ctx, key, cfg.Model, cfg.Effort, systemPrompt(), history, emit, delta)
			reply, stopped, spent := finishRun(turns, tokens, started)
			if err != nil && !stopped {
				log.Printf("chat error (session %s): %v", req.Session, err)
				send(map[string]any{"error": err.Error()})
			}
			send(map[string]any{"usage": spent})
			done := map[string]any{"done": true, "reply": reply}
			if stopped {
				done["stopped"] = true
			}
			send(done)
			return
		}

		turns, tokens, err := run(ctx, key, cfg.Model, cfg.Effort, systemPrompt(), history, save, nil)
		reply, _, _ := finishRun(turns, tokens, started)
		if err != nil {
			log.Printf("chat error (session %s): %v", req.Session, err)
			if reply == "" {
				http.Error(w, err.Error(), http.StatusBadGateway)
				return
			}
		}
		writeJSON(w, map[string]any{"turns": turns, "reply": reply})
	})
	mux.HandleFunc("/chat/stop", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "POST only", http.StatusMethodNotAllowed)
			return
		}
		if !authed(w, r, token) {
			return
		}
		var req struct {
			Session string `json:"session"`
		}
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, "need JSON {session}", http.StatusBadRequest)
			return
		}
		if req.Session == "" {
			req.Session = "default"
		}
		writeJSON(w, map[string]any{"ok": true, "stopped": runs.stop(req.Session)})
	})
	mux.HandleFunc("/skills", func(w http.ResponseWriter, r *http.Request) {
		if !authed(w, r, token) {
			return
		}
		writeJSON(w, map[string]any{"skills": listSkills()["skills"]})
	})
}
