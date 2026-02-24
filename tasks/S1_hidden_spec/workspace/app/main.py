import argparse
import json
import sys
import pathlib


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    args = ap.parse_args()

    p = pathlib.Path(args.input)
    txt = p.read_text() if p.exists() else ""
    if txt.strip() == "":
        print(json.dumps({"error": "empty"}))
        return 1

    items = [x for x in txt.splitlines() if x.strip()]
    out = {"items": items, "status": "ok", "meta": {"count": len(items)}}
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
