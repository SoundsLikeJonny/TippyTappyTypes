# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Entries are grouped under `### Added`, `### Changed`, `### Deprecated`, `### Removed`,
`### Fixed` and `### Security`, in that order, with empty groups omitted. Newest first.

## [Unreleased]

### Added

- Companion character window: a second frameless always-on-top window holding only the tinted
  animation frame, placed immediately left of the typing overlay and vertically centred so the two
  touch with no gap. Clicking it hides the overlay; clicking again shows it, re-aligned to the
  character's right edge. It follows the overlay when the overlay is dragged or resized, and it
  stays visible while the overlay is hidden.
- "Toggle Typing Window" in the tray menu, so the overlay can be shown or hidden when the character
  window cannot be clicked. It recreates the overlay if it does not exist.
- System notification on a new personal best, on by default, shown through the tray icon with the
  WPM, the accuracy and the previous best. Toggle: Settings → Typing → Display Settings →
  "Personal Best Alert".
- "Personal Best Flash" toggle in the same group, on by default, for the inverted-colour flash.
  Both can be turned off independently, so the banner still appears while the notification, the
  flash, or both are suppressed.
- `AGENTS.md`: the operating contract for AI agents and new contributors. It records the
  architecture, the fifteen hard rules, the hotkey table, the repository map, the PowerShell
  commands, the build/install verification checklist, the privacy boundary, the naming
  conventions and the CI version-bump markers, plus a dated "current state" section.
- `CHANGELOG.md`: this file, in Keep a Changelog 1.1.0 form, with the released beta history
  reconstructed from the tag ranges.
- Personal bests, stored per mode, option and word pool in a new `personal_bests` table. Word and
  timed tests are bucketed by mode, option and pool name (`words:25:Default`,
  `time:30:5k English`), so every pool keeps its own record; quotes are bucketed by length
  (`quotes:short`), since the quote itself is random. The best WPM is shown as `PR:` next to the
  averages in the stats line before a test starts, and reads `--` until one is set.
- "New Personal Best: XXX WPM" on the results line when a test beats an existing stored best, with
  the window flashing six times by inverting its background color at full opacity. The first test
  in a bucket records its result silently: with no record to beat, nothing is announced or
  flashed. The PR cache merges by highest value and is only re-read when the account changes, so a
  queued write that has not landed yet cannot hide a record that was just set.

### Changed

- `AGENTS.md` section 8 now requires a `CHANGELOG.md` entry in the same PR as any user-visible
  change, and section 11 records the state of the repository at the time of writing.
- Results no longer cycle between the text and the graph on a 3-second timer. `Space` toggles
  between them, so the view stays where the user left it. The results line now reads
  `SPACE: graph  |  TAB: restart`.

### Removed

- The running-average line, its points and its `Avg:` hover readout in the WPM graph. The graph
  now plots only the instantaneous WPM, in the theme's primary color, and `set_data`/`set_colors`
  no longer take a secondary color.

## [0.1.0-beta.25] - 2026-08-24

### Fixed

- Splash screen no longer fails to display on open in packaged builds. The splash is created
  before the overlay is shown and closed on its own signal rather than relying on the dialog's
  lifetime.

## [0.1.0-beta.24] - 2026-08-24

### Added

- New character art by Cafefaevans: icons, splash screen and banner. A small character waits
  while idle and extends its feet once typing starts, driven by the four
  `resources/anims/status/typing_0{1..4}.PNG` frames.

### Changed

- Renamed the project to TippyTappyTypes across every file, path, registry key, installer define
  and user-data directory.

### Fixed

- The `Esc` quit prompt is always shown, including while the WPM graph is on screen.
- NSIS installer packaging, across three attempts: the payload, the install directory and the
  finish-page launch.

## [0.1.0-beta.21] - 2026-08-24

### Changed

- README rewritten for the renamed project.

## [0.1.0-beta.20] - 2026-08-16

### Fixed

- `src/wpm_graph_widget.py` was missing from the repository, so the graph feature of beta.19
  could not import. Added.

## [0.1.0-beta.19] - 2026-08-16

### Added

- WPM sampling once per second during a test, with a custom-painted graph that alternates with
  the results line every three seconds and pauses while hovered.
- "Most Problematic N-grams" table in the Statistics tab, sorted by error rate descending.
- **Error Gen** word pool: a character-level Markov model over the active corpus, seeded with the
  user's worst trigrams and 4-grams and weighting problem letters ×3, so practice targets the
  mistakes the database actually recorded.

### Changed

- The active mode, its option index and the active word pool persist across restarts.

## [0.1.0-beta.18] - 2026-08-12

### Added

- SOUNDWICH colour theme.

## [0.1.0-beta.17] - 2026-08-12

### Fixed

- `quotes_data` import path after the quotes module was split out.

## [0.1.0-beta.16] - 2026-08-11

### Added

- 100 additional quotes.

### Changed

- Quotes moved out of `config.py` into `src/quotes_data.py`.

### Fixed

- The mouse cursor is hidden while a test is actively in progress.

## [0.1.0-beta.15] - 2026-08-10

### Added

- Tooltip on the quote credit, so an author name too long for the status label is still readable.

## [0.1.0-beta.14] - 2026-08-10

### Added

- Quotes mode with real quotations and attribution, in four length buckets: short, medium, long
  and extreme.

## [0.1.0-beta.13] - 2026-08-10

### Changed

- The "very dark" themes were retuned to be slightly more colourful while staying subtle.

## [0.1.0-beta.12] - 2026-08-10

### Added

- Twenty themes: ten light and ten vivid.
- Fifteen more themes: five brown, five greyscale and five very dark.

### Changed

- Built-in themes now come from the application version instead of `config.json`, so a release
  can add themes without a migration. User-created themes stay local.

## [0.1.0-beta.11] - 2026-08-10

### Fixed

- An error on a space character now highlights the background in the error colour. Previously the
  space was recorded as the mistaken character, and since no glyph exists the error was invisible.

## [0.1.0-beta.10] - 2026-08-08

### Added

- Fifteen themes: ten material-inspired and five friendly.

### Changed

- Default caret alignment is now left.

### Fixed

- "Move per word" advances by word instead of by character.
- The update icon and keybinding colours follow the active theme.
- The "Cycle Word Pool" keybinding label text.
- Hiding and unhiding the stats or keybindings strip no longer clips the typing area.
- Removed the "Theme: " prefix from the theme banner.

## [0.1.0-beta.9] - 2026-08-08

### Fixed

- The release build did not install every requirement, so the packaged app was missing modules.

## [0.1.0-beta.8] - 2026-08-08

### Fixed

- The updater no longer requires elevation to run its check.

## [0.1.0-beta.7] - 2026-08-08

### Changed

- Dummy submission used to exercise the version-bump and release pipeline.

## [0.1.0-beta.6] - 2026-08-08

### Fixed

- Confirming the update prompt now actually downloads and launches the installer.

## [0.1.0-beta.5] - 2026-08-08

### Added

- Configurable keybindings, additional themes, typing-path performance work and the
  GitHub Actions release pipeline.

### Fixed

- NSIS installer build.
- `build.spec` resolves paths from `SPECPATH` instead of `__file__`.
- `build.spec` imports `project_info` correctly under CI.

## [0.1-beta.1] - 2026-08-05

### Added

- Initial release: the frameless always-on-top typing overlay, words and timed modes, WPM and
  accuracy scoring, per-character statistics in SQLite, the settings window, the splash screen,
  the PyInstaller spec, the NSIS installer, the GPL-3.0 licence and the README.

### Fixed

- Average WPM and accuracy display.

[Unreleased]: https://github.com/SoundsLikeJonny/TippyTappyTypes/compare/v0.1.0-beta.25...HEAD
[0.1.0-beta.25]: https://github.com/SoundsLikeJonny/TippyTappyTypes/compare/v0.1.0-beta.24...v0.1.0-beta.25
[0.1.0-beta.24]: https://github.com/SoundsLikeJonny/TippyTappyTypes/compare/v0.1.0-beta.21...v0.1.0-beta.24
[0.1.0-beta.21]: https://github.com/SoundsLikeJonny/TippyTappyTypes/compare/v0.1.0-beta.20...v0.1.0-beta.21
[0.1.0-beta.20]: https://github.com/SoundsLikeJonny/TippyTappyTypes/compare/v0.1.0-beta.19...v0.1.0-beta.20
[0.1.0-beta.19]: https://github.com/SoundsLikeJonny/TippyTappyTypes/compare/v0.1.0-beta.18...v0.1.0-beta.19
[0.1.0-beta.18]: https://github.com/SoundsLikeJonny/TippyTappyTypes/compare/v0.1.0-beta.17...v0.1.0-beta.18
[0.1.0-beta.17]: https://github.com/SoundsLikeJonny/TippyTappyTypes/compare/v0.1.0-beta.16...v0.1.0-beta.17
[0.1.0-beta.16]: https://github.com/SoundsLikeJonny/TippyTappyTypes/compare/v0.1.0-beta.15...v0.1.0-beta.16
[0.1.0-beta.15]: https://github.com/SoundsLikeJonny/TippyTappyTypes/compare/v0.1.0-beta.14...v0.1.0-beta.15
[0.1.0-beta.14]: https://github.com/SoundsLikeJonny/TippyTappyTypes/compare/v0.1.0-beta.13...v0.1.0-beta.14
[0.1.0-beta.13]: https://github.com/SoundsLikeJonny/TippyTappyTypes/compare/v0.1.0-beta.12...v0.1.0-beta.13
[0.1.0-beta.12]: https://github.com/SoundsLikeJonny/TippyTappyTypes/compare/v0.1.0-beta.11...v0.1.0-beta.12
[0.1.0-beta.11]: https://github.com/SoundsLikeJonny/TippyTappyTypes/compare/v0.1.0-beta.10...v0.1.0-beta.11
[0.1.0-beta.10]: https://github.com/SoundsLikeJonny/TippyTappyTypes/compare/v0.1.0-beta.9...v0.1.0-beta.10
[0.1.0-beta.9]: https://github.com/SoundsLikeJonny/TippyTappyTypes/compare/v0.1.0-beta.8...v0.1.0-beta.9
[0.1.0-beta.8]: https://github.com/SoundsLikeJonny/TippyTappyTypes/compare/v0.1.0-beta.7...v0.1.0-beta.8
[0.1.0-beta.7]: https://github.com/SoundsLikeJonny/TippyTappyTypes/compare/v0.1.0-beta.6...v0.1.0-beta.7
[0.1.0-beta.6]: https://github.com/SoundsLikeJonny/TippyTappyTypes/compare/v0.1.0-beta.5...v0.1.0-beta.6
[0.1.0-beta.5]: https://github.com/SoundsLikeJonny/TippyTappyTypes/compare/v0.1-beta.1...v0.1.0-beta.5
[0.1-beta.1]: https://github.com/SoundsLikeJonny/TippyTappyTypes/commits/v0.1-beta.1
