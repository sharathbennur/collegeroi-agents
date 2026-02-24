import asyncio
import httpx
import sys

async def main():
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # 1. Create thread
        print("Creating thread...", flush=True)
        try:
            res = await client.post(f"{base_url}/chat/threads")
            if res.status_code != 200:
                print(f"Error ({res.status_code}): {res.text}")
                return
            thread_id = res.json()["thread_id"]
            print(f"Created thread: {thread_id}", flush=True)
        except Exception as e:
            print(f"Failed HTTP POST: {e}")
            return
            
        # 2. Stream 
        url = f"{base_url}/chat/threads/{thread_id}/runs/stream"
        payload = {
            "input": {
                "messages": [{"role": "user", "content": "I want to apply to NYU. What are the costs?"}]
            },
            "stream_mode": ["messages-tuple", "values"]
        }
        
        print(f"\\nConnecting to stream endpoint...", flush=True)
        try:
            async with client.stream("POST", url, json=payload, timeout=60.0) as response:
                print(f"Connected. Status: {response.status_code}\\n", flush=True)
                async for chunk in response.aiter_text():
                    print(chunk, end="", flush=True)
                    
        except Exception as e:
            print(f"Failed HTTP STREAM: {e}")

if __name__ == "__main__":
    asyncio.run(main())
