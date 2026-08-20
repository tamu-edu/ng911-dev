from proxy_server.http.app import run as run_app
from test_suite.services.cleanup_registry import run_cleanup


def run_management_server(host: str = "0.0.0.0", port: int = 8000):
    try:
        run_app(host=host, port=port)
    finally:
        run_cleanup()
