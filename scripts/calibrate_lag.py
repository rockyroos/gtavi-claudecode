"""Suggest a --lag for live.py from where the trigger moment shows up in your spike clips.

Watch 3 or more clips from a live run, note when the moment happens in each (seconds into the clip), then:
  python calibrate_lag.py --job jobs/<id> --event 21 0:09 18.5
  python calibrate_lag.py --lag 8 --before 15 --event 21 9 18        (no job folder: pass the values the run used)
The clip is centred so the moment lands at the --before mark. Later than that -> lower lag, earlier -> raise it.
"""
import argparse, statistics, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import load_json


def secs(s):
    m, _, r = s.rpartition(":")
    return (float(m) * 60 if m else 0) + float(r)


def suggest(lag, before, event_secs):
    """lag that would have put each event exactly at the `before` mark, and their median."""
    each = [lag + before - e for e in event_secs]
    return each, statistics.median(each)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", help="jobs/<id> of the live run (reads lag and before from live/live.json)")
    ap.add_argument("--lag", type=float, default=8); ap.add_argument("--before", type=float, default=15)
    ap.add_argument("--event", nargs="+", required=True, help="when the moment happens in each clip: seconds or m:ss")
    a = ap.parse_args()
    lag, before = a.lag, a.before
    if a.job:
        j = load_json(Path(a.job) / "live" / "live.json")
        if "lag" not in j:
            sys.exit("live.json has no lag/before (run made before calibration support): pass --lag and --before instead of --job")
        lag, before = j["lag"], j["before"]
    each, med = suggest(lag, before, [secs(e) for e in a.event])
    print(f"run used --lag {lag:g} --before {before:g}")
    print("per clip: " + ", ".join(f"{x:.1f}" for x in each))
    print(f"suggested --lag {med:.1f}" + ("" if len(each) >= 3 else "   (only %d clip(s): use 3 or more)" % len(each)))
    if max(each) - min(each) > 8:
        print("spread is large: the lag is not constant on this stream; the clips need a wide --before, not a better --lag")


if __name__ == "__main__":
    main()
