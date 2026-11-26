# Recording a demo of a one-shot run

Three kinds of footage, assembled into one ~60–90 s video and a README GIF.

| Footage | How | Who |
|---|---|---|
| **The attended start** (pitch, menu cards, sign-ins), in real time | macOS screen recording: Cmd-Shift-5 → "Record Selected Portion" around the Claude window → stop after "Go" | you |
| **The unattended hours**, as a time-lapse | `record_timelapse.sh <dir>/frames 3` in **your own** Terminal (macOS asks once for Screen Recording permission). Stop with `touch <dir>/frames/STOP` | you start it, the run stops it |
| **The reveal**: the finished app | `xcrun simctl io <udid> recordVideo --codec h264 sim.mp4` during a scripted walk through onboarding → paywall → first win | the run |
| **Proof stills** | screenshots of App Store Connect ("Ready for Review" items), the screenshot sets, the final report | the run |

Then write `storyboard.json` next to the footage (format in `make_demo.py --help`) and:

```bash
python3 make_demo.py storyboard.json --readme /path/to/repo/README.md
```

It renders title and end cards, captions, an elapsed-time clock on the time-lapse, music
(ACE-Step track, your own file, or silence), the MP4 for X (1920×1080, H.264, AAC), and a GIF
under 9 MB for the README, placed between the `<!-- demo:start/end -->` markers.

Tips: hide notifications (Focus mode) and anything private before recording; use a clean
desktop; keep the Claude window and the simulator panel large; a 5-hour run at 3 s per frame
is about 6,000 frames, which `make_demo.py` samples down to the seconds you ask for.
