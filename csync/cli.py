"""The csync command line. Every verb prints the host row first and the outcome last,
takes --json, and never asks a question when nothing is watching."""

import argparse
import atexit
import json
import os
import subprocess
import sys
import time

from . import __version__, doctor, emit, funnel, invite, keys, ops, paths, recipes, relay, state, teardown, tunnel
from .envcfg import env
from .errors import USAGE, CsyncError

READ_VERBS = {"ls", "status", "log", "wait", "pull", "shot", "info", "logs", "recipes", "doctor", "recipe-dry"}
HOST_VERBS = {"wait", "sh", "run", "push", "pull", "shot", "info", "logs", "recipe", "open", "say", "teardown", "persist"}


def actor():
    forced = env("CSYNC_ACTOR")
    if forced in ("human", "agent"):
        return forced
    if env("CLAUDECODE") or not sys.stdout.isatty():
        return "agent"
    return "human"


def build_parser():
    p = argparse.ArgumentParser(prog="csync", description="Drive another laptop from this one after a single pasted line there.")
    p.add_argument("--json", action="store_true", help="one JSON object on stdout, no prompts")
    p.add_argument("--allow-write", action="store_true", help="let an agent actor run a writing verb")
    p.add_argument("--yes", action="store_true", help="skip the confirmation on destructive verbs")
    p.add_argument("--version", action="version", version=__version__)
    sp = p.add_subparsers(dest="verb")

    s = sp.add_parser("init", help="prepare this Mac as the console")
    s.add_argument("--no-funnel", action="store_true")
    s.add_argument("--no-launchd", action="store_true", help="start the relay sshd directly instead of a LaunchAgent")
    s.add_argument("--relay-port", type=int)
    s.add_argument("--funnel-port", type=int)
    s.add_argument("--bind")
    s.add_argument("--lan-ip", help="the address LAN targets reach this Mac on; auto-detected when unset")
    s.add_argument("--console-name")

    s = sp.add_parser("doctor", help="check the console and print the fixing command per failure")
    s.add_argument("--fix", action="store_true")

    s = sp.add_parser("invite", help="mint the one line to paste on the other laptop")
    s.add_argument("name")
    s.add_argument("--route", default="auto", choices=["auto", "lan", "funnel"])
    s.add_argument("--ttl")
    s.add_argument("--expires")
    s.add_argument("--src")
    s.add_argument("--relay-host", help="address the target dials for the reverse tunnel on the lan route; use the console's tailnet IP to reach the relay directly over the tailnet, skipping Funnel")
    s.add_argument("--target-port", type=int, default=22, help=argparse.SUPPRESS)
    s.add_argument("--show-script", action="store_true", help="print bootstrap.sh instead of the paste line")

    s = sp.add_parser("wait", help="block until a host connects")
    s.add_argument("name")
    s.add_argument("--timeout", default="10m")

    s = sp.add_parser("ls", help="hosts")
    s.add_argument("--all", action="store_true")
    sp.add_parser("status", help="hosts plus relay, Funnel, Tailscale health")

    s = sp.add_parser("log", help="the audit journal, or the relay log")
    s.add_argument("name", nargs="?")
    s.add_argument("--last", type=int, default=20)
    s.add_argument("--relay", action="store_true")

    s = sp.add_parser("sh", help="interactive shell")
    s.add_argument("name")

    s = sp.add_parser("run", help="run a command")
    s.add_argument("name")
    s.add_argument("--force", action="store_true", help="lift the target's refusals for this command; needs a terminal")
    s.add_argument("--full", action="store_true")
    s.add_argument("--timeout", type=int)
    s.add_argument("cmd", nargs="*", help="after --")

    s = sp.add_parser("push", help="copy files to the host")
    s.add_argument("name")
    s.add_argument("paths", nargs="+")
    s.add_argument("--overwrite", action="store_true")
    s.add_argument("--dry-run", action="store_true")

    s = sp.add_parser("pull", help="copy files from the host")
    s.add_argument("name")
    s.add_argument("paths", nargs="+")

    s = sp.add_parser("shot", help="screenshot")
    s.add_argument("name")
    s.add_argument("--display", type=int, default=1)
    s.add_argument("--open", action="store_true")

    s = sp.add_parser("info", help="hardware and devices")
    s.add_argument("name")
    s.add_argument("sections", nargs="*")

    s = sp.add_parser("logs", help="system and crash logs, bundled")
    s.add_argument("name")
    s.add_argument("--since", default="1h")
    s.add_argument("--app")
    s.add_argument("--crash", action="store_true")

    s = sp.add_parser("recipe", help="run a reviewed script from recipes/")
    s.add_argument("name")
    s.add_argument("recipe")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--dev", action="store_true")
    s.add_argument("args", nargs="*", help="after --")
    sp.add_parser("recipes", help="list recipes")

    s = sp.add_parser("open", help="open a URL, app, or path on the host's screen")
    s.add_argument("name")
    s.add_argument("target")

    s = sp.add_parser("say", help="show a notification on the host's screen")
    s.add_argument("name")
    s.add_argument("text")

    s = sp.add_parser("persist", help="turn the host's always-on behaviour on or off (Android wake-lock and boot script)")
    s.add_argument("name")
    s.add_argument("action", nargs="?", default="status", choices=["on", "off", "status"])

    s = sp.add_parser("teardown", help="undo the session on both ends")
    s.add_argument("name")
    s.add_argument("--verify", action="store_true")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--no-receipt", action="store_true")

    s = sp.add_parser("forget", help="drop a host record whose tunnel is already gone")
    s.add_argument("name")

    s = sp.add_parser("revoke", help="close invites")
    s.add_argument("--all", action="store_true")

    s = sp.add_parser("relay-hello", help=argparse.SUPPRESS)
    s.add_argument("invite_id")
    return p


def confirm(prompt, args):
    if args.yes:
        return True
    if args.json or not sys.stdin.isatty():
        raise CsyncError(USAGE, "this needs a confirmation and nothing is watching", fix="add --yes")
    sys.stdout.write(f"{prompt} [y/N] ")
    sys.stdout.flush()
    return sys.stdin.readline().strip().lower() in ("y", "yes")


def out_human(text=""):
    sys.stdout.write(text + ("\n" if not text.endswith("\n") else ""))


def do_init(args, cfg):
    paths.ensure_dirs()
    for k, v in (("relay_port", args.relay_port), ("funnel_port", args.funnel_port), ("relay_bind", args.bind), ("console_name", args.console_name), ("lan_ip", args.lan_ip)):
        if v:
            cfg[k] = v
    state.save_config(cfg)
    keys.ensure_key(paths.CONSOLE_KEY, "csync-console")
    relay.write_config(cfg)
    if not paths.HOSTS.exists():
        state.save_hosts({})
    if args.no_launchd:
        if not relay.pid_alive():
            relay.start_daemon()
        relay_how = f"sshd pid {relay.pid_alive()}"
    else:
        relay.install_agent()
        relay_how = paths.LAUNCH_LABEL
    fun = "skipped"
    if not args.no_funnel:
        funnel.up()
        if not funnel.funnel_ready(cfg["funnel_port"], cfg["relay_port"]):
            funnel.funnel_on(cfg["funnel_port"], cfg["relay_port"])
        fun = f"{funnel.dns_name()}:{cfg['funnel_port']} → localhost:{cfg['relay_port']}"
    rows = doctor.checks(cfg)
    return {"relay": relay_how, "funnel": fun, "checks": rows, "next": "csync invite <name>"}


def do_status(cfg):
    hosts = state.load_hosts()
    for h in hosts.values():
        if h.get("status") == "online" and not tunnel.hello_alive(h):
            h["status"] = "offline"
    rows = doctor.checks(cfg)
    return {"hosts": hosts, "checks": rows}


def show_checks(rows):
    for r in rows:
        mark = emit.green("ok  ") if r["ok"] else emit.red("FAIL")
        line = f"{mark} {r['check']:<24} {r['detail']}"
        if not r["ok"] and r.get("fix"):
            line += emit.dim(f"   fix: {r['fix']}")
        out_human(line)


def main(argv=None):
    parser = build_parser()
    argv = list(sys.argv[1:] if argv is None else argv)
    tail = None
    if "--" in argv:
        cut = argv.index("--")
        tail = argv[cut + 1:]
        argv = argv[:cut]
    # global flags are accepted anywhere before --, so "csync teardown x --yes" works
    globals_ = [a for a in argv if a in ("--json", "--yes", "--allow-write")]
    argv = globals_ + [a for a in argv if a not in ("--json", "--yes", "--allow-write")]
    args = parser.parse_args(argv)
    if tail is not None:
        if args.verb == "run":
            args.cmd = tail
        elif args.verb == "recipe":
            args.args = tail
    if not args.verb:
        tui = paths.REPO / "bin" / "csync-tui"
        if sys.stdout.isatty() and tui.exists():
            os.execv("/bin/bash", ["/bin/bash", str(tui)])
        parser.print_help()
        return 2
    started = time.time()
    who = actor()
    cfg = state.load_config()
    entry = {"verb": args.verb, "actor": who, "args": [a for a in argv if a != "--json"] + (["--"] + tail if tail else [])}
    result = {}
    code = 0
    name = getattr(args, "name", None)
    if name:
        entry["host"] = name

    def finish():
        entry["exit"] = code
        entry["ms"] = int((time.time() - started) * 1000)
        if args.verb != "relay-hello":
            state.audit(entry)

    atexit.register(finish)
    try:
        if args.verb == "relay-hello":
            return relay.hello_main(args.invite_id)
        writing = (
            args.verb not in READ_VERBS
            and not (args.verb == "recipe" and args.dry_run)
            and not (args.verb == "teardown" and args.dry_run)
            and not (args.verb == "persist" and args.action == "status")
        )
        if writing and who == "agent" and not args.allow_write and args.verb not in ("revoke", "forget"):
            raise CsyncError(USAGE, f"{args.verb} changes something, and this call comes from an agent", fix=f"csync --allow-write {' '.join(entry['args'])}")
        if getattr(args, "force", False) and not sys.stdin.isatty():
            raise CsyncError(USAGE, "--force needs a terminal", fix="run it yourself at a prompt, without --force first")
        h = None
        if args.verb in HOST_VERBS:
            h = state.host_get(name)
            if not args.json:
                out_human(emit.host_row(h))
        if args.verb == "init":
            result = do_init(args, cfg)
            if not args.json:
                out_human(f"relay    {result['relay']}")
                out_human(f"funnel   {result['funnel']}")
                show_checks(result["checks"])
                out_human(emit.dim("→ csync invite <name>"))
        elif args.verb == "doctor":
            result = {"checks": doctor.checks(cfg, fix=args.fix)}
            failing = [r for r in result["checks"] if not r["ok"]]
            if not args.json:
                show_checks(result["checks"])
                out_human(emit.dim("→ all good, csync invite <name>" if not failing else f"→ {len(failing)} failing, run the fix lines or csync doctor --fix"))
            code = 0 if not failing else 6
        elif args.verb == "invite":
            if args.show_script:
                out_human((paths.REPO / "bootstrap.sh").read_text())
            else:
                result = invite.create(args.name, args.route, args.ttl, args.expires, args.src, args.target_port, relay_host=args.relay_host)
                if not args.json:
                    if result.get("warning"):
                        out_human(emit.yellow("note: " + result["warning"]))
                    out_human("")
                    out_human(result["paste"])
                    out_human("")
                    out_human(emit.dim(f"→ send that line, then csync wait {args.name}   (invite expires in {emit.fmt_duration(result['expires'] - time.time())})"))
        elif args.verb == "wait":
            h = tunnel.wait(name, invite.parse_duration(args.timeout))
            result = {"host": h}
            if not args.json:
                out_human(emit.host_row(h))
                out_human(emit.dim(f"→ csync run {name} -- uname -a   ·   csync shot {name}   ·   csync info {name}"))
        elif args.verb == "ls":
            hosts = state.load_hosts()
            shown = {n: h for n, h in hosts.items() if args.all or h.get("status") != "gone"}
            for h in shown.values():
                if h.get("status") == "online" and not tunnel.hello_alive(h):
                    h["status"] = "offline"
            result = {"hosts": shown}
            if not args.json:
                if not shown:
                    out_human(emit.dim("no hosts. → csync invite <name>"))
                for h in shown.values():
                    out_human(emit.host_row(h))
        elif args.verb == "status":
            result = do_status(cfg)
            if not args.json:
                if not result["hosts"]:
                    out_human(emit.dim("no hosts"))
                for h in result["hosts"].values():
                    if h.get("status") != "gone":
                        out_human(emit.host_row(h))
                out_human("")
                show_checks(result["checks"])
        elif args.verb == "log":
            if args.relay:
                text = paths.RELAY_LOG.read_text() if paths.RELAY_LOG.exists() else ""
                lines = text.splitlines()[-args.last:]
                result = {"lines": lines}
                if not args.json:
                    out_human("\n".join(lines) or emit.dim("relay log is empty"))
            else:
                entries = state.audit_tail(args.last, args.name)
                result = {"entries": entries}
                if not args.json:
                    for e in entries:
                        mark = emit.green("ok") if e.get("exit") == 0 else emit.red(str(e.get("exit")))
                        out_human(f"{e.get('ts', '')[:19]}  {mark:<4} {e.get('host') or '-':<12} {e.get('verb'):<9} {' '.join(e.get('args', [])[1:])[:80]}  {emit.dim(e.get('actor', ''))}")
        elif args.verb == "sh":
            tunnel.require_online(h, 20)
            emit.set_title(f"csync {name}")
            finish()
            atexit.unregister(finish)
            os.execvp("ssh", tunnel.ssh_base(h) + ["-t"])
        elif args.verb == "run":
            cmd = args.cmd
            tunnel.require_online(h, 20)
            result = ops.run(h, cmd, force=args.force, full=args.full, json_mode=args.json, timeout=args.timeout)
            code = 0 if result["exit"] == 0 else 5
            if not args.json:
                out_human(emit.dim(f"→ exit {result['exit']} · {result['lines']} lines · {result['log']}"))
        elif args.verb == "push":
            srcs, dst = (args.paths[:-1], args.paths[-1]) if len(args.paths) > 1 else (args.paths, None)
            tunnel.require_online(h, 20)
            result = ops.push(h, srcs, dst, overwrite=args.overwrite, dry_run=args.dry_run, json_mode=args.json)
            if not args.json:
                out_human(emit.dim("→ " + ("would land" if args.dry_run else "landed") + ": " + ", ".join(result["landed"])))
        elif args.verb == "pull":
            srcs, dst = (args.paths[:-1], args.paths[-1]) if len(args.paths) > 1 and (args.paths[-1].startswith(("/", "~", ".")) ) else (args.paths, None)
            tunnel.require_online(h, 20)
            result = ops.pull(h, srcs, dst, json_mode=args.json)
            if not args.json:
                out_human(emit.dim("→ got: " + ", ".join(result["got"])))
        elif args.verb == "shot":
            tunnel.require_online(h, 20)
            result = ops.shot(h, args.display, args.open, json_mode=args.json)
            if not args.json:
                out_human(emit.dim(f"→ {result['path']} ({result['bytes']} bytes)   ·   open {result['path']}"))
        elif args.verb == "info":
            tunnel.require_online(h, 20)
            result = ops.info(h, args.sections)
            if not args.json:
                for sec, lines in result["sections"].items():
                    out_human(emit.bold(sec))
                    for l in lines[:25]:
                        out_human("  " + l)
                    if len(lines) > 25:
                        out_human(emit.dim(f"  … {len(lines) - 25} more lines in {result['file']}"))
                out_human(emit.dim(f"→ full text: {result['file']}"))
        elif args.verb == "logs":
            tunnel.require_online(h, 20)
            result = ops.logs(h, args.since, args.app, args.crash, json_mode=args.json)
            if not args.json:
                for l in result["digest"]:
                    out_human("  " + l)
                out_human(emit.dim(f"→ {result['bundle']} ({result['bytes']} bytes)"))
        elif args.verb == "recipe":
            rargs = args.args
            if not args.dry_run:
                tunnel.require_online(h, 20)
            result = recipes.run(h, args.recipe, rargs, dry_run=args.dry_run, dev=args.dev, json_mode=args.json)
            if args.dry_run and not args.json:
                out_human(result["script"])
            elif not args.json:
                code = 0 if result["exit"] == 0 else 5
                out_human(emit.dim(f"→ recipe {args.recipe} exit {result['exit']}"))
        elif args.verb == "recipes":
            result = {"recipes": recipes.listing()}
            if not args.json:
                out_human(emit.table([(r["name"], r["os"], r["summary"]) for r in result["recipes"]], ["recipe", "os", "summary"]) or emit.dim("no recipes"))
        elif args.verb == "open":
            tunnel.require_online(h, 20)
            result = ops.open_(h, args.target)
            if not args.json:
                out_human(emit.dim(f"→ opened {args.target} on {name}"))
        elif args.verb == "say":
            tunnel.require_online(h, 20)
            result = ops.say(h, args.text)
            if not args.json:
                out_human(emit.dim(f"→ shown on {name}"))
        elif args.verb == "persist":
            if args.action != "status" and who == "agent" and not args.allow_write:
                raise CsyncError(USAGE, "persist changes the host, and this call comes from an agent", fix=f"csync --allow-write persist {name} {args.action}")
            tunnel.require_online(h, 20)
            result = ops.persist(h, args.action)
            if not args.json:
                for line in result["lines"]:
                    out_human("  " + line)
                out_human(emit.dim(f"→ csync persist {name} off   ends always-on without ending the session"))
        elif args.verb == "teardown":
            if args.dry_run:
                result = teardown.run(h, dry_run=True)
                if not args.json:
                    for side in ("target", "console"):
                        out_human(emit.bold(side))
                        for item in result["plan"][side]:
                            out_human("  - " + item)
                    out_human(emit.dim("kept: " + ", ".join(result["plan"]["kept"])))
            else:
                if not args.json:
                    for item in teardown.plan(h)["target"]:
                        out_human("  - " + item)
                if not confirm(f"tear down {name} on both ends?", args):
                    raise CsyncError(USAGE, "cancelled")
                try:
                    result = teardown.run(h, receipt=not args.no_receipt, verify=True)
                except CsyncError as e:
                    if e.data.get("residue") is not None:
                        result = e.data
                        code = e.code
                        if not args.json:
                            out_human(emit.red(f"{len(result['residue'])} left:"))
                            for r in result["residue"]:
                                out_human(f"  {r['where']:<8} {r['what']}")
                    else:
                        raise
                else:
                    if not args.json:
                        out_human(emit.green("clean") + emit.dim(f"   kept {result['kept']}"))
                emit.notify("csync", f"{name} torn down" + ("" if code == 0 else f", {len(result['residue'])} left"), cfg.get("notify", True))
        elif args.verb == "forget":
            with state.locked():
                hosts = state.load_hosts()
                hh = hosts.get(name)
                if not hh:
                    raise CsyncError(3, f"no host named {name!r}", fix="csync ls --all")
                if hh.get("status") in ("online",) and tunnel.hello_alive(hh):
                    raise CsyncError(USAGE, f"{name} is connected", fix=f"csync teardown {name}")
                relay.remove_line(hh.get("id"))
                del hosts[name]
                tunnel.rewrite_ssh_config(hosts)
                state.save_hosts(hosts)
            result = {"forgot": name}
            if not args.json:
                out_human(emit.dim(f"→ forgot {name}"))
        elif args.verb == "revoke":
            if not args.all:
                raise CsyncError(USAGE, "say what to revoke", fix="csync revoke --all")
            with state.locked():
                hosts = state.load_hosts()
                closed = []
                for inv in relay.open_invites():
                    relay.remove_line(inv)
                    closed.append(inv)
                for hh in hosts.values():
                    if hh.get("status") != "gone":
                        hh["status"] = "gone"
                        if hh.get("hello_pid"):
                            try:
                                os.kill(hh["hello_pid"], 15)
                            except OSError:
                                pass
                            hh["hello_pid"] = None
                tunnel.rewrite_ssh_config(hosts)
                state.save_hosts(hosts)
            result = {"closed": closed}
            if not args.json:
                out_human(emit.dim(f"→ closed {len(closed)} invite(s); targets clean themselves up at their TTL or via ~/.csync/teardown.sh"))
    except CsyncError as e:
        code = e.code
        if args.json:
            print(json.dumps({"ok": False, "verb": args.verb, "host": name, "error": e.message, "fix": e.fix, "code": e.code, **({"data": e.data} if e.data else {})}, sort_keys=True))
        else:
            sys.stderr.write(emit.red("error: ") + e.message + "\n")
            if e.fix:
                sys.stderr.write(emit.dim("fix: " + e.fix) + "\n")
        return code
    except KeyboardInterrupt:
        code = 130
        return code
    if args.json:
        payload = {"ok": code == 0, "verb": args.verb, "host": name, "code": code}
        payload.update(result)
        print(json.dumps(payload, sort_keys=True, default=str))
    return code
