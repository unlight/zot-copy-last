#!/usr/bin/env python3
"""zot /copy — copy the last agent response to the system clipboard."""

import json
import os
import shutil
import subprocess
import sys

NAME = "copy"
VERSION = "1.0.0"
CAPABILITIES = ["commands", "events"]

last_text = ""
last_session_id = ""


def send(frame):
    sys.stdout.write(json.dumps(frame) + "\n")
    sys.stdout.flush()


def log(message):
    sys.stderr.write(f"[{NAME}] {message}\n")
    sys.stderr.flush()


def clipboard_argv_candidates():
    if sys.platform == "darwin":
        return [["/usr/bin/pbcopy"]]
    if sys.platform == "windows":
        script = "[Console]::InputEncoding = [System.Text.Encoding]::UTF8\r\nSet-Clipboard -Value ([Console]::In.ReadToEnd())"
        return [["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script]]
    candidates = []
    if os.environ.get("WAYLAND_DISPLAY"):
        candidates.append(["wl-copy"])
    candidates.append(["xclip", "-selection", "clipboard"])
    candidates.append(["xsel", "--clipboard", "--input"])
    return candidates


def copy_to_clipboard(text):
    candidates = clipboard_argv_candidates()
    found_any = False
    for argv in candidates:
        exe = shutil.which(argv[0])
        if exe is None:
            continue
        found_any = True
        try:
            proc = subprocess.run([exe, *argv[1:]], input=text, capture_output=True, timeout=2, text=True)
            if proc.returncode == 0:
                return True, ""
        except Exception as err:
            return False, f"clipboard command failed: {err}"
    if not found_any:
        return False, "no clipboard tool available (xclip, wl-copy, pbcopy, ...)"
    return False, "clipboard command failed"


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
    global last_text, last_session_id
    event_name = frame.get("event")
    if event_name == "assistant_message":
        text = frame.get("text") or ""
        if text.strip():
            last_text = text
            last_session_id = frame.get("session_id") or ""
    elif event_name == "session_end":
        last_text = ""
        last_session_id = ""


def main():
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
            send({"type": "subscribe", "events": ["assistant_message", "session_end"]})
            send({"type": "ready"})
        elif frame_type == "command_invoked":
            handle_command_invoked(frame)
        elif frame_type == "event":
            handle_event(frame)
        elif frame_type == "shutdown":
            send({"type": "shutdown_ack"})
            break


if __name__ == "__main__":
    main()
