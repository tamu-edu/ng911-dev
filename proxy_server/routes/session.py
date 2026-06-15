from fastapi import APIRouter, HTTPException

from proxy_server.models.session_models import (
    StartSessionRequest,
    SessionRequest,
)
from proxy_server.services.session_service import SessionService
from proxy_server.state.session_state import SessionState

router = APIRouter()
_state = SessionState()
_service = SessionService(_state)


# =========================
# START SESSION
# =========================


@router.post("/session/start", status_code=201)
def start_session(request: StartSessionRequest):
    try:
        _service.start_session(request)
        return {"status": "RUNNING"}

    except RuntimeError:
        raise HTTPException(status_code=409, detail="Session already active")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# STATUS
# =========================


@router.post("/session/status")
def get_status(request: SessionRequest):
    try:
        return _service.get_status(request.session_id)

    except ValueError:
        raise HTTPException(status_code=404, detail="No active session")

    except PermissionError:
        raise HTTPException(status_code=409, detail="Invalid session_id")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# STOP
# =========================


@router.post("/session/stop")
def stop_session(request: SessionRequest):
    try:
        _service.stop_session(request.session_id)
        return {"status": "STOPPING"}

    except ValueError:
        raise HTTPException(status_code=404, detail="No active session")

    except PermissionError:
        raise HTTPException(status_code=409, detail="Invalid session_id")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# RESET
# =========================


@router.post("/session/reset")
def reset_session(request: SessionRequest):
    try:
        _service.reset_session(request.session_id)
        return {"status": "RESETTING"}

    except ValueError:
        raise HTTPException(status_code=404, detail="No active session")

    except PermissionError:
        raise HTTPException(status_code=409, detail="Invalid session_id")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
