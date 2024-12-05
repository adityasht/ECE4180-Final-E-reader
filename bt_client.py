# client.py (Raspberry Pi)
from bleak import BleakScanner, BleakClient
import asyncio

async def handle_data(sender, data):
    print(f"Received: {data.decode()}")

async def main():
    # Make the Pi discoverable
    print("Making device discoverable...")
    print("Waiting for connection...")
    
    while True:
        try:
            # Scan for servers
            devices = await BleakScanner.discover()
            for device in devices:
                print(f"Found device: {device.name or 'Unknown'} ({device.address})")
                async with BleakClient(device.address) as client:
                    print(f"Connected to {device.address}")
                    
                    # Get services
                    services = await client.get_services()
                    
                    # Find writable characteristic
                    write_char = None
                    for service in services:
                        for char in service.characteristics:
                            if "write" in char.properties:
                                write_char = char
                                break
                        if write_char:
                            break
                    
                    if not write_char:
                        continue
                        
                    print(f"Using characteristic: {write_char.uuid}")
                    
                    while True:
                        message = input("Enter message (or 'quit'): ")
                        if message.lower() == 'quit':
                            break
                            
                        await client.write_gatt_char(write_char.uuid, message.encode())
                        print(f"Sent: {message}")
                        
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())