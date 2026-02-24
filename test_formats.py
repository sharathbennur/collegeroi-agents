import asyncio
import json
from langchain_core.messages import HumanMessage
from src.orchestrator import get_async_orchestrator_graph
import uuid

async def test_streaming_formats():
    print("Testing LangGraph stream modes mapping")
    
    async with get_async_orchestrator_graph("test_stream.sqlite") as graph:
        config = {"configurable": {"thread_id": "test_mapping_1"}}
        inputs = {"messages": [HumanMessage(content="Hello! Can you help me find tuition costs?")]}
        
        async for chunk_type, chunk_data in graph.astream(inputs, config=config, stream_mode=["messages-tuple", "values"]):
            if chunk_type == "messages-tuple":
                message_obj, metadata = chunk_data
                chunk_payload = {
                    "event": "messages-tuple",
                    "data": [
                        {
                            "content": message_obj.content,
                            "id": getattr(message_obj, "id", str(uuid.uuid4())),
                            "type": getattr(message_obj, "type", "ai"),
                            "response_metadata": getattr(message_obj, "response_metadata", {})
                        },
                        metadata
                    ]
                }
            
            elif chunk_type == "values":
                data_messages = []
                if "messages" in chunk_data:
                    for m in chunk_data["messages"]:
                        data_messages.append({
                            "content": m.content,
                            "id": getattr(m, "id", str(uuid.uuid4())),
                            "type": getattr(m, "type", "human" if m.type == "human" else "ai")
                        })
                
                # Try creating the payload dict without unpacking chunk_data directly, 
                # because chunk_data might have complex state values not serializable
                state_copy = {}
                for k, v in chunk_data.items():
                    if k != "messages":
                        state_copy[k] = v
                
                chunk_payload = {
                    "event": "values",
                    "data": {
                        **state_copy,
                        "messages": data_messages
                    }
                }
                
            try:
                json_str = json.dumps(chunk_payload['data'])
                print(f"event: {chunk_payload['event']}\\ndata: {json_str}\\n\\n")
            except Exception as e:
                print(f"FAILED TO SERIALIZE {chunk_type}: {e}")
                print(f"DATA: {chunk_payload['data']}")

if __name__ == "__main__":
    asyncio.run(test_streaming_formats())
