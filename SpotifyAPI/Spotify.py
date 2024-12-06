import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

class SpotifyController:
    def __init__(self):
        # Set up file paths
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.token_path = os.path.join(self.current_dir, 'spotify_token.pickle')
        
        # Initialize Spotify client with token caching
        self.auth_manager = SpotifyOAuth(
            client_id='04e5442986914b698849921ae45c8a8f',
            client_secret='60cde23c8114408292fad654471babf5',
            redirect_uri='http://localhost:8888/callback',
            scope='user-read-playback-state user-modify-playback-state',
            cache_path=self.token_path
        )
        
        self.sp = spotipy.Spotify(auth_manager=self.auth_manager)

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

    def play(self):
        """Start playback and return track info"""
        try:
            self.sp.start_playback()
            return self.get_formatted_track_info()
        except Exception as e:
            print(f"Error starting playback: {e}")
            return None

    def pause(self):
        """Pause playback and return track info"""
        try:
            self.sp.pause_playback()
            return self.get_formatted_track_info()
        except Exception as e:
            print(f"Error pausing playback: {e}")
            return None
        
    def skip_next(self):
        """Skip to next track and return track info"""
        try:
            self.sp.next_track()
            # Add a small delay to allow Spotify to update
            import time
            time.sleep(0.5)
            return self.get_formatted_track_info()
        except Exception as e:
            print(f"Error skipping to next track: {e}")
            return None

    def skip_previous(self):
        """Skip to previous track and return track info"""
        try:
            self.sp.previous_track()
            # Add a small delay to allow Spotify to update
            import time
            time.sleep(0.5)
            return self.get_formatted_track_info()
        except Exception as e:
            print(f"Error skipping to previous track: {e}")
            return None

    def toggle_playback(self):
        """Toggle between play and pause, return track info"""
        try:
            current_playback = self.sp.current_playback()
            if current_playback is None:
                print("No active device found")
                return None
            
            if current_playback['is_playing']:
                return self.pause()
            else:
                return self.play()
        except Exception as e:
            print(f"Error toggling playback: {e}")
            return None

    def get_formatted_track_info(self):
        """Get formatted information about the current track"""
        track_info = self.get_current_track()
        if track_info:
            return {
                'track': track_info['name'],
                'artist': track_info['artist'],
                'album': track_info['album'],
                'status': 'Playing' if track_info['is_playing'] else 'Paused',
                'progress': f"{track_info['progress']/1000:.0f}s / {track_info['duration']/1000:.0f}s"
            }
        return None

if __name__ == "__main__":
    controller = SpotifyController()
    print(controller.get_formatted_track_info())