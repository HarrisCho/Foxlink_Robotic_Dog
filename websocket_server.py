import asyncio
import websockets

async def handler(websocket, path):
    async for message in websocket:
        print(f"接收到的訊息：{message}")

# 啟動 WebSocket 伺服器
start_server = websockets.serve(handler, "localhost", 8765)

# 啟動事件循環
asyncio.get_event_loop().run_until_complete(start_server)
print("WebSocket 伺服器啟動在 ws://localhost:8765")
asyncio.get_event_loop().run_forever()
