from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import List

import typer

from .models import TrackRecord
from .spotify_client import SpotifyClient
from .transform import build_yearly_snapshots, render_markdown_report

app = typer.Typer(help="Explore how your Spotify music taste evolved over time.")


def _load_records(path: Path) -> List[TrackRecord]:
    data = json.loads(path.read_text())
    for item in data:
        if isinstance(item.get("added_at"), str):
            item["added_at"] = datetime.fromisoformat(item["added_at"])
        if isinstance(item.get("release_date"), str):
            item["release_date"] = date.fromisoformat(item["release_date"])
    return [TrackRecord(**item) for item in data]


@app.command()
def fetch(
    output: Path = typer.Option(Path("data/saved_tracks.json"), help="Where to store the downloaded library."),
    limit: int | None = typer.Option(None, help="Limit downloads for testing."),
):
    """Download saved tracks (with genres and audio features) into JSON."""

    output.parent.mkdir(parents=True, exist_ok=True)
    client = SpotifyClient.from_env()
    records = client.fetch_saved_tracks(max_items=limit)
    output.write_text(json.dumps(SpotifyClient.serialize(records), indent=2, default=str))
    typer.echo(f"Saved {len(records)} tracks to {output}")


@app.command()
def report(
    source: Path = typer.Option(Path("data/saved_tracks.json"), help="Path to saved track JSON produced by `fetch`"),
    output: Path | None = typer.Option(Path("data/yearly_taste.md"), help="Where to write the markdown report."),
):
    """Build yearly taste snapshots and optionally persist a markdown report."""

    if not source.exists():
        raise typer.BadParameter(f"Input file not found: {source}")

    records = _load_records(source)
    snapshots = build_yearly_snapshots(records)
    markdown = render_markdown_report(snapshots)

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown)
        typer.echo(f"Wrote {len(snapshots)} yearly snapshots to {output}")
    else:
        typer.echo(markdown)


if __name__ == "__main__":
    app()
