// Command csync-assist is the personal-assistant half of csync: a small service
// that runs on the home server (the Pi), holds the Gemini API key, and answers
// chat over the tailnet. A phone on the mesh talks to it with the same token it
// already uses for the mesh; the key never leaves this device.
package main

import (
	"context"
	"crypto/subtle"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// maxTurns caps the per-session history replayed to the model, so a long chat
// stays affordable and within context.
const maxTurns = 40

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
	sessions := newConvStore(conversationsDir())

	mux := http.NewServeMux()
	conversationRoutes(mux, token, sessions)
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
		writeJSON(w, map[string]any{"providers": providersForApp(), "active": loadAssistConfig()})
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
		c.Provider = providerForModel(c.Model, c.Provider)
		if !chatProviderSupported(c.Provider) {
			http.Error(w, c.Provider+" has no key on this Pi, so it cannot chat yet", http.StatusBadRequest)
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
	chatRoutes(mux, token, sessions)
	phoneRoutes(mux, token)
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
		if err := sessions.remove(req.Session); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
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
	// Stopped marks an answer the owner cut short; its text is what had arrived.
	Stopped bool `json:"stopped,omitempty"`
	// Usage is what the reply cost, kept on the final answer.
	Usage *usage `json:"usage,omitempty"`
}

// maxToolSteps is a runaway guard, not a task budget. A real multi-step task
// stays well under it; it only exists so a model that never produces a final
// answer cannot call tools forever and drain the API key.
const maxToolSteps = 100

// runChat drives one user turn to a final answer through Gemini, collecting the
// thinking and tool calls along the way so the app can show how the answer was
// reached. Each functionCall is executed and its result replayed. emit gets every
// turn the moment it happens and delta gets the answer's words as they are
// written; either may be nil.
func runChat(ctx context.Context, key, model, effort, system string, history []gContent, emit func(turn), delta func(string)) ([]turn, tokenCount, error) {
	working := make([]gContent, len(history))
	copy(working, history)
	sys := &gContent{Parts: []gPart{{Text: system}}}
	tools := toolDeclarations()
	think := effortToThinking(effort)
	st := newRunState(ctx, emit, delta)

	for step := 0; step < maxToolSteps; step++ {
		if st.stopped() {
			return st.stop()
		}
		st.step()
		content, tokens, err := streamGenerate(ctx, key, model, gRequest{
			SystemInstruction: sys, Contents: working, Tools: tools, GenerationConfig: think,
		}, st.text)
		if tokens.Reported {
			st.count(tokens.In, tokens.Out)
		}
		if err != nil {
			return st.fail(err)
		}
		for _, t := range thoughts(content) {
			st.add(turn{Type: "thinking", Text: t})
		}
		calls := functionCalls(content)
		if len(calls) == 0 {
			return st.answer(answerText(content))
		}
		working = append(working, content) // the model's tool-call turn
		var responses []gPart
		for _, fc := range calls {
			result := executeTool(fc.Name, fc.Args)
			st.add(turn{Type: "tool_call", Name: fc.Name, Args: fc.Args, Result: result})
			responses = append(responses, gPart{
				FunctionResponse: &gFunctionResponse{Name: fc.Name, Response: result},
			})
		}
		working = append(working, gContent{Role: functionResponseRole, Parts: responses})
	}
	return st.turns, st.tokens, fmt.Errorf("stopped after %d tool steps (safety ceiling) without a final answer", maxToolSteps)
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
	// ask --model <id> "<message>" tries one model without changing the saved choice.
	if len(args) >= 3 && args[0] == "--model" {
		cfg.Model, args = args[1], args[2:]
	}
	cfg.Provider = providerForModel(cfg.Model, cfg.Provider)
	key, err := providerKey(cfg.Provider)
	if err != nil {
		return err
	}
	turns, _, err := chatRunners[cfg.Provider](context.Background(), key, cfg.Model, cfg.Effort, systemPrompt(),
		[]gContent{{Role: "user", Parts: []gPart{{Text: args[0]}}}}, nil, nil)
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
	for _, p := range providersForApp() {
		if !p.ChatSupported {
			fmt.Printf("%s: %s\n", p.Label, p.Reason)
			continue
		}
		fmt.Printf("%s (%d): %s\n", p.Label, len(p.Models), strings.Join(p.Models, ", "))
	}
	return nil
}
