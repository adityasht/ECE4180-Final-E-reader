# server.py (Windows PC)
import serial
import time

def main():
    # Find your COM port in Device Manager under Ports (COM & LPT)
    # It will appear as "Standard Serial over Bluetooth link (COMX)"
    port = "COM3"  # Change this to your COM port
    
    try:
        # Open serial port
        ser = serial.Serial(port, 9600, timeout=1)
        print(f"Connected to {port}")
        
        while True:
            # Send message
            message = input("Enter message (or 'quit'): ")
            if message.lower() == 'quit':
                break
                
            ser.write(message.encode())
            print(f"Sent: {message}")
            
            # Read response
            response = ser.readline().decode().strip()
            if response:
                print(f"Received: {response}")
                
    except Exception as e:
        print(f"Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check if the COM port number is correct in Device Manager")
        print("2. Make sure the Pi is paired and connected")
        print("3. Try unplugging/replugging or repairing the Bluetooth connection")
    
    finally:
        if 'ser' in locals():
            ser.close()

if __name__ == "__main__":
    main()