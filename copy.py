#!/usr/bin/env python3
"""zot /copy — copy the last agent response to the system clipboard."""

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import time
from typing import cast

NAME = "copy"
VERSION = "1.0.0"
CAPABILITIES = ["commands"]
CLIPBOARD_TIMEOUT = 2  # seconds per candidate
CLIPBOARD_BUDGET = 5  # seconds for the whole chain, keeps the frame loop responsive

IS_MACOS = sys.platform == "darwin"

last_text = ""


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


def handle_command_invoked(frame):
    command_id = frame.get("id")
    if frame.get("name") != "copy":
        send({"type": "command_response", "id": command_id, "action": "noop", "error": f"unknown command /{frame.get('name')}"})
        return
    if not last_text.strip():
        send({"type": "command_response", "id": command_id, "action": "display", "display": "Nothing to copy yet — no agent response in this session."})
        return
    ok, reason = copy_to_clipboard(last_text)
    if ok:
        send({"type": "command_response", "id": command_id, "action": "display", "display": "Copied the last agent response to the clipboard."})
    else:
        send({"type": "command_response", "id": command_id, "action": "display", "error": reason})


def handle_event(frame):
    global last_text
    event_name = frame.get("event")
    if event_name == "assistant_message":
        # The host emits one event per model step; the last one wins.
        text = frame.get("text") or ""
        if text.strip():
            last_text = text
    elif event_name in ("turn_start", "session_end"):
        # A fresh turn has no complete answer yet, so drop the stale text.
        last_text = ""


def serve():
    send({"type": "hello", "name": NAME, "version": VERSION, "capabilities": CAPABILITIES})
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
            send({"type": "register_command", "name": "copy", "description": "copy the last agent response to the clipboard"})
            send({"type": "subscribe", "events": ["assistant_message", "turn_start", "session_end"]})
            send({"type": "ready"})
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
