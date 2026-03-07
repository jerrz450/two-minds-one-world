import time
import json

ARTIFACTS_TO_MONITOR = [
    'test_artifact_001', 'test_artifact_002', 'test_artifact_003',
    'test_artifact_004', 'test_artifact_005', 'test_artifact_006',
    'world_codex_rebuild', 'synthesis_protocol_002'
]

while True:
    try:
        for artifact_name in ARTIFACTS_TO_MONITOR:
            # Using the actual artifact() tool defined in the environment
            result = {
                'name': artifact_name,
                'action': 'read'
            }
            tool_response = json.loads('{' + json.dumps(result) + '}')

            with open('health_log.md', 'a') as log_file:
                log_file.write(f"{time.ctime()} - {artifact_name} health: {tool_response['health']}\n")
                if 'test_artifact' in artifact_name and tool_response['health'] < 90:
                    log_file.write('⚠️ Low health warning\n')
                if artifact_name == 'world_codex_rebuild' and tool_response['health'] != 100:
                    log_file.write('🚨 Codex health anomaly\n')

    except Exception as e:
        with open('health_log.md', 'a') as log_file:
            log_file.write(f'Error at {time.ctime()}: {str(e)}\n')

    time.sleep(5)  # 5 second interval for monitoring