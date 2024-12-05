#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import logging
from waveshare_epd import epd5in83_V2
import time
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# Setup paths
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

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
        # Create new Image with white background
        image = Image.new('1', (self.width, self.height), 255)
        draw = ImageDraw.Draw(image)

        # Draw borders and dividing lines
        draw.rectangle((0, 0, self.width-1, self.height-1), outline=0)  # Main border
        draw.line((0, 70, self.width, 70), fill=0)  # Header divider

        return image, draw

    def draw_header(self, draw):
        # Draw time and date
        current_time = datetime.now().strftime("%H:%M")
        current_date = datetime.now().strftime("%B %d, %Y")
        
        draw.text((20, 20), current_time, font=self.font_large, fill=0)
        draw.text((200, 25), current_date, font=self.font_medium, fill=0)

    def draw_todos(self, draw):
        # Draw Todo section
        draw.text((20, 90), "Today's Schedule:", font=self.font_medium, fill=0)
        
        todos = self.get_dummy_todos()
        for i, todo in enumerate(todos):
            draw.text((40, 130 + i*30), f"• {todo}", font=self.font_small, fill=0)

    def draw_spotify(self, draw):
        # Draw Spotify section
        music_data = self.get_dummy_spotify()
        
        draw.text((20, 320), "Now Playing:", font=self.font_medium, fill=0)
        draw.text((40, 360), f"{music_data['track']}", font=self.font_medium, fill=0)
        draw.text((40, 390), f"by {music_data['artist']}", font=self.font_small, fill=0)
        
        # Draw play/pause button
        if music_data['is_playing']:
            # Draw pause symbol
            draw.rectangle((40, 420, 50, 440), fill=0)
            draw.rectangle((60, 420, 70, 440), fill=0)
        else:
            # Draw play symbol (triangle)
            draw.polygon([(40, 420), (40, 440), (70, 430)], fill=0)

    def update_display(self):
        try:
            # Initialize display
            self.epd.init()
            
            # Create and draw frame
            image, draw = self.draw_frame()
            
            # Draw all sections
            self.draw_header(draw)
            self.draw_todos(draw)
            self.draw_spotify(draw)
            
            # Display the image
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