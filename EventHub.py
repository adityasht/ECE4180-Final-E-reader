import os
import logging
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import requests
import sys
import subprocess
import re
from resources import epd5in83_V2
from GoogleCalendarAPI.Calendar import CalendarAPI
from SpotifyAPI.Spotify import SpotifyController
from OpenWeatherMapAPI.Weather import WeatherData

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventHub:
    def __init__(self):
        self.epd = epd5in83_V2.EPD()
        self.width = self.epd.width  # 648
        self.height = self.epd.height  # 480
        
        # Initialize fonts
        self.resources_dir = 'resources'  # Simplified path
        self.font_large = ImageFont.truetype(os.path.join(self.resources_dir, 'Font.ttc'), 36)
        self.font_medium = ImageFont.truetype(os.path.join(self.resources_dir, 'Font.ttc'), 24)
        self.font_small = ImageFont.truetype(os.path.join(self.resources_dir, 'Font.ttc'), 18)
        
        # Load and validate all required images
        self.load_images()

        # Initialize Location based on Wifi Connection
        self.location = self.get_location()

        # Load and Initialize Calendar and Spotify APIs
        self.calendar = CalendarAPI()
        self.spotify = SpotifyController()
        self.weather = WeatherData(self.location)

    ####################################################### DATA LOADERS

    def load_images(self):
        """Load and validate all required bitmap images"""
        try:
            # Weather icons (48x48 recommended)
            self.weather_icons = {
                'Clear': self.load_and_resize_image('sunny.bmp', (48, 48)),
                'Clouds': self.load_and_resize_image('cloudy.bmp', (48, 48)),
                'Rain': self.load_and_resize_image('rain.bmp', (48, 48)),
                'Snow': self.load_and_resize_image('snow.bmp', (48, 48)),
                'Thunderstorm': self.load_and_resize_image('thunder.bmp', (48, 48)),
                'Drizzle': self.load_and_resize_image('rain.bmp', (48, 48)),
                'Mist': self.load_and_resize_image('mist.bmp', (48, 48)),
                'default': self.load_and_resize_image('default_weather.bmp', (48, 48)),
                'sunrise': self.load_and_resize_image('sunrise.bmp', (48, 48)),
                'sunset': self.load_and_resize_image('sunset.bmp', (48, 48)),
                'drop': self.load_and_resize_image('raindrop.bmp', (24, 40))
            }
            
            # WiFi icons (32x32 recommended)
            self.wifi_icons = {
                'high': self.load_and_resize_image('wifi_high.bmp', (32, 32)),
                'medium': self.load_and_resize_image('wifi_medium.bmp', (32, 32)),
                'low': self.load_and_resize_image('wifi_low.bmp', (32, 32)),
                'none': self.load_and_resize_image('wifi_none.bmp', (32, 32))
            }
            
            # Spotify icons (32x32 recommended)
            self.spotify_icons = {
                'logo': self.load_and_resize_image('spotify_logo.bmp', (32, 32)),
                'play': self.load_and_resize_image('play.bmp', (32, 32)),
                'pause': self.load_and_resize_image('pause.bmp', (32, 32))
            }
            
        except Exception as e:
            logger.error(f"Failed to load images: {str(e)}")
            sys.exit(1)

    def get_text_dimensions(self, text, font):
        """Helper function to get text dimensions using modern PIL methods"""
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    def load_and_resize_image(self, filename, size):
        """Load a bitmap image and resize it to the specified size"""
        try:
            path = os.path.join(self.resources_dir, filename)
            if not os.path.exists(path):
                logger.error(f"Image file not found: {path}")
                return self.create_default_image(size)
                
            image = Image.open(path)
            if image.size != size:
                image = image.resize(size, Image.LANCZOS)
            return image
        except Exception as e:
            logger.error(f"Error loading image {filename}: {str(e)}")
            return self.create_default_image(size)

    def create_default_image(self, size):
        """Create a default blank image with an X pattern"""
        img = Image.new('1', size, 255)
        draw = ImageDraw.Draw(img)
        draw.line((0, 0, size[0], size[1]), fill=0)
        draw.line((0, size[1], size[0], 0), fill=0)
        return img

    def center_image(self, image, center_x, center_y):
        """Calculate position to center an image at the given point"""
        x = center_x - image.width // 2
        y = center_y - image.height // 2
        return (x, y)

    def get_location(self):
        try:
            response = requests.get('https://ipapi.co/json/')
            data = response.json()
            return {
                'lat': data['latitude'],
                'lon': data['longitude'],
                'city': data['city']
            }
        except Exception as e:
            return {'lat': 40.7128, 'lon': -74.0060, 'city': 'New York'}

    def get_wifi_info(self):
        try:
            cmd = "iwgetid -r"
            ssid = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
            
            cmd = "iwconfig wlan0 | grep 'Signal level'"
            output = subprocess.check_output(cmd, shell=True).decode('utf-8')
            signal_level = re.search(r'Signal level=(-\d+)', output)
            signal_strength = int(signal_level.group(1))
            
            signal_percent = min(100, max(0, 2 * (signal_strength + 100)))
            
            return {
                'ssid': ssid,
                'strength': signal_percent
            }
        except Exception as e:
            logger.error(f'wifi error {e}')
            return {
                'ssid': 'WiFi Not Found',
                'strength': 0
            }
        
    def get_spotify_track(self):
        return self.spotify.get_formatted_track_info()
        
    #################################################################### DRAWING FUNCS#################

    def draw_frame(self):
        image = Image.new('1', (self.width, self.height), 255)
        draw = ImageDraw.Draw(image)
        
        # Main border
        draw.rectangle((0, 0, self.width-1, self.height-1), outline=0)
        
        # Header separator
        draw.line((10, 70, self.width-10, 70), fill=0)
        
        # Vertical divider between left and right panels
        draw.line((self.width//2, 80, self.width//2, self.height-10), fill=0)
        
        return image, draw

    def draw_header(self, image, draw):
        current_time = datetime.now().strftime("%H:%M")
        current_date = datetime.now().strftime("%B %d, %Y")
        
        draw.text((20, 20), current_time, font=self.font_large, fill=0)
        draw.text((200, 25), current_date, font=self.font_medium, fill=0)
        
        # WiFi info with icon
        wifi_info = self.get_wifi_info()
        if wifi_info['strength'] >= 75:
            wifi_icon = self.wifi_icons['high']
        elif wifi_info['strength'] >= 50:
            wifi_icon = self.wifi_icons['medium']
        elif wifi_info['strength'] >= 25:
            wifi_icon = self.wifi_icons['low']
        else:
            wifi_icon = self.wifi_icons['none']
        
        # Place WiFi icon and text with truncation
        image.paste(wifi_icon, (450, 15))
        wifi_text = f"{wifi_info['ssid']} ({wifi_info['strength']}%)"
        if self.get_text_dimensions(wifi_text, self.font_small)[0] > 150:  # Adjust threshold as needed
            while self.get_text_dimensions(wifi_text + "...", self.font_small)[0] > 150:
                wifi_text = wifi_text[:-1]
            wifi_text += "..."
        draw.text((450 + wifi_icon.width + 10, 25), wifi_text, font=self.font_small, fill=0)

    def draw_todos(self, image, draw):
        draw.text((20, 90), "Today's Schedule:", font=self.font_large, fill=0)
        
        events = self.calendar.get_calendar_events()
        y_offset = 140
        max_width = self.width//2 - 60  # Maximum width for todo text
        
        for i, event in enumerate(events):
            event_text = f"{event['time']} - {event['title']}"
            text_width, text_height = self.get_text_dimensions(event_text, self.font_medium)
            
            if text_width > max_width:
                while self.get_text_dimensions(event_text + "...", self.font_medium)[0] > max_width:
                    event_text = event_text[:-1]
                event_text += "..."
                
            draw.text((30, y_offset), f"• {event_text}", font=self.font_medium, fill=0)
            
            if i < len(events) - 1:
                draw.line((40, y_offset + 30, self.width//2 - 20, y_offset + 30), 
                        fill=0, width=1)
            
            y_offset += 40

    def draw_weather(self, image, draw):
        weather_data = self.weather.get_weather()
        today_data = weather_data[0]
        
        # Draw header
        draw.text((self.width//2 + 20, 90), f"Weather - {self.location['city']}", 
                font=self.font_medium, fill=0)
        
        # Today's detailed section (top portion)
        x_start = self.width//2 + 30
        y_start = 130
        
        # Current temperature and precipitation
        current_temp = f"{today_data['temp']}°F"
        
        # Draw current conditions
        draw.text((x_start, y_start), "Now:", font=self.font_medium, fill=0)
        temp_width = self.get_text_dimensions(current_temp, self.font_large)[0]
        draw.text((x_start + 80, y_start), current_temp, font=self.font_large, fill=0)
        
        # Add precipitation with drop icon
        image.paste(self.weather_icons['drop'], (x_start + 100 + temp_width + 20, y_start + 5))
        draw.text((x_start + 100 + temp_width + 60, y_start + 10), 
                f"{today_data['precipitation']}%", font=self.font_medium, fill=0)
        
        # High/Low temperatures
        y_start += 50
        draw.text((x_start, y_start), f"High: {today_data['temp_max']}°F", font=self.font_medium, fill=0)
        draw.text((x_start + 150, y_start), f"Low: {today_data['temp_min']}°F", font=self.font_medium, fill=0)
        
        # Sunrise/Sunset with icons
        y_start += 40
        image.paste(self.weather_icons['sunrise'], (x_start, y_start))
        sunrise_time = datetime.fromtimestamp(today_data['sunrise']).strftime("%H:%M")
        draw.text((x_start + 60, y_start + 10), sunrise_time, font=self.font_medium, fill=0)
        
        image.paste(self.weather_icons['sunset'], (x_start + 150, y_start))
        sunset_time = datetime.fromtimestamp(today_data['sunset']).strftime("%H:%M")
        draw.text((x_start + 210, y_start + 10), sunset_time, font=self.font_medium, fill=0)
        
        # Separator line
        draw.line((self.width//2 + 20, y_start + 60, self.width - 20, y_start + 60), fill=0)
        
        # Future forecast (bottom portion with 3 days)
        y_start += 80
        col_width = (self.width//2 - 40) // 3  # Divide space into 3 columns
        
        for i, day in enumerate(weather_data[1:4]):  # Show next 3 days
            x_pos = self.width//2 + 20 + (i * col_width)
            
            if i > 0:
                draw.line((x_pos - 5, y_start, x_pos - 5, y_start + 140), fill=0)
            
            # Date
            date_str = day['date'].strftime("%a\n%b %d")
            date_width = self.get_text_dimensions(date_str.split('\n')[0], self.font_small)[0]
            x_center = x_pos + (col_width - date_width) // 2
            draw.text((x_center, y_start), date_str, font=self.font_small, fill=0)
            
            # Weather icon
            weather_icon = self.weather_icons.get(day['description'], 
                                                self.weather_icons['default'])
            icon_pos = self.center_image(weather_icon, 
                                    x_pos + col_width//2, 
                                    y_start + 70)
            image.paste(weather_icon, icon_pos)
            
            # Temperature range
            temp_str = f"{day['temp_max']}°/{day['temp_min']}°"
            temp_width = self.get_text_dimensions(temp_str, self.font_medium)[0]
            x_center = x_pos + (col_width - temp_width) // 2
            draw.text((x_center, y_start + 100), temp_str, 
                    font=self.font_medium, fill=0)
            
            # Precipitation chance with drop icon
            precip_icon_pos = (x_center - 25, y_start + 120)
            draw.text((x_center + 15, y_start + 125), 
                    f"{day['precipitation']}%", font=self.font_small, fill=0)

    def draw_spotify(self, image, draw):
        music_data = self.get_spotify_track()
        
        # Spotify section box
        spotify_box_top = 320
        spotify_box_bottom = 450
        box_left = 20
        box_right = self.width//2 - 20
        
        draw.rectangle((box_left, spotify_box_top, box_right, spotify_box_bottom), 
                    outline=0)
        
        # Spotify logo
        logo_pos = (box_left + 10, spotify_box_top + 10)
        image.paste(self.spotify_icons['logo'], logo_pos)
        
        # Calculate available width for text
        available_width = box_right - (box_left + 40)
        
        # Title
        title_x = logo_pos[0] + self.spotify_icons['logo'].width + 10
        draw.text((title_x, spotify_box_top + 10), 
                "Now Playing:", font=self.font_medium, fill=0)
        
        # Track name (with wrapping)
        track_name = music_data['track']
        track_width = self.get_text_dimensions(track_name, self.font_medium)[0]
        if track_width > available_width:
            while self.get_text_dimensions(track_name + '...', self.font_medium)[0] > available_width:
                track_name = track_name[:-1]
            track_name += '...'
        draw.text((box_left + 20, spotify_box_top + 50), 
                track_name, font=self.font_medium, fill=0)
        
        # Artist name (with wrapping)
        artist_name = f"by {music_data['artist']}"
        artist_width = self.get_text_dimensions(artist_name, self.font_small)[0]
        if artist_width > available_width:
            while self.get_text_dimensions(artist_name + '...', self.font_small)[0] > available_width:
                artist_name = artist_name[:-1]
            artist_name += '...'
        draw.text((box_left + 20, spotify_box_top + 80), 
                artist_name, font=self.font_small, fill=0)
        
        # Play/Pause button with icon
        button_x = box_left + 20
        button_y = spotify_box_top + 110
        
        if music_data['status'] == 'Playing':
            image.paste(self.spotify_icons['play'], (button_x, button_y))
        else:
            image.paste(self.spotify_icons['pause'], (button_x, button_y))

    def update_display(self):
        try:
            self.epd.init()
            image, draw = self.draw_frame()
            self.draw_header(image, draw)
            self.draw_todos(image, draw)
            self.draw_spotify(image, draw)
            self.draw_weather(image, draw)
            
            self.epd.display(self.epd.getbuffer(image))
        
        except Exception as e:
            logger.error(f"Error updating display: {e}")