# TrendSetter

Data engineering-friendly toolkit for exploring how your Spotify music taste evolved from the day you started saving tracks through today. TrendSetter downloads your saved library, enriches it with genres and audio features, and produces year-over-year summaries you can visualize or share.

## Features
- **Historical coverage**: Uses the "Saved Tracks" library timestamps to map what you were listening to each year.
- **Taste signals**: Captures genres, top artists, and audio feature averages (danceability, energy, tempo, and more).
- **Year-over-year comparisons**: Generates per-year snapshots plus a markdown report that highlights how your taste shifts over time.

## Getting started
1. Create a Spotify application at <https://developer.spotify.com/dashboard/> and note the **Client ID** and **Client secret**.
   - In the Spotify Dashboard, add `http://localhost:8888/callback` (or `http://127.0.0.1:8888/callback`) as a redirect URI. The URI must match what TrendSetter uses during OAuth.
2. Set up environment variables (or a `.env` file) with your credentials and redirect URI:
   ```bash
   SPOTIFY_CLIENT_ID=your-client-id
   SPOTIFY_CLIENT_SECRET=your-client-secret
   SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
   ```
3. Install dependencies and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## Usage
The CLI is built with [Typer](https://typer.tiangolo.com/). Run commands with `python -m trendsetter.cli <command>`.

- **Download your library**
  ```bash
  python -m trendsetter.cli fetch --output data/saved_tracks.json
  ```
  The first run opens a browser window for Spotify login/authorization. Data is cached in `.cache-trendsetter` to avoid repeated prompts, so the redirect URI only needs to be configured once.

- **Generate a yearly report**
  ```bash
  python -m trendsetter.cli report --source data/saved_tracks.json --output data/yearly_taste.md
  ```
  The report lists yearly totals, top artists/genres, audio feature averages, and how much you listened to brand-new releases vs. back-catalog tracks.

Both commands write to `data/` by default so results are easy to version-control separately from credentials.

## How it works
1. **Ingestion**: The `fetch` command paginates through your Saved Tracks, collecting add timestamps, artists, and album release dates.
2. **Enrichment**: For each track we pull artist genres and audio features like danceability and tempo.
3. **Aggregation**: `build_yearly_snapshots` groups tracks by the year you saved them and computes top artists/genres, average audio features, and release recency buckets.
4. **Reporting**: `render_markdown_report` formats the yearly snapshots into a markdown report ready for dashboards, blog posts, or notebooks.

## Testing
Unit tests focus on the aggregation layer and do not require Spotify credentials:
```bash
pytest
```
