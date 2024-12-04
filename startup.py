import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

os.environ["SPOTIPY_CLIENT_ID"] = '04e5442986914b698849921ae45c8a8f'
os.environ["SPOTIPY_CLIENT_SECRET"] = '60cde23c8114408292fad654471babf5'
os.environ["SPOTIPY_REDIRECT_URI"] = 'http://localhost:8888/callback'

# Create a token with a longer cache path
auth_manager = SpotifyOAuth(
    scope='user-read-playback-state user-modify-playback-state',
    cache_path='.spotifycache'  # This will save the token in a file named .spotifycache
)

# Force token retrieval
token_info = auth_manager.get_cached_token()
if not token_info:
    auth_manager.get_access_token()

print("Token saved to .spotifycache")