// Command csync-agent is the trusted-device half of csync: a small peer that
// every one of your machines runs, listening on the tailnet to receive text,
// files, and images, and able to send them to any other peer. Discovery rides
// on Tailscale (identity and reachability); the wire protocol is plain HTTP over
// the tailnet, gated by a shared token.
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
)

func usage() {
	fmt.Print(`csync-agent — the csync mesh peer

Usage:
  csync-agent serve                 start the receiver (binds to this device's tailnet IP)
  csync-agent peers                 list tailnet peers and which run an agent
  csync-agent send <peer> [items]   send to a peer by name or IP
        --text "..."                send literal text (lands on the peer's clipboard on macOS)
        <path>                      send a file or image (repeatable)
  csync-agent whoami                print this device's identity
  csync-agent token [--show]        print the shared mesh token (mint one if absent)

Examples:
  csync-agent send aakarshs-m5-pro --text "hello from the pi"
  csync-agent send aakarshs-m5-pro ~/report.pdf ~/shot.png
`)
}

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	var err error
	switch os.Args[1] {
	case "serve":
		err = serve()
	case "peers":
		err = cmdPeers()
	case "send":
		err = cmdSend(os.Args[2:])
	case "whoami":
		err = cmdWhoAmI()
	case "token":
		err = cmdToken()
	case "-h", "--help", "help":
		usage()
	default:
		fmt.Fprintf(os.Stderr, "unknown command %q\n", os.Args[1])
		usage()
		os.Exit(2)
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, "error:", err)
		os.Exit(1)
	}
}

func cmdWhoAmI() error {
	b, _ := json.MarshalIndent(localWhoAmI(), "", "  ")
	fmt.Println(string(b))
	return nil
}

func cmdToken() error {
	t, err := loadOrCreateToken()
	if err != nil {
		return err
	}
	fmt.Println(t)
	fmt.Fprintf(os.Stderr, "\n(copy this to every device you trust, at %s)\n", tokenPath())
	return nil
}

func cmdPeers() error {
	token, err := loadToken()
	if err != nil {
		return err
	}
	peers, err := scanPeers(token)
	if err != nil {
		return err
	}
	if len(peers) == 0 {
		fmt.Println("no tailnet peers found")
		return nil
	}
	fmt.Printf("%-24s %-16s %-8s %s\n", "PEER", "IP", "AGENT", "PLATFORM")
	for _, p := range peers {
		agent := "-"
		if p.Reachable {
			agent = "yes"
		} else if p.Online {
			agent = "no"
		} else {
			agent = "offline"
		}
		fmt.Printf("%-24s %-16s %-8s %s\n", p.Name, p.IP, agent, p.Platform)
	}
	return nil
}

func cmdSend(args []string) error {
	if len(args) < 1 {
		return fmt.Errorf("usage: csync-agent send <peer> [--text \"...\"] [file ...]")
	}
	peer := args[0]
	rest := args[1:]

	token, err := loadToken()
	if err != nil {
		return err
	}
	ip, err := resolvePeer(peer)
	if err != nil {
		return err
	}
	from := selfName()

	if len(rest) == 0 {
		return fmt.Errorf("nothing to send: pass --text \"...\" or one or more file paths")
	}

	for i := 0; i < len(rest); i++ {
		a := rest[i]
		switch {
		case a == "--text":
			if i+1 >= len(rest) {
				return fmt.Errorf("--text needs a value")
			}
			i++
			if err := sendItem(ip, token, from, "text", rest[i]); err != nil {
				return err
			}
		default:
			kind := "file"
			if isImage(a) {
				kind = "image"
			}
			if err := sendItem(ip, token, from, kind, a); err != nil {
				return err
			}
		}
	}
	return nil
}

func isImage(path string) bool {
	ext := strings.ToLower(path)
	for _, s := range []string{".png", ".jpg", ".jpeg", ".gif", ".webp", ".heic", ".bmp"} {
		if strings.HasSuffix(ext, s) {
			return true
		}
	}
	return false
}
