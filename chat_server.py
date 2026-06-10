#!/usr/bin/env python3
"""WebSocket chat server for Hermes chat UI."""
import asyncio
import json
import subprocess
import sys
import os
import signal
from datetime import datetime, timezone

try:
    import websockets
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

PORT = 8082
HERMES_BIN = "hermes"
TIMEOUT = 120  # seconds for hermes to respond

async def handle_message(websocket):
    """Handle a single WebSocket connection."""
    print(f"Client connected")
    try:
        async for raw in websocket:
            try:
                data = json.loads(raw)
                text = data.get("text", "").strip()
                if not text:
                    continue

                print(f"Received: {text[:80]}...")

                # Run hermes in non-interactive mode
                proc = await asyncio.create_subprocess_exec(
                    HERMES_BIN, "-z", text,
                    "--yolo",
                    "-t", "terminal,file,web,search,skills",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=os.path.expanduser("~"),
                )

                try:
                    stdout, stderr = await asyncio.wait_for(
                        proc.communicate(), timeout=TIMEOUT
                    )
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()
                    response = "Sorry, that took too long. Try a shorter question."
                else:
                    output = stdout.decode("utf-8", errors="replace").strip()
                    err = stderr.decode("utf-8", errors="replace").strip()

                    if err and "ERROR" in err.upper():
                        print(f"Hermes stderr: {err[:200]}")
                    if output:
                        response = output
                    elif err:
                        response = f"Error: {err[:500]}"
                    else:
                        response = "No response from Hermes."

                now = datetime.now().strftime("%H:%M")
                await websocket.send(json.dumps({
                    "text": response,
                    "time": now
                }))
                print(f"Sent response ({len(response)} chars)")

            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    "text": "Invalid message format.",
                    "time": datetime.now().strftime("%H:%M")
                }))
            except Exception as e:
                print(f"Error processing message: {e}")
                await websocket.send(json.dumps({
                    "text": f"Internal error: {str(e)[:200]}",
                    "time": datetime.now().strftime("%H:%M")
                }))
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")

async def main():
    print(f"Starting chat WebSocket server on port {PORT}...")
    async with websockets.serve(handle_message, "0.0.0.0", PORT):
        print(f"Chat server running on ws://0.0.0.0:{PORT}")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
