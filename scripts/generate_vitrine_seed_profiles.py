#!/usr/bin/env python3
"""Generate ~48 rich exhibition seed profiles for the Vitrine catalog."""

from __future__ import annotations

import hashlib
import random
import textwrap
from datetime import date, datetime, timedelta
from pathlib import Path

OUTPUT = (
    Path(__file__).resolve().parents[1]
    / "packages"
    / "catalog"
    / "src"
    / "vitrine_catalog"
    / "seed_profiles.py"
)

CURATORS = [
    "Amara Chen", "Benjamin Okonkwo", "Clara Mendez", "David Kim", "Elena Rossi",
    "Felix Bauer", "Grace Nakamura", "Hassan Al-Rashid", "Isabelle Duval", "James Okafor",
    "Keiko Tanaka", "Lucia Ferreira", "Marcus Webb", "Nadia Petrov", "Oliver Hughes",
    "Priya Sharma", "Quentin Blake", "Rosa Alvarez", "Samuel Cho", "Theresa Walsh",
]

IMPRINTS = [
    "Vitrine Press", "Gallery North", "MoCA Contemporary", "White Cube Editions",
    "Serpentine Labs", "Tate Modern Series", "Guggenheim Curatorial", "Palais de Tokyo",
    "Haus der Kunst", "Centre Pompidou", "SFMOMA Projects", "Art Basel Curated",
]

GENRES = [
    "contemporary", "modern", "installation", "photography", "sculpture",
    "mixed-media", "digital", "performance", "abstract", "figurative",
    "minimalist", "conceptual",
]

RESIDENCIES = [
    "MoCA Los Angeles", "Tate Modern", "Centre Pompidou", "Guggenheim Bilbao",
    "Serpentine Galleries", "Whitney Museum", "National Gallery", "Art Institute Chicago",
    "Walker Art Center", "Hirshhorn Museum", "Museum of Modern Art", "LACMA",
]

SERIES = [
    "Spring Survey", "Autumn Focus", "Winter Salon", "Summer Pavilion",
    "Emerging Voices", "Masterworks", "New Media", "Global Perspectives",
    "Site Specific", "Archive Dialogues", "Curator's Choice", "Open Call",
]

VENUES = [
    ("Museum of Contemporary Art", "Los Angeles", "USA", "museum", 800),
    ("Tate Modern", "London", "UK", "museum", 1200),
    ("Centre Pompidou", "Paris", "France", "museum", 950),
    ("Guggenheim Museum", "New York", "USA", "museum", 700),
    ("Serpentine Galleries", "London", "UK", "gallery", 400),
    ("Whitney Museum", "New York", "USA", "museum", 600),
    ("Walker Art Center", "Minneapolis", "USA", "museum", 500),
    ("Haus der Kunst", "Munich", "Germany", "museum", 550),
    ("Palais de Tokyo", "Paris", "France", "gallery", 450),
    ("National Gallery of Victoria", "Melbourne", "Australia", "museum", 650),
    ("Art Gallery of Ontario", "Toronto", "Canada", "museum", 480),
    ("Mori Art Museum", "Tokyo", "Japan", "museum", 520),
]

ARTISTS = [
    "Yayoi Kusama", "Olafur Eliasson", "Kara Walker", "Ai Weiwei", "Anish Kapoor",
    "Marina Abramović", "Gerhard Richter", "Takashi Murakami", "Julie Mehretu",
    "Kehinde Wiley", "Cindy Sherman", "Damien Hirst", "Jenny Holzer", "Chris Ofili",
    "Shirin Neshat", "El Anatsui", "Tracey Emin", "Do Ho Suh", "Wolfgang Tillmans",
    "Rashid Johnson", "Simone Leigh", "Theaster Gates", "Njideka Akunyili Crosby",
    "Hilma af Klint", "Mark Bradford", "Kerry James Marshall", "Tschabalala Self",
    "Firelei Báez", "Wangechi Mutu", "Oscar Murillo", "Hito Steyerl", "Arthur Jafa",
    "Sondra Perry", "Deana Lawson", "Jordan Casteel", "Amy Sherald", "Toyin Ojih Odutola",
    "Kara Walker", "Mickalene Thomas", "Lorna Simpson", "Carrie Mae Weems",
    "Zanele Muholi", "Yinka Shonibare", "Ibrahim Mahama", "William Kentridge",
    "William Eggleston", "Nan Goldin", "Robert Mapplethorpe", "Richard Avedon",
]

MEDIUMS = [
    "oil on canvas", "acrylic on linen", "bronze sculpture", "mixed media installation",
    "digital projection", "chromogenic print", "video installation", "steel and glass",
    "ceramic and textile", "neon and aluminum", "ink on paper", "found objects",
    "resin and pigment", "wood and metal", "photography", "performance documentation",
]

SIGNAL_SOURCES = [
    ("Artforum", "https://www.artforum.com", 0.92),
    ("Frieze", "https://www.frieze.com", 0.88),
    ("The Guardian Arts", "https://www.theguardian.com/art", 0.85),
    ("Hyperallergic", "https://hyperallergic.com", 0.82),
    ("ArtNews", "https://www.artnews.com", 0.90),
    ("Artnet News", "https://news.artnet.com", 0.78),
    ("ArtReview", "https://artreview.com", 0.86),
    ("Flash Art", "https://flashart.com", 0.80),
    ("Mousse Magazine", "https://moussemagazine.it", 0.75),
    ("Contemporary Art Daily", "https://contemporaryartdaily.com", 0.70),
    ("Visitor Survey", None, 0.65),
    ("Curatorial Notes", None, 0.95),
]

TAG_POOL = [
    ("contemporary", "movement"), ("abstract", "style"), ("political", "theme"),
    ("identity", "theme"), ("landscape", "subject"), ("portrait", "subject"),
    ("minimal", "style"), ("immersive", "format"), ("site-specific", "format"),
    ("emerging", "audience"), ("established", "audience"), ("avant-garde", "movement"),
    ("feminist", "theme"), ("postcolonial", "theme"), ("environmental", "theme"),
    ("technology", "medium"), ("craft", "medium"), ("narrative", "theme"),
]

TITLES_PREFIX = [
    "Luminous", "Silent", "Fractured", "Ethereal", "Resonant", "Temporal",
    "Chromatic", "Visceral", "Ephemeral", "Architectonic", "Mnemonic", "Spectral",
    "Prismatic", "Tectonic", "Liminal", "Nocturnal", "Radiant", "Subterranean",
]

TITLES_SUFFIX = [
    "Fields", "Horizons", "Fragments", "Echoes", "Thresholds", "Cartographies",
    "Territories", "Constellations", "Passages", "Intersections", "Volumes",
    "Strata", "Currents", "Vectors", "Matters", "Forms", "Gestures", "Rhythms",
]

ARTWORK_TITLES = [
    "Untitled (Composition)", "Study in Light", "After the Flood", "Memory Palace",
    "Interior Dialogue", "Surface Tension", "Negative Space", "Accumulation",
    "Trace Elements", "Broken Mirror", "Soft Architecture", "Liquid Geometry",
    "Shadow Index", "Color Field No.", "Material Witness", "Silent Witness",
    "Open Wound", "Closed Circuit", "Parallel Lives", "Drift", "Pulse",
    "Threshold", "Archive", "Remnant", "Fragment", "Echo", "Residue",
]


def stable_rng(seed: str) -> random.Random:
    h = int(hashlib.sha256(seed.encode()).hexdigest()[:16], 16)
    return random.Random(h)


def py_str(s: str) -> str:
    return repr(s)


def py_float(v: float) -> str:
    return f"{v:.4f}".rstrip("0").rstrip(".") if "." in f"{v:.4f}" else str(int(v))


def generate_exhibition(index: int) -> str:
    rng = stable_rng(f"vitrine-exhibition-{index}")
    ex_id = f"ex-{index:03d}"
    title = f"{rng.choice(TITLES_PREFIX)} {rng.choice(TITLES_SUFFIX)}"
    if rng.random() > 0.6:
        title = f"{title}: {rng.choice(['A Retrospective', 'New Works', 'Selected Pieces', 'In Conversation'])}"
    curator = CURATORS[index % len(CURATORS)]
    imprint = rng.choice(IMPRINTS)
    genre = GENRES[index % len(GENRES)]
    series = SERIES[index % len(SERIES)]
    residency = RESIDENCIES[index % len(RESIDENCIES)]
    base_date = date(2023, 1, 1) + timedelta(days=index * 14)
    opened = base_date
    closed = opened + timedelta(days=rng.randint(30, 120))
    venue = VENUES[index % len(VENUES)]
    crowd_score = round(rng.uniform(35, 98), 2)
    vitrine_score = round(rng.uniform(40, 96), 2)

    num_rooms = rng.randint(2, 5)
    num_tags = rng.randint(3, 8)
    num_signals = rng.randint(4, 12)

    lines: list[str] = []
    lines.append(f"    Exhibition(")
    lines.append(f"        id={py_str(ex_id)},")
    lines.append(f"        title={py_str(title)},")
    lines.append(f"        curator={py_str(curator)},")
    lines.append(f"        imprint={py_str(imprint)},")
    lines.append(f"        genre={py_str(genre)},")
    lines.append(f"        series={py_str(series)},")
    lines.append(f"        residency={py_str(residency)},")
    lines.append(f"        opened_on=date({opened.year}, {opened.month}, {opened.day}),")
    lines.append(f"        closed_on=date({closed.year}, {closed.month}, {closed.day}),")
    lines.append(f"        crowd_score={crowd_score},")
    lines.append(f"        vitrine_score={vitrine_score},")
    lines.append(f"        venue=VenueMetadata(")
    lines.append(f"            name={py_str(venue[0])},")
    lines.append(f"            city={py_str(venue[1])},")
    lines.append(f"            country={py_str(venue[2])},")
    lines.append(f"            format={py_str(venue[3])},")
    lines.append(f"            capacity={venue[4]},")
    lines.append(f"        ),")
    lines.append(f"        tags=[")

    chosen_tags = rng.sample(TAG_POOL, min(num_tags, len(TAG_POOL)))
    for ti, (label, category) in enumerate(chosen_tags):
        tag_id = f"tag-{ex_id}-{ti}"
        weight = round(rng.uniform(0.5, 1.0), 2)
        comma = "," if ti < len(chosen_tags) - 1 else ""
        lines.append(
            f"            Tag(id={py_str(tag_id)}, label={py_str(label)}, "
            f"category={py_str(category)}, weight={weight}){comma}"
        )
    lines.append(f"        ],")

    lines.append(f"        rooms=[")
    artwork_ids: list[str] = []
    pos = 0
    for ri in range(num_rooms):
        room_id = f"room-{ex_id}-{ri}"
        room_name = rng.choice(["North Gallery", "South Wing", "Main Hall", "Project Space", "Vitrine", "East Room", "West Pavilion"])
        floor = rng.randint(0, 3)
        capacity = rng.randint(20, 150)
        num_artworks = rng.randint(3, 8)
        lines.append(f"            Room(")
        lines.append(f"                id={py_str(room_id)},")
        lines.append(f"                name={py_str(room_name)},")
        lines.append(f"                floor={floor},")
        lines.append(f"                capacity={capacity},")
        lines.append(f"                artworks=[")
        for ai in range(num_artworks):
            art_id = f"art-{ex_id}-{ri}-{ai}"
            artwork_ids.append(art_id)
            artist = rng.choice(ARTISTS)
            art_title = f"{rng.choice(ARTWORK_TITLES)} {ai + 1}" if ai > 0 else rng.choice(ARTWORK_TITLES)
            medium = rng.choice(MEDIUMS)
            year = rng.randint(1990, 2025)
            dwell = round(rng.uniform(15, 420), 1)
            intensity = round(rng.uniform(0.1, 0.95), 3)
            tension = round(rng.uniform(0.05, 0.9), 3)
            wall_text = round(rng.uniform(0.0, 0.85), 3)
            art_tags = rng.sample([t[0] for t in TAG_POOL], rng.randint(1, 4))
            tag_list = ", ".join(py_str(t) for t in art_tags)
            comma = "," if ai < num_artworks - 1 else ""
            lines.append(f"                    Artwork(")
            lines.append(f"                        id={py_str(art_id)},")
            lines.append(f"                        title={py_str(art_title)},")
            lines.append(f"                        artist={py_str(artist)},")
            lines.append(f"                        medium={py_str(medium)},")
            lines.append(f"                        year={year},")
            lines.append(f"                        dwell_sec={dwell},")
            lines.append(f"                        intensity={intensity},")
            lines.append(f"                        narrative_tension={tension},")
            lines.append(f"                        wall_text_ratio={wall_text},")
            lines.append(f"                        position={pos},")
            lines.append(f"                        tags=[{tag_list}],")
            lines.append(f"                    ){comma}")
            pos += 1
        lines.append(f"                ],")
        lines.append(f"            )," if ri < num_rooms - 1 else f"            ),")
    lines.append(f"        ],")

    lines.append(f"        signals=[")
    for si in range(num_signals):
        sig_id = f"sig-{ex_id}-{si}"
        kind = rng.choice(["review", "visitor", "critic", "social", "sales", "curator"])
        score = round(rng.uniform(30, 100), 1)
        src_name, src_url, base_conf = rng.choice(SIGNAL_SOURCES)
        conf = round(min(1.0, base_conf + rng.uniform(-0.1, 0.1)), 2)
        rank = rng.randint(1, 10) if rng.random() > 0.3 else None
        cap_day = opened + timedelta(days=rng.randint(0, 60))
        cap_dt = datetime(cap_day.year, cap_day.month, cap_day.day, 12, 0, 0)
        text_snippets = [
            f"Compelling curation in {title}.",
            f"Standout installation with strong narrative arc.",
            f"Visitor engagement metrics exceed baseline.",
            f"Critical reception highlights {genre} innovation.",
            f"Provenance chain verified for key works.",
            f"Wall text density supports interpretive depth.",
        ]
        text = rng.choice(text_snippets)
        url_part = f"source_url={py_str(src_url)}," if src_url else "source_url=None,"
        rank_part = f"rank={rank}," if rank else ""
        comma = "," if si < num_signals - 1 else ""
        lines.append(f"            Signal(")
        lines.append(f"                id={py_str(sig_id)},")
        lines.append(f"                exhibition_id={py_str(ex_id)},")
        lines.append(f"                kind=SignalKind.{kind.upper()},")
        lines.append(f"                score={score},")
        lines.append(f"                text={py_str(text)},")
        lines.append(f"                weight={round(rng.uniform(0.5, 1.5), 2)},")
        lines.append(f"                provenance=Provenance(")
        lines.append(f"                    source_name={py_str(src_name)},")
        lines.append(f"                    {url_part}")
        lines.append(f"                    confidence={conf},")
        lines.append(f"                    captured_at=datetime({cap_dt.year}, {cap_dt.month}, {cap_dt.day}, {cap_dt.hour}, {cap_dt.minute}),")
        lines.append(f"                    {rank_part}".rstrip(","))
        if rank_part:
            lines.append(f"                ),")
        else:
            lines.append(f"                ),")
        lines.append(f"            ){comma}")
    lines.append(f"        ],")

    lines.append(f"        graph_nodes=[")
    for ni, aid in enumerate(artwork_ids):
        label = f"Node {ni}"
        comma = "," if ni < len(artwork_ids) - 1 else ""
        lines.append(
            f"            GraphNode(id={py_str(aid)}, label={py_str(label)}, "
            f"node_type='artwork', metadata={{'room_index': {ni % num_rooms}, 'position': {ni}}}){comma}"
        )
    lines.append(f"        ],")

    lines.append(f"        graph_edges=[")
    edge_count = 0
    max_edges = min(len(artwork_ids) * 2, len(artwork_ids) + 8)
    for i in range(len(artwork_ids) - 1):
        if edge_count >= max_edges:
            break
        src = artwork_ids[i]
        tgt = artwork_ids[i + 1]
        weight = round(rng.uniform(0.5, 3.0), 2)
        relation = rng.choice(["adjacent", "thematic", "sequential", "contrast"])
        lines.append(
            f"            GraphEdge(source_id={py_str(src)}, target_id={py_str(tgt)}, "
            f"weight={weight}, relation={py_str(relation)}),"
        )
        edge_count += 1
    for _ in range(rng.randint(0, 5)):
        if edge_count >= max_edges or len(artwork_ids) < 3:
            break
        src, tgt = rng.sample(artwork_ids, 2)
        if abs(artwork_ids.index(src) - artwork_ids.index(tgt)) <= 1:
            continue
        weight = round(rng.uniform(0.3, 2.0), 2)
        lines.append(
            f"            GraphEdge(source_id={py_str(src)}, target_id={py_str(tgt)}, "
            f"weight={weight}, relation='thematic'),"
        )
        edge_count += 1
    if lines[-1].endswith(","):
        lines[-1] = lines[-1][:-1]
    lines.append(f"        ],")
    lines.append(f"    ),")
    return "\n".join(lines)


def main() -> None:
    header = textwrap.dedent(
        '''\
        """Auto-generated Vitrine exhibition seed profiles.

        Generated by scripts/generate_vitrine_seed_profiles.py — do not edit by hand.
        """

        from __future__ import annotations

        from datetime import date, datetime

        from vitrine_types.models import (
            Artwork,
            Exhibition,
            GraphEdge,
            GraphNode,
            Provenance,
            Room,
            Signal,
            SignalKind,
            Tag,
            VenueMetadata,
        )

        SEED_EXHIBITIONS: list[Exhibition] = [
        '''
    )

    exhibitions = [generate_exhibition(i) for i in range(48)]
    footer = "]\n"

    content = header + "\n".join(exhibitions) + footer
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(content, encoding="utf-8")
    line_count = content.count("\n") + 1
    print(f"Wrote {OUTPUT}")
    print(f"Exhibitions: 48, lines: {line_count}")


if __name__ == "__main__":
    main()
