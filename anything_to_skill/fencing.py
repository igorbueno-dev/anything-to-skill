from __future__ import annotations


def fence_untrusted(text: str) -> str:
    """Envolve conteúdo não-confiável (ex.: buscado de URL) numa cerca, neutralizando
    tags de fechamento forjadas para que instruções injetadas não escapem da cerca."""
    safe = text.replace("</untrusted-source>", "<\\/untrusted-source>")
    return f"<untrusted-source>\n{safe}\n</untrusted-source>"
