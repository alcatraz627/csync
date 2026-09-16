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
	key, err := geminiKey()
	if err != nil {
		return err
	}
	token, err := meshToken()
	if err != nil {
		return err
	}
	ip, err := tailscaleIP()
	if err != nil {
		return err
	}
	m := model()
	sessions := newStore()

	mux := http.NewServeMux()
	mux.HandleFunc("/whoami", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, map[string]any{
			"name": selfName(), "platform": platform(), "role": "assist", "model": m,
		})
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
		}
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Message == "" {
			http.Error(w, "need JSON {session, message}", http.StatusBadRequest)
			return
		}
		if req.Session == "" {
			req.Session = "default"
		}
		history := sessions.append(req.Session, gContent{Role: "user", Parts: []gPart{{Text: req.Message}}})
		reply, err := runChat(key, m, systemPrompt(), history)
		if err != nil {
			log.Printf("chat error (session %s): %v", req.Session, err)
			http.Error(w, err.Error(), http.StatusBadGateway)
			return
		}
		sessions.append(req.Session, gContent{Role: "model", Parts: []gPart{{Text: reply}}})
		writeJSON(w, map[string]any{"reply": reply})
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

	addr := fmt.Sprintf("%s:%d", ip, AssistPort)
	srv := &http.Server{Addr: addr, Handler: mux, ReadHeaderTimeout: 10 * time.Second}
	log.Printf("csync-assist on %s (model %s) listening on http://%s", selfName(), m, addr)
	return srv.ListenAndServe()
}

// runChat drives one user turn to a text answer, letting the model call tools in
// between. Each functionCall is executed and its result replayed, up to a cap so
// a misbehaving loop cannot run forever.
func runChat(key, model, system string, history []gContent) (string, error) {
	working := make([]gContent, len(history))
	copy(working, history)
	sys := &gContent{Parts: []gPart{{Text: system}}}
	tools := toolDeclarations()

	for step := 0; step < 8; step++ {
		content, err := generate(key, model, gRequest{
			SystemInstruction: sys, Contents: working, Tools: tools,
		})
		if err != nil {
			return "", err
		}
		calls := functionCalls(content)
		if len(calls) == 0 {
			return firstText(content), nil
		}
		working = append(working, content) // the model's tool-call turn
		var responses []gPart
		for _, fc := range calls {
			result := executeTool(fc.Name, fc.Args)
			responses = append(responses, gPart{
				FunctionResponse: &gFunctionResponse{Name: fc.Name, Response: result},
			})
		}
		working = append(working, gContent{Role: functionResponseRole, Parts: responses})
	}
	return "", fmt.Errorf("gave up after 8 tool steps without a final answer")
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
	key, err := geminiKey()
	if err != nil {
		return err
	}
	reply, err := runChat(key, model(), systemPrompt(),
		[]gContent{{Role: "user", Parts: []gPart{{Text: args[0]}}}})
	if err != nil {
		return err
	}
	fmt.Println(reply)
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
