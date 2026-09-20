// Command csync-assist is the personal-assistant half of csync: a small service
// that runs on the home server (the Pi), holds the Gemini API key, and answers
// chat over the tailnet. A phone on the mesh talks to it with the same token it
// already uses for the mesh; the key never leaves this device.
package main

import (
	"crypto/subtle"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// maxTurns caps the per-session history replayed to the model, so a long chat
// stays affordable and within context.
const maxTurns = 40

type store struct {
	mu       sync.Mutex
	sessions map[string][]gContent
}

func newStore() *store { return &store{sessions: map[string][]gContent{}} }

func (s *store) append(session string, c gContent) []gContent {
	s.mu.Lock()
	defer s.mu.Unlock()
	h := append(s.sessions[session], c)
	if len(h) > maxTurns {
		h = h[len(h)-maxTurns:]
	}
	s.sessions[session] = h
	out := make([]gContent, len(h))
	copy(out, h)
	return out
}

func (s *store) reset(session string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.sessions, session)
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("usage: csync-assist serve | ask \"<message>\" | models")
		os.Exit(2)
	}
	var err error
	switch os.Args[1] {
	case "serve":
		err = serve()
	case "ask":
		err = cmdAsk(os.Args[2:])
	case "models":
		err = cmdModels()
	case "-h", "--help", "help":
		fmt.Println("usage: csync-assist serve | ask \"<message>\" | models")
	default:
		err = fmt.Errorf("unknown command %q", os.Args[1])
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, "error:", err)
		os.Exit(1)
	}
}

func serve() error {
	token, err := meshToken()
	if err != nil {
		return err
	}
	ip, err := tailscaleIP()
	if err != nil {
		return err
	}
	sessions := newStore()

	mux := http.NewServeMux()
	mux.HandleFunc("/whoami", func(w http.ResponseWriter, r *http.Request) {
		cfg := loadAssistConfig()
		writeJSON(w, map[string]any{
			"name": selfName(), "platform": platform(), "role": "assist",
			"provider": cfg.Provider, "model": cfg.Model, "effort": cfg.Effort,
		})
	})
	mux.HandleFunc("/providers", func(w http.ResponseWriter, r *http.Request) {
		if !authed(w, r, token) {
			return
		}
		writeJSON(w, map[string]any{"providers": loadProviders(), "active": loadAssistConfig()})
	})
	mux.HandleFunc("/config", func(w http.ResponseWriter, r *http.Request) {
		if !authed(w, r, token) {
			return
		}
		var c assistConfig
		if err := json.NewDecoder(r.Body).Decode(&c); err != nil {
			http.Error(w, "need JSON {provider, model, effort}", http.StatusBadRequest)
			return
		}
		if err := saveAssistConfig(c); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		writeJSON(w, map[string]any{"ok": true, "active": loadAssistConfig()})
	})
	mux.HandleFunc("/capabilities", func(w http.ResponseWriter, r *http.Request) {
		if !authed(w, r, token) {
			return
		}
		var caps []map[string]string
		for _, t := range toolDeclarations() {
			for _, d := range t.FunctionDeclarations {
				caps = append(caps, map[string]string{"name": d.Name, "description": d.Description})
			}
		}
		writeJSON(w, map[string]any{"tools": caps})
	})
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
		}
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Message == "" {
			http.Error(w, "need JSON {session, message}", http.StatusBadRequest)
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
		if cfg.Provider != "gemini" {
			http.Error(w, cfg.Provider+" provider is selected but not yet wired; choose Gemini in Settings", http.StatusNotImplemented)
			return
		}
		key, err := providerKey(cfg.Provider)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadGateway)
			return
		}
		history := sessions.append(req.Session, gContent{Role: "user", Parts: []gPart{{Text: req.Message}}})

		// Streaming mode (?stream=1): send each turn as newline-delimited JSON,
		// flushed the moment it happens, so the app shows tool calls and results
		// live. A final {"done":true,"reply":...} line closes the stream.
		if r.URL.Query().Get("stream") == "1" {
			w.Header().Set("Content-Type", "application/x-ndjson")
			w.Header().Set("X-Accel-Buffering", "no")
			flusher, _ := w.(http.Flusher)
			enc := json.NewEncoder(w)
			emit := func(t turn) {
				_ = enc.Encode(map[string]any{"turn": t})
				if flusher != nil {
					flusher.Flush()
				}
			}
			turns, err := runChat(key, cfg.Model, cfg.Effort, systemPrompt(), history, emit)
			reply := finalText(turns)
			if reply != "" {
				sessions.append(req.Session, gContent{Role: "model", Parts: []gPart{{Text: reply}}})
			}
			if err != nil {
				log.Printf("chat error (session %s): %v", req.Session, err)
				_ = enc.Encode(map[string]any{"error": err.Error()})
			}
			_ = enc.Encode(map[string]any{"done": true, "reply": reply})
			if flusher != nil {
				flusher.Flush()
			}
			return
		}

		turns, err := runChat(key, cfg.Model, cfg.Effort, systemPrompt(), history, nil)
		reply := finalText(turns)
		if reply != "" {
			sessions.append(req.Session, gContent{Role: "model", Parts: []gPart{{Text: reply}}})
		}
		if err != nil {
			log.Printf("chat error (session %s): %v", req.Session, err)
			if reply == "" {
				http.Error(w, err.Error(), http.StatusBadGateway)
				return
			}
		}
		writeJSON(w, map[string]any{"turns": turns, "reply": reply})
	})
	mux.HandleFunc("/reset", func(w http.ResponseWriter, r *http.Request) {
		if !authed(w, r, token) {
			return
		}
		var req struct {
			Session string `json:"session"`
		}
		json.NewDecoder(r.Body).Decode(&req)
		if req.Session == "" {
			req.Session = "default"
		}
		sessions.reset(req.Session)
		writeJSON(w, map[string]any{"ok": true})
	})
	// /media serves a captured or shared file by name so the app can show it inline.
	// filepath.Base strips any path, so a name cannot escape the media dir.
	mux.HandleFunc("/media/", func(w http.ResponseWriter, r *http.Request) {
		if !authed(w, r, token) {
			return
		}
		name := filepath.Base(r.URL.Path)
		if name == "." || name == "/" || name == "media" {
			http.Error(w, "no file named", http.StatusBadRequest)
			return
		}
		http.ServeFile(w, r, filepath.Join(mediaDir(), name))
	})

	addr := fmt.Sprintf("%s:%d", ip, AssistPort)
	srv := &http.Server{Addr: addr, Handler: mux, ReadHeaderTimeout: 10 * time.Second}
	log.Printf("csync-assist on %s (%s/%s) listening on http://%s", selfName(), loadAssistConfig().Provider, loadAssistConfig().Model, addr)
	return srv.ListenAndServe()
}

// turn is one visible step of an answer: the model's thinking, a tool it called
// with the result, or the final markdown text. The app renders these in order.
type turn struct {
	Type   string         `json:"type"` // thinking | tool_call | text
	Text   string         `json:"text,omitempty"`
	Name   string         `json:"name,omitempty"`
	Args   map[string]any `json:"args,omitempty"`
	Result map[string]any `json:"result,omitempty"`
}

// maxToolSteps is a runaway guard, not a task budget. A real multi-step task
// stays well under it; it only exists so a model that never produces a final
// answer cannot call tools forever and drain the API key.
const maxToolSteps = 100

// runChat drives one user turn to a final answer, collecting the thinking and
// tool calls along the way so the app can show how the answer was reached. Each
// functionCall is executed and its result replayed. When emit is set it is called
// with every turn the moment it happens, so the caller can stream progress to the
// app live rather than waiting for the whole answer.
func runChat(key, model, effort, system string, history []gContent, emit func(turn)) ([]turn, error) {
	working := make([]gContent, len(history))
	copy(working, history)
	sys := &gContent{Parts: []gPart{{Text: system}}}
	tools := toolDeclarations()
	think := effortToThinking(effort)
	var turns []turn
	add := func(t turn) {
		turns = append(turns, t)
		if emit != nil {
			emit(t)
		}
	}

	for step := 0; step < maxToolSteps; step++ {
		content, err := generate(key, model, gRequest{
			SystemInstruction: sys, Contents: working, Tools: tools, GenerationConfig: think,
		})
		if err != nil {
			return turns, err
		}
		for _, t := range thoughts(content) {
			add(turn{Type: "thinking", Text: t})
		}
		calls := functionCalls(content)
		if len(calls) == 0 {
			add(turn{Type: "text", Text: firstAnswerText(content)})
			return turns, nil
		}
		working = append(working, content) // the model's tool-call turn
		var responses []gPart
		for _, fc := range calls {
			result := executeTool(fc.Name, fc.Args)
			add(turn{Type: "tool_call", Name: fc.Name, Args: fc.Args, Result: result})
			responses = append(responses, gPart{
				FunctionResponse: &gFunctionResponse{Name: fc.Name, Response: result},
			})
		}
		working = append(working, gContent{Role: functionResponseRole, Parts: responses})
	}
	return turns, fmt.Errorf("stopped after %d tool steps (safety ceiling) without a final answer", maxToolSteps)
}

// finalText returns the last text turn, the answer the app treats as the reply.
func finalText(turns []turn) string {
	for i := len(turns) - 1; i >= 0; i-- {
		if turns[i].Type == "text" {
			return turns[i].Text
		}
	}
	return ""
}

func authed(w http.ResponseWriter, r *http.Request, token string) bool {
	if subtle.ConstantTimeCompare([]byte(r.Header.Get("X-Csync-Token")), []byte(token)) == 1 {
		return true
	}
	http.Error(w, "unauthorized", http.StatusUnauthorized)
	return false
}

func writeJSON(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(v)
}

// cmdAsk is a one-shot local test: no server, no history, just prove the key and
// model reach Gemini.
func cmdAsk(args []string) error {
	if len(args) < 1 {
		return fmt.Errorf("usage: csync-assist ask \"<message>\"")
	}
	cfg := loadAssistConfig()
	key, err := providerKey(cfg.Provider)
	if err != nil {
		return err
	}
	turns, err := runChat(key, cfg.Model, cfg.Effort, systemPrompt(),
		[]gContent{{Role: "user", Parts: []gPart{{Text: args[0]}}}}, nil)
	if err != nil {
		return err
	}
	for _, t := range turns {
		switch t.Type {
		case "thinking":
			fmt.Println("[thinking] " + t.Text)
		case "tool_call":
			fmt.Printf("[tool] %s -> %v\n", t.Name, t.Result)
		case "text":
			fmt.Println(t.Text)
		}
	}
	return nil
}

func cmdModels() error {
	key, err := geminiKey()
	if err != nil {
		return err
	}
	out, err := listModels(key)
	if err != nil {
		return err
	}
	fmt.Println(out)
	return nil
}
