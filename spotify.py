import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import os

class SpotifyController:
    def __init__(self):
        # Set up credentials
        os.environ["SPOTIPY_CLIENT_ID"] = '04e5442986914b698849921ae45c8a8f'
        os.environ["SPOTIPY_CLIENT_SECRET"] = '60cde23c8114408292fad654471babf5'
        os.environ["SPOTIPY_REDIRECT_URI"] = 'http://localhost:8888/callback'

        # Use the cached token from the file
        auth_manager = SpotifyOAuth(
            scope='user-read-playback-state user-modify-playback-state',
            open_browser=False,
            cache_path='.spotifycache'  # Use the cache file we created
        )
        
        self.sp = spotipy.Spotify(auth_manager=auth_manager)

    def get_current_track(self):
        """Get information about the currently playing track"""
        try:
            current_track = self.sp.current_playback()
            if current_track is not None and current_track['item'] is not None:
                track_info = {
                    'name': current_track['item']['name'],
                    'artist': current_track['item']['artists'][0]['name'],
                    'album': current_track['item']['album']['name'],
                    'is_playing': current_track['is_playing'],
                    'duration': current_track['item']['duration_ms'],
                    'progress': current_track['progress_ms']
                }
                return track_info
            return None
        except Exception as e:
            print(f"Error getting track info: {e}")
            return None

    def toggle_playback(self):
        """Toggle between play and pause"""
        try:
            current_playback = self.sp.current_playback()
            if current_playback is None:
                print("No active device found")
                return
            
            if current_playback['is_playing']:
                self.sp.pause_playback()
                print("Paused playback")
            else:
                self.sp.start_playback()
                print("Resumed playback")
        except Exception as e:
            print(f"Error toggling playback: {e}")

    def display_track_info(self):
        """Display formatted information about the current track"""
        track_info = self.get_current_track()
        if track_info:
            print("\n=== Currently Playing ===")
            print(f"Track: {track_info['name']}")
            print(f"Artist: {track_info['artist']}")
            print(f"Album: {track_info['album']}")
            print(f"Status: {'Playing' if track_info['is_playing'] else 'Paused'}")
            print(f"Progress: {track_info['progress']/1000:.0f}s / {track_info['duration']/1000:.0f}s")
            print("=====================")
        else:
            print("No track currently playing")

def main():
    controller = SpotifyController()
    
    while True:
        print("\nSpotify Controller")
        print("1. Display current track")
        print("2. Toggle play/pause")
        print("3. Exit")
        
        choice = input("Enter your choice (1-3): ")
        
        if choice == '1':
            controller.display_track_info()
        elif choice == '2':
            controller.toggle_playback()
        elif choice == '3':
            print("Exiting...")
            break
        else:
            print("Invalid choice, please try again")
        
        time.sleep(1)

if __name__ == "__main__":
    main()