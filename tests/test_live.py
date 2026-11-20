"""Self-check for live.py cut(): python tests/test_live.py (needs ffmpeg, skipped without it).
Cuts a clip out of two fake recorded segments that sit in a folder named like O'Brien."""
import shutil, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import live

if not shutil.which("ffmpeg"):
    print("skipped (no ffmpeg)")
    sys.exit(0)

with tempfile.TemporaryDirectory() as t:
    ld = Path(t) / "O'Brien's live"
    ld.mkdir()
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=25:duration=10", "-c:v", "libx264",
                    "-g", "25", "-pix_fmt", "yuv420p", "-f", "segment", "-segment_time", "5", "-segment_format", "mpegts",
                    "-reset_timestamps", "1", "-segment_list", str(ld / "segments.csv"), "-segment_list_type", "csv",
                    str(ld / "seg_%05d.ts")], check=True)
    rec = live.Recorder.__new__(live.Recorder)
    rec.ld, rec.csv = ld, ld / "segments.csv"
    mt = rec.segments()[-1][3]
    out = ld / "spike_1.mp4"
    center, ok = live.cut(rec, mt, 5, 5, 0, out)
    assert ok and out.stat().st_size > 0, "cut failed"
    assert not out.with_suffix(".txt").exists()
# Timing model: chat reacts to video the viewer sees D seconds after the recorder got it, plus reaction time R.
# So at chat time W the event sits (D+R) seconds BEFORE the recorder's live position, and --lag must shift the clip earlier.
import os, re
with tempfile.TemporaryDirectory() as t:
    ld = Path(t)
    EVENT, D, R, W0 = 60, 5, 3, 1_000_000.0   # white flash at stream position 60..61 s
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                    f"color=c=black:s=320x180:r=25:d=100,drawbox=x=0:y=0:w=iw:h=ih:color=white:t=fill:enable='between(t,{EVENT},{EVENT + 1})'",
                    "-c:v", "libx264", "-g", "25", "-pix_fmt", "yuv420p", "-f", "segment", "-segment_time", "20", "-segment_format", "mpegts",
                    "-reset_timestamps", "1", "-segment_list", str(ld / "segments.csv"), "-segment_list_type", "csv",
                    str(ld / "seg_%05d.ts")], check=True)
    rec = live.Recorder.__new__(live.Recorder)
    rec.ld, rec.csv = ld, ld / "segments.csv"
    for f, _, en, _, _ in rec.segments():
        os.utime(f, (W0 + en, W0 + en))          # a segment is finished at the wall time its end was received
    chat_time = W0 + EVENT + D + R               # when chat reacts to the flash
    out = ld / "spike.mp4"
    center, ok = live.cut(rec, chat_time, 15, 20, D + R, out)
    assert ok, "cut failed"
    def flash_at(clip):
        p = subprocess.run(["ffmpeg", "-v", "error", "-i", str(clip), "-vf", "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-",
                            "-f", "null", "-"], capture_output=True, text=True).stdout
        hits = [float(m.group(1)) for m in re.finditer(r"pts_time:([\d.]+)\nlavfi\.signalstats\.YAVG=(\d+)", p) if float(m.group(2)) > 200]
        assert hits, "the event is not in the clip at all"
        return hits[0]
    o = flash_at(out)
    assert 5 < o < 25, f"event {o:.1f}s into the clip, expected near the 'before' mark (15 s)"

    # calibration: a run with too small a lag (4 instead of 8) starts the clip too late, so the event shows early in it; calibrate_lag must recover ~8
    import calibrate_lag
    out2 = ld / "spike_lag4.mp4"
    assert live.cut(rec, chat_time, 15, 20, 4, out2)[1], "cut failed"
    o2 = flash_at(out2)
    assert o2 < o - 2, "a smaller lag should move the event earlier in the clip"
    each, med = calibrate_lag.suggest(4, 15, [o2])
    assert abs(med - (D + R)) <= 1.5, f"suggested lag {med:.1f}, true {D + R}"
    assert calibrate_lag.secs("1:05.5") == 65.5 and calibrate_lag.secs("21") == 21
print("ok")
