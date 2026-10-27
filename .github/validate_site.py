#!/usr/bin/env python3
"""Check the bilingual build, local links, and public resource boundary."""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_DIRS = {"_backup", "_extensions", "_filters", "_includes", ".git", ".quarto", "node_modules", "scripts", "research"}
SOURCE_SUFFIXES = {".qmd", ".ipynb", ".py", ".lua", ".tex", ".bib", ".npz", ".csv"}
WITHHELD_IMAGES = {"synchronization-overview.svg", "synchronization-reentrance.svg"}


class Document(HTMLParser):
    def __init__(self, path: Path):
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.references: list[str] = []
        self.language = None
        self.has_main = False
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "html":
            self.language = attrs.get("lang")
        if tag == "main":
            self.has_main = True
        self.references.extend(attrs[key] for key in ("href", "src") if attrs.get(key))


def validate(site: Path) -> list[str]:
    errors: list[str] = []
    if not site.is_dir():
        return [f"Site directory does not exist: {site}"]
    sources = [*ROOT.glob("*.qmd"), *(ROOT / "ja").glob("*.qmd")]
    expected = {p.relative_to(ROOT).with_suffix(".html").as_posix() for p in sources}
    documents: dict[Path, Document] = {}

    def document(path: Path) -> Document:
        if path not in documents:
            documents[path] = Document(path)
        return documents[path]

    def check_reference(owner: Path, reference: str):
        url = urlsplit(reference)
        if url.scheme == "file":
            errors.append(f"{owner.relative_to(site)}: local filesystem URL")
            return
        if url.scheme or url.netloc:
            return
        target = site / unquote(url.path.lstrip("/")) if url.path.startswith("/") else owner.parent / unquote(url.path)
        if not url.path:
            target = owner
        target = target.resolve()
        if not target.is_relative_to(site):
            errors.append(f"{owner.relative_to(site)}: path outside output: {reference}")
            return
        if target.is_dir():
            target /= "index.html"
        if not target.is_file():
            errors.append(f"{owner.relative_to(site)}: missing target: {reference}")
        elif url.fragment and target.suffix == ".html" and unquote(url.fragment) not in document(target).ids:
            errors.append(f"{owner.relative_to(site)}: missing anchor: {reference}")

    for route in sorted(expected):
        path = site / route
        if not path.is_file():
            errors.append(f"Missing page: {route}")
            continue
        page = document(path)
        language = "ja" if route.startswith("ja/") else "en"
        if page.language != language or not page.has_main:
            errors.append(f"Invalid language or missing main content: {route}")
        for reference in page.references:
            check_reference(path, reference)

    for path in site.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(site)
        if (relative.parts[0] in PRIVATE_DIRS
                or relative.parts[:2] == ("assets", "cv")
                or path.suffix.lower() in SOURCE_SUFFIXES
                or path.name in {"SOURCES.md", ".DS_Store"}
                or path.name in WITHHELD_IMAGES
                or path.name.startswith("home-synchronization-schematic.")):
            errors.append(f"Non-public file in output: {relative}")
        if path.suffix == ".html" and relative.parts[0] != "site_libs" and relative.as_posix() not in expected:
            errors.append(f"Unexpected page: {relative}")
        if path.suffix == ".css":
            for _, reference in re.findall(r"url\(\s*(['\"]?)(.*?)\1\s*\)", path.read_text(encoding="utf-8"), re.S):
                check_reference(path, reference)

    search_path = site / "search.json"
    try:
        search = json.loads(search_path.read_text(encoding="utf-8"))
        for entry in search:
            check_reference(search_path, entry["href"])
        indexed = {entry["href"].split("#")[0] for entry in search}
        if indexed != expected:
            errors.append(f"Search pages differ from source pages: {sorted(indexed ^ expected)}")
    except (OSError, ValueError, KeyError, TypeError) as error:
        errors.append(f"Invalid search index: {error}")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", type=Path, default=ROOT / "_site")
    args = parser.parse_args()
    errors = validate(args.site_dir.resolve())
    if errors:
        print("Website validation failed:\n" + "\n".join(f"- {error}" for error in errors))
        return 1
    print("Website validated: bilingual pages, local links, fonts, search, and public resources.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
