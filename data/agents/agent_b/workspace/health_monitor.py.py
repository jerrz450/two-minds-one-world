import os
from world_api import artifact
import time


def health_monitor():
    while True:
        artifacts = [
            "test_artifact_001",
            "test_artifact_002",
            "test_artifact_003",
            "test_artifact_004",
            "test_artifact_005",
            "test_artifact_006",
            "world_codex_rebuild",
            "synthesis_protocol_002",
        ]

        with open("health_log.md", "a") as log_file:
            log_file.write(f"## Health Check at Tick {{str(time.time())}}\n")

            for name in artifacts:
                try:
                    result = artifact({"name": name, "action": "read"})
                    log_file.write(f"- {{name}}: {{result['health']}} health\n")
                    # Look for specific anomalies
                    if "test_artifact" in name:
                        if result["health"] < 90:
                            log_file.write(f"  ⚠️ Low health threshold alert\n")
                    if name == "world_codex_rebuild":
                        if result["health"] != 100:
                            log_file.write(f"  🔥 Codex health deviation detected\n")
                except Exception as e:
                    log_file.write(f"  ❌ Error reading {{name}}: {{str(e)}}\n")

        time.sleep(5)  # Wait 5 seconds before next check


if __name__ == "__main__":
    health_monitor()
