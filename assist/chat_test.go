package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"
)

const testToken = "fixture-token"

// assistHome gives a test its own home folder with a fake key for each provider,
// so nothing reads or touches the real configuration.
func assistHome(t *testing.T) string {
	t.Helper()
	home := t.TempDir()
	t.Setenv("HOME", home)
	config := filepath.Join(home, ".config", "csync")
	if err := os.MkdirAll(config, 0o700); err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"gemini.key", "claude.key", "openai.key"} {
		if err := os.WriteFile(filepath.Join(config, name), []byte("fixture-key"), 0o600); err != nil {
			t.Fatal(err)
		}
	}
	return home
}

// sse writes server-sent events and flushes after each one.
type sse struct {
	w http.ResponseWriter
}

func newSSE(w http.ResponseWriter) sse {
	w.Header().Set("Content-Type", "text/event-stream")
	w.WriteHeader(http.StatusOK)
	return sse{w}
}

func (s sse) send(event string, data any) {
	raw, _ := json.Marshal(data)
	if event != "" {
		fmt.Fprintf(s.w, "event: %s\n", event)
	}
	fmt.Fprintf(s.w, "data: %s\n\n", raw)
	s.w.(http.Flusher).Flush()
}

// fakeGemini answers each streaming call with the next script in turn.
func fakeGemini(t *testing.T, steps ...func(s sse, r *http.Request)) *[]map[string]any {
	t.Helper()
	var mu sync.Mutex
	var bodies []map[string]any
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if !strings.HasSuffix(r.URL.Path, ":streamGenerateContent") || r.URL.Query().Get("alt") != "sse" {
			t.Errorf("not a streaming call: %s", r.URL)
		}
		var body map[string]any
		_ = json.NewDecoder(r.Body).Decode(&body)
		mu.Lock()
		bodies = append(bodies, body)
		n := len(bodies)
		mu.Unlock()
		if n > len(steps) {
			t.Errorf("unexpected call %d", n)
			return
		}
		steps[n-1](newSSE(w), r)
	}))
	t.Cleanup(server.Close)
	previous := geminiBaseURL
	geminiBaseURL = server.URL
	t.Cleanup(func() { geminiBaseURL = previous })
	return &bodies
}

func geminiText(text string, thought bool) map[string]any {
	return map[string]any{"candidates": []any{map[string]any{"content": map[string]any{
		"role": "model", "parts": []any{map[string]any{"text": text, "thought": thought}}}}}}
}

func geminiUsage(prompt, candidates, thoughts int) map[string]any {
	return map[string]any{"promptTokenCount": prompt, "candidatesTokenCount": candidates, "thoughtsTokenCount": thoughts}
}

// A tool step that asks for the harmless list_skills tool, then an answer in three pieces.
func geminiToolStep(s sse, r *http.Request) {
	s.send("", map[string]any{"candidates": []any{map[string]any{"content": map[string]any{"role": "model",
		"parts": []any{map[string]any{"functionCall": map[string]any{"name": "list_skills", "args": map[string]any{}},
			"thoughtSignature": "sig-1"}}}}}, "usageMetadata": geminiUsage(10, 3, 1)})
}

func geminiAnswerStep(s sse, r *http.Request) {
	s.send("", geminiText("Weighing it up.", true))
	s.send("", geminiText("Hel", false))
	s.send("", geminiText("lo wor", false))
	chunk := geminiText("ld", false)
	chunk["usageMetadata"] = geminiUsage(20, 5, 1)
	s.send("", chunk)
}

// releaser holds a fake provider mid-reply until the test lets it go. Register
// release as a cleanup after both servers start, so a failing test lets it go
// too and the servers can shut down.
func releaser() (<-chan struct{}, func()) {
	ch := make(chan struct{})
	var once sync.Once
	return ch, func() { once.Do(func() { close(ch) }) }
}

type collected struct {
	turns  []turn
	deltas []string
}

func (c *collected) emit(t turn)       { c.turns = append(c.turns, t) }
func (c *collected) delta(text string) { c.deltas = append(c.deltas, text) }

// checkStreamed asserts the words streamed as deltas add up to the final answer.
func checkStreamed(t *testing.T, got collected, turns []turn, want string) {
	t.Helper()
	if len(got.deltas) < 2 {
		t.Fatalf("the answer was not streamed in pieces: %q", got.deltas)
	}
	final := turns[len(turns)-1]
	if final.Type != "text" || final.Text != want || strings.Join(got.deltas, "") != final.Text {
		t.Fatalf("deltas %q do not add up to the final answer %+v", got.deltas, final)
	}
}

func TestGeminiStreamsTheAnswerAndSumsTokens(t *testing.T) {
	assistHome(t)
	bodies := fakeGemini(t, geminiToolStep, geminiAnswerStep)
	var got collected
	turns, tokens, err := runChat(context.Background(), "k", "gemini-test", "medium", "sys", []gContent{say("hi")}, got.emit, got.delta)
	if err != nil {
		t.Fatal(err)
	}
	checkStreamed(t, got, turns, "Hello world")
	if tokens != (tokenCount{In: 30, Out: 10, Reported: true}) {
		t.Fatalf("tokens %+v, want 30 in and 10 out over both steps", tokens)
	}
	if turns[0].Type != "tool_call" || turns[1].Type != "thinking" || turns[1].Text != "Weighing it up." {
		t.Fatalf("turns %+v", turns)
	}
	// The tool-call turn goes back with its signature so Gemini can continue from it.
	replay, _ := json.Marshal((*bodies)[1]["contents"])
	if !strings.Contains(string(replay), `"thoughtSignature":"sig-1"`) || !strings.Contains(string(replay), "functionResponse") {
		t.Fatalf("second call did not replay the tool step: %s", replay)
	}
}

func TestClaudeStreamsTheAnswerAndSumsTokens(t *testing.T) {
	assistHome(t)
	calls := 0
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var body map[string]any
		_ = json.NewDecoder(r.Body).Decode(&body)
		if r.URL.Path != "/v1/messages" || body["stream"] != true {
			t.Errorf("not a streaming Messages call: %s %v", r.URL.Path, body["stream"])
		}
		calls++
		s := newSSE(w)
		start := func(in int) {
			s.send("message_start", map[string]any{"type": "message_start", "message": map[string]any{
				"id": fmt.Sprintf("msg_%d", calls), "type": "message", "role": "assistant", "model": "claude-test",
				"content": []any{}, "stop_reason": nil, "stop_sequence": nil,
				"usage": map[string]any{"input_tokens": in, "output_tokens": 1}}})
		}
		stop := func(reason string, out int) {
			s.send("message_delta", map[string]any{"type": "message_delta",
				"delta": map[string]any{"stop_reason": reason, "stop_sequence": nil}, "usage": map[string]any{"output_tokens": out}})
			s.send("message_stop", map[string]any{"type": "message_stop"})
		}
		if calls == 1 {
			start(10)
			s.send("content_block_start", map[string]any{"type": "content_block_start", "index": 0,
				"content_block": map[string]any{"type": "tool_use", "id": "toolu_1", "name": "list_skills", "input": map[string]any{}}})
			s.send("content_block_delta", map[string]any{"type": "content_block_delta", "index": 0,
				"delta": map[string]any{"type": "input_json_delta", "partial_json": "{}"}})
			s.send("content_block_stop", map[string]any{"type": "content_block_stop", "index": 0})
			stop("tool_use", 4)
			return
		}
		start(20)
		s.send("content_block_start", map[string]any{"type": "content_block_start", "index": 0,
			"content_block": map[string]any{"type": "text", "text": ""}})
		for _, piece := range []string{"Hel", "lo wor", "ld"} {
			s.send("content_block_delta", map[string]any{"type": "content_block_delta", "index": 0,
				"delta": map[string]any{"type": "text_delta", "text": piece}})
		}
		s.send("content_block_stop", map[string]any{"type": "content_block_stop", "index": 0})
		stop("end_turn", 6)
	}))
	t.Cleanup(server.Close)
	previous := claudeBaseURL
	claudeBaseURL = server.URL
	t.Cleanup(func() { claudeBaseURL = previous })

	var got collected
	turns, tokens, err := runClaude(context.Background(), "k", "claude-test", "low", "sys", []gContent{say("hi")}, got.emit, got.delta)
	if err != nil {
		t.Fatal(err)
	}
	checkStreamed(t, got, turns, "Hello world")
	if tokens != (tokenCount{In: 30, Out: 10, Reported: true}) {
		t.Fatalf("tokens %+v, want 30 in and 10 out over both steps", tokens)
	}
}

// fakeResponses stands in for the OpenAI Responses stream: a function call, then an answer.
func fakeResponses(t *testing.T, check func(call int, body map[string]any)) *httptest.Server {
	t.Helper()
	calls := 0
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var body map[string]any
		_ = json.NewDecoder(r.Body).Decode(&body)
		calls++
		if body["stream"] != true {
			t.Errorf("call %d was not a streaming call", calls)
		}
		check(calls, body)
		s := newSSE(w)
		if calls == 1 {
			s.send("response.output_item.done", map[string]any{"type": "response.output_item.done",
				"item": map[string]any{"type": "function_call", "call_id": "c1", "name": "list_skills", "arguments": "{}"}})
			s.send("response.completed", map[string]any{"type": "response.completed",
				"response": map[string]any{"id": "r1", "usage": map[string]any{"input_tokens": 10, "output_tokens": 4}}})
			return
		}
		for _, piece := range []string{"Hel", "lo wor", "ld"} {
			s.send("response.output_text.delta", map[string]any{"type": "response.output_text.delta", "delta": piece})
		}
		s.send("response.output_item.done", map[string]any{"type": "response.output_item.done",
			"item": map[string]any{"type": "message", "content": []any{map[string]any{"type": "output_text", "text": "Hello world"}}}})
		s.send("response.completed", map[string]any{"type": "response.completed",
			"response": map[string]any{"id": "r2", "usage": map[string]any{"input_tokens": 20, "output_tokens": 6}}})
	}))
	t.Cleanup(server.Close)
	return server
}

func TestOpenAIStreamsTheAnswerAndSumsTokens(t *testing.T) {
	assistHome(t)
	server := fakeResponses(t, func(call int, body map[string]any) {
		if call == 2 && body["previous_response_id"] != "r1" {
			t.Errorf("follow-up did not name the first response: %v", body["previous_response_id"])
		}
	})
	previous := openAIBaseURL
	openAIBaseURL = server.URL
	t.Cleanup(func() { openAIBaseURL = previous })

	var got collected
	turns, tokens, err := runOpenAI(context.Background(), "k", "gpt-5.5", "low", "sys", []gContent{say("hi")}, got.emit, got.delta)
	if err != nil {
		t.Fatal(err)
	}
	checkStreamed(t, got, turns, "Hello world")
	if tokens != (tokenCount{In: 30, Out: 10, Reported: true}) {
		t.Fatalf("tokens %+v, want 30 in and 10 out over both steps", tokens)
	}
}

func TestChatGPTStreamsTheAnswerAndSumsTokens(t *testing.T) {
	home := assistHome(t)
	// A sign-in whose token is good for an hour, so no refresh is attempted.
	claims, _ := json.Marshal(map[string]any{"exp": time.Now().Add(time.Hour).Unix()})
	access := "x." + base64.RawURLEncoding.EncodeToString(claims) + ".y"
	auth, _ := json.Marshal(map[string]any{"tokens": map[string]any{
		"access_token": access, "refresh_token": "fixture-refresh", "account_id": "acct"}})
	if err := os.MkdirAll(filepath.Join(home, ".codex"), 0o700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(home, ".codex", "auth.json"), auth, 0o600); err != nil {
		t.Fatal(err)
	}
	server := fakeResponses(t, func(call int, body map[string]any) {
		if call == 2 && !strings.Contains(fmt.Sprint(body["input"]), "function_call_output") {
			t.Errorf("follow-up did not resend the tool result")
		}
	})
	previous := chatGPTEndpoint
	chatGPTEndpoint = server.URL
	t.Cleanup(func() { chatGPTEndpoint = previous })

	var got collected
	turns, tokens, err := runOpenAI(context.Background(), chatGPTKey, "gpt-5.5", "low", "sys", []gContent{say("hi")}, got.emit, got.delta)
	if err != nil {
		t.Fatal(err)
	}
	checkStreamed(t, got, turns, "Hello world")
	if tokens != (tokenCount{In: 30, Out: 10, Reported: true}) {
		t.Fatalf("tokens %+v, want 30 in and 10 out over both steps", tokens)
	}
}

// assistServer serves the chat and conversation routes over a fresh store.
func assistServer(t *testing.T) (*httptest.Server, *convStore) {
	t.Helper()
	store := newConvStore(t.TempDir())
	mux := http.NewServeMux()
	conversationRoutes(mux, testToken, store)
	chatRoutes(mux, testToken, store)
	server := httptest.NewServer(mux)
	t.Cleanup(server.Close)
	return server, store
}

func call(t *testing.T, ctx context.Context, server *httptest.Server, method, path string, body any) *http.Response {
	t.Helper()
	var reader io.Reader
	if body != nil {
		raw, _ := json.Marshal(body)
		reader = bytes.NewReader(raw)
	}
	req, err := http.NewRequestWithContext(ctx, method, server.URL+path, reader)
	if err != nil {
		t.Fatal(err)
	}
	req.Header.Set("X-Csync-Token", testToken)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	return resp
}

func readLine(t *testing.T, lines *bufio.Scanner) map[string]any {
	t.Helper()
	if !lines.Scan() {
		t.Fatalf("the stream ended early: %v", lines.Err())
	}
	var line map[string]any
	if err := json.Unmarshal(lines.Bytes(), &line); err != nil {
		t.Fatalf("not a JSON line: %s", lines.Text())
	}
	return line
}

func readAll(t *testing.T, lines *bufio.Scanner) []map[string]any {
	t.Helper()
	var out []map[string]any
	for lines.Scan() {
		var line map[string]any
		if err := json.Unmarshal(lines.Bytes(), &line); err != nil {
			t.Fatalf("not a JSON line: %s", lines.Text())
		}
		out = append(out, line)
	}
	return out
}

func lastTurn(t *testing.T, store *convStore, id string) map[string]any {
	t.Helper()
	c, err := store.load(id)
	if err != nil || len(c.Transcript) == 0 {
		t.Fatalf("conversation %s: %v, %d entries", id, err, len(c.Transcript))
	}
	return c.Transcript[len(c.Transcript)-1]
}

func TestStreamSendsDeltasThenUsageThenDone(t *testing.T) {
	assistHome(t)
	fakeGemini(t, geminiToolStep, geminiAnswerStep)
	server, store := assistServer(t)
	resp := call(t, context.Background(), server, http.MethodPost, "/chat?stream=1",
		map[string]any{"session": "c1", "message": "hi", "model": "gemini-test"})
	defer resp.Body.Close()
	lines := readAll(t, bufio.NewScanner(resp.Body))

	var deltas strings.Builder
	var kinds []string
	for _, line := range lines {
		for kind := range line {
			if kind == "reply" || kind == "stopped" {
				continue
			}
			kinds = append(kinds, kind)
		}
		if d, ok := line["delta"].(map[string]any); ok {
			deltas.WriteString(d["text"].(string))
		}
	}
	n := len(lines)
	if n < 3 || lines[n-1]["done"] != true || lines[n-2]["usage"] == nil || lines[n-3]["turn"] == nil {
		t.Fatalf("stream should end turn, usage, done: %v", kinds)
	}
	final := lines[n-3]["turn"].(map[string]any)
	if final["text"] != "Hello world" || deltas.String() != "Hello world" || lines[n-1]["reply"] != "Hello world" {
		t.Fatalf("deltas %q, final turn %v", deltas.String(), final)
	}
	spent := lines[n-2]["usage"].(map[string]any)
	if spent["input_tokens"] != float64(30) || spent["output_tokens"] != float64(10) || spent["model"] != "gemini-test" || spent["ms"] == nil {
		t.Fatalf("usage line %v", spent)
	}
	saved := lastTurn(t, store, "c1")
	if saved["text"] != "Hello world" || fmt.Sprint(saved["usage"]) != fmt.Sprint(spent) {
		t.Fatalf("the saved answer does not carry its usage: %v", saved)
	}
	raw, _ := os.ReadFile(filepath.Join(store.dir, "c1.json"))
	if strings.Contains(string(raw), "delta") {
		t.Fatalf("deltas were saved to the conversation")
	}
}

func TestUsageLeavesOutTokensTheProviderDidNotReport(t *testing.T) {
	assistHome(t)
	fakeGemini(t, func(s sse, r *http.Request) {
		s.send("", geminiText("Hi", false))
		s.send("", geminiText(" there", false))
	})
	server, _ := assistServer(t)
	resp := call(t, context.Background(), server, http.MethodPost, "/chat?stream=1",
		map[string]any{"session": "c1", "message": "hi", "model": "gemini-test"})
	defer resp.Body.Close()
	lines := readAll(t, bufio.NewScanner(resp.Body))
	spent := lines[len(lines)-2]["usage"].(map[string]any)
	if _, has := spent["input_tokens"]; has || spent["model"] != "gemini-test" || spent["ms"] == nil {
		t.Fatalf("usage without counts: %v", spent)
	}
}

func TestStopEndsWithThePartialAnswerSaved(t *testing.T) {
	assistHome(t)
	fakeGemini(t, func(s sse, r *http.Request) {
		s.send("", geminiText("Partial ", false))
		s.send("", geminiText("answer", false))
		<-r.Context().Done() // holds the reply open until the run is stopped
	})
	server, store := assistServer(t)
	resp := call(t, context.Background(), server, http.MethodPost, "/chat?stream=1",
		map[string]any{"session": "c1", "message": "hi", "model": "gemini-test"})
	defer resp.Body.Close()
	lines := bufio.NewScanner(resp.Body)
	readLine(t, lines)
	readLine(t, lines) // both pieces have arrived

	stop := call(t, context.Background(), server, http.MethodPost, "/chat/stop", map[string]any{"session": "c1"})
	var answer map[string]any
	_ = json.NewDecoder(stop.Body).Decode(&answer)
	stop.Body.Close()
	if answer["ok"] != true || answer["stopped"] != true {
		t.Fatalf("stop answered %v", answer)
	}

	rest := readAll(t, lines)
	for _, line := range rest {
		if line["error"] != nil {
			t.Fatalf("a stop sent an error line: %v", line)
		}
	}
	n := len(rest)
	if n != 3 {
		t.Fatalf("after a stop want turn, usage, done; got %v", rest)
	}
	final := rest[0]["turn"].(map[string]any)
	if final["text"] != "Partial answer" || final["stopped"] != true {
		t.Fatalf("stopped turn %v", final)
	}
	if rest[2]["done"] != true || rest[2]["stopped"] != true || rest[2]["reply"] != "Partial answer" {
		t.Fatalf("done line %v", rest[2])
	}
	saved := lastTurn(t, store, "c1")
	if saved["text"] != "Partial answer" || saved["stopped"] != true || saved["usage"] == nil {
		t.Fatalf("saved turn %v", saved)
	}

	again := call(t, context.Background(), server, http.MethodPost, "/chat/stop", map[string]any{"session": "c1"})
	_ = json.NewDecoder(again.Body).Decode(&answer)
	again.Body.Close()
	if answer["stopped"] != false {
		t.Fatalf("stop with nothing running answered %v", answer)
	}
}

func TestADroppedPhoneDoesNotCancelTheReply(t *testing.T) {
	assistHome(t)
	held, release := releaser()
	fakeGemini(t, func(s sse, r *http.Request) {
		s.send("", geminiText("Hello ", false))
		select {
		case <-held:
		case <-r.Context().Done():
			return
		}
		s.send("", geminiText("world", false))
	})
	server, store := assistServer(t)
	t.Cleanup(release) // runs before either server shuts down
	ctx, hangUp := context.WithCancel(context.Background())
	resp := call(t, ctx, server, http.MethodPost, "/chat?stream=1",
		map[string]any{"session": "c1", "message": "hi", "model": "gemini-test"})
	readLine(t, bufio.NewScanner(resp.Body))
	hangUp()
	resp.Body.Close()
	time.Sleep(50 * time.Millisecond) // lets the server notice the phone has gone
	release()

	deadline := time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) {
		if last := lastTurn(t, store, "c1"); last["type"] == "text" {
			if last["text"] != "Hello world" || last["stopped"] != nil {
				t.Fatalf("the reply was cut short: %v", last)
			}
			return
		}
		time.Sleep(10 * time.Millisecond)
	}
	t.Fatal("the reply was never saved after the phone dropped")
}

func TestASecondMessageWaitsForTheRunningOne(t *testing.T) {
	assistHome(t)
	held, release := releaser()
	fakeGemini(t, func(s sse, r *http.Request) {
		s.send("", geminiText("First ", false))
		select {
		case <-held:
		case <-r.Context().Done():
			return
		}
		s.send("", geminiText("answer", false))
	})
	server, store := assistServer(t)
	t.Cleanup(release) // runs before either server shuts down
	resp := call(t, context.Background(), server, http.MethodPost, "/chat?stream=1",
		map[string]any{"session": "c1", "message": "one", "model": "gemini-test"})
	defer resp.Body.Close()
	lines := bufio.NewScanner(resp.Body)
	readLine(t, lines)

	second := call(t, context.Background(), server, http.MethodPost, "/chat?stream=1",
		map[string]any{"session": "c1", "message": "two", "model": "gemini-test"})
	text, _ := io.ReadAll(second.Body)
	second.Body.Close()
	if second.StatusCode != http.StatusConflict || !strings.Contains(string(text), "still answering") {
		t.Fatalf("second message got %d %q", second.StatusCode, text)
	}
	release()
	readAll(t, lines)
	c, _ := store.load("c1")
	users := 0
	for _, entry := range c.Transcript {
		if entry["role"] == "user" {
			users++
		}
	}
	if users != 1 {
		t.Fatalf("the refused message was saved: %d user messages", users)
	}
}

func saveConversation(t *testing.T, store *convStore, id string, updated int64, said ...string) {
	t.Helper()
	c := &conversation{ID: id, Title: "Chat " + id, Updated: updated}
	for i, text := range said {
		if i%2 == 0 {
			c.Transcript = append(c.Transcript, map[string]any{"role": "user", "text": text})
		} else {
			c.Transcript = append(c.Transcript, map[string]any{"type": "tool_call", "name": "notes"},
				map[string]any{"type": "text", "text": text})
		}
	}
	if err := store.save(c); err != nil {
		t.Fatal(err)
	}
}

func searchFor(t *testing.T, server *httptest.Server, q string) (int, []map[string]any) {
	t.Helper()
	resp := call(t, context.Background(), server, http.MethodGet, "/conversations/search?q="+q, nil)
	defer resp.Body.Close()
	var body struct {
		Results []map[string]any `json:"results"`
	}
	_ = json.NewDecoder(resp.Body).Decode(&body)
	return resp.StatusCode, body.Results
}

func TestSearchFindsWhatWasSaid(t *testing.T) {
	server, store := assistServer(t)
	saveConversation(t, store, "old", 1, "Where is the holiday video?", "It is on the Pi USB drive.")
	saveConversation(t, store, "new", 2, "Order a PIZZA for tonight", "Done, a pizza is on its way.")
	saveConversation(t, store, "other", 3, "What is the weather", "Sunny.")

	if code, results := searchFor(t, server, "pizza"); code != 200 || len(results) != 1 || results[0]["id"] != "new" ||
		results[0]["index"] != float64(0) || !strings.Contains(results[0]["snippet"].(string), "PIZZA") {
		t.Fatalf("a user message did not match ignoring case: %d %v", code, results)
	}
	// The assistant's answer is transcript entry 2, after the user message and a tool call.
	if _, results := searchFor(t, server, "usb%20DRIVE"); len(results) != 1 || results[0]["id"] != "old" || results[0]["index"] != float64(2) {
		t.Fatalf("an assistant answer did not match: %v", results)
	}
	if _, results := searchFor(t, server, "notes"); len(results) != 0 {
		t.Fatalf("a tool call matched, want only messages and answers: %v", results)
	}
	if code, results := searchFor(t, server, "nothing%20like%20this"); code != 200 || results == nil || len(results) != 0 {
		t.Fatalf("a miss should be an empty list: %d %v", code, results)
	}
	if code, _ := searchFor(t, server, ""); code != http.StatusBadRequest {
		t.Fatalf("an empty search got %d", code)
	}
	if _, results := searchFor(t, server, "is"); len(results) != 3 || results[0]["id"] != "other" || results[2]["id"] != "old" {
		t.Fatalf("results are not newest first: %v", results)
	}
}

func TestSearchReturnsAtMostFifty(t *testing.T) {
	server, store := assistServer(t)
	for i := range 55 {
		saveConversation(t, store, fmt.Sprintf("c%02d", i), int64(i), "tell me about lamps")
	}
	_, results := searchFor(t, server, "lamps")
	if len(results) != 50 || results[0]["id"] != "c54" {
		t.Fatalf("got %d results, want the newest 50", len(results))
	}
}

func TestSearchIsNotReadAsAConversationId(t *testing.T) {
	server, store := assistServer(t)
	saveConversation(t, store, "abc", 1, "hello there")
	resp := call(t, context.Background(), server, http.MethodGet, "/conversations/search?q=hello", nil)
	var body map[string]any
	_ = json.NewDecoder(resp.Body).Decode(&body)
	resp.Body.Close()
	if _, ok := body["results"]; !ok || body["transcript"] != nil {
		t.Fatalf("search was read as a conversation: %v", body)
	}
	resp = call(t, context.Background(), server, http.MethodGet, "/conversations/abc", nil)
	_ = json.NewDecoder(resp.Body).Decode(&body)
	resp.Body.Close()
	if body["id"] != "abc" || body["transcript"] == nil {
		t.Fatalf("a conversation stopped loading by id: %v", body)
	}
}

func TestSkillsListsTheSavedSkills(t *testing.T) {
	assistHome(t)
	if err := os.WriteFile(filepath.Join(skillsDir(), "tea.md"), []byte("# Make tea\n\nBoil water first."), 0o600); err != nil {
		t.Fatal(err)
	}
	server, _ := assistServer(t)
	resp := call(t, context.Background(), server, http.MethodGet, "/skills", nil)
	defer resp.Body.Close()
	var body struct {
		Skills []map[string]any `json:"skills"`
	}
	_ = json.NewDecoder(resp.Body).Decode(&body)
	if len(body.Skills) != 1 || body.Skills[0]["name"] != "tea" || body.Skills[0]["summary"] != "Make tea" {
		t.Fatalf("skills %v", body.Skills)
	}
	req, _ := http.NewRequest(http.MethodGet, server.URL+"/skills", nil)
	if resp, _ := http.DefaultClient.Do(req); resp.StatusCode != http.StatusUnauthorized {
		t.Fatalf("skills without the token got %d", resp.StatusCode)
	}
}
