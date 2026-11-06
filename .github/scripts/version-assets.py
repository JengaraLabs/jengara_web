#!/usr/bin/env python3
"""Stamp every local CSS/JS reference in the site's HTML with a content hash.

The server caches /assets/*.css and *.js for a year, so browsers only fetch
a changed file when its URL changes. This rewrites
    href="/assets/platform.css"  or  href="/assets/platform.css?v=old"
to
    href="/assets/platform.css?v=<first 10 chars of the file's SHA-256>"
so a URL changes only when the file's content does.

Run from the repository root. Prints the files it changed; exits 0 either way.
"""
import hashlib
import pathlib
import re

ROOT = pathlib.Path(".").resolve()
REF = re.compile(r'(?P<attr>href|src)="(?P<path>/[^"?#]+\.(?:css|js))(?:\?v=[^"]*)?"')
_hashes: dict[str, str | None] = {}


def content_hash(url_path: str) -> str | None:
    if url_path not in _hashes:
        f = ROOT / url_path.lstrip("/")
        _hashes[url_path] = (
            hashlib.sha256(f.read_bytes()).hexdigest()[:10] if f.is_file() else None
        )
    return _hashes[url_path]


def stamp(match: re.Match) -> str:
    h = content_hash(match["path"])
    if h is None:  # not a file in this repo; leave the reference untouched
        return match[0]
    return f'{match["attr"]}="{match["path"]}?v={h}"'


changed = []
for page in sorted(ROOT.rglob("*.html")):
    if ".git" in page.parts:
        continue
    text = page.read_text(encoding="utf-8")
    new = REF.sub(stamp, text)
    if new != text:
        page.write_text(new, encoding="utf-8")
        changed.append(str(page.relative_to(ROOT)))

print(f"version-assets: updated {len(changed)} page(s)")
for p in changed:
    print("  " + p)
