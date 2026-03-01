from config.clients import get_openai
import asyncio
import requests
from executor.models import ExecRequest

async def test():

    response = await get_openai().chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "user", "content": "Please generate a python code for a from scratch transformer, just code no text."}
        ],
    )

    content = response.choices[0].message.content or ""

    params = ExecRequest(code= content, agent_id= "agent_a", name = "test")
    print(content)
    response =requests.post(url = "http://localhost:8080/execute", json= params.model_dump())
    
    print(response.json())

asyncio.run(test())

