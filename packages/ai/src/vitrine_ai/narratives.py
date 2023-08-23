"""Curator assistant narrative generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from vitrine_mix.craft import build_craft_report, pacing_score, transition_density
from vitrine_types.models import Exhibition

NarrativeTone = Literal["formal", "conversational", "brief"]


@dataclass
class NarrativeSection:
    heading: str
    body: str
    priority: int = 0


@dataclass
class CuratorNarrative:
    exhibition_id: str
    title: str
    tone: NarrativeTone
    sections: list[NarrativeSection]
    summary: str
    action_items: list[str] = field(default_factory=list)
    word_count: int = 0


def _describe_pacing(exhibition: Exhibition) -> str:
    arts = exhibition.all_artworks()
    score = pacing_score(arts)
    trans = transition_density(arts)
    if score >= 70:
        quality = "well-balanced"
    elif score >= 45:
        quality = "moderately varied"
    else:
        quality = "needs attention"
    return (
        f"Pacing is {quality} (score {score:.0f}/100) with transition density "
        f"{trans.density:.2f} and max intensity jump {trans.max_delta:.2f}."
    )


def _describe_signals(exhibition: Exhibition) -> str:
    if not exhibition.signals:
        return "No audience or critic signals are attached yet."
    kinds = {s.kind.value for s in exhibition.signals}
    avg = sum(s.score for s in exhibition.signals) / len(exhibition.signals)
    return (
        f"{len(exhibition.signals)} signals across {len(kinds)} channels; "
        f"average score {avg:.1f}."
    )


def _describe_catalog(exhibition: Exhibition) -> str:
    arts = exhibition.all_artworks()
    rooms = len(exhibition.rooms)
    tags = len(exhibition.tags)
    parts = [f"{len(arts)} artworks in {rooms} room(s)"]
    if exhibition.genre:
        parts.append(f"genre {exhibition.genre}")
    if tags:
        parts.append(f"{tags} thematic tags")
    if exhibition.venue:
        parts.append(f"at {exhibition.venue.name}")
    return "; ".join(parts) + "."


def generate_curator_narrative(
    exhibition: Exhibition,
    tone: NarrativeTone = "conversational",
) -> CuratorNarrative:
    """Generate structured curator-facing narrative for an exhibition."""
    craft = build_craft_report(exhibition)
    sections: list[NarrativeSection] = []
    actions: list[str] = []

    catalog_body = _describe_catalog(exhibition)
    sections.append(NarrativeSection("Overview", catalog_body, priority=1))

    pacing_body = _describe_pacing(exhibition)
    sections.append(NarrativeSection("Pacing Analysis", pacing_body, priority=2))
    if craft.pacing_score < 50:
        actions.append("Review artwork ordering for intensity peaks and valleys")

    signal_body = _describe_signals(exhibition)
    sections.append(NarrativeSection("Signal Landscape", signal_body, priority=3))
    if len(exhibition.signals) < 2:
        actions.append("Add diverse signal sources before publication")

    if exhibition.tags:
        top_tags = ", ".join(t.label for t in exhibition.tags[:5])
        theme_body = f"Dominant themes: {top_tags}."
    else:
        theme_body = "Consider adding thematic tags to strengthen discoverability."
        actions.append("Enrich exhibition with thematic tags")
    sections.append(NarrativeSection("Thematic Notes", theme_body, priority=4))

    if tone == "formal":
        summary = (
            f"The exhibition '{exhibition.title}' ({exhibition.id}) presents "
            f"a craft score of {craft.pacing_score:.0f} with {len(exhibition.all_artworks())} works."
        )
    elif tone == "brief":
        summary = f"{exhibition.title}: pacing {craft.pacing_score:.0f}, {len(exhibition.signals)} signals."
    else:
        summary = (
            f"For '{exhibition.title}' — you've got solid material "
            f"({len(exhibition.all_artworks())} pieces, pacing {craft.pacing_score:.0f}). "
            f"{'A few tweaks could help.' if actions else 'Looking good for launch.'}"
        )

    word_count = sum(len(s.body.split()) for s in sections) + len(summary.split())

    return CuratorNarrative(
        exhibition_id=exhibition.id,
        title=exhibition.title,
        tone=tone,
        sections=sorted(sections, key=lambda s: s.priority),
        summary=summary,
        action_items=actions,
        word_count=word_count,
    )


def narrative_to_markdown(narrative: CuratorNarrative) -> str:
    lines = [f"# {narrative.title}", "", narrative.summary, ""]
    for section in narrative.sections:
        lines.extend([f"## {section.heading}", "", section.body, ""])
    if narrative.action_items:
        lines.append("## Action Items")
        for item in narrative.action_items:
            lines.append(f"- {item}")
    return "\n".join(lines)


def batch_narratives(
    exhibitions: list[Exhibition],
    tone: NarrativeTone = "brief",
    min_pacing: float | None = None,
) -> list[CuratorNarrative]:
    """Generate narratives for multiple exhibitions with optional filter."""
    results: list[CuratorNarrative] = []
    for ex in exhibitions:
        if min_pacing is not None:
            if pacing_score(ex.all_artworks()) < min_pacing:
                continue
        results.append(generate_curator_narrative(ex, tone=tone))
    return results


def compare_narratives(a: CuratorNarrative, b: CuratorNarrative) -> dict[str, object]:
    return {
        "word_count_delta": a.word_count - b.word_count,
        "action_delta": len(a.action_items) - len(b.action_items),
        "section_count_a": len(a.sections),
        "section_count_b": len(b.sections),
    }
