import sys
import os
import logging
import time
import gc  # Garbage collector for memory management
import threading
from gpiozero import Button
from EventHub import EventHub
from EReader import EReader

# Set up logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define absolute paths for resources to ensure they work when run as a service
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
resources_dir = os.path.join(BASE_DIR, 'resources')

# GPIO pin definitions for buttons
LEFT_PIN = 5      # Previous track/page
TOGGLE_PIN = 6    # Play-pause/select
RIGHT_PIN = 13    # Next track/page
MODE_PIN = 16     # Switch between hub and reader modes

class ButtonController:
    """Manages button inputs with debouncing and thread safety"""
    def __init__(self):
        # Initialize buttons with internal pull-up resistors and basic hardware debouncing
        self.left_button = Button(LEFT_PIN, pull_up=True, bounce_time=0.1)
        self.toggle_button = Button(TOGGLE_PIN, pull_up=True, bounce_time=0.1)
        self.right_button = Button(RIGHT_PIN, pull_up=True, bounce_time=0.1)
        self.mode_button = Button(MODE_PIN, pull_up=True, bounce_time=0.1)
        
        # Additional software debouncing parameters
        self.last_press_time = 0
        self.debounce_time = 0.5  # 500ms between valid button presses
        self.update_lock = threading.Lock()  # Prevent concurrent display updates
        
    def check_debounce(self):
        """Software debounce check to prevent rapid repeated button presses"""
        current_time = time.time()
        if current_time - self.last_press_time >= self.debounce_time:
            self.last_press_time = current_time
            return True
        return False

def reinitialize_display(epd):
    """Reset and clear the e-paper display"""
    try:
        epd.init()
        epd.Clear()
        time.sleep(0.1)  # Brief pause to ensure display settles
    except Exception as e:
        logger.error(f"Error reinitializing display: {e}")
        raise

def safe_mode_switch(buttons, current_mode, hub, reader):
    """Thread-safe mode switching between hub and reader modes"""
    # Try to acquire lock for display update, return current mode if busy
    if not buttons.update_lock.acquire(blocking=False):
        return current_mode
    
    try:
        if current_mode == 'hub':
            # Switching to reader mode
            gc.collect()  # Clear unused memory
            reinitialize_display(hub.epd)
            reader.update_display()
            return 'reader'
        else:
            # Switching to hub mode
            reader.cleanup()  # Clean reader resources
            gc.collect()
            reinitialize_display(hub.epd)
            hub.update_display()
            return 'hub'
    except Exception as e:
        logger.error(f"Error during mode switch: {e}")
        return current_mode
    finally:
        buttons.update_lock.release()
        gc.collect()

def safe_update_display(buttons, display_func):
    """Thread-safe display update with memory management"""
    if buttons.update_lock.acquire(blocking=False):
        try:
            display_func()
            gc.collect()  # Clean up memory after update
        finally:
            buttons.update_lock.release()

def main():
    """Main program loop"""
    hub = None
    try:
        # Initialize core components
        hub = EventHub()
        reader = EReader(hub.epd, resources_dir)
        buttons = ButtonController()
        current_mode = 'hub'
        last_update = time.time()
        
        # Initial display update
        hub.update_display()
        gc.collect()
        logger.info("System initialized successfully")
        
        def handle_mode_switch():
            """Handle mode switch button press"""
            nonlocal current_mode
            if buttons.check_debounce():
                new_mode = safe_mode_switch(buttons, current_mode, hub, reader)
                if new_mode != current_mode:
                    logger.info(f"Mode switched from {current_mode} to {new_mode}")
                    current_mode = new_mode
        
        def handle_button_press(button_type):
            """Handle navigation button presses based on current mode"""
            if not buttons.check_debounce():
                return
                
            try:
                if current_mode == 'hub':
                    # Handle Spotify controls in hub mode
                    if button_type == 'left':
                        hub.spotify.skip_previous()
                    elif button_type == 'toggle':
                        hub.spotify.toggle_playback()
                    elif button_type == 'right':
                        hub.spotify.skip_next()
                    safe_update_display(buttons, hub.update_display)
                else:  # reader mode
                    # Handle navigation in reader mode
                    if button_type == 'left':
                        reader.handle_command('left')
                    elif button_type == 'toggle':
                        reader.handle_command('select')
                    elif button_type == 'right':
                        reader.handle_command('right')
                    safe_update_display(buttons, reader.update_display)
            except Exception as e:
                logger.error(f"Error handling button press: {e}")
        
        # Set up button event handlers
        buttons.mode_button.when_pressed = handle_mode_switch
        buttons.left_button.when_pressed = lambda: handle_button_press('left')
        buttons.toggle_button.when_pressed = lambda: handle_button_press('toggle')
        buttons.right_button.when_pressed = lambda: handle_button_press('right')
        
        # Main program loop
        while True:
            try:
                # Regular display updates in hub mode (every 60 seconds)
                if current_mode == 'hub':
                    current_time = time.time()
                    if current_time - last_update >= 60:
                        safe_update_display(buttons, hub.update_display)
                        last_update = current_time
                
                time.sleep(0.1)  # Prevent CPU hogging
                
                # Periodic garbage collection
                if time.time() % 60 < 0.1:  # Every minute
                    gc.collect()
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                if "device" in str(e).lower() or "display" in str(e).lower():
                    raise
                
    except KeyboardInterrupt:
        # Handle clean shutdown on Ctrl+C
        logger.info("Shutting down...")
        if hub:
            hub.epd.init()
            hub.epd.Clear()
            hub.epd.sleep()
        sys.exit(0)
    except Exception as e:
        # Handle critical errors
        logger.error(f"Critical error: {e}")
        if hub:
            try:
                hub.epd.init()
                hub.epd.Clear()
                hub.epd.sleep()
            except:
                pass
        sys.exit(1)

if __name__ == "__main__":
    main()