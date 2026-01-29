import os
from sip_stub_server_service import SIPServerService

if __name__ == "__main__":
    role = os.getenv("ROLE")
    ip = os.getenv("IP")
    ports = os.getenv("PORTS")
    port = int(os.getenv("PORT"))
    scenario_file = os.getenv("SCENARIO_FILE", None)
    target_uri = os.getenv("TARGET_URI", None)

    sip_service = SIPServerService(
        ip=ip,
        port=port,
        role=role,
        scenario_file=scenario_file,
        target_uri=target_uri
    )
    sip_service.start_server()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        sip_service.stop_server()
