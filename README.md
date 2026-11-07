> **Deprecated:** This extension is superseded by
> [zot-copy](https://github.com/unlight/zot-copy), which supports Markdown,
> Jira wiki markup and file output. Install that instead.

# zot-copy-last

Copy the last agent response to the system clipboard.

## Install

This extension is no longer maintained. Install the replacement:

```bash
zot ext install https://github.com/unlight/zot-copy
```

For reference, the old ad-hoc command was:

```bash
zot --ext ./zot-copy-last
```

Restart zot after installing or updating.

## Usage

Type:

```text
/copy
```

Copies the most recent agent response from the current session to the
system clipboard and posts a confirmation note back into the chat.

## How it works

- **Event subscription** — the extension subscribes to `assistant_message`
  and `turn_end`. A response is committed only when its turn ends without
  `stop: "tool_use"`, so intermediate narration is never copied. `turn_start`
  resets only the current step, which keeps the previous answer available
  while a new turn is running; session boundaries clear the cache.
- **Clipboard write** — on `/copy` the stored text is written through the
  platform clipboard tool: `pbcopy` on macOS, `wl-copy` / `xclip` / `xsel`
  on Linux. Candidates are tried in order; a broken tool does not stop the
  fallback chain.
- **Encoding** — frames are read and written as UTF-8 regardless of the host
  locale, and clipboard payloads are handed over as UTF-8 too.
- **Transcript fallback** — a session loaded with `/sessions` replays no
  events, so when the cache is empty `/copy` reads the last assistant message
  from `<state dir>/sessions/<hash of cwd>/*.jsonl` instead of failing.

## Known limitations

- A `/btw` side dialog emits `assistant_message` attributed to the active
  session (host behaviour), so its reply can replace the text `/copy` reads.
- Only the Linux and macOS clipboard tools are supported.
- The transcript fallback depends on zot's state layout (no host API exposes
  the session file), so a future change there degrades `/copy` back to
  "nothing to copy" rather than to a wrong answer.

## TODO / Ideas

- **P1** Keep a short response history and support `/copy N`.
- **P1** Add `/copy file [path]` to bypass the clipboard on SSH/headless hosts.
- **P1** Add a panel picker for fenced code blocks, the full response and an
  "always copy full response" setting.
- **P1** Add Windows (`clip.exe`/PowerShell), Termux and WSL clipboard backends.
- **P2** Add OSC 52 and tmux fallbacks. OSC 52 from an extension needs a
  `/dev/tty` write or a host API; this has to be verified first.
- **P2** Read long transcripts from the tail and cache the result instead of
  scanning the whole session file on every `/copy`.
- **P2** Add tests for platform-specific backends, the picker and transcript
  edge cases.
- **P2** Align the documented Python floor with CI.

## Development

The extension is a single executable Python script — no build step.

```bash
chmod +x copy.py
python3 -m unittest test_copy -v
```

The tests drive the real subprocess over stdio and stub the clipboard tool, so
no zot session and no clipboard access are needed.

## Structure

```text
zot-copy-last/
├── extension.json   # manifest
├── copy.py          # source code
├── sync_version.py   # release version sync
└── test_copy.py     # wire-level tests
```

## Requirements

- Python 3.7+
- zot 0.4.x
- A system clipboard tool: `pbcopy` (macOS), `wl-copy` / `xclip` / `xsel`
  (Linux)

## License

[MIT](https://opensource.org/licenses/MIT), Copyright (c) 2026
