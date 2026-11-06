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

## Release

Releases are cut by CI, never by hand. `.github/workflows/release.yml` runs
`semantic-release` on every push to `master`:

- Conventional Commits decide the bump (`fix` → patch, `feat` → minor,
  `!`/`BREAKING CHANGE` → major).
- `CHANGELOG.md`, the `vX.Y.Z` git tag and the GitHub release are generated.
- Nothing is published to npm and the repository carries no Node manifest:
  the release tooling is installed by `npx` with versions pinned in the
  workflow, and `release.config.mjs` only configures the plugins.

`.github/workflows/ci.yml` runs the test suite on Python 3.9, 3.12 and 3.14 for
every push and pull request. It stays on `ubuntu-24.04`: the runner image has to
ship a prebuilt interpreter for every entry in the matrix.

## Requirements

- Python 3.7+
- zot 0.4.x
- A system clipboard tool: `pbcopy` (macOS), `wl-copy` / `xclip` / `xsel` (Linux)

## License

[MIT](https://opensource.org/licenses/MIT), Copyright (c) 2026
