"""Wire-level tests for copy.py: real subprocess, fake clipboard tools."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("copy.py")
CAPTURED = "captured.txt"


def line(item):
    return (json.dumps(item) if isinstance(item, dict) else item) + "\n"


def run_extension(lines, bin_dir, env_extra=None):
    """Feed frames to the extension and return its stdout lines as frames."""
    env = dict(os.environ)
    env.pop("WAYLAND_DISPLAY", None)
    env["DISPLAY"] = ":0"
    env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"
    env.update(env_extra or {})
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input="".join(line(item) for item in lines),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        timeout=30,
    )
    return [json.loads(out) for out in proc.stdout.splitlines() if out.strip()], proc


def responses(frames):
    return [frame for frame in frames if frame["type"] == "command_response"]


LINUX_ONLY = unittest.skipIf(sys.platform != "linux", "clipboard stubs are Linux-only")


class ExtensionTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.bin = Path(tmp.name)
        self.capture = self.bin / CAPTURED

    def stub_tool(self, name, exit_code=0):
        """Install a fake clipboard tool that captures stdin and exits with code."""
        script = self.bin / name
        script.write_text(f'#!/bin/sh\ncat > "{self.capture}"\nexit {exit_code}\n', encoding="utf-8")
        script.chmod(0o755)
        return script

    def run_lines(self, lines):
        return run_extension(lines, self.bin)[0]

    def test_handshake_order(self):
        frames = self.run_lines([{"type": "hello_ack"}])
        self.assertEqual(
            [frame["type"] for frame in frames],
            ["hello", "register_command", "subscribe", "ready"],
        )
        self.assertEqual(frames[0]["name"], "copy")
        self.assertIn("assistant_message", frames[2]["events"])

    def test_nothing_to_copy_before_any_message(self):
        frames = self.run_lines([
            {"type": "hello_ack"},
            {"type": "command_invoked", "id": "c1", "name": "copy"},
        ])
        self.assertTrue(responses(frames)[0]["display"].startswith("Nothing to copy yet"))

    @LINUX_ONLY
    def test_copies_last_assistant_message(self):
        self.stub_tool("xclip")
        frames = self.run_lines([
            {"type": "hello_ack"},
            {"type": "event", "event": "assistant_message", "text": "привет"},
            {"type": "command_invoked", "id": "c1", "name": "copy"},
        ])
        self.assertTrue(responses(frames)[0]["display"].startswith("Copied the last"))
        self.assertEqual(self.capture.read_text(encoding="utf-8"), "привет")

    @LINUX_ONLY
    def test_clipboard_failure_sends_only_error(self):
        self.stub_tool("xclip", exit_code=1)
        self.stub_tool("xsel", exit_code=1)
        frames = self.run_lines([
            {"type": "hello_ack"},
            {"type": "event", "event": "assistant_message", "text": "text"},
            {"type": "command_invoked", "id": "c1", "name": "copy"},
        ])
        response = responses(frames)[0]
        self.assertIn("exited with 1", response["error"])
        self.assertNotIn("display", response)

    def test_turn_start_clears_cache(self):
        for boundary in ("turn_start", "session_end"):
            with self.subTest(boundary=boundary):
                frames = self.run_lines([
                    {"type": "hello_ack"},
                    {"type": "event", "event": "assistant_message", "text": "preamble"},
                    {"type": "event", "event": boundary, "step": 2},
                    {"type": "command_invoked", "id": "c1", "name": "copy"},
                ])
                self.assertTrue(responses(frames)[0]["display"].startswith("Nothing to copy yet"))

    def test_malformed_frame_keeps_running(self):
        frames = self.run_lines([
            {"type": "hello_ack"},
            "not json",
            {"type": "command_invoked", "id": "c1", "name": "copy"},
        ])
        self.assertEqual(responses(frames)[0]["id"], "c1")


if __name__ == "__main__":
    unittest.main()
