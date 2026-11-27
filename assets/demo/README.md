# Recording a demo of a one-shot run

Keep raw footage outside repositories. Complete sign-ins, key entry and contact-data
setup before recording. Use a staged example for any setup sequence in a public demo.

| Footage | How |
|---|---|
| Pitch and menu | A staged example with synthetic data, recorded with Cmd-Shift-5 around the intended window |
| Unattended build | `record_timelapse.sh --window-id <id> <outside-repo-dir>/frames 3` in your own terminal; use the Core Graphics ID of the intended window |
| Finished app | `xcrun simctl io <udid> recordVideo --codec h264 sim.mp4` with synthetic app data |
| Store proof | Crop or redact account names, IDs, contact details and unpublished app information before use |

The time-lapse recorder requires a specific window and stops on a capture failure. It
never falls back to a whole-display capture. Stop with Ctrl-C or
`touch <outside-repo-dir>/frames/STOP`. Focus mode helps, but private information within
the chosen window is still recorded. Inspect every frame before sharing; the text scanner
cannot detect information inside images or video.

Write `storyboard.json` next to the footage (format in `make_demo.py --help`) and render:

```bash
python3 make_demo.py storyboard.json
```

It renders title/end cards, captions, a time-lapse clock, optional music, an MP4 and an
optional GIF. Review and redact those final outputs locally. Only after that review,
rerun with `--readme /path/to/repo/README.md --reviewed-for-sharing` to link the GIF.
The flag is your acknowledgement of a manual review, not an automated privacy check.
Raw footage and media are excluded from source packages.
