import requests


class MSClientError(Exception):

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class MSClient:
    def __init__(self, base_url: str, timeout: int = 5):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()

    def _post(self, path: str, json: dict) -> requests.Response:
        try:
            resp = self._session.post(
                f"{self._base_url}{path}",
                json=json,
                timeout=self._timeout,
            )
        except requests.RequestException as e:
            raise MSClientError(f"Network error: {e}") from e

        return resp

    @staticmethod
    def _handle_response(resp: requests.Response, expected: list[int]) -> dict | None:
        if resp.status_code in expected:
            if resp.content:
                return resp.json()
            return None

        if resp.status_code == 409:
            raise MSClientError("Conflict (busy or wrong session_id)", 409)

        if resp.status_code == 404:
            raise MSClientError("Not found / invalid state", 404)

        if resp.status_code == 400:
            raise MSClientError(f"Bad request: {resp.text}", 400)

        if resp.status_code >= 500:
            raise MSClientError(f"Server error: {resp.text}", 500)

        raise MSClientError(f"Unexpected response {resp.text}", resp.status_code)

    def start_session(self, session_id: str, config: dict) -> None:
        resp = self._post(
            "/session/start",
            {"session_id": session_id, "config": config},
        )
        self._handle_response(resp, [201])

    def get_status(self, session_id: str):
        resp = self._post(
            "/session/status",
            {"session_id": session_id},
        )
        data = self._handle_response(resp, [200])
        return data

    def stop_session(self, session_id: str) -> None:
        resp = self._post(
            "/session/stop",
            {"session_id": session_id},
        )
        self._handle_response(resp, [200])

    def reset_session(self, session_id: str) -> None:
        resp = self._post(
            "/session/reset",
            {"session_id": session_id},
        )
        self._handle_response(resp, [200])

    def download_artifact(self, artifact_path: str, dst_path: str) -> None:
        url = f"{self._base_url}{artifact_path}"

        try:
            with self._session.get(url, stream=True, timeout=self._timeout) as resp:
                if resp.status_code != 200:
                    raise MSClientError(
                        f"Failed to download artifact: {resp.status_code}"
                    )

                with open(dst_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

        except requests.RequestException as e:
            raise MSClientError(f"Download error: {e}") from e
