import re
from typing import Tuple, Optional

_C_RE = re.compile(r"(?im)^\s*c=\s*IN\s+IP4?\s+([0-9\.A-Fa-f:]+)\s*$")
_M_RE = re.compile(r"(?im)^\s*m=\s*audio\s+(\d+)\s+(\S+)\s+(.+)$")


def parse_sdp_connection_and_audio_port(sdp_text: str) -> Tuple[Optional[str], Optional[int]]:
    """
    Returns (ip, port) for RTP from SDP offer/answer.
    - If 'c=' is absent at session-level, many stacks rely on per-media 'c='.
      Here we only read session-level 'c=' for simplicity, which is common enough.
    - Returns (None, None) if cannot parse.
    """
    if not sdp_text:
        return None, None

    ip = None
    m_port = None

    # session-level c= line
    m = _C_RE.search(sdp_text)
    if m:
        ip = m.group(1).strip()

    # audio m= line
    m2 = _M_RE.search(sdp_text)
    if m2:
        try:
            m_port = int(m2.group(1))
        except Exception:
            m_port = None

    return ip, m_port