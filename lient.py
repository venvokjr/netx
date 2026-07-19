import asyncio
import websockets

async def main():
    uri = "ws://127.0.0.1:8080"

    async with websockets.connect(uri) as websocket:
        print("Connected to server")

        await websocket.send(b"Hello Brother")
        print("Sent payload")

        response = await websocket.recv()

        print("Received:", response)

asyncio.run(main())