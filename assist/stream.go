package main

import (
	"bufio"
	"context"
	"io"
	"strings"
)

// The pieces every provider's runner shares while it answers one message: the
// words streamed so far, the tokens spent, and whether the owner pressed stop.

// tokenCount is what one run spent across all of its tool steps. Reported stays
// false when the provider never said, so the app can show nothing rather than zero.
type tokenCount struct {
	In, Out  int64
	Reported bool
}

// usage is what one reply cost, as the app shows it under the answer. The token
// counts are left out when the provider did not report them.
type usage struct {
	InputTokens  *int64 `json:"input_tokens,omitempty"`
	OutputTokens *int64 `json:"output_tokens,omitempty"`
	Ms           int64  `json:"ms"`
	Model        string `json:"model"`
}

func newUsage(tokens tokenCount, ms int64, model string) *usage {
	u := &usage{Ms: ms, Model: model}
	if tokens.Reported {
		in, out := tokens.In, tokens.Out
		u.InputTokens, u.OutputTokens = &in, &out
	}
	return u
}

// runState follows one run from the owner's message to its answer.
//
// Answer text goes through text(), which streams it to the app and remembers it,
// so a stop can save whatever had arrived. A stop is the run's context being
// cancelled; a runner checks stopped() after each provider call and before the
// next one, which lets a tool that is already running finish first.
type runState struct {
	ctx     context.Context
	emit    func(turn)
	delta   func(string)
	turns   []turn
	partial strings.Builder
	tokens  tokenCount
}

func newRunState(ctx context.Context, emit func(turn), delta func(string)) *runState {
	return &runState{ctx: ctx, emit: emit, delta: delta}
}

func (r *runState) add(t turn) {
	r.turns = append(r.turns, t)
	if r.emit != nil {
		r.emit(t)
	}
}

// step starts a new call to the provider; answer text from an earlier step is
// not part of the reply.
func (r *runState) step() { r.partial.Reset() }

func (r *runState) text(s string) {
	if s == "" {
		return
	}
	r.partial.WriteString(s)
	if r.delta != nil {
		r.delta(s)
	}
}

func (r *runState) count(in, out int64) {
	r.tokens.In += in
	r.tokens.Out += out
	r.tokens.Reported = true
}

func (r *runState) stopped() bool { return r.ctx.Err() != nil }

// stop ends the run with the answer as far as it got, marked as stopped.
func (r *runState) stop() ([]turn, tokenCount, error) {
	r.add(turn{Type: "text", Text: r.partial.String(), Stopped: true})
	return r.turns, r.tokens, nil
}

// answer ends the run with its final text.
func (r *runState) answer(text string) ([]turn, tokenCount, error) {
	r.add(turn{Type: "text", Text: text})
	return r.turns, r.tokens, nil
}

func (r *runState) fail(err error) ([]turn, tokenCount, error) {
	if r.stopped() {
		return r.stop()
	}
	return r.turns, r.tokens, err
}

// readSSE calls fn with the data of each server-sent event until fn says it is
// done or the stream ends. Gemini, OpenAI and the ChatGPT endpoint all stream
// this way, with one JSON object per data line.
func readSSE(body io.Reader, fn func(data []byte) (done bool, err error)) error {
	lines := bufio.NewScanner(body)
	lines.Buffer(make([]byte, 0, 1<<20), 32<<20)
	for lines.Scan() {
		data, ok := strings.CutPrefix(lines.Text(), "data:")
		if !ok {
			continue
		}
		data = strings.TrimSpace(data)
		if data == "" || data == "[DONE]" {
			continue
		}
		done, err := fn([]byte(data))
		if err != nil || done {
			return err
		}
	}
	return lines.Err()
}
