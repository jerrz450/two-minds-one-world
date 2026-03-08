from config.clients import get_db, get_redis
import asyncio
import json
from agents.loop import AgentLoop

class AgentService:

    def __init__(self, agent_id) -> None:
   
        self.agent_id = agent_id                                                                                                                                                                
        self.redis = get_redis()                                                                                                                                                                
        self.inbox: asyncio.Queue = asyncio.Queue()                                                                                                                                             
        self.session_running = False                                                                                                                                                            
        self.pending_context: list[dict] = []

    async def listen_to_inbox(self):

        pubsub = self.redis.pubsub()

        pubsub.subscribe(f"agent:{self.agent_id}")

        while True:
            message = pubsub.get_message(ignore_subscribe_messages=True)

            if message:
                await self.inbox.put(message)

            await asyncio.sleep(0.01)

    async def handle_messages(self):

        while True:

            message = await self.inbox.get()

            try:
                data = json.loads(message['data'])
            
            except Exception:
                continue

            if data.get("type") == "dm":

                self.pending_context.append(data)

                if not self.session_running:
                    await self.run_session(data)

            else:

                if self.session_running:
                    self.pending_context.append(data)

                else:
                    await self.run_session(data)

    async def run_session(self, payload):
        
        self.session_running = True

        try:

            loop = AgentLoop(self.agent_id)

            if self.pending_context:
                loop.pending_context = self.pending_context

                self.pending_context = []
            
            await loop.run()

        finally:

            self.session_running = False
            cycle = payload.get("cycle", 0)

            self.redis.publish(                                                                                                                                                                 
                  f"agent:{self.agent_id}:outbox",                                                                                                                                                
                  json.dumps({"agent_id": self.agent_id, "cycle": cycle, "status": "session_done"}),                                                                                              
              )               
                                                                                                                                                                                
            print(f"[{self.agent_id}] session done, signalled outbox")                                                                                                                          

    async def start(self) -> None:       
                                                                                                                                                              
        await asyncio.gather(                                                                                                                                                                   
            self.listen_to_inbox(),                                                                                                                                                             
            self.handle_messages(),                                                                                                                                                             
          )      

if __name__ == "__main__":                                                                                                                                                                      
    
    import os

    agent_id = os.getenv("AGENT_ID", "jordan")                                                                                                                                                  
    asyncio.run(AgentService(agent_id).start())