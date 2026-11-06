# zot-copy

Copy the last agent response to the system clipboard.

## Install

```bash
zot ext install https://github.com/unlight/zot-copy-last
```

Or run ad-hoc:

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
  and keeps the last non-empty text. `turn_start` and `session_end` clear the
  cache, so `/copy` never returns a preamble left over from an earlier step.
- **Clipboard write** — on `/copy` the stored text is written through the
  platform clipboard tool: `pbcopy` on macOS, `wl-copy` / `xclip` / `xsel`
  on Linux. Candidates are tried in order; a broken tool does not stop the
  fallback chain.
- **Encoding** — frames are read and written as UTF-8 regardless of the host
  locale, and clipboard payloads are handed over as UTF-8 too.

## Known limitations

- A `/btw` side dialog emits `assistant_message` attributed to the active
  session (host behaviour), so its reply can replace the text `/copy` reads.
- Only the Linux and macOS clipboard tools are supported.

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
└── test_copy.py     # wire-level tests
```

## Requirements

- Python 3.7+
- zot 0.4.x
- A system clipboard tool: `pbcopy` (macOS), `wl-copy` / `xclip` / `xsel` (Linux)

## License

MIT, Copyright (c) 2026 unlight.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
