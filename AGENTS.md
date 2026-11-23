# AGENTS.md

Guidance for AI coding agents (and new contributors) working on **TippyTappyTypes**. Read this
before changing anything. Human-facing docs: [README.md](README.md) and
[CHANGELOG.md](CHANGELOG.md). There is no `CONTRIBUTING.md`, `SECURITY.md`, `docs/` tree or
`changelog.d/` fragment directory yet; this file is the contract until they exist.

## 1. What this project is and why it exists

TippyTappyTypes is a **minimal typing test that lives in the corner of your screen** while you work.
It is a Windows desktop overlay, not a website and not a benchmark suite: a frameless, always-on-top,
semi-transparent strip you can park over another app, type into for 15–120 seconds, and forget about.

It is a single-user, local-first tool. There is no server, no account requirement and no telemetry.
The only network calls are an optional GitHub Releases version check and an optional Google sign-in
that only changes which local stats bucket you see.

**Owner's goals (keep these in mind when making trade-offs):**

- Simple, minimal, genuinely useful. Prefer a smaller window, fewer settings and less code over a
  feature. The overlay must never steal focus or block the app underneath for longer than a test.
- Typing must stay smooth. Nothing on the keystroke path may touch disk, the network or a lock.
  That is why database writes go through a queue and a background thread.
- The character art (by Cafefaevans) and the tiny idle/typing animation are part of the product's
  identity, not decoration to be replaced with generic icons.
- Stats exist to make practice useful: per-character and per-n-gram error rates feed the
  **Error Gen** word pool, which is the one feature that is more than a typing test.
- Windows only, by design. Elevation, UIPI, `%APPDATA%`, NSIS and `ShellExecuteW` are load-bearing.

## 2. Hard rules

1. **Git.** `master` is the only long-lived branch and it is release-coupled: **every push to
   `master` runs `.github/workflows/release.yml`, which bumps the version, commits, tags and
   publishes a GitHub release.** Never push to `master` yourself, never force-push it, and never
   merge your own PR. Work on `feat/...`, `fix/...`, `docs/...` or `chore/...` and open a PR; the
   owner reviews and merges. Tags `v*` are created by CI, not by hand.
2. **Never commit** `builds/`, `dist/`, `build/`, `build_log.txt`, `data/`, `venv/`, `.venv/`,
   `__pycache__/`, `*.pyc`, `*.pyo`, `*.pyd`, `*.so`, `*.egg*`, `*.db`, `*.sqlite*`,
   `credentials.json`, `token.json`, `.env`, `oauth_server/`, `.idea/`, `.vscode/`, `.abacusai/`.
   Stage files explicitly; do not use `git add -A` or `git add .`. `info.txt` is the exception: it
   is listed in `.gitignore` but **is tracked** and bundled by `build.spec`, so leave it alone
   rather than deleting it as ignored.
3. **No secrets, ever.** The Cloudflare OAuth worker lives in the gitignored `oauth_server/` and
   holds the Google client secret. Never paste a client secret, refresh token or access token into
   source, commits, issues, PRs, logs or chat. `src/auth.py` ships a placeholder worker URL on
   purpose; do not "fix" it by hard-coding a real one.
4. **The keystroke path stays non-blocking.** No disk I/O, network, `sleep`, `subprocess`, dialog or
   lock acquisition inside `TypingEngine.process_char`, `TypingOverlay.keyPressEvent` or anything
   they call synchronously. Persist through `Database`'s queue or `Config.save()` at a natural
   boundary (test end, settings apply, window move), never per character.
5. **User data stays on the machine.** Stats, config, custom tests, custom themes and quotes live in
   `%APPDATA%\TippyTappyTypes`. Do not add analytics, crash reporting, "anonymous usage" pings or a
   remote sync. Do not log typed text, transcripts of tests, tokens or the user's email at info
   level.
6. **Local data is user data.** `config.json` and `typing.db` may contain months of practice history.
   Never delete, reset or "clean" them in code, tests or scripts. Migrations copy, never move or
   overwrite. The uninstaller intentionally leaves `%APPDATA%\TippyTappyTypes` intact; keep it that
   way.
7. **Generated UI is generated.** `ui/generated/*.py` comes from `ui/generated/*.ui` via
   `pyside6-uic`. Edit the `.ui` file and regenerate; do not hand-edit the generated Python, and do
   not delete the generated files from the repo (the app imports them directly and PyInstaller does
   not run `uic`).
8. **Truthful reporting.** Never say something "works", is "verified" or is "released" unless you
   ran it and saw the result. There is no test suite, so "tests pass" is not available as evidence:
   say what you actually launched and what you saw. Lead with failures and caveats. State plainly
   when only imports or static reading were checked.
9. **GPL-3.0 headers.** Every Python source file starts with the 15-line GNU GPL v3 notice used
   throughout `src/`, `ui/` and the root scripts. New source files carry the same header with
   `Copyright (C) 2026 Jon Evans`. Do not relicense, and do not strip the header.
10. **Third-party assets need a licence.** Do not add fonts, icon packs, sound files, quote
    collections or images you cannot redistribute. Art in `resources/` is the owner's commission;
    do not replace it, recolour it or ship it elsewhere. `src/quotes_data.py` entries must be public
    domain, freely licensed, or the owner's own.
11. **Windows behaviour is the product.** Do not "simplify away" the unelevated relaunch, the
    `explorer.exe` launch from the installer, `ShellExecuteW(..., "runas", ...)` for updates, or the
    `%APPDATA%` paths. Each exists because of a real Windows failure (UIPI key injection, UAC
    inheritance, PyInstaller one-dir layout). If you change one, say which failure you re-tested.
12. **No commented-out code, no banner art, no attribution comments.** A comment explains *why*,
    never *what*. Keep the existing section dividers (`# ---` rules) if you are already in a file
    that uses them; do not add new decorative ones.
13. **Assertions are for invariants, not error handling.** Never use `assert` for input validation
    or control flow in production code: `python -O` strips it. Raise, return a sentinel or log.
14. **Do not widen the dependency list casually.** Runtime deps are PySide6 plus `requests` and
    `packaging`; everything else in `requirements.txt` is PyInstaller/NSIS/build tooling. A new
    runtime dependency needs a reason, a licence check and a PyInstaller hidden-import check.
15. **Every user-visible change updates `CHANGELOG.md` in the same PR.** No exceptions, no
    "changelog in a follow-up". If a change is not user-visible (a refactor, a test, a CI tweak, a
    comment), it does not get an entry. The mechanics are in section 8; the rule is that a PR
    without its entry is incomplete and must not be described as ready to merge.

## 3. How it works (high level)

```
main.py
  └─ src.main.main()
       ├─ _relaunch_unelevated_if_needed()   # elevated → explorer.exe → exit
       └─ TippyTappyTypesApp (QObject)
            ├─ QApplication (quitOnLastWindowClosed = False)
            ├─ Config      %APPDATA%\TippyTappyTypes\config.json
            ├─ Database    %APPDATA%\TippyTappyTypes\typing.db  (SQLite, WAL, writer thread)
            ├─ GoogleAuth  optional, via Cloudflare worker proxy
            ├─ SettingsWindow  (QMainWindow, 5 tabs, hidden on close)
            ├─ Updater     GitHub Releases API, background thread
            ├─ SplashScreen (QSplashScreen, 1 s, blocks the main thread)
            └─ TypingOverlay (QWidget, frameless, always-on-top)  ← the product
```

- **Entry point.** `main.py` only imports and calls `src.main.main()`. `TippyTappyTypesApp` builds
  every long-lived object once, installs a global event filter for `Ctrl+,` (settings), then shows
  the overlay immediately. The tray icon is how a hidden or closed overlay is restored.
- **Overlay.** `TypingOverlay` owns a `TypingEngine`, a `Config` and a `Database` handle. It is a
  `QWidget` with `Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool`, translucent
  background painted at `bg_opacity` (0–255), and a `ChildEventFilter` that forwards mouse, wheel
  and hover events from child labels so dragging and scrolling work anywhere in the window.
- **Character window.** `CharacterWindow` is a second frameless `Qt.Tool` holding only the tinted
  animation frame. Its width is fixed to the frame and its height is set to match the overlay in
  `align_to()`, with the frame centred inside that height by `paintEvent`. It is deliberately
  **not** a child of the overlay: it must stay on screen while the overlay is hidden. `align_to()`
  puts its right edge on the overlay's left edge and its top on the overlay's top, and
  `overlay_position()` is the inverse used when the overlay is re-shown. `moveEvent` and
  `resizeEvent` on the overlay re-align it, so dragging or resizing keeps the two touching. A click
  (press and release within 4 px) emits `clicked`, which the overlay turns into `hide()` or
  `_show_aligned()`; a drag does not toggle. The tray menu's "Toggle Typing Window" calls the
  public `toggle_visibility()` as a fallback for when the character cannot be clicked, and
  recreates the overlay if it does not exist.
- **The character is drawn once.** `label_status` in the overlay no longer receives a pixmap; it
  carries only the transient status text and the quote author. Do not reintroduce the image there,
  and do not hide the label outright or those two uses break.
- **Modes.** `words` (10/25/50/100), `time` (15/30/60/120 s) and `quotes`
  (short/medium/long/extreme by character count). Mode, option index and active word pool persist
  across launches via `_persist_state()`. Left/Right cycle mode, Up/Down cycle the option, but only
  before the first keystroke of a test.
- **Word pools.** `config["typing_tests"]` is a list of `{name, text, category?}`. `Default` has
  empty text and uses `TypingEngine.COMMON_WORDS`; `5k English` carries a large inline corpus;
  `Error Gen` has `category: "error_gen"` and is synthesised at runtime. `use_random` picks a pool
  per test. `_ensure_error_gen_pool()` re-adds Error Gen if a saved config lost it.
- **Error Gen.** A character-level Markov model (contexts of length 1 and 2) is built from the
  active corpus, then words are sampled with problem letters weighted ×3 and seeded with the user's
  worst trigrams/4-grams. Inputs are the top problem characters and top n-grams from SQLite.
- **Scoring.** WPM is `(total_chars / 5) / minutes` measured from first keystroke to last; accuracy
  is `(total_chars - error_count) / total_chars`. Backspace rewinds the position and removes the
  error marker but does **not** decrement `total_chars` or `error_count`, so accuracy is
  keystroke-based, not final-text-based. Do not "fix" this without the owner's agreement: it is the
  number users compare against other typing tests.
- **Pause.** A 500 ms `QTimer` classifies the test as `Typing`, `Stopped`, `Unfocused` (window not
  active) or `Unresponsive` (no key for 5 s). Unfocused/unresponsive pauses the clock by nulling
  `start_time` and accumulating `paused_elapsed`; resuming reconstructs `start_time`. Timed tests
  extend their word buffer when fewer than 10 words remain.
- **Results.** `_show_results()` writes the test and n-gram deltas to the database, compares the
  WPM against the cached personal best for the current mode/option/pool, emits `test_completed`,
  and shows the results line. `Space` toggles between that line and `WpmGraphWidget`; nothing
  cycles on a timer. WPM is sampled once per second, first sample at 1 s.
- **Personal bests.** `personal_bests` is keyed by `(user_email, pr_key)` where `pr_key` is
  `words:<count>:<pool>`, `time:<seconds>:<pool>` or `quotes:<length>`. The whole table is read
  once at startup into `_pr_cache` so no read happens per test; a new best updates the cache and
  enqueues the write. Beating an existing best prints `New Personal Best: XXX WPM` and flashes the
  window by inverting the background colour six times at 120 ms. A bucket with no stored best
  records its first result silently — `previous_pr is None` must never count as a win, or every
  new pool and every random-pool switch announces a "record" at any speed. `_load_personal_bests`
  merges with `max` and `update_user` reloads only on an account change: it is called after every
  test, and a plain reload there races the queued write and drops the best just recorded.
- **Personal-best alerts.** The flash is gated by `flash_personal_best` and the system
  notification by `notify_personal_best`, both default `True` and both exposed in Settings →
  Typing → Display Settings. The overlay never touches the tray icon itself: it emits
  `personal_best` and `src/main.py` shows the message, because the tray icon lives in
  `TippyTappyTypesApp`. The handler returns early when `isSystemTrayAvailable()` is false, which
  is the case under `QT_QPA_PLATFORM=offscreen`. The results banner is not gated by either
  setting.
- **Database.** Four tables: `tests`, `character_stats`, `ngram_stats`, `personal_bests`, each
  keyed by `user_email` (NULL for local-only). Writes are queued and drained by one daemon thread;
  read queries open a short-lived connection. `close()` enqueues a sentinel and joins with a 5 s
  timeout.
- **Config.** `Config.settings` is a flat dict. `themes` and `quotes` are **never persisted**: they
  always come from the running app version so releases can add to them. Only the four current theme
  colours, `custom_themes`, `custom_quotes` and `typing_tests` survive a save.
- **Updater.** Fetches `/repos/{repo}/releases`, newest first, and picks the first release newer
  than the running version. Stable builds ignore pre-releases; beta builds see both. The first
  `.exe` asset is downloaded to `%TEMP%\TippyTappyTypes-Update-Setup.exe` and launched with
  `ShellExecuteW(..., "runas", ..., "/SILENT")`, then the app quits. Failures are swallowed: an
  update check must never block startup or show an error dialog.
- **Auth.** `GoogleAuth` opens `{oauth_server}/auth/start` in the browser, then asks the user to
  confirm. Tokens are refreshed via `{oauth_server}/auth/refresh` and the email via
  `/auth/userinfo`. Being logged in only changes the `user_email` key used for stats.

### Hotkeys (defaults, all rebindable except where noted)

| keys | action |
|---|---|
| any printable key | type; first keystroke starts the clock |
| `Tab` | new test |
| `Esc` | quit prompt (`y` / `n`) |
| `Backspace` / `Ctrl+Backspace` | delete character / word |
| `Left` / `Right` | cycle mode (words → time → quotes), before start only |
| `Up` / `Down` | cycle word count / time limit / quote length, before start only |
| `Ctrl+Up` / `Ctrl+Down` | cycle active word pool |
| `Alt+Left` / `Alt+Right` | cycle theme (hard-coded, not rebindable) |
| `Alt+Up` / `Alt+Down` | opacity ±10 (persisted) |
| `Ctrl+=` / `Ctrl+-` | font size ±1 (persisted) |
| `Ctrl+Alt+Left` / `Ctrl+Alt+Right` | caret alignment left / center |
| `` ` `` | toggle the details strip |
| `/` | toggle the about/keys strip |
| `Space` | after a test, toggle between the results text and the WPM graph |
| `Ctrl+,` | open settings (global event filter) |
| tray → Toggle Typing Window | show or hide the overlay without clicking the character |
| drag | move the window (persisted on release); documented as `Alt`+drag, but `ChildEventFilter` currently accepts any press |
| wheel | cycle the active mode's option (word count / time / quote length) |

### Repository map

| path | what |
|---|---|
| `main.py` | launcher; imports `src.main` and calls `main()` |
| `CHANGELOG.md` | Keep a Changelog history; `[Unreleased]` at the top, updated by every user-visible PR |
| `project_info.py` | `Info` (title, version, paths, repo slug) and `resource_path()`; **single source of the version** |
| `src/main.py` | `TippyTappyTypesApp`: tray, signals, overlay lifecycle, unelevated relaunch |
| `src/typing_overlay.py` | the overlay: modes, input, painting, status, results, themes, animation |
| `src/character_window.py` | the companion window holding only the character; click toggles the overlay |
| `src/typing_engine.py` | text generation, Error Gen Markov model, scoring, n-gram tracking |
| `src/settings_window.py` | 5-tab settings window (Appearance, Typing, Account, Statistics, Keybindings) |
| `src/config.py` | defaults, load/save, legacy migration, theme and quote accessors |
| `src/database.py` | SQLite schema, queued writer thread, stats queries |
| `src/auth.py` | Google OAuth through the Cloudflare worker proxy |
| `src/updater.py` | GitHub release check, download, elevated installer launch |
| `src/wpm_graph_widget.py` | custom-painted WPM-over-time graph with hover readout |
| `src/quotes_data.py` | `BUILTIN_QUOTES` list of `{text, author}` |
| `ui/generated/*.ui` | Qt Designer sources — edit these |
| `ui/generated/*.py` | `pyside6-uic` output — regenerate, never hand-edit |
| `ui/splash.py` | splash dialog wrapper around `QSplashScreen` |
| `ui/generate_ui_files.py` | regenerates every `.py` from every `.ui` in `ui/generated` |
| `resources/` | banner, favicon, splash, `anims/status/typing_0{1..4}.PNG` |
| `build.spec` | PyInstaller one-dir spec; bundles all of `resources/`, `info.txt`, `LICENSE`, `README.md` |
| `build.py` | local build helper: PyInstaller then NSIS (not used by CI) |
| `installer.nsi` | NSIS installer: `$PROGRAMFILES64`, HKCU Run key, unelevated finish-page launch |
| `.github/workflows/release.yml` | the only workflow: bump → build → NSIS → GitHub release |

## 4. Environment and commands

The owner works on **Windows (PowerShell 5.1)** and uses **PyCharm**. When you give the owner
commands, provide PowerShell versions:

- no `&&`: put each command on its own line;
- `$env:NAME = "value"` for environment variables;
- no backslash line continuations;
- quote paths containing spaces.

Verified on this machine: Python **3.12.2** in `.venv`, PySide6 **6.7.2**, app version
**0.1.0-beta.25**. `build.py` expects the venv at `venv\Scripts`; the checked-in environment is
`.venv`, so either pass the interpreter explicitly or fix the path deliberately.

```powershell
# run from source
.\.venv\Scripts\python.exe main.py

# regenerate UI after editing a .ui file (must run from ui\, it uses os.getcwd())
cd ui
..\.venv\Scripts\python.exe generate_ui_files.py
cd ..

# build the one-dir app (CI path)
.\.venv\Scripts\pyinstaller.exe build.spec

# build app + installer locally (needs NSIS on PATH or in Program Files)
.\.venv\Scripts\python.exe build.py
```

| task | command |
|---|---|
| run the app | `.\.venv\Scripts\python.exe main.py` |
| import smoke test | `.\.venv\Scripts\python.exe -c "import src.main, src.typing_overlay, src.settings_window"` |
| regenerate UI | `cd ui` then `..\.venv\Scripts\python.exe generate_ui_files.py` |
| build one-dir app | `.\.venv\Scripts\pyinstaller.exe build.spec` (output in `dist\TippyTappyTypes`) |
| build installer | `makensis /DAPP_VERSION=<ver> /DBUILD_DIR=dist\TippyTappyTypes installer.nsi` |
| local full build | `.\.venv\Scripts\python.exe build.py` (output in `builds\`) |
| install deps | `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` |

There is **no test suite, no linter config and no formatter config**. Do not claim `pytest`,
`ruff`, `mypy` or `black` results. If you add tests, put them under `tests/`, keep them
deterministic (no network, no wall clock, no fixed ports, no unseeded randomness) and add the
command here.

Style, in the absence of tooling: 4-space indent, no tabs, type hints on public functions and
attributes, Google-style docstrings on classes and non-trivial methods, code lines within ~100
columns (the 111-column GPL header is the only exception), `snake_case` functions and variables,
`PascalCase` classes, `UPPER_SNAKE` module constants. Match the file you are in.

## 5. Build, install and verification

Do this before claiming a build works. There is no CI test gate, so the only evidence is a run.

1. `pyinstaller build.spec` completes and `dist\TippyTappyTypes\TippyTappyTypes.exe` exists.
2. Launch the **packaged** exe, not the source: the splash must appear, the overlay must appear,
   and the tray icon must be present. Splash regressions have shipped before (see
   `ba1d9d6`), so check it explicitly.
3. Type a full test in each mode (`words`, `time`, `quotes`, `Error Gen`). Confirm WPM/accuracy
   appear, `Tab` restarts, and the graph alternates with the results line.
4. Close and relaunch: mode, option index, word pool, position, opacity and font size must persist.
5. Confirm `%APPDATA%\TippyTappyTypes\config.json` and `typing.db` were written and that a new row
   exists in `tests`.
6. Install with the NSIS setup, confirm a single Add/Remove Programs entry, the HKCU Run key, and
   that the finish-page launch is **not** elevated (Task Manager → Elevated = No). An elevated app
   cannot receive PowerToys/AutoHotkey injected keys.
7. Uninstall and confirm `%APPDATA%\TippyTappyTypes` survives.
8. For an update, install the previous version first and let the badge appear; confirm the
   downloaded installer prompts for UAC and the app exits.

Never test against the owner's real `%APPDATA%\TippyTappyTypes` if a destructive step is involved.
Point `Config(config_path=...)` and `Database(db_path=...)` at a temp directory instead; both
accept explicit paths for exactly this reason.

## 6. Privacy and network

| stays on the machine, always | may leave the machine |
|---|---|
| every keystroke and every generated test text | app version and repo slug (update check) |
| `config.json`, `typing.db`, custom tests, themes, quotes | nothing else, unless the user signs in |
| per-character and per-n-gram error statistics | OAuth code/refresh exchange with the worker |
| window position, opacity, font, hotkeys | the user's Google email, only to the worker |
| the user's email, if they signed in | — |

- Two outbound destinations only: `api.github.com` (release check, `User-Agent:
  TippyTappyTypes-Updater`) and the configured OAuth worker. Adding a third is a product decision,
  not an implementation detail.
- Both are optional in effect: the app is fully usable offline, and every network failure is
  swallowed silently by design. Do not turn those `except Exception: pass` blocks into dialogs.
- Never log tokens, the user's email or typed text. `print()` is acceptable for missing-resource
  warnings only.
- `token.json` is written with default permissions and currently resolves **relative to the working
  directory** (`data/token.json`), not `%APPDATA%`. That is a known inconsistency with `Config` and
  `Database`; if you fix it, migrate the old file and say so in the PR.

## 7. Naming conventions

| thing | name |
|---|---|
| product / display name | `TippyTappyTypes` (no space, no hyphen) |
| repo | `SoundsLikeJonny/TippyTappyTypes` |
| executable | `TippyTappyTypes.exe` |
| installer | `TippyTappyTypes-Setup-<version>.exe` |
| PyInstaller output dir | `builds\TippyTappyTypes_<YYYY_MM_DD-HH_MM_SS>\TippyTappyTypes` (local), `dist\TippyTappyTypes` (CI) |
| release tag | `v<version>`, e.g. `v0.1.0-beta.25` |
| user data dir | `%APPDATA%\TippyTappyTypes` |
| config / database | `config.json` / `typing.db` |
| Python package | `src` (flat modules, no subpackages) |
| Qt object names | `label_*`, `btn_*`, `checkBox_*`, `radio_*`, `spinBox_*`, `slider_*`, `keySeq_*`, `widget_*`, `tab_*` |
| branches | `feat/...`, `fix/...`, `docs/...`, `chore/...` |
| commits | short imperative subject, sentence case, no prefix convention enforced |

`FileTypes` in `project_info.py` (`.tiny`, `.tinydata`, `.tinyprefs`) is vestigial: nothing reads
those extensions. Do not build a file format around it without asking; do not delete it as
"unused" either, it is part of the published module surface.

## 8. Versioning and releases

- **One version, one place:** `Info.VERSION` in `project_info.py`. `build.spec`, `installer.nsi`,
  the NSIS `/DAPP_VERSION` argument and the release tag all derive from it. Do not add a second
  version constant.
- **CI owns the bump.** `.github/workflows/release.yml` runs on every push to `master`, rewrites
  `VERSION` by regex, commits `Bump version to <new> [skip ci]`, tags `v<new>` and publishes a
  release. The commit message of the triggering push selects the bump:

  | marker in commit message | effect |
  |---|---|
  | `[major]` | `X+1.0.0` |
  | `[minor]` | `X.Y+1.0` |
  | `[stable]` | drop the `-beta.N` suffix, keep `X.Y.Z` |
  | `[beta]`, or the current version is already a beta | increment `beta.N` |
  | none of the above | `X.Y.Z+1` |

- **Pre-release flag** is derived from the new version string: anything containing `-beta`,
  `-alpha` or `-rc` is published as a pre-release.
- **A tag is not a release and a push is not a PR.** Because a push to `master` publishes, treat
  `master` as production. Never tag, publish or create a release by hand.
- The version regex in CI is `VERSION:\s*str\s*=\s*'([^']+)'`. Keep that exact shape (single
  quotes, annotated `str`) or the bump silently stops matching.

### Changelog

`CHANGELOG.md` follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) and is
**mandatory for every user-visible change** (hard rule 15). It is the human-readable history; the
GitHub release notes are still generated from `git log` by CI, so the two are independent and the
changelog is not yet wired into the release body.

- **Where the entry goes.** Under `## [Unreleased]` at the top of the file. Never edit a released
  section: those are history. Do not open a version heading for an unreleased change; CI owns the
  version, and the heading is added after the tag exists (section 9, step 5).
- **Which group.** `### Added`, `### Changed`, `### Deprecated`, `### Removed`, `### Fixed`,
  `### Security`, in that order, omitting empty groups. A change that alters existing behaviour is
  `Changed`, not `Added`. A behaviour change that breaks a saved config, a hotkey default or a
  database row is marked **Breaking:** at the start of the entry.
- **What counts as user-visible.** Anything a user can see or feel: a hotkey, a default, a theme, a
  word pool, a mode, a window, an installer or updater behaviour, a stat, a persisted key, a
  performance change the user would notice. Not user-visible: refactors, renames of internals,
  tests, CI, comments, docstrings, dependency bumps that change nothing observable.
- **How to write it.** One bullet per change, starting with the file or area in backticks when it
  helps (`src/typing_overlay.py`, `installer.nsi`), then what changed and *why it mattered*. Give
  concrete before/after numbers when accuracy, WPM, timing or size changes, and name the test set
  or the machine. Do not write "improved performance" without a measurement.
- **Same PR.** The entry lands in the same commit range as the code. A PR that changes behaviour
  without a changelog entry is incomplete; say so rather than calling it ready.
- **Compare links.** Keep the link block at the bottom current: `[Unreleased]` compares the newest
  tag to `HEAD`, and each released heading compares the previous tag to its own. A new release
  heading needs its link added in the same edit.
- **No fragments yet.** There is no `changelog.d/` directory and no assembly tool. Write directly
  under `[Unreleased]`. Do not invent a fragment scheme, a `towncrier` config or a `CHANGELOG`
  generator without the owner asking.
- **Tags are not contiguous.** `v0.1.0-beta.22` and `v0.1.0-beta.23` were never tagged even though
  their bump commits are in history, so compare links skip from `beta.21` to `beta.24`. Do not
  "fix" that by inventing tags.

## 9. Release process (what actually happens)

1. PR merged into `master` by the owner. The PR carries its `CHANGELOG.md` entry under
   `[Unreleased]`.
2. `release.yml` checks out with full history, installs `requirements.txt`, bumps the version,
   commits and pushes the bump, generates `RELEASE_NOTES.md` from `git log`, runs
   `pyinstaller build.spec`, installs NSIS, builds the setup exe and creates the GitHub release
   with that one asset.
3. There is no signing, no checksum manifest, no SBOM and no install smoke test in CI. Do not
   describe a release as signed or verified.
4. The workflow needs `contents: write` and pushes with `GITHUB_TOKEN`; a branch protection rule
   that blocks bot pushes will break it.
5. Nothing moves `[Unreleased]` into a version heading automatically. After a release, the owner
   (or an agent asked to do it) adds `## [X.Y.Z] - YYYY-MM-DD`, moves the entries under it, leaves
   a fresh empty `[Unreleased]`, and adds the compare link. Do not do this before the tag exists.

## 10. Working with the owner

- Be concise, concrete and honest. Give numbers with their n and caveats. Label estimates as
  estimates.
- Give Windows PowerShell 5.1 commands when asking the owner to run something.
- Open a PR and stop; the owner reviews and merges. Ask before anything outward-facing (pushing to
  `master`, tagging, publishing, uploading assets) unless it was explicitly requested.
- A PR you hand over includes its `CHANGELOG.md` entry under `[Unreleased]`. Say in the PR body
  which section you added to, and say plainly if the change is not user-visible and therefore has
  no entry.
- The owner is a senior technical sound designer who ships desktop tools and knows Qt, PyInstaller
  and Windows packaging well. Do not over-explain the domain; do explain a trade-off in one or two
  sentences and move on.
- The owner's settled choices: PySide6, PyInstaller one-dir, NSIS, `%APPDATA%` for user data,
  GitHub Releases as the update channel, Cloudflare Worker as the OAuth proxy. Raise a blocker
  rather than substituting a different stack.
- Prefer editing an existing file over adding a module. This codebase is deliberately flat: 17
  modules under `src/` and `ui/`, no packages below either.

## 11. Current state (update this section when it changes)

As of 2026-11-23:

- **Repository:** `github.com/SoundsLikeJonny/TippyTappyTypes`, branch `master` at `f9823bb`
  (`Bump version to 0.1.0-beta.25 [skip ci]`). Tags run `v0.1-beta.1`, then `v0.1.0-beta.5`
  through `v0.1.0-beta.21`, then `v0.1.0-beta.24` and `v0.1.0-beta.25`; `beta.22` and `beta.23`
  were never tagged. The latest release is a pre-release.
- **Version:** `0.1.0-beta.25` in `project_info.py`. Python 3.12.2, PySide6 6.7.2.
- **Verified on 2026-11-23:** `import project_info, src.config, src.database, src.typing_engine,
  src.updater, src.auth` succeeds and reports `0.1.0-beta.25`. `requirements.txt` is UTF-16LE with
  a BOM and fails a UTF-8 decode. `make_icon.py`, referenced by `build.py`, does not exist.
  `build.py` points at `venv\Scripts`, but the environment on disk is `.venv`.
- **Not verified:** the GUI was not launched, no test was typed, no PyInstaller build and no NSIS
  install were run for this document. Treat the build and install steps in section 5 as untested
  until someone runs them.
- **No tests.** No `tests/`, no `pytest.ini`, no CI test job, no linter or formatter configuration.
- **Changelog:** `CHANGELOG.md` exists with `[Unreleased]` plus released sections for
  `0.1-beta.1` and `0.1.0-beta.5` through `0.1.0-beta.25`, reconstructed from the tag ranges on
  2026-11-23. Entries before `beta.5` are summarised from commit subjects, not from a contemporaneous
  record. CI does not yet read the changelog or enforce an entry.
- **Unreleased work on 2026-11-23:** personal bests (`personal_bests` table, `PR:` in the stats
  line, new-best banner and inverted-colour flash), `Space` toggling the results/graph view
  instead of a 3-second auto-cycle, and the average line removed from the WPM graph. Verified
  headless with `QT_QPA_PLATFORM=offscreen`: PR bucketing for words/time/quotes, the PR line, the
  new-best banner, the flash inverting to `(255, 255, 255)` and restoring, `Space` toggling both
  ways, no banner on a non-best run, and a full 10-word test typed through `keyPressEvent`. The
  GUI was not launched interactively and no build was run.
- **Fixed after user testing on 2026-11-23:** the banner and flash fired on the first test of any
  bucket, because `previous_pr is None` was treated as a new best. Switching pool, using random
  pools, or losing a queued write made a slow test announce a "record". A missing best now records
  silently; only a strictly higher WPM than a stored best announces.
- **Fixed after a second user report on 2026-11-23:** a genuine record was sometimes missed.
  `_handle_test_completed` calls `update_user()`, which reloaded the PR cache from the database and
  replaced the value just recorded before the queued write had landed, so the cache lagged one test
  behind (reproduced in 1 of 5 runs of the real app path). `_load_personal_bests` now merges by
  keeping the higher value per key, and `update_user` only reloads when the account actually
  changes. Verified 10/10 runs of the real `TippyTappyTypesApp` path.
- **Unreleased work on 2026-11-23 (alerts):** `notify_personal_best` and `flash_personal_best`,
  both default `True`, with two checkboxes in Settings → Typing → Display Settings. Verified
  through the real `TippyTappyTypesApp` with `isSystemTrayAvailable` patched, since offscreen has
  no tray: first test silent; a faster test shows the banner, flashes and emits one notification
  reading `230.5 WPM at 100.0% accuracy, up from 90.3 WPM`; both off gives banner with no flash and
  no notification; notification-only and flash-only each behave independently. Settings
  round-trip verified across a reload. `QSystemTrayIcon.isSystemTrayAvailable()` and
  `supportsMessages()` both return `True` on the real Windows platform. The settings group was
  rendered and inspected: two new rows, both checked.
- **Unreleased work on 2026-11-23 (character window):** `src/character_window.py` holds only the
  tinted animation frame and sits flush against the overlay's left edge at the same height and top.
  A click toggles the overlay; a drag of 5 px or more does not. Verified through the real
  `TippyTappyTypesApp` offscreen: `char.x + char.width == overlay.x`, `char.y == overlay.y` and
  `char.height == overlay.height` at startup, after a click round-trip, after a tray toggle, after
  moving the overlay and after resizing it; the overlay hides while the character stays visible;
  the animation index advances on typed characters and `_set_status("Typing")` flips the character
  to active; a theme change re-tints it; the status label's pixmap is null while the transient
  status text and the quote credit still render. Both windows were rendered together and inspected.
  The duplicate character in the details strip is gone, along with the overlay's `_tint_pixmap`,
  idle-bob timer and `_show_status_image`.
- **Unreleased work on 2026-11-23 (tray toggle):** "Toggle Typing Window" added to the tray menu
  between "Start Typing Test" and "Settings", calling the new public `toggle_visibility()`. Verified
  through the real `TippyTappyTypesApp` offscreen: the menu reads
  `Start Typing Test, Toggle Typing Window, Settings, ---, Quit`; triggering it hides the overlay
  with the character still visible, shows it again re-aligned flush, stays consistent over four
  more toggles, and recreates the overlay from `None` when it had been closed.
- **Known gaps:** `src/auth.py` ships a placeholder worker URL
  (`https://TippyTappyTypes-oauth.YOUR-SUBDOMAIN.workers.dev`), so sign-in cannot succeed until a
  real worker is configured; `oauth_server/` is gitignored and undeployed from this repo.
  `token.json` resolves relative to the working directory. `FileTypes` is unused. The settings
  window's fallback defaults (`Consolas`, 24, 1200×120) disagree with `Config`'s (`Courier New`,
  8, 500×60); `Config` is authoritative because it always supplies the key.
- **Untracked:** `AGENTS.md` and `CHANGELOG.md` are new and not yet committed; everything else is
  clean.
