from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, List, Sequence

from .models import TrackRecord, YearlyTasteSnapshot, merge_audio_feature_sets


def _bucket_release_years(records: Sequence[TrackRecord], year: int) -> Dict[str, float]:
    if not records:
        return {}

    buckets = Counter()
    for record in records:
        if record.release_year == year:
            buckets["New this year"] += 1
        elif record.release_year >= year - 2:
            buckets["Released in last 2 years"] += 1
        else:
            buckets["Older catalog"] += 1

    total = sum(buckets.values())
    return {bucket: count / total for bucket, count in buckets.items()}


def build_yearly_snapshots(records: Sequence[TrackRecord]) -> List[YearlyTasteSnapshot]:
    """Aggregate saved tracks into yearly taste snapshots."""

    grouped: Dict[int, List[TrackRecord]] = defaultdict(list)
    for record in records:
        grouped[record.added_year].append(record)

    snapshots: List[YearlyTasteSnapshot] = []
    for year in sorted(grouped):
        items = grouped[year]
        artist_counter = Counter(artist for record in items for artist in record.artists)
        genre_counter = Counter(genre for record in items for genre in record.genres)
        average_features = merge_audio_feature_sets([record.audio_features for record in items])
        release_mix = _bucket_release_years(items, year)

        snapshots.append(
            YearlyTasteSnapshot(
                year=year,
                total_tracks=len(items),
                top_artists=artist_counter.most_common(10),
                top_genres=genre_counter.most_common(10),
                average_audio_features=average_features,
                release_year_mix=release_mix,
            )
        )

    return snapshots


def render_markdown_report(snapshots: Sequence[YearlyTasteSnapshot]) -> str:
    lines: List[str] = ["# Your Spotify Taste Over Time", ""]
    for snapshot in snapshots:
        lines.append(f"## {snapshot.year}")
        lines.append(f"Total saved tracks: **{snapshot.total_tracks}**")
        lines.append("")
        if snapshot.top_artists:
            lines.append("Top artists:")
            for name, count in snapshot.top_artists[:5]:
                lines.append(f"- {name}: {count} tracks")
        else:
            lines.append("Top artists: N/A")

        lines.append("")
        if snapshot.top_genres:
            lines.append("Top genres:")
            for name, count in snapshot.top_genres[:5]:
                lines.append(f"- {name}: {count} tracks")
        else:
            lines.append("Top genres: N/A")

        if snapshot.average_audio_features:
            lines.append("")
            lines.append("Average audio features:")
            for name, value in sorted(snapshot.average_audio_features.items()):
                lines.append(f"- {name}: {value:.2f}")

        if snapshot.release_year_mix:
            lines.append("")
            lines.append("Release year mix:")
            for bucket, share in snapshot.release_year_mix.items():
                lines.append(f"- {bucket}: {share:.0%}")

        lines.append("")
    return "\n".join(lines).strip() + "\n"
