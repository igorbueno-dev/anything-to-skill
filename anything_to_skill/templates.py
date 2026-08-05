from __future__ import annotations

_SCHEMAS = {
    "paper": ["Pergunta", "Método", "Achados", "Limitações"],
    "article": ["Tese", "Argumentos", "Ressalvas"],
    "technical_book": ["Ideia central", "Como aplicar", "Armadilhas"],
    "transcript": ["Pontos principais", "Momentos citáveis"],
}


def render_section(profile: str, theme: str, items: list[dict]) -> str:
    lines = [f"# {theme}", ""]
    bullets = [f"- {it['label']} {it.get('citation', '')}".rstrip() for it in items]
    if profile == "reference":
        lines += bullets or ["_(sem itens)_"]
        return "\n".join(lines) + "\n"
    schema = _SCHEMAS.get(profile, _SCHEMAS["article"])
    for i, header in enumerate(schema):
        lines.append(f"## {header}")
        if i == 0:
            lines += bullets or ["_(a preencher a partir de content/)_"]
        lines.append("")
    return "\n".join(lines) + "\n"
