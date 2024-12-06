#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import logging
from . import epd5in83_V2
import time
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import requests
import subprocess
import json
import re

# Setup paths
picdir = os.path.join(os.path, 'pic')


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_weather_icon(description):
    # Simple ASCII weather icons
    weather_icons = {
        'Clear': '*',
        'Clouds': '=',
        'Rain': 'v',
        'Snow': '*',
        'Thunderstorm': '//',
        'Drizzle': '.',
        'Mist': '-',
        'Fog': '-',
    }
    return weather_icons.get(description, 'o')

def get_wifi_signal_icon(strength):
    if strength >= 75:
        return '[||||]'
    elif strength >= 50:
        return '[||| ]'
    elif strength >= 25:
        return '[||  ]'
    elif strength > 0:
        return '[|   ]'
    else:
        return '[    ]'

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
        self.weather_api_key = 'YOUR_API_KEY'
        self.location = self.get_location()
        
        # Initialize cache
        self.weather_cache = None
        self.last_weather_update = None
        self.WEATHER_UPDATE_INTERVAL = 3600  # Update weather every hour

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
            # Get WiFi network name
            cmd = "iwgetid -r"
            ssid = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
            
            # Get signal strength
            cmd = "iwconfig wlan0 | grep 'Signal level'"
            output = subprocess.check_output(cmd, shell=True).decode('utf-8')
            signal_level = re.search(r'Signal level=(-\d+)', output)
            signal_strength = int(signal_level.group(1))
            
            # Convert dBm to percentage
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

    def get_weather(self):
        current_time = time.time()
        
        if (self.weather_cache is not None and 
            self.last_weather_update is not None and 
            current_time - self.last_weather_update < self.WEATHER_UPDATE_INTERVAL):
            return self.weather_cache

        try:
            url = f"https://api.openweathermap.org/data/2.5/forecast/daily?lat={self.location['lat']}&lon={self.location['lon']}&appid={self.weather_api_key}&units=imperial&cnt=4"
            response = requests.get(url)
            data = response.json()
            
            weather_data = []
            if 'list' in data:
                for i, day in enumerate(data['list'][:3]):
                    weather_data.append({
                        'date': datetime.now().date() + timedelta(days=i+1),
                        'temp': round(day['temp']['day']),
                        'temp_min': round(day['temp']['min']),
                        'temp_max': round(day['temp']['max']),
                        'description': day['weather'][0]['main']
                    })
            else:
                url = f"https://api.openweathermap.org/data/2.5/weather?lat={self.location['lat']}&lon={self.location['lon']}&appid={self.weather_api_key}&units=imperial"
                response = requests.get(url)
                data = response.json()
                
                for i in range(3):
                    weather_data.append({
                        'date': datetime.now().date() + timedelta(days=i+1),
                        'temp': round(data['main']['temp']),
                        'temp_min': round(data['main']['temp_min']),
                        'temp_max': round(data['main']['temp_max']),
                        'description': data['weather'][0]['main']
                    })
            
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

    def draw_header(self, draw):
        current_time = datetime.now().strftime("%H:%M")
        current_date = datetime.now().strftime("%B %d, %Y")
        
        draw.text((20, 20), current_time, font=self.font_large, fill=0)
        draw.text((200, 25), current_date, font=self.font_medium, fill=0)
        
        # Modified WiFi display with line wrapping
        wifi_info = self.get_wifi_info()
        wifi_icon = get_wifi_signal_icon(wifi_info['strength'])
        
        ssid = wifi_info['ssid']
        if len(ssid) > 12:
            ssid = f"{ssid[:12]}\n{ssid[12:]}"
        
        wifi_text = f"{wifi_icon}\n{ssid}"
        draw.text((450, 15), wifi_text, font=self.font_small, fill=0)
        draw.text((450, 50), f"{wifi_info['strength']}%", font=self.font_small, fill=0)

    def draw_weather(self, draw):
        weather_data = self.get_weather()
        
        # Draw weather title
        draw.text((self.width//2 + 20, 90), f"Weather - {self.location['city']}", font=self.font_medium, fill=0)
        
        # Calculate column widths and positions
        col_width = (self.width//2 - 40) // 3
        
        # Draw three vertical columns for weather
        for i, day in enumerate(weather_data):
            x_pos = self.width//2 + 20 + (i * col_width)
            y_start = 130
            
            # Draw vertical separator lines
            if i > 0:
                draw.line((x_pos - 5, 120, x_pos - 5, 280), fill=0)
            
            # Format date more compactly
            date_str = day['date'].strftime("%a\n%b %d")
            weather_icon = get_weather_icon(day['description'])
            
            # Center align text in column
            date_w = self.font_small.getbbox(date_str.split('\n')[0])[2]
            temp_w = self.font_medium.getbbox(f"{day['temp']}°F")[2]
            desc_w = self.font_small.getbbox(day['description'])[2]
            
            x_center = x_pos + (col_width - max(date_w, temp_w, desc_w)) // 2
            
            # Draw weather info vertically
            draw.text((x_center, y_start), date_str, font=self.font_small, fill=0, align="center")
            draw.text((x_center, y_start + 40), weather_icon, font=self.font_medium, fill=0)
            draw.text((x_center, y_start + 70), f"{day['temp']}°F", font=self.font_medium, fill=0)
            
            # Add high/low temperatures
            high_low = f"H:{day['temp_max']}° L:{day['temp_min']}°"
            high_low_w = self.font_small.getbbox(high_low)[2]
            draw.text((x_center + (col_width - high_low_w)//2, y_start + 95), 
                     high_low, font=self.font_small, fill=0)
            
            # Description moved below high/low
            draw.text((x_center, y_start + 120), day['description'], font=self.font_small, fill=0)
        
        # Draw update time at bottom
        if self.last_weather_update is not None:
            minutes_until_update = int((self.WEATHER_UPDATE_INTERVAL - (time.time() - self.last_weather_update)) / 60)
            next_update = f"Next update in: {minutes_until_update}m"
            draw.text((self.width//2 + 20, 280), next_update, font=self.font_small, fill=0)

    def draw_todos(self, draw):
        draw.text((20, 90), "Today's Schedule:", font=self.font_medium, fill=0)
        
        todos = self.get_dummy_todos()
        for i, todo in enumerate(todos):
            # Add bullet points and improve spacing
            draw.text((40, 130 + i*35), f"• {todo}", font=self.font_small, fill=0)
            
            # Draw separator line between todos
            if i < len(todos) - 1:
                draw.line((40, 130 + i*35 + 25, self.width//2 - 20, 130 + i*35 + 25), fill=0, width=1)

    def draw_spotify(self, draw):
        music_data = self.get_dummy_spotify()
        
        # Add a box around the Spotify section
        spotify_box_top = 320
        spotify_box_bottom = 450
        draw.rectangle((20, spotify_box_top, self.width//2 - 20, spotify_box_bottom), outline=0)
        
        draw.text((30, spotify_box_top + 10), "Now Playing:", font=self.font_medium, fill=0)
        draw.text((40, spotify_box_top + 50), f"{music_data['track']}", font=self.font_medium, fill=0)
        draw.text((40, spotify_box_top + 80), f"by {music_data['artist']}", font=self.font_small, fill=0)
        
        # Improved play/pause button
        button_x = 40
        button_y = spotify_box_top + 110
        if music_data['is_playing']:
            draw.rectangle((button_x, button_y, button_x + 8, button_y + 20), fill=0)
            draw.rectangle((button_x + 20, button_y, button_x + 28, button_y + 20), fill=0)
        else:
            draw.polygon([(button_x, button_y), (button_x, button_y + 20), 
                         (button_x + 25, button_y + 10)], fill=0)

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