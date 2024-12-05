#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import logging
import time
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import requests
import subprocess
import json
import re

# Setup paths
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)
from waveshare_epd import epd5in83_V2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventHub:
    def __init__(self):
        self.epd = epd5in83_V2.EPD()
        self.width = self.epd.width  # 648
        self.height = self.epd.height  # 480
        
        # Initialize fonts
        self.font_large = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 36)
        self.font_medium = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)
        self.font_small = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 18)
        
        # OpenWeatherMap configuration
        self.weather_api_key = '67165e9a733df491e5ed1242fa0362fb'
        self.location = self.get_location()
        
        # Initialize cache
        self.weather_cache = None
        self.last_weather_update = None
        self.WEATHER_UPDATE_INTERVAL = 3600  # Update weather every hour

    def get_weather(self):
        current_time = time.time()
        
        # Return cached data if it's still valid
        if (self.weather_cache is not None and 
            self.last_weather_update is not None and 
            current_time - self.last_weather_update < self.WEATHER_UPDATE_INTERVAL):
            return self.weather_cache

        try:
            url = f"https://api.openweathermap.org/data/2.5/forecast?lat={self.location['lat']}&lon={self.location['lon']}&appid={self.weather_api_key}&units=metric"
            response = requests.get(url)
            data = response.json()
            
            # Process next 3 days
            weather_data = []
            current_date = datetime.now().date()
            
            for item in data['list']:
                forecast_date = datetime.fromtimestamp(item['dt']).date()
                if forecast_date > current_date and len(weather_data) < 3:
                    if not any(w['date'] == forecast_date for w in weather_data):
                        weather_data.append({
                            'date': forecast_date,
                            'temp': round(item['main']['temp']),
                            'description': item['weather'][0]['main']
                        })
            
            # Update cache
            self.weather_cache = weather_data
            self.last_weather_update = current_time
            
            return weather_data
            
        except Exception as e:
            logger.error(f"Weather API error: {str(e)}")
            # If there's an error, return cached data if available
            if self.weather_cache is not None:
                return self.weather_cache
                
            # Otherwise return dummy data
            return [
                {'date': datetime.now().date() + timedelta(days=1), 'temp': 20, 'description': 'Sunny'},
                {'date': datetime.now().date() + timedelta(days=2), 'temp': 18, 'description': 'Cloudy'},
                {'date': datetime.now().date() + timedelta(days=3), 'temp': 22, 'description': 'Clear'}
            ]

    def draw_weather(self, draw):
        weather_data = self.get_weather()
        next_update = ""
        if self.last_weather_update is not None:
            minutes_until_update = int((self.WEATHER_UPDATE_INTERVAL - (time.time() - self.last_weather_update)) / 60)
            next_update = f"Next update in: {minutes_until_update}m"
        
        draw.text((self.width//2 + 20, 90), f"Weather - {self.location['city']}", font=self.font_medium, fill=0)
        draw.text((self.width//2 + 20, 115), next_update, font=self.font_small, fill=0)
        
        for i, day in enumerate(weather_data):
            y_pos = 140 + i*60
            date_str = day['date'].strftime("%A, %b %d")
            draw.text((self.width//2 + 40, y_pos), date_str, font=self.font_small, fill=0)
            draw.text((self.width//2 + 40, y_pos + 25), 
                     f"{day['temp']}°C - {day['description']}", 
                     font=self.font_small, fill=0)
            
    def get_location(self):
        try:
            # Get IP-based location
            response = requests.get('https://ipapi.co/json/')
            data = response.json()
            return {
                'lat': data['latitude'],
                'lon': data['longitude'],
                'city': data['city']
            }
        except:
            # Default to dummy location if API fails
            return {'lat': 40.7128, 'lon': -74.0060, 'city': 'New York'}

    def get_wifi_info(self):
        try:
            # Get WiFi network name
            cmd = "iwgetid -r"
            ssid = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
            
            # Get signal strength
            cmd = "iwconfig wlan0 | grep 'Signal level'"
            output = subprocess.check_output(cmd, shell=True).decode('utf-8')
            signal_level = re.search(r'Signal level=(-\d+)', output)
            signal_strength = int(signal_level.group(1))
            
            # Convert dBm to percentage (rough approximation)
            # -50 dBm or higher is ~100%, -100 dBm or lower is ~0%
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
        
        # Divide screen into sections
        draw.line((0, 70, self.width, 70), fill=0)  # Header divider
        draw.line((self.width//2, 70, self.width//2, self.height), fill=0)  # Vertical divider
        
        return image, draw

    def draw_header(self, draw):
        current_time = datetime.now().strftime("%H:%M")
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Draw time and date
        draw.text((20, 20), current_time, font=self.font_large, fill=0)
        draw.text((200, 25), current_date, font=self.font_medium, fill=0)
        
        # Draw WiFi info
        wifi_info = self.get_wifi_info()
        wifi_text = f"WiFi: {wifi_info['ssid']} ({wifi_info['strength']}%)"
        draw.text((450, 25), wifi_text, font=self.font_small, fill=0)


    def draw_todos(self, draw):
        draw.text((20, 90), "Today's Schedule:", font=self.font_medium, fill=0)
        
        todos = self.get_dummy_todos()
        for i, todo in enumerate(todos):
            draw.text((40, 130 + i*30), f"• {todo}", font=self.font_small, fill=0)

    def draw_spotify(self, draw):
        music_data = self.get_dummy_spotify()
        
        draw.text((20, 320), "Now Playing:", font=self.font_medium, fill=0)
        draw.text((40, 360), f"{music_data['track']}", font=self.font_medium, fill=0)
        draw.text((40, 390), f"by {music_data['artist']}", font=self.font_small, fill=0)
        
        if music_data['is_playing']:
            draw.rectangle((40, 420, 50, 440), fill=0)
            draw.rectangle((60, 420, 70, 440), fill=0)
        else:
            draw.polygon([(40, 420), (40, 440), (70, 430)], fill=0)

    def update_display(self):
        try:
            self.epd.init()
            
            image, draw = self.draw_frame()
            
            self.draw_header(draw)
            self.draw_todos(draw)
            self.draw_spotify(draw)
            self.draw_weather(draw)
            
            self.epd.display(self.epd.getbuffer(image))
            
        except Exception as e:
            logger.error(f"Error updating display: {str(e)}")

def main():
    try:
        hub = EventHub()
        
        while True:
            hub.update_display()
            time.sleep(60)  # Update every minute
            
    except KeyboardInterrupt:
        logging.info("Exiting...")
        epd5in83_V2.epdconfig.module_exit(cleanup=True)
        exit()

if __name__ == "__main__":
    main()