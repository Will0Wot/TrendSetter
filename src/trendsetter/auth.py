from __future__ import annotations

import os
from typing import Iterable, Optional

from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth


SCOPE = "user-library-read"


def load_env_files(paths: Optional[Iterable[str]] = None) -> None:
    """Load environment variables from .env-style files.

    By default this loads ``.env`` in the project root if present. Passing an
    iterable allows callers to specify additional files (for example, test
    fixtures).
    """

    if paths is None:
        load_dotenv()
    else:
        for path in paths:
            load_dotenv(path)


def build_auth_manager(cache_path: str | None = None) -> SpotifyOAuth:
    """Create a Spotipy OAuth manager using environment variables.

    Requires ``SPOTIFY_CLIENT_ID``, ``SPOTIFY_CLIENT_SECRET``, and
    ``SPOTIFY_REDIRECT_URI``. A token cache path can optionally be passed to
    avoid repeated logins.
    """

    load_env_files()
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")

    missing = [name for name, value in {
        "SPOTIFY_CLIENT_ID": client_id,
        "SPOTIFY_CLIENT_SECRET": client_secret,
        "SPOTIFY_REDIRECT_URI": redirect_uri,
    }.items() if not value]

    if missing:
        raise EnvironmentError(
            "Missing required environment variables: " + ", ".join(missing)
        )

    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=SCOPE,
        cache_path=cache_path,
        show_dialog=True,
        open_browser=True,
    )
