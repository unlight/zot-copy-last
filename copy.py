#!/usr/bin/env python3
"""zot /copy — copy the last agent response to the system clipboard."""

import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import cast

NAME = "copy"
VERSION = "1.0.0"
CAPABILITIES = ["commands"]
CLIPBOARD_TIMEOUT = 2  # seconds per candidate
CLIPBOARD_BUDGET = 5  # seconds for the whole chain, keeps the frame loop responsive
SUBSCRIBED_EVENTS = ["assistant_message", "session_start", "turn_start", "session_end"]

IS_MACOS = sys.platform == "darwin"

last_text = ""
current_session_id = ""
current_cwd = ""
extension_dir = ""


def configure_stdio():
    # zot speaks UTF-8 JSON lines; the host locale must not decode them.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        cast(io.TextIOWrapper, stream).reconfigure(encoding="utf-8", errors="replace")


def send(frame):
    sys.stdout.write(json.dumps(frame) + "\n")
    sys.stdout.flush()


def log(message):
    sys.stderr.write(f"[{NAME}] {message}\n")
    sys.stderr.flush()


def clipboard_candidates():
    if IS_MACOS:
        return [["/usr/bin/pbcopy"]]
    candidates = []
    if os.environ.get("WAYLAND_DISPLAY"):
        candidates.append(["wl-copy"])
    candidates.append(["xclip", "-selection", "clipboard"])
    candidates.append(["xsel", "--clipboard", "--input"])
    return candidates


def clipboard_available():
    if IS_MACOS:
        return True
    return bool(os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY"))


def try_candidate(argv, text, timeout):
    exe = shutil.which(argv[0])
    if exe is None:
        return f"{argv[0]} not found"
    try:
        proc = subprocess.run(
            [exe, *argv[1:]],
            input=text,
            encoding="utf-8",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return f"{argv[0]} timed out after {round(timeout, 1):g}s"
    except OSError as err:
        return f"{argv[0]}: {err.strerror or err}"
    if proc.returncode != 0:
        return f"{argv[0]} exited with {proc.returncode}"
    return ""


def copy_to_clipboard(text):
    if not clipboard_available():
        return False, "clipboard unavailable: no X11/Wayland display (DISPLAY/WAYLAND_DISPLAY unset)"
    deadline = time.monotonic() + CLIPBOARD_BUDGET
    failures = []
    for argv in clipboard_candidates():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            failures.append("out of time budget")
            break
        failure = try_candidate(argv, text, min(CLIPBOARD_TIMEOUT, remaining))
        if not failure:
            return True, ""
        log(failure)
        failures.append(failure)
    return False, "clipboard failed: " + "; ".join(failures)


def respond(command_id, display="", error=""):
    # The host drops display text when error is set, so send only one of them.
    frame = {"type": "command_response", "id": command_id}
    if error:
        frame["error"] = error
    else:
        frame["action"] = "display"
        frame["display"] = display
    send(frame)


def zot_home_candidates():
    """Guess zot's state directory; the host never reveals it directly."""
    homes = []
    if os.environ.get("ZOT_HOME"):
        homes.append(Path(os.environ["ZOT_HOME"]))
    if os.environ.get("XDG_STATE_HOME"):
        homes.append(Path(os.environ["XDG_STATE_HOME"]) / "zot")
    home = Path.home()
    if IS_MACOS:
        homes.append(home / "Library" / "Application Support" / "zot")
    else:
        homes.append(home / ".local" / "state" / "zot")
    parent = Path(extension_dir).parent if extension_dir else None
    if parent and parent.name == "extensions" and parent.parent.name != ".zot":
        homes.append(parent.parent)
    return homes


def session_dir_name(cwd):
    return hashlib.sha256(cwd.encode("utf-8")).hexdigest()[:16]


def read_session_id(path):
    """Session id recorded in the meta line of a transcript."""
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            row = json.loads(handle.readline() or "{}")
    except (OSError, json.JSONDecodeError):
        return ""
    meta = row.get("meta")
    return meta.get("id", "") if isinstance(meta, dict) else ""


def find_session_file():
    """Transcript of the active session, or None when it cannot be found."""
    if not current_session_id or not current_cwd:
        return None
    for home in zot_home_candidates():
        directory = home / "sessions" / session_dir_name(current_cwd)
        if not directory.is_dir():
            continue
        for path in directory.glob("*.jsonl"):
            if read_session_id(path) == current_session_id:
                return path
    return None


def message_text(message):
    """Visible assistant text of one stored message, tool blocks skipped."""
    if not isinstance(message, dict) or message.get("role") != "assistant":
        return ""
    blocks = message.get("content") or []
    parts = [
        block["text"]
        for block in blocks
        if isinstance(block, dict) and isinstance(block.get("text"), str) and "name" not in block
    ]
    return "".join(parts)


def transcript_last_text(path):
    """Last non-empty assistant text stored in a session transcript."""
    last = ""
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            for raw in handle:
                try:
                    row = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if row.get("type") == "message":
                    text = message_text(row.get("message"))
                elif row.get("type") == "compaction":
                    stored = list(map(message_text, reversed(row.get("messages") or [])))
                    text = next((item for item in stored if item.strip()), "")
                else:
                    continue
                if text.strip():
                    last = text
    except OSError as err:
        log(f"cannot read transcript {path}: {err}")
    return last


def cached_or_stored_text():
    """Message text for /copy, falling back to the session transcript."""
    if last_text.strip():
        return last_text
    path = find_session_file()
    if path is None:
        return ""
    return transcript_last_text(path)


def handle_command_invoked(frame):
    command_id = frame.get("id")
    if frame.get("name") != "copy":
        respond(command_id, error=f"unknown command /{frame.get('name')}")
        return
    text = cached_or_stored_text()
    if not text.strip():
        respond(command_id, display="Nothing to copy yet — no agent response in this session.")
        return
    ok, reason = copy_to_clipboard(text)
    if not ok:
        respond(command_id, error=reason)
        return
    respond(command_id, display="Copied the last agent response to the clipboard.")


def handle_event(frame):
    global last_text, current_session_id, current_cwd
    event_name = frame.get("event")
    current_session_id = frame.get("session_id") or current_session_id
    current_cwd = frame.get("cwd") or current_cwd
    if event_name == "assistant_message":
        # The host emits one event per model step; the last one wins.
        text = frame.get("text") or ""
        if text.strip():
            last_text = text
    elif event_name in ("session_start", "turn_start", "session_end"):
        # A fresh turn or session has no complete answer yet.
        last_text = ""


def handle_hello_ack(frame):
    global extension_dir, current_cwd
    extension_dir = frame.get("extension_dir") or ""
    current_cwd = frame.get("cwd") or ""
    register = {
        "type": "register_command",
        "name": NAME,
        "description": "copy the last agent response to the clipboard",
    }
    send(register)
    send({"type": "subscribe", "events": SUBSCRIBED_EVENTS})
    send({"type": "ready"})


def serve():
    hello = {"type": "hello", "name": NAME, "version": VERSION, "capabilities": CAPABILITIES}
    send(hello)
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            frame = json.loads(line)
        except json.JSONDecodeError as err:
            log(f"malformed frame: {err}")
            continue
        frame_type = frame.get("type")
        if frame_type == "hello_ack":
            handle_hello_ack(frame)
        elif frame_type == "command_invoked":
            handle_command_invoked(frame)
        elif frame_type == "event":
            handle_event(frame)
        elif frame_type == "shutdown":
            send({"type": "shutdown_ack"})
            break


def main():
    configure_stdio()
    try:
        serve()
    except (BrokenPipeError, KeyboardInterrupt):
        # The host is gone; silence the flush-at-exit noise.
        with contextlib.suppress(OSError):
            os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        log("host closed the connection; exiting")


if __name__ == "__main__":
    main()
