from proxy_server.http.app import run as run_app


def run_management_server(host: str = "0.0.0.0", port: int = 8000):
    run_app(host=host, port=port)
