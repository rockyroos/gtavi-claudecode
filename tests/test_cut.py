"""Self-check for cut.py: python tests/test_cut.py (no ffmpeg needed)."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import cut

# slurs and hard swears still masked
for bad in ["nigga", "n1gga", "nigger", "faggot", "f@ggots", "retard", "retarded", "tranny", "chinks", "spics", "kikes",
            "fuck", "shit", "Dick", "dickhead", "pussy", "bitch"]:
    assert "*" in cut.clean(bad), bad
# ordinary words left alone
for ok in ["spice", "spicy", "retardant", "niggle", "niggling", "Dickens", "pussycat", "bike", "Scunthorpe", "chinking"]:
    assert cut.clean(ok) == ok, (ok, cut.clean(ok))
assert cut.clean("shit", profanity=True) == "shit" and cut.clean("nigga", profanity=True) != "nigga"

# hook and title are masked like the captions (and respect profanity=True)
for kw in ({"hook": "what the shit"}, {"hook": "", "title": ("box", "what the shit", 730, 0)}, {"hook": "", "title": ("outline", "what the shit", 770, 0)}):
    assert "shit" not in cut.build_ass([], 0, 5, kw.pop("hook"), 1380, **kw), kw
assert "shit" in cut.build_ass([], 0, 5, "what the shit", 1380, profanity=True)

# facecam: both panel heights even and stacked height exactly 1920
g = cut.video_filter("facecam", "0.7:0:0.3:0.3", "x.ass")
cam_h, game_h = map(int, re.search(r"crop=1080:(\d+)\[cam\].*crop=1080:(\d+)\[game\]", g).groups())
assert cam_h % 2 == 0 and game_h % 2 == 0 and cam_h + game_h == cut.H, (cam_h, game_h)
# subtitle path with ' , [ ] ; and spaces must reach libass intact (needs ffmpeg, skipped without it)
import shutil, subprocess, tempfile
if shutil.which("ffmpeg"):
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "O'Brien, [x]; a b"
        d.mkdir()
        ass = d / "c.ass"
        ass.write_text(cut.build_ass([], 0, 1, "hi", 1380), encoding="utf-8")
        r = subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=1", "-filter_complex",
                            f"[0:v]null[v];[v]subtitles={cut.filter_path(ass)}[vo]", "-map", "[vo]", "-f", "null", "-"],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[-300:]
print("ok")
