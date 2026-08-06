from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ImageRef:
    filename: str
    anchor: str
    page: int | None = None


@dataclass
class NormalizedDoc:
    markdown: str
    images: list[ImageRef] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    page_count: int | None = None


def _normalize_pdf(path: Path, out_images_dir: Path, source_id: str) -> NormalizedDoc:
    import fitz  # PyMuPDF

    out_images_dir = Path(out_images_dir)
    out_images_dir.mkdir(parents=True, exist_ok=True)
    parts: list[str] = []
    images: list[ImageRef] = []
    warnings: list[str] = []
    doc = fitz.open(path)
    for pno in range(doc.page_count):
        page = doc.load_page(pno)
        parts.append(page.get_text("text"))
        for i, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            if pix.n - pix.alpha >= 4:  # CMYK/outros -> RGB
                pix = fitz.Pixmap(fitz.csRGB, pix)
            fname = f"{source_id}-p{pno + 1}-i{i}.png"
            pix.save(str(out_images_dir / fname))
            anchor = f"![{fname}](figures/{fname})"
            parts.append(anchor)
            images.append(ImageRef(filename=fname, anchor=anchor, page=pno + 1))
    if doc.page_count and not images:
        warnings.append("nenhuma imagem extraida; verificar se o PDF tinha figuras")
    return NormalizedDoc(markdown="\n\n".join(parts) + "\n", images=images,
                         warnings=warnings, page_count=doc.page_count)


def _normalize_html(text: str) -> NormalizedDoc:
    from markdownify import markdownify as md

    return NormalizedDoc(markdown=md(text).strip() + "\n")


def normalize(path: Path, *, kind: str, out_images_dir: Path,
              source_id: str, html_text: str | None = None) -> NormalizedDoc:
    if kind in {"md", "markdown"}:
        return NormalizedDoc(markdown=Path(path).read_text(encoding="utf-8", errors="replace"))
    if kind == "txt":
        return NormalizedDoc(markdown=Path(path).read_text(encoding="utf-8", errors="replace"))
    if kind == "pdf":
        return _normalize_pdf(Path(path), Path(out_images_dir), source_id)
    if kind == "html":
        return _normalize_html(
            html_text if html_text is not None
            else Path(path).read_text(encoding="utf-8", errors="replace")
        )
    raise ValueError(f"tipo não suportado: {kind}")
