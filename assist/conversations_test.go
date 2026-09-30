package main

import (
	"errors"
	"testing"
)

func say(text string) gContent { return gContent{Role: "user", Parts: []gPart{{Text: text}}} }

func TestConversationSurvivesAReload(t *testing.T) {
	dir := t.TempDir()
	first := newConvStore(dir)
	if _, err := first.userTurn("phone-1", "Which drives are connected?", say("Which drives are connected?")); err != nil {
		t.Fatal(err)
	}
	first.assistantTurn("phone-1", turn{Type: "text", Text: "Pi USB."})
	first.answered("phone-1", "Pi USB.")

	// A second store on the same folder stands in for the assistant restarting.
	again, err := newConvStore(dir).load("phone-1")
	if err != nil {
		t.Fatal(err)
	}
	if again.Title != "Which drives are connected?" || len(again.Transcript) != 2 || len(again.History) != 2 {
		t.Fatalf("after a reload: title %q, %d transcript entries, %d history entries", again.Title, len(again.Transcript), len(again.History))
	}
}

func TestRewindDropsTheMessageAndEverythingAfterIt(t *testing.T) {
	s := newConvStore(t.TempDir())
	for _, q := range []string{"one", "two", "three"} {
		if _, err := s.userTurn("c", q, say(q)); err != nil {
			t.Fatal(err)
		}
		s.assistantTurn("c", turn{Type: "tool_call", Name: "media_drives"})
		s.assistantTurn("c", turn{Type: "text", Text: "answer to " + q})
		s.answered("c", "answer to "+q)
	}
	// Entry 3 is the second question: keep the first exchange only.
	c, err := s.rewind("c", 3)
	if err != nil {
		t.Fatal(err)
	}
	if len(c.Transcript) != 3 {
		t.Fatalf("transcript has %d entries, want 3", len(c.Transcript))
	}
	if len(c.History) != 2 || c.History[0].Parts[0].Text != "one" || c.History[1].Role != "model" {
		t.Fatalf("history after rewind: %+v", c.History)
	}
}

func TestRewindPastTheEndChangesNothing(t *testing.T) {
	s := newConvStore(t.TempDir())
	_, _ = s.userTurn("c", "one", say("one"))
	c, _ := s.rewind("c", 9)
	if len(c.Transcript) != 1 || len(c.History) != 1 {
		t.Fatalf("got %d transcript and %d history entries, want 1 and 1", len(c.Transcript), len(c.History))
	}
}

func TestAnIdCannotLeaveTheFolder(t *testing.T) {
	s := newConvStore(t.TempDir())
	for _, id := range []string{"../etc/passwd", "a/b", "", ".hidden", "with space"} {
		if _, err := s.userTurn(id, "x", say("x")); !errors.Is(err, errBadConversation) {
			t.Errorf("id %q: got %v, want it refused", id, err)
		}
	}
}

func TestListIsNewestFirstAndCountsMessages(t *testing.T) {
	s := newConvStore(t.TempDir())
	_, _ = s.userTurn("old", "first", say("first"))
	_, _ = s.userTurn("new", "second", say("second"))
	s.assistantTurn("new", turn{Type: "thinking", Text: "hm"})
	s.assistantTurn("new", turn{Type: "text", Text: "done"})
	got := s.list()
	if len(got) != 2 || got[0]["id"] != "new" || got[0]["messages"] != 2 {
		t.Fatalf("list: %+v", got)
	}
}
