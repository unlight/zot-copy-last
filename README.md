# zot-copy

Copy the last agent response to the system clipboard.

## Install

```bash
zot ext install https://github.com/unlight/zot-copy-last
```

On Windows, additionally point the installed manifest at the bundled
`copy.cmd` launcher (zot spawns `exec` via `CreateProcess`, which ignores the
shebang):

```powershell
powershell -ExecutionPolicy Bypass -File install-windows.ps1 -Path "$env:LOCALAPPDATA\zot\extensions\zot-copy-last"
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

- **Event subscription** — the extension subscribes to the
  `assistant_message` lifecycle event and keeps the latest visible
  assistant text for the active session.
- **Clipboard write** — on `/copy` the stored text is written through the
  platform clipboard tool: `pbcopy` on macOS, `wl-copy` / `xclip` / `xsel`
  on Linux, or PowerShell `Set-Clipboard` on Windows. Candidates are tried in
  order; a broken tool does not stop the fallback chain.
- **Encoding** — frames are read and written as UTF-8 regardless of the host
  locale, and clipboard payloads are handed over as UTF-8 too.

## Development

The extension is a single executable Python script — no build step.

```bash
chmod +x copy.py
```

## Structure

```text
zot-copy-last/
├── extension.json       # manifest
├── copy.py              # source code
├── copy.cmd             # Windows launcher shim
└── install-windows.ps1  # one-time manifest fixup for Windows
```

## Requirements

- Python 3.7+
- zot 0.4.x
- A system clipboard tool: `pbcopy` (macOS), `wl-copy` / `xclip` / `xsel` (Linux), PowerShell `Set-Clipboard` (Windows)
