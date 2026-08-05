from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path

_HEADING = re.compile(r"^\s*#\s+(.+?)\s*$", re.MULTILINE)


@dataclass
class Source:
    id: str
    title: str
    kind: str
    origin: str
    profile: str | None = None


def _title_for(path: Path) -> str:
    if path.suffix.lower() in {".md", ".markdown"}:
        m = _HEADING.search(path.read_text(encoding="utf-8", errors="replace"))
        if m:
            return m.group(1)
    return path.stem


def _kind_for(path: Path) -> str:
    ext = path.suffix.lower().lstrip(".")
    return {"markdown": "md"}.get(ext, ext or "unknown")


def register_sources(paths: list[Path], out_dir: Path) -> list[Source]:
    sources: list[Source] = []
    for i, p in enumerate(paths, start=1):
        p = Path(p)
        sources.append(
            Source(
                id=f"S{i}",
                title=_title_for(p),
                kind=_kind_for(p),
                origin=str(p.resolve()),
            )
        )
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "sources.json").write_text(
        json.dumps([asdict(s) for s in sources], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return sources
