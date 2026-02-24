import asyncio
from langchain_core.messages import HumanMessage
from src.orchestrator import get_async_orchestrator_graph

async def test_streaming():
    async with get_async_orchestrator_graph("test_stream.sqlite") as graph:
        config = {"configurable": {"thread_id": "test_streaming_2"}}
        inputs = {"messages": [HumanMessage(content="Hello! I want to calculate my college ROI.")]}
        
        print("Streaming messages...", flush=True)
        async for msg, metadata in graph.astream(inputs, config=config, stream_mode="messages"):
            if msg.content:
                print(msg.content, end="", flush=True)
        print("\n\nDone.")

if __name__ == "__main__":
    asyncio.run(test_streaming())
