

import sys
import os
import logging
import time
from gpiozero import Button
from resources import epd5in83_V2
from EventHub import EventHub
from EReader import EReader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup paths
resources_dir = 'resources'  # Simplified path

# GPIO Button Setup
LEFT_PIN = 5
TOGGLE_PIN = 6
RIGHT_PIN = 13
MODE_PIN = 16

class ButtonController:
    def __init__(self):
        # Initialize buttons with pull_up=True (internal pull-up resistor)
        self.left_button = Button(LEFT_PIN, pull_up=True, bounce_time=0.1)
        self.toggle_button = Button(TOGGLE_PIN, pull_up=True, bounce_time=0.1)
        self.right_button = Button(RIGHT_PIN, pull_up=True, bounce_time=0.1)
        self.mode_button = Button(MODE_PIN, pull_up=True, bounce_time=0.1)
        
        # State tracking
        self.last_press_time = 0
        self.debounce_time = 0.3  # 300ms debounce
        
    def check_debounce(self):
        """Check if enough time has passed since last button press"""
        current_time = time.time()
        if current_time - self.last_press_time >= self.debounce_time:
            self.last_press_time = current_time
            return True
        return False

def cleanup_display(epd):
    """Safely clean up the e-paper display"""
    try:
        logger.info("Cleaning up display...")
        epd.init()
        epd.Clear()
        epd.sleep()
        epd5in83_V2.epdconfig.module_exit(cleanup=True)
    except Exception as e:
        logger.error(f"Error during display cleanup: {e}")
        try:
            epd5in83_V2.epdconfig.module_exit(cleanup=True)
        except:
            pass

def handle_exit(hub, signal_received=None):
    """Handle graceful exit with proper cleanup"""
    if signal_received:
        logger.info(f"Received signal: {signal_received}")
    logger.info("Initiating graceful shutdown...")
    
    try:
        cleanup_display(hub.epd)
        logger.info("Shutdown completed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    finally:
        sys.exit(0)

def main():
    hub = None
    try:
        # Initialize components
        hub = EventHub()
        reader = EReader(hub.epd, resources_dir)
        buttons = ButtonController()
        current_mode = 'hub'
        last_update = time.time()
        
        # Initial display update
        hub.update_display()
        logger.info("System initialized successfully")
        
        # Button callbacks
        def handle_mode_switch():
            nonlocal current_mode
            if buttons.check_debounce():
                if current_mode == 'hub':
                    current_mode = 'reader'
                    reader.update_display()
                else:
                    current_mode = 'hub'
                    hub.update_display()
        
        def handle_button_press(button_type):
            if not buttons.check_debounce():
                return
                
            if current_mode == 'hub':
                if button_type == 'left':
                    hub.spotify.skip_previous()
                elif button_type == 'toggle':
                    hub.spotify.toggle_playback()
                elif button_type == 'right':
                    hub.spotify.skip_next()
                hub.update_display()
            else:  # reader mode
                if button_type == 'left':
                    reader.handle_command('left')
                elif button_type == 'toggle':
                    reader.handle_command('select')
                elif button_type == 'right':
                    reader.handle_command('right')
                reader.update_display()
        
        # Set up button callbacks
        buttons.mode_button.when_pressed = handle_mode_switch
        buttons.left_button.when_pressed = lambda: handle_button_press('left')
        buttons.toggle_button.when_pressed = lambda: handle_button_press('toggle')
        buttons.right_button.when_pressed = lambda: handle_button_press('right')
        
        # Main loop
        while True:
            try:
                # Regular update check (hub mode only)
                if current_mode == 'hub':
                    current_time = time.time()
                    if current_time - last_update >= 60:
                        hub.update_display()
                        last_update = current_time
                
                # Small delay to prevent CPU hogging
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                logger.info("KeyboardInterrupt received, initiating shutdown")
                handle_exit(hub)
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                if "device" in str(e).lower() or "display" in str(e).lower():
                    raise
                
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received during initialization")
        if hub:
            handle_exit(hub)
        else:
            sys.exit(1)
    except Exception as e:
        logger.error(f"Critical error: {e}")
        if hub:
            handle_exit(hub)
        else:
            try:
                epd = epd5in83_V2.EPD()
                cleanup_display(epd)
            except:
                pass
            sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)