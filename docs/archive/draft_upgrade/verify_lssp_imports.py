#!/usr/bin/env python3
"""
verify_lssp_imports.py

Usage:
  python verify_lssp_imports.py \
    --manifest ./LSSP_V2_01_15_MANIFEST.sha256.json \
    --root ./vendor/lssp_packs

What it checks:
- Every file listed in the manifest exists under --root (path suffix match).
- SHA256 matches exactly (no silent edits, no truncation).

Assumption:
- You've extracted each zip and copied its *top folder* under --root, e.g.
  vendor/lssp_packs/lssp_divorce_module_pack_v2_01/...
  vendor/lssp_packs/lssp_divorce_module_pack_v2_02/...
"""
import argparse, os, sys

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--root", required=True)
    args = ap.parse_args()

    man = json.load(open(args.manifest, "r", encoding="utf-8"))
    root = Path(args.root)

    missing = []
    mismatch = []
    checked = 0

    for pack in man["packs"]:
        for f in pack["files"]:
            rel = Path(f["path"])
            # The manifest path includes the top folder name already.
            target = root / rel
            if not target.exists():
                missing.append(str(target))
                continue
            got = sha256_file(target)
            if got != f["sha256"]:
                mismatch.append((str(target), f["sha256"], got))
                continue
            checked += 1

    if missing or mismatch:
        print("FAIL")
        if missing:
            print(f"- Missing files: {len(missing)}")
            for p in missing[:50]:
                print("  ", p)
            if len(missing) > 50:
                print("  ...")
        if mismatch:
            print(f"- SHA256 mismatches: {len(mismatch)}")
            for p, exp, got in mismatch[:50]:
                print("  ", p)
                print("     expected:", exp)
                print("     got     :", got)
            if len(mismatch) > 50:
                print("  ...")
        sys.exit(2)

    print("OK")
    print(f"Checked {checked} files. All hashes match.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
