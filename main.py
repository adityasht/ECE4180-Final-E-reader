import sys
import os
import logging
import time
import select
from resources import epd5in83_V2
from EventHub import EventHub
from EReader import EReader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup paths
resources_dir = 'resources'  # Simplified path

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
        # Try one more time to exit the module
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
        # Initialize EventHub and EReader
        hub = EventHub()
        reader = EReader(hub.epd, resources_dir)
        current_mode = 'hub'
        last_update = time.time()
        
        # Initial display update
        hub.update_display()
        logger.info("System initialized successfully")
        
        while True:
            try:
                if select.select([sys.stdin], [], [], 0.1)[0]:  # Check input with 0.1s timeout
                    command = input().strip()  # Get the command
                    
                    # Handle exit command
                    if command.lower() in ['exit', 'quit']:
                        logger.info("Exit command received")
                        handle_exit(hub)
                    
                    # Mode switching
                    if command == 'reader' and current_mode == 'hub':
                        current_mode = 'reader'
                        reader.update_display()
                        continue
                    elif command == 'hub' and current_mode == 'reader':
                        current_mode = 'hub'
                        hub.update_display()
                        continue
                    
                    # Mode-specific commands
                    if current_mode == 'hub':
                        if command == 'toggle':
                            hub.spotify.toggle_playback()
                            hub.update_display()
                            last_update = time.time()
                        elif command == 'prev_track':
                            hub.spotify.skip_previous()
                            hub.update_display()
                            last_update = time.time()
                        elif command == 'next_track':
                            hub.spotify.skip_next()
                            hub.update_display()
                            last_update = time.time()
                    elif current_mode == 'reader':
                        reader.handle_command(command)
                        reader.update_display()
                
                # Regular update check (hub mode only)
                if current_mode == 'hub':
                    current_time = time.time()
                    if current_time - last_update >= 60:
                        hub.update_display()
                        last_update = current_time
                        
            except EOFError:
                logger.info("EOF received, initiating shutdown")
                handle_exit(hub)
            except KeyboardInterrupt:
                logger.info("KeyboardInterrupt received, initiating shutdown")
                handle_exit(hub)
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                # Only exit if it's a serious error
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
            # If we couldn't initialize hub, try basic cleanup
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