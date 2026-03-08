import json
from datetime import datetime
from psycopg2.extras import RealDictCursor
from config.clients import get_db, get_redis
from config.settings import AGENT_IDS                                                                                                                                                                   

class Orchestrator:

    def __init__(self) -> None:
        self.redis = get_redis()

    def get_current_cycle(self) -> int:

        with get_db() as conn:

            with conn.cursor() as cur:
                cur.execute("SELECT cycle_number FROM world_cycles ORDER BY cycle_number DESC LIMIT 1")
                row = cur.fetchone()
                return row[0] if row else 0

    def get_agent_last_run(self, agent_id: str) -> datetime | None:

        with get_db() as conn:

            with conn.cursor() as cur:
                cur.execute("SELECT MAX(created_at) FROM events WHERE agent_id = %s", (agent_id,))
                row = cur.fetchone()
                return row[0] if row else None


    def get_pending_dms(self, agent_id: str) -> list[dict]:

        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT from_agent_id, content, created_at
                    FROM direct_messages
                    WHERE to_agent_id = %s AND read = FALSE
                    ORDER BY created_at ASC
                    """,
                    (agent_id,),
                )

                return [dict(r) for r in cur.fetchall()]

    def get_board_activity(self, since: datetime) -> list[dict]:

        with get_db() as conn:

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT agent_id, channel, content, created_at
                    FROM board_posts
                    WHERE created_at > %s
                    ORDER BY created_at ASC
                    """,
                    (since,),
                )
                return [dict(r) for r in cur.fetchall()]

    def get_world_events(self, since: datetime) -> list[dict]:

        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT event_type, description, affected_agent, payload, created_at
                    FROM world_events
                    WHERE created_at > %s
                    ORDER BY created_at ASC
                    """,
                    (since,),
                )

                return [dict(r) for r in cur.fetchall()]

    def build_agent_payload(self, agent_id: str) -> dict:                                                                                                                                                     
        
        since = self.get_agent_last_run(agent_id) or datetime(2025, 1, 1)                                                                                                                              

        return {                                                                                                                                                                                        
            "cycle": self.get_current_cycle(),
            "pending_dms": self.get_pending_dms(agent_id),
            "board_activity": self.get_board_activity(since),
            "world_events": self.get_world_events(since),
        }

    def listen_messages(self) -> None:

        r = self.redis
        pubsub = r.pubsub()
        pubsub.subscribe("messages:outbox")

        print("[orchestrator] listening on messages:outbox")

        for message in pubsub.listen():
            
            if message["type"] != "message":
                continue

            data = json.loads(message["data"])
            to = data.get("to")

            if to:
                r.publish(f"agent:{to}", json.dumps(data))
                print(f"[orchestrator] forwarded message to agent:{to}")

    def run_cycle(self) -> None:

        r = self.redis
        cycle = self.get_current_cycle()

        print(f"[orchestrator] run_cycle cycle={cycle}")

        for agent_id in AGENT_IDS:

            payload = self.build_agent_payload(agent_id)
            r.publish(f"agent:{agent_id}", json.dumps(payload, default=str))

            print(f"[orchestrator] published start_session to {agent_id}")

if __name__ == "__main__":
    Orchestrator().listen_messages()
