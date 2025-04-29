import requests
import logging
from typing import Optional, Dict, Any


class HttpRequestService:
    """
    A service for sending HTTP(S) requests.
    Supports GET, POST, PUT, DELETE methods with configurable headers, data, and timeout.
    """

    def __init__(self, base_url: str, timeout: float = 5.0, verify_ssl: bool = True):
        """
        Initialize the HTTP request service.

        :param base_url: The base URL for the API or server
        :param timeout: Request timeout in seconds (default: 5.0)
        :param verify_ssl: Whether to verify SSL certificates (default: True)
        """
        self.base_url = base_url.rstrip("/")  # Ensure no trailing slash
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.session = requests.Session()  # Reuse session for efficiency

        logging.info(f"HttpRequestService initialized for {self.base_url}")

    def _send_request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """
        Private method to send an HTTP request.

        :param method: HTTP method (GET, POST, PUT, DELETE)
        :param endpoint: API endpoint (e.g., "/users")
        :param kwargs: Additional parameters for the request (headers, data, etc.)
        :return: Response object if successful, None if failed
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                verify=self.verify_ssl,
                **kwargs
            )
            response.raise_for_status()  # Raise an error for 4xx & 5xx status codes
            logging.info(f"{method} request to {url} succeeded with status {response.status_code}")
            return response
        except requests.exceptions.RequestException as e:
            logging.error(f"{method} request to {url} failed: {e}")
            return None

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Optional[requests.Response]:
        """Send a GET request."""
        return self._send_request("GET", endpoint, params=params, headers=headers)

    def post(self, endpoint: str, data: Optional[Any] = None, json: Optional[Any] = None, headers: Optional[Dict[str, str]] = None) -> Optional[requests.Response]:
        """Send a POST request."""
        return self._send_request("POST", endpoint, data=data, json=json, headers=headers)

    def put(self, endpoint: str, data: Optional[Any] = None, json: Optional[Any] = None, headers: Optional[Dict[str, str]] = None) -> Optional[requests.Response]:
        """Send a PUT request."""
        return self._send_request("PUT", endpoint, data=data, json=json, headers=headers)

    def delete(self, endpoint: str, headers: Optional[Dict[str, str]] = None) -> Optional[requests.Response]:
        """Send a DELETE request."""
        return self._send_request("DELETE", endpoint, headers=headers)

    def close(self):
        """Close the session to release resources."""
        self.session.close()
        logging.info("HttpRequestService session closed.")

    def __enter__(self):
        """Enable `with` statement support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure session is closed after use."""
        self.close()
