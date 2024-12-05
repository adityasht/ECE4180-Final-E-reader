# server.py (Windows PC)
from bleak import BleakScanner, BleakClient
import asyncio

async def handle_data(sender, data):
    print(f"Received: {data.decode()}")

async def main():
    # Scan for devices
    print("Scanning for devices...")
    devices = await BleakScanner.discover()
    
    # Show all found devices
    for i, device in enumerate(devices):
        print(f"{i}: {device.name or 'Unknown'} ({device.address})")
    
    # Let user select device
    selection = int(input("Select device number to connect to: "))
    device = devices[selection]
    
    async with BleakClient(device.address) as client:
        print(f"Connected to {device.address}")
        
        # Get all services
        services = await client.get_services()
        
        # Find the first characteristic that supports write
        write_char = None
        for service in services:
            for char in service.characteristics:
                if "write" in char.properties:
                    write_char = char
                    break
            if write_char:
                break
                
        if not write_char:
            print("No writable characteristic found")
            return
            
        print(f"Using characteristic: {write_char.uuid}")
        
        while True:
            message = input("Enter message (or 'quit'): ")
            if message.lower() == 'quit':
                break
                
            # Send message
            await client.write_gatt_char(write_char.uuid, message.encode())
            print(f"Sent: {message}")

if __name__ == "__main__":
    asyncio.run(main())