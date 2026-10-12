from __future__ import annotations

import logging

from msrp_message import (
    MSRPMessage,
    build_response,
    build_send_request,
    parse_msrp_message,
)
from msrp_transport import MSRPTransport


class MSRPSession:
    """
    High-level MSRP/MSRPS session.

    Responsibilities:

    - start passive MSRP/MSRPS listener;
    - send MSRP SEND requests;
    - receive MSRP SEND requests;
    - generate transaction responses;
    - validate request/response transaction correlation;
    - own the underlying MSRPTransport lifecycle.

    SDP interpretation and scenario policy remain outside this class.
    """

    def __init__(
        self,
        transport: MSRPTransport,
        log: logging.Logger | None = None,
    ):
        self.transport = transport

        self.log = log or logging.getLogger("MSRPSession")

        self._closed = False

    @property
    def secure(self) -> bool:
        return self.transport.secure

    @property
    def local_address(self) -> tuple[str, int]:
        return self.transport.local_address

    @property
    def connected(self) -> bool:
        return self.transport.connected

    @property
    def listening(self) -> bool:
        return self.transport.listening

    def start_listener(
        self,
        timeout: float | None = None,
    ) -> None:
        """
        Prepare the passive MSRP/MSRPS endpoint.

        This does not wait for the remote peer to connect.
        """

        self._ensure_open()

        self.transport.start_listener()

        self.transport.start_accepting(
            timeout=timeout,
        )

    def send_text(
        self,
        *,
        to_path: str,
        from_path: str,
        text: str,
        content_type: str = "text/plain",
        timeout: float = 5.0,
        expect_response: bool = True,
        expected_status: int = 200,
    ) -> MSRPMessage | None:
        """
        Send one complete MSRP SEND request.

        When expect_response is True, wait for the corresponding MSRP
        response and validate transaction ID and status code.
        """

        self._ensure_open()

        wire = build_send_request(
            to_path=to_path,
            from_path=from_path,
            text=text,
            content_type=content_type,
        )

        # Parse our own generated message so the transaction ID used for
        # correlation comes from the exact wire representation.
        request = parse_msrp_message(wire)

        self.transport.send(wire)

        self.log.info(
            "%s SEND transmitted transaction=%s body=%dB",
            "MSRPS" if self.secure else "MSRP",
            request.transaction_id,
            len(request.body),
        )

        if not expect_response:
            return None

        response = self.transport.receive(
            timeout=timeout,
        )

        if not response.is_response:
            raise RuntimeError("Expected MSRP response but received request")

        if response.transaction_id != request.transaction_id:
            raise RuntimeError(
                "MSRP transaction mismatch: "
                f"expected={request.transaction_id}, "
                f"received={response.transaction_id}"
            )

        if response.status_code != int(expected_status):
            raise RuntimeError(
                "Unexpected MSRP response status: "
                f"expected={expected_status}, "
                f"received={response.status_code}"
            )

        self.log.info(
            "%s response received transaction=%s status=%s",
            "MSRPS" if self.secure else "MSRP",
            response.transaction_id,
            response.status_code,
        )

        return response

    def receive_text(
        self,
        *,
        timeout: float = 5.0,
        expected_text: str | None = None,
        expected_to_path: str | None = None,
        expected_from_path: str | None = None,
        response_status: int = 200,
        response_comment: str = "OK",
    ) -> MSRPMessage:
        """
        Receive one MSRP SEND request and acknowledge it.

        Validation is optional so scenarios can intentionally exercise
        malformed, unexpected or negative protocol behavior.
        """

        self._ensure_open()

        request = self.transport.receive(
            timeout=timeout,
        )

        if not request.is_request:
            raise RuntimeError("Expected MSRP request but received response")

        if request.method != "SEND":
            raise RuntimeError(f"Expected MSRP SEND but received {request.method!r}")

        if expected_text is not None:
            actual_text = request.body_text()

            if actual_text != expected_text:
                raise AssertionError(
                    "MSRP text mismatch: "
                    f"expected={expected_text!r}, "
                    f"received={actual_text!r}"
                )

        if expected_to_path is not None:
            actual_to_path = request.header("to-path")

            if actual_to_path != expected_to_path:
                raise AssertionError(
                    "MSRP To-Path mismatch: "
                    f"expected={expected_to_path!r}, "
                    f"received={actual_to_path!r}"
                )

        if expected_from_path is not None:
            actual_from_path = request.header("from-path")

            if actual_from_path != expected_from_path:
                raise AssertionError(
                    "MSRP From-Path mismatch: "
                    f"expected={expected_from_path!r}, "
                    f"received={actual_from_path!r}"
                )

        self.log.info(
            "%s SEND received transaction=%s body=%dB",
            "MSRPS" if self.secure else "MSRP",
            request.transaction_id,
            len(request.body),
        )

        response = build_response(
            request=request,
            status_code=response_status,
            comment=response_comment,
        )

        self.transport.send(response)

        self.log.info(
            "%s response transmitted transaction=%s status=%s",
            "MSRPS" if self.secure else "MSRP",
            request.transaction_id,
            response_status,
        )

        return request

    def stop(self) -> None:
        """
        Idempotently close the MSRP/MSRPS session.
        """

        if self._closed:
            return

        self._closed = True

        self.transport.stop()

        self.log.info(
            "%s session stopped",
            "MSRPS" if self.secure else "MSRP",
        )

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("MSRP session is closed")
