from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, date
from typing import Iterable, List, Sequence

import spotipy
from spotipy import Spotify

from .auth import build_auth_manager
from .models import TrackRecord

ISO_FORMATS = ["%Y-%m-%d", "%Y-%m", "%Y"]


def _parse_release_date(raw: str) -> date:
    for fmt in ISO_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognized release date format: {raw}")


def _chunked(seq: Sequence[str], size: int) -> Iterable[List[str]]:
    for start in range(0, len(seq), size):
        yield list(seq[start : start + size])


class SpotifyClient:
    """Thin wrapper around the Spotify Web API focused on saved tracks."""

    def __init__(self, spotify: Spotify):
        self.spotify = spotify

    @classmethod
    def from_env(cls, cache_path: str | None = ".cache-trendsetter") -> "SpotifyClient":
        auth_manager = build_auth_manager(cache_path=cache_path)
        return cls(spotipy.Spotify(auth_manager=auth_manager))

    def fetch_saved_tracks(self, max_items: int | None = None) -> List[TrackRecord]:
        """Load the user's saved tracks with genres and audio features.

        ``max_items`` can be supplied to limit downloads during local testing.
        """

        results: List[TrackRecord] = []
        offset = 0
        batch_size = 50

        while True:
            response = self.spotify.current_user_saved_tracks(limit=batch_size, offset=offset)
            items = response.get("items", [])
            if not items:
                break

            for item in items:
                track = item["track"]
                added_at = datetime.fromisoformat(item["added_at"].replace("Z", "+00:00"))
                release_date = _parse_release_date(track["album"]["release_date"])
                artist_ids = [artist["id"] for artist in track.get("artists", []) if artist.get("id")]

                results.append(
                    TrackRecord(
                        track_id=track["id"],
                        name=track.get("name", ""),
                        artists=[artist["name"] for artist in track.get("artists", [])],
                        artist_ids=artist_ids,
                        added_at=added_at,
                        release_date=release_date,
                    )
                )

            offset += len(items)
            if max_items and offset >= max_items:
                results = results[:max_items]
                break

            if len(items) < batch_size:
                break

        self._enrich_with_genres(results)
        self._enrich_with_audio_features(results)
        return results

    def _enrich_with_genres(self, records: List[TrackRecord]) -> None:
        unique_artist_ids = {artist_id for record in records for artist_id in record.artist_ids}
        genres_by_artist: dict[str, List[str]] = {}

        for chunk in _chunked(sorted(unique_artist_ids), 50):
            response = self.spotify.artists(chunk)
            for artist in response.get("artists", []):
                genres_by_artist[artist["id"]] = artist.get("genres", [])

        for record in records:
            genre_set = set()
            for artist_id in record.artist_ids:
                genre_set.update(genres_by_artist.get(artist_id, []))
            record.genres = sorted(genre_set)

    def _enrich_with_audio_features(self, records: List[TrackRecord]) -> None:
        track_ids = [record.track_id for record in records if record.track_id]
        features_by_id: dict[str, dict] = {}

        for chunk in _chunked(track_ids, 100):
            response = self.spotify.audio_features(chunk)
            for feature in response or []:
                if feature and feature.get("id"):
                    features_by_id[feature["id"]] = feature

        keep_keys = {
            "danceability",
            "energy",
            "acousticness",
            "instrumentalness",
            "liveness",
            "speechiness",
            "valence",
            "tempo",
        }

        for record in records:
            feature_source = features_by_id.get(record.track_id, {})
            record.audio_features = {k: float(v) for k, v in feature_source.items() if k in keep_keys}

    @staticmethod
    def serialize(records: List[TrackRecord]) -> List[dict]:
        serialized: List[dict] = []
        for record in records:
            payload = asdict(record)
            payload["added_at"] = record.added_at.isoformat()
            payload["release_date"] = record.release_date.isoformat()
            serialized.append(payload)
        return serialized
