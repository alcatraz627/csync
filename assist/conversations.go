package main

import (
	"encoding/json"
	"errors"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"sync"
	"time"
	"unicode/utf8"
)

// A conversation is kept on this device, not on the phone that started it, so
// any client the owner opens later sees the same chats and the assistant keeps
// its context across a restart. The phone holds a copy for reading offline.
//
// Each conversation is one JSON file. Transcript is what a person sees (their
// messages, and the assistant's thinking, tool calls and answers). History is
// what the model is replayed; it is shorter, because only final answers go back.
type conversation struct {
	ID         string           `json:"id"`
	Title      string           `json:"title"`
	Updated    int64            `json:"updated"`
	Model      string           `json:"model,omitempty"`
	Effort     string           `json:"effort,omitempty"`
	Favorite   bool             `json:"favorite,omitempty"`
	Archived   bool             `json:"archived,omitempty"`
	Transcript []map[string]any `json:"transcript"`
	History    []gContent       `json:"history,omitempty"`
}

type convStore struct {
	mu  sync.Mutex
	dir string
}

var convID = regexp.MustCompile(`^[A-Za-z0-9._-]{1,120}$`)

var errBadConversation = errors.New("that is not a conversation id")

func conversationsDir() string {
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".local", "state", "csync", "conversations")
}

func newConvStore(dir string) *convStore {
	_ = os.MkdirAll(dir, 0o700)
	return &convStore{dir: dir}
}

func (s *convStore) path(id string) (string, error) {
	if !convID.MatchString(id) || strings.HasPrefix(id, ".") {
		return "", errBadConversation
	}
	return filepath.Join(s.dir, id+".json"), nil
}

// load returns the saved conversation, or a fresh empty one when none is saved yet.
func (s *convStore) load(id string) (*conversation, error) {
	p, err := s.path(id)
	if err != nil {
		return nil, err
	}
	c := &conversation{ID: id, Transcript: []map[string]any{}}
	data, err := os.ReadFile(p)
	if errors.Is(err, os.ErrNotExist) {
		return c, nil
	}
	if err != nil {
		return nil, err
	}
	if err := json.Unmarshal(data, c); err != nil {
		return nil, err
	}
	c.ID = id
	return c, nil
}

// save writes through a temporary file so a crash mid-write cannot leave half a conversation.
func (s *convStore) save(c *conversation) error {
	p, err := s.path(c.ID)
	if err != nil {
		return err
	}
	data, err := json.Marshal(c)
	if err != nil {
		return err
	}
	tmp := p + ".tmp"
	if err := os.WriteFile(tmp, data, 0o600); err != nil {
		return err
	}
	return os.Rename(tmp, p)
}

// change loads a conversation, lets fn alter it, stamps it and saves it, all under one lock.
func (s *convStore) change(id string, fn func(*conversation)) (*conversation, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	c, err := s.load(id)
	if err != nil {
		return nil, err
	}
	fn(c)
	c.Updated = time.Now().UnixMilli()
	return c, s.save(c)
}

// userTurn records what the person said and returns the history to replay to the model.
func (s *convStore) userTurn(id, text string, content gContent) ([]gContent, error) {
	c, err := s.change(id, func(c *conversation) {
		if c.Title == "" {
			c.Title = titleFrom(text)
		}
		c.Transcript = append(c.Transcript, map[string]any{"role": "user", "text": text, "at": time.Now().UnixMilli()})
		c.History = append(c.History, content)
		if len(c.History) > maxTurns {
			c.History = c.History[len(c.History)-maxTurns:]
		}
	})
	if err != nil {
		return nil, err
	}
	return append([]gContent(nil), c.History...), nil
}

// assistantTurn records one step of the reply as it happens.
func (s *convStore) assistantTurn(id string, t turn) {
	var entry map[string]any
	raw, _ := json.Marshal(t)
	if json.Unmarshal(raw, &entry) != nil || entry == nil {
		return
	}
	// When it happened, so a device can group messages by day and show the time in each.
	entry["at"] = time.Now().UnixMilli()
	_, _ = s.change(id, func(c *conversation) { c.Transcript = append(c.Transcript, entry) })
}

// answered adds the final answer to what the model is replayed next time.
func (s *convStore) answered(id, reply string) {
	if reply == "" {
		return
	}
	_, _ = s.change(id, func(c *conversation) {
		c.History = append(c.History, gContent{Role: "model", Parts: []gPart{{Text: reply}}})
	})
}

// rewind cuts a conversation back to its first keep transcript entries, so a message
// can be edited or an answer asked for again. The model's history loses the same
// number of the person's messages from its end, and everything after them.
func (s *convStore) rewind(id string, keep int) (*conversation, error) {
	return s.change(id, func(c *conversation) {
		if keep < 0 || keep >= len(c.Transcript) {
			return
		}
		dropped := 0
		for _, entry := range c.Transcript[keep:] {
			if entry["role"] == "user" {
				dropped++
			}
		}
		c.Transcript = c.Transcript[:keep]
		for dropped > 0 && len(c.History) > 0 {
			last := c.History[len(c.History)-1]
			c.History = c.History[:len(c.History)-1]
			if last.Role == "user" {
				dropped--
			}
		}
	})
}

func (s *convStore) remove(id string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	p, err := s.path(id)
	if err != nil {
		return err
	}
	if err := os.Remove(p); err != nil && !errors.Is(err, os.ErrNotExist) {
		return err
	}
	return nil
}

// list returns every conversation without its transcript, newest first.
func (s *convStore) list() []map[string]any {
	s.mu.Lock()
	defer s.mu.Unlock()
	entries, _ := os.ReadDir(s.dir)
	out := []map[string]any{}
	for _, e := range entries {
		id, ok := strings.CutSuffix(e.Name(), ".json")
		if !ok {
			continue
		}
		c, err := s.load(id)
		if err != nil {
			continue
		}
		said := 0
		for _, entry := range c.Transcript {
			if entry["role"] == "user" || entry["type"] == "text" {
				said++
			}
		}
		out = append(out, map[string]any{"id": c.ID, "title": c.Title, "updated": c.Updated, "model": c.Model,
			"effort": c.Effort, "favorite": c.Favorite, "archived": c.Archived, "messages": said})
	}
	sort.Slice(out, func(i, j int) bool { return out[i]["updated"].(int64) > out[j]["updated"].(int64) })
	return out
}

// maxSearchResults caps how many conversations one search returns.
const maxSearchResults = 50

// search finds the conversations where the owner or the assistant said q,
// ignoring case, newest first. Each result carries a snippet around the first
// place it was said and that message's position in the transcript.
func (s *convStore) search(q string) []map[string]any {
	s.mu.Lock()
	defer s.mu.Unlock()
	entries, _ := os.ReadDir(s.dir)
	out := []map[string]any{}
	for _, e := range entries {
		id, ok := strings.CutSuffix(e.Name(), ".json")
		if !ok {
			continue
		}
		c, err := s.load(id)
		if err != nil {
			continue
		}
		for i, entry := range c.Transcript {
			if entry["role"] != "user" && entry["type"] != "text" {
				continue
			}
			text, _ := entry["text"].(string)
			at := indexFold(text, q)
			if at < 0 {
				continue
			}
			out = append(out, map[string]any{"id": c.ID, "title": c.Title, "updated": c.Updated,
				"snippet": snippet(text, at), "index": i})
			break
		}
	}
	sort.Slice(out, func(i, j int) bool { return out[i]["updated"].(int64) > out[j]["updated"].(int64) })
	if len(out) > maxSearchResults {
		out = out[:maxSearchResults]
	}
	return out
}

// indexFold is strings.Index ignoring case, returning a byte offset into s.
func indexFold(s, sub string) int {
	for i := range s {
		if hasPrefixFold(s[i:], sub) {
			return i
		}
	}
	return -1
}

func hasPrefixFold(s, prefix string) bool {
	for _, want := range prefix {
		got, size := utf8.DecodeRuneInString(s)
		if size == 0 || got != want && !strings.EqualFold(string(got), string(want)) {
			return false
		}
		s = s[size:]
	}
	return true
}

// snippet is about 120 characters of text on one line, starting a little before
// the match at byte offset at, marked with ... where it was cut.
func snippet(text string, at int) string {
	const before, width = 40, 120
	runes := []rune(text)
	start := max(0, utf8.RuneCountInString(text[:at])-before)
	end := min(len(runes), start+width)
	if end == len(runes) {
		start = max(0, end-width)
	}
	out := strings.Join(strings.Fields(string(runes[start:end])), " ")
	if start > 0 {
		out = "..." + out
	}
	if end < len(runes) {
		out += "..."
	}
	return out
}

// titleFrom makes a short title from a first message: one line, cut at a word.
func titleFrom(text string) string {
	line := strings.TrimSpace(strings.SplitN(text, "\n", 2)[0])
	if len(line) <= 40 {
		return line
	}
	if cut := strings.LastIndex(line[:40], " "); cut > 20 {
		return line[:cut]
	}
	return line[:40]
}

// conversationRoutes serves the saved conversations to the owner's devices:
// GET /conversations lists them, GET /conversations/<id> returns one in full,
// POST /conversations/<id> changes its title, favourite, archive, model or effort,
// POST /conversations/<id>/rewind cuts it back, and DELETE removes it.
// GET /conversations/search?q= finds conversations by what was said in them.
func conversationRoutes(mux *http.ServeMux, token string, convs *convStore) {
	mux.HandleFunc("/conversations", func(w http.ResponseWriter, r *http.Request) {
		if !authed(w, r, token) {
			return
		}
		writeJSON(w, map[string]any{"conversations": convs.list()})
	})
	// An exact path wins over the /conversations/ prefix, so "search" is never read as an id.
	mux.HandleFunc("/conversations/search", func(w http.ResponseWriter, r *http.Request) {
		if !authed(w, r, token) {
			return
		}
		q := strings.TrimSpace(r.URL.Query().Get("q"))
		if q == "" {
			http.Error(w, "say what to search for with ?q=", http.StatusBadRequest)
			return
		}
		writeJSON(w, map[string]any{"results": convs.search(q)})
	})
	mux.HandleFunc("/conversations/", func(w http.ResponseWriter, r *http.Request) {
		if !authed(w, r, token) {
			return
		}
		rest := strings.TrimPrefix(r.URL.Path, "/conversations/")
		id, action, _ := strings.Cut(rest, "/")
		fail := func(err error) {
			code := http.StatusInternalServerError
			if errors.Is(err, errBadConversation) {
				code = http.StatusBadRequest
			}
			http.Error(w, err.Error(), code)
		}
		switch {
		case r.Method == http.MethodGet && action == "":
			c, err := convs.load(id)
			if err != nil {
				fail(err)
				return
			}
			c.History = nil
			writeJSON(w, c)
		case r.Method == http.MethodDelete && action == "":
			if err := convs.remove(id); err != nil {
				fail(err)
				return
			}
			writeJSON(w, map[string]any{"ok": true})
		case r.Method == http.MethodPost && action == "rewind":
			var req struct {
				Keep int `json:"keep"`
			}
			if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
				http.Error(w, "need JSON {keep}", http.StatusBadRequest)
				return
			}
			c, err := convs.rewind(id, req.Keep)
			if err != nil {
				fail(err)
				return
			}
			writeJSON(w, map[string]any{"ok": true, "messages": len(c.Transcript)})
		case r.Method == http.MethodPost && action == "":
			var req struct {
				Title    *string `json:"title"`
				Favorite *bool   `json:"favorite"`
				Archived *bool   `json:"archived"`
				Model    *string `json:"model"`
				Effort   *string `json:"effort"`
			}
			if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
				http.Error(w, "need a JSON object", http.StatusBadRequest)
				return
			}
			_, err := convs.change(id, func(c *conversation) {
				if req.Title != nil {
					c.Title = *req.Title
				}
				if req.Favorite != nil {
					c.Favorite = *req.Favorite
				}
				if req.Archived != nil {
					c.Archived = *req.Archived
				}
				if req.Model != nil {
					c.Model = *req.Model
				}
				if req.Effort != nil {
					c.Effort = *req.Effort
				}
			})
			if err != nil {
				fail(err)
				return
			}
			writeJSON(w, map[string]any{"ok": true})
		default:
			http.Error(w, "not found", http.StatusNotFound)
		}
	})
}
