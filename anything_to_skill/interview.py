from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path

_DEPTHS = {"reference", "study"}


@dataclass
class BuildConfig:
    purpose: str = "work-reference"
    depth: str = "reference"
    scope: str = ""
    authoritative: list[str] = field(default_factory=list)


def normalize_answers(raw: dict) -> BuildConfig:
    depth = raw.get("depth", "reference")
    if depth not in _DEPTHS:
        depth = "reference"
    auth = raw.get("authoritative") or []
    if not isinstance(auth, list):
        auth = [auth]
    return BuildConfig(
        purpose=raw.get("purpose") or "work-reference",
        depth=depth,
        scope=raw.get("scope", ""),
        authoritative=[str(a) for a in auth],
    )


def write_config(cfg: BuildConfig, out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "build_config.json"
    p.write_text(json.dumps(asdict(cfg), indent=2, ensure_ascii=False), encoding="utf-8")
    return p
