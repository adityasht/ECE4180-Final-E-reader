import sys
import os
import logging
import time
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import requests
import subprocess
import re
import epd5in83_V2
from CalendarAPI.CalendarAPI import *



# Setup paths
resources_dir = 'resources'  # Simplified path


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventHub:
    def __init__(self):
        self.epd = epd5in83_V2.EPD()
        self.width = self.epd.width  # 648
        self.height = self.epd.height  # 480
        
        # Initialize fonts
        self.font_large = ImageFont.truetype(os.path.join(resources_dir, 'Font.ttc'), 36)
        self.font_medium = ImageFont.truetype(os.path.join(resources_dir, 'Font.ttc'), 24)
        self.font_small = ImageFont.truetype(os.path.join(resources_dir, 'Font.ttc'), 18)
        
        # Load and validate all required images
        self.load_images()

        # Load and Intialize Calendar and Spotify APIs
        self.calendar = CalendarAPI()
        
        # OpenWeatherMap configuration
        self.weather_api_key = '67165e9a733df491e5ed1242fa0362fb'
        self.location = self.get_location()
        
        # Initialize cache
        self.weather_cache = None
        self.last_weather_update = None
        self.WEATHER_UPDATE_INTERVAL = 3600  # Update weather every hour


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
                'default': self.load_and_resize_image('default_weather.bmp', (48, 48))
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

    def load_and_resize_image(self, filename, size):
        """Load a bitmap image and resize it to the specified size"""
        try:
            path = os.path.join(resources_dir, filename)
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
        except:
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
        except:
            return {
                'ssid': 'WiFi Not Found',
                'strength': 0
            }
        

    # Calendar Todo Drawing
    def draw_todos(self, image, draw):
        draw.text((20, 90), "Today's Schedule:", font=self.font_medium, fill=0)
        
        events = self.calendar.get_calendar_events()
        y_offset = 130

        for i, event in enumerate(events):
            # Format the event text
            event_text = f"{event['time']} - {event['title']}"
            
            # Draw the text
            draw.text((40, y_offset), f"• {event_text}", font=self.font_small, fill=0)
            
            # Draw separator line
            if i < len(events) - 1:
                draw.line((40, y_offset + 25, self.width//2 - 20, y_offset + 25), 
                         fill=0, width=1)
            
            y_offset += 35

    def get_weather(self):
        current_time = time.time()
        
        if (self.weather_cache is not None and 
            self.last_weather_update is not None and 
            current_time - self.last_weather_update < self.WEATHER_UPDATE_INTERVAL):
            return self.weather_cache

        try:
            url = f"https://api.openweathermap.org/data/2.5/forecast?lat={self.location['lat']}&lon={self.location['lon']}&appid={self.weather_api_key}&units=imperial"
            response = requests.get(url)
            data = response.json()
            
            weather_data = []
            if 'list' in data:
                current_date = datetime.now().date()
                days_processed = set()
                
                for item in data['list']:
                    forecast_date = datetime.fromtimestamp(item['dt']).date()
                    if forecast_date > current_date and forecast_date not in days_processed and len(weather_data) < 3:
                        weather_data.append({
                            'date': forecast_date,
                            'temp': round(item['main']['temp']),
                            'temp_min': round(item['main']['temp_min']),
                            'temp_max': round(item['main']['temp_max']),
                            'description': item['weather'][0]['main']
                        })
                        days_processed.add(forecast_date)
            
            self.weather_cache = weather_data
            self.last_weather_update = current_time
            
            return weather_data
            
        except Exception as e:
            logger.error(f"Weather API error: {str(e)}")
            if self.weather_cache is not None:
                return self.weather_cache
            
            return [
                {'date': datetime.now().date() + timedelta(days=1), 'temp': 68, 'temp_min': 60, 'temp_max': 75, 'description': 'Sunny'},
                {'date': datetime.now().date() + timedelta(days=2), 'temp': 65, 'temp_min': 58, 'temp_max': 72, 'description': 'Cloudy'},
                {'date': datetime.now().date() + timedelta(days=3), 'temp': 70, 'temp_min': 62, 'temp_max': 78, 'description': 'Clear'}
            ]

    def get_dummy_todos(self):
        return [
            "9:00 AM - Team standup meeting",
            "11:30 AM - Dentist appointment",
            "2:00 PM - Review project deadline",
            "4:30 PM - Gym session",
            "6:00 PM - Dinner with friends"
        ]

    def get_dummy_spotify(self):
        return {
            "track": "Bohemian Rhapsody",
            "artist": "Queen",
            "is_playing": True
        }

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
        
        # Place WiFi icon and text
        image.paste(wifi_icon, (450, 15))
        draw.text((450 + wifi_icon.width + 10, 25), 
                 f"{wifi_info['ssid']} ({wifi_info['strength']}%)", 
                 font=self.font_small, fill=0)

    def draw_weather(self, image, draw):
        weather_data = self.get_weather()
        draw.text((self.width//2 + 20, 90), f"Weather - {self.location['city']}", 
                font=self.font_medium, fill=0)
        
        col_width = (self.width//2 - 40) // 3
        
        for i, day in enumerate(weather_data):
            x_pos = self.width//2 + 20 + (i * col_width)
            y_start = 130
            
            if i > 0:
                draw.line((x_pos - 5, 120, x_pos - 5, 280), fill=0)
            
            # Date
            date_str = day['date'].strftime("%a\n%b %d")
            date_w = self.font_small.getsize(date_str.split('\n')[0])[0]
            x_center = x_pos + (col_width - date_w) // 2
            draw.text((x_center, y_start), date_str, font=self.font_small, fill=0)
            
            # Weather icon
            weather_icon = self.weather_icons.get(day['description'], 
                                                self.weather_icons['default'])
            icon_pos = self.center_image(weather_icon, 
                                    x_pos + col_width//2, 
                                    y_start + 80)
            image.paste(weather_icon, icon_pos)
            
            # Temperature range
            temp_str = f"{day['temp_max']}°/{day['temp_min']}°"
            temp_w = self.font_medium.getsize(temp_str)[0]
            x_center = x_pos + (col_width - temp_w) // 2
            draw.text((x_center, y_start + 120), temp_str, 
                    font=self.font_medium, fill=0)
            
            # Description
            desc_w = self.font_small.getsize(day['description'])[0]
            x_center = x_pos + (col_width - desc_w) // 2
            draw.text((x_center, y_start + 150), day['description'], 
                    font=self.font_small, fill=0)

    def draw_dummy_todos(self, image, draw):
        draw.text((20, 90), "Today's Schedule:", font=self.font_medium, fill=0)
        
        todos = self.get_dummy_todos()
        for i, todo in enumerate(todos):
            draw.text((40, 130 + i*35), f"• {todo}", font=self.font_small, fill=0)
            
            if i < len(todos) - 1:
                draw.line((40, 130 + i*35 + 25, self.width//2 - 20, 
                          130 + i*35 + 25), fill=0, width=1)

    def draw_spotify(self, image, draw):
        music_data = self.get_dummy_spotify()
        
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
        
        # Title and track info
        draw.text((logo_pos[0] + self.spotify_icons['logo'].width + 10, 
                  spotify_box_top + 10), 
                 "Now Playing:", font=self.font_medium, fill=0)
        draw.text((box_left + 20, spotify_box_top + 50), 
                 f"{music_data['track']}", font=self.font_medium, fill=0)
        draw.text((box_left + 20, spotify_box_top + 80), 
                 f"by {music_data['artist']}", font=self.font_small, fill=0)
        
        # Play/Pause button with icon
        button_x = box_left + 20
        button_y = spotify_box_top + 110
        
        if music_data['is_playing']:
            image.paste(self.spotify_icons['pause'], 
                      (button_x, button_y))
        else:
            image.paste(self.spotify_icons['play'], 
                      (button_x, button_y))

    def update_display(self):
        try:
            self.epd.init()
            
            image, draw = self.draw_frame()
            self.draw_header(image, draw)
            #self.draw_dummy_todos(image, draw)
            self.draw_todos(image, draw)
            self.draw_spotify(image, draw)
            self.draw_weather(image, draw)
            
            self.epd.display(self.epd.getbuffer(image))
            
        except Exception as e:
            logger.error(f"Error updating display: {str(e)}")

def main():
    try:
        hub = EventHub()
        
        while True:
            hub.update_display()
            time.sleep(60)
            
    except KeyboardInterrupt:
        logging.info("Exiting gracefully...")
        hub.epd.init()
        hub.epd.Clear()
        hub.epd.sleep()
        epd5in83_V2.epdconfig.module_exit(cleanup=True)
        exit()
    except Exception as e:
        logging.error(f"Error in main loop: {str(e)}")
        try:
            hub.epd.init()
            hub.epd.Clear()
            hub.epd.sleep()
        except:
            pass
        epd5in83_V2.epdconfig.module_exit(cleanup=True)
        exit(1)

if __name__ == "__main__":
    main()