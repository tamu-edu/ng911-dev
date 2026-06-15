from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import os

from proxy_server.routes.session import router as session_router

ARTIFACT_ROOT = "/tmp/psm"


def create_app() -> FastAPI:
    app = FastAPI(title="Proxy Server Management")

    # register routes
    app.include_router(session_router)

    # register artifact endpoint
    @app.get("/artifact/{file_path:path}")
    def get_artifact(file_path: str):
        """
        Serves artifact files.

        Example:
        /artifact/pcap/session_123.pcap
        """

        full_path = os.path.join(ARTIFACT_ROOT, file_path)
        print(full_path)

        # security check: prevent path traversal
        if not os.path.abspath(full_path).startswith(os.path.abspath(ARTIFACT_ROOT)):
            raise HTTPException(status_code=403, detail="Forbidden")

        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(full_path)

    return app


def run(host: str = "0.0.0.0", port: int = 8000):
    """
    Entry point used by main.py
    """

    import uvicorn

    uvicorn.run(
        "proxy_server.http.app:create_app",
        host=host,
        port=port,
        reload=False,
        factory=True,
    )
