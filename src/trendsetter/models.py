from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Sequence

AudioFeatureMap = Dict[str, float]


@dataclass
class TrackRecord:
    """Data pulled from Spotify representing a saved track.

    The model keeps enough information to compute yearly taste trends
    while remaining serializable to JSON.
    """

    track_id: str
    name: str
    artists: List[str]
    artist_ids: List[str]
    added_at: datetime
    release_date: date
    genres: List[str] = field(default_factory=list)
    audio_features: AudioFeatureMap = field(default_factory=dict)

    @property
    def release_year(self) -> int:
        return self.release_date.year

    @property
    def added_year(self) -> int:
        return self.added_at.year


@dataclass
class YearlyTasteSnapshot:
    """Aggregated representation of a user's listening taste for a year."""

    year: int
    total_tracks: int
    top_artists: List[tuple[str, int]]
    top_genres: List[tuple[str, int]]
    average_audio_features: AudioFeatureMap
    release_year_mix: Dict[str, float]

    def format_summary(self) -> str:
        artist_summary = ", ".join(f"{name} ({count})" for name, count in self.top_artists[:5]) or "N/A"
        genre_summary = ", ".join(f"{name} ({count})" for name, count in self.top_genres[:5]) or "N/A"
        avg_features = ", ".join(
            f"{name}: {value:.2f}" for name, value in sorted(self.average_audio_features.items())
        ) or "N/A"
        releases = ", ".join(f"{bucket}: {share:.0%}" for bucket, share in self.release_year_mix.items()) or "N/A"

        return (
            f"Year {self.year}: {self.total_tracks} tracks — "
            f"Top artists: {artist_summary}; Top genres: {genre_summary}; "
            f"Audio features: {avg_features}; Release mix: {releases}"
        )


def merge_audio_feature_sets(feature_sets: Sequence[AudioFeatureMap]) -> AudioFeatureMap:
    """Compute the mean of each audio feature across tracks.

    Empty feature sets result in an empty mapping.
    """

    if not feature_sets:
        return {}

    totals: Dict[str, float] = {}
    counts: Dict[str, int] = {}

    for features in feature_sets:
        for key, value in features.items():
            totals[key] = totals.get(key, 0.0) + value
            counts[key] = counts.get(key, 0) + 1

    return {key: totals[key] / counts[key] for key in totals}
