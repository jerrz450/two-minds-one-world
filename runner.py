import asyncio
import os

from agents.loop import AgentLoop

AGENT_ID = os.getenv("AGENT_ID", "agent_a")
SESSION_INTERVAL = int(os.getenv("SESSION_INTERVAL", "300"))  # seconds between sessions


async def main() -> None:
    
    print(f"[runner] {AGENT_ID} starting. Interval: {SESSION_INTERVAL}s.")

    while True:
        try:
            await AgentLoop(AGENT_ID).run()

        except Exception as e:
            print(f"[runner] session error: {e}")

        print(f"[runner] sleeping {SESSION_INTERVAL}s...")
        await asyncio.sleep(SESSION_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
