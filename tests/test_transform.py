from datetime import datetime, date

import pytest

from trendsetter.models import TrackRecord
from trendsetter.transform import build_yearly_snapshots, render_markdown_report


def _record(
    track_id: str,
    added: str,
    release: str,
    artists: list[str],
    genres: list[str],
    audio_features: dict[str, float],
):
    return TrackRecord(
        track_id=track_id,
        name=f"Track {track_id}",
        artists=artists,
        artist_ids=[f"artist-{name}" for name in artists],
        added_at=datetime.fromisoformat(added),
        release_date=date.fromisoformat(release),
        genres=genres,
        audio_features=audio_features,
    )


def test_yearly_snapshots_group_tracks_by_added_year():
    records = [
        _record("1", "2020-01-02T00:00:00", "2020-01-01", ["A"], ["pop"], {"danceability": 0.8}),
        _record("2", "2020-02-03T00:00:00", "2019-12-01", ["B"], ["rock"], {"danceability": 0.6}),
        _record("3", "2021-03-04T00:00:00", "2018-01-01", ["A"], ["indie"], {"danceability": 0.4}),
    ]

    snapshots = build_yearly_snapshots(records)

    assert [snap.year for snap in snapshots] == [2020, 2021]
    assert snapshots[0].total_tracks == 2
    assert snapshots[0].top_artists[0][0] == "A"
    assert snapshots[0].average_audio_features["danceability"] == 0.7

    # Release mix should classify 2019 release as recent, 2018 as older
    release_mix_2021 = snapshots[1].release_year_mix
    assert release_mix_2021["Older catalog"] == 1.0


def test_render_markdown_report_has_sections():
    records = [
        _record("1", "2019-01-01T00:00:00", "2019-01-01", ["A"], ["pop"], {"energy": 0.9}),
    ]
    snapshots = build_yearly_snapshots(records)
    markdown = render_markdown_report(snapshots)
    assert "Your Spotify Taste Over Time" in markdown
    assert "2019" in markdown
    assert "Top artists" in markdown


def test_merge_audio_feature_sets_handles_empty_and_means():
    from trendsetter.models import merge_audio_feature_sets

    assert merge_audio_feature_sets([]) == {}

    averages = merge_audio_feature_sets(
        [
            {"energy": 0.8, "danceability": 0.6},
            {"energy": 0.4, "danceability": 0.9},
        ]
    )

    assert averages.keys() == {"energy", "danceability"}
    assert averages["danceability"] == 0.75
    assert averages["energy"] == pytest.approx(0.6)
