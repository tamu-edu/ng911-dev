import socket
import threading
import time
import os
import random  # nosec B311
import struct
import logging
import wave
import audioop


class RTPTransport:
    """
    Minimal RTP transport: bind UDP socket, receive packets via callback,
    send raw payloads, and optionally generate a dummy RTP stream.
    """

    def __init__(self, bind, log: logging.Logger | None = None):
        """
        bind: (ip, port)
        """
        self.bind = bind
        self.log = log or logging.getLogger("RTP")
        self.sock: socket.socket | None = None
        self._stop = threading.Event()
        self._rx_cb = None
        self._rx_thread: threading.Thread | None = None

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Reuse addr helps quick restarts in tests
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception as e:
            if self.log:
                self.log.error(e)
            else:
                print(e)

        self.sock.bind(self.bind)
        if self.log:
            self.log.info("RTP bound at %s:%s", *self.sock.getsockname())
        else:
            print(f"RTP not bound -> {self.sock.getsockname()}")

    def stop(self):
        self._stop.set()
        try:
            if self.sock:
                self.sock.close()
        except Exception as e:
            if self.log:
                self.log.debug(e)
        if self.log:
            self.log.info("RTP transport stopped.")

    def send_raw(self, payload: bytes, remote):
        if not self.sock:
            raise RuntimeError("RTP socket is not started.")
        self.sock.sendto(payload, remote)

    def recv_loop(self, cb, timeout=0.2):
        """
        Start background receive loop and call cb(data, addr) for each packet.
        """
        self._rx_cb = cb

        def _loop():
            while not self._stop.is_set():
                try:
                    self.sock.settimeout(timeout)
                    data, addr = self.sock.recvfrom(2048)
                except Exception as e:
                    self.log.debug(e)
                    continue
                if self._rx_cb:
                    try:
                        cb(data, addr)
                    except Exception as e:
                        self.log.debug(e)

        self._rx_thread = threading.Thread(target=_loop, daemon=True)
        self._rx_thread.start()

    def send_dummy_stream(
        self, remote, duration_sec: float = 2.0, interval_sec: float = 0.02
    ):
        """
        Generate simple RTP packets (no audio encoding) for Wireshark-visible media.
        - Payload type 0 (PCMU), 160 samples per packet @ 8kHz for 20ms frame.
        """
        if not self.sock:
            raise RuntimeError("RTP socket is not started.")
        ssrc = os.getpid() & 0xFFFFFFFF
        seq = random.randint(0, 65535)
        timestamp = random.randint(0, 0xFFFFFFFF)
        end = time.time() + duration_sec
        payload = b"\x7f" * 160  # 160 bytes dummy payload

        while time.time() < end and not self._stop.is_set():
            seq = (seq + 1) & 0xFFFF
            timestamp = (timestamp + 160) & 0xFFFFFFFF  # 160 samples per packet
            # RTP header: V=2,P=0,X=0,CC=0 | M=0, PT=0 | seq | timestamp | ssrc
            header = struct.pack(">BBHII", 0x80, 0x60, seq, timestamp, ssrc)
            try:
                self.sock.sendto(header + payload, remote)
            except Exception as e:
                self.log.debug(e)
                break
            time.sleep(interval_sec)


class RTPProxyTransport:
    """
    RTP proxy
    """

    def __init__(
        self,
        bind_ip,
        bind_port,
        dst_ip,
        dst_port,
        src_ip_filter: str = "",
        log: logging.Logger | None = None,
    ):
        # bind на proxy_ip:proxy_port
        self.bind = (bind_ip, int(bind_port))
        self.dst = (dst_ip, int(dst_port))
        self.src_ip_filter = src_ip_filter.strip() if src_ip_filter else ""
        self.log = log or logging.getLogger("RTPProxy")

        self.sock: socket.socket | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception as e:
            self.log.debug(e)

        self.sock.bind(self.bind)
        if self.log:
            self.log.info(
                "RTP proxy bound at %s:%s → %s:%s", *self.sock.getsockname(), *self.dst
            )

        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        while not self._stop.is_set():
            try:
                self.sock.settimeout(0.2)
                data, addr = self.sock.recvfrom(2048)
            except Exception as e:
                self.log.debug(e)
                continue

            if self.src_ip_filter:
                if addr[0] != self.src_ip_filter:
                    continue

            try:
                self.sock.sendto(data, self.dst)
            except Exception as e:
                if self.log:
                    self.log.debug(f"RTP proxy send error {e}", exc_info=True)

    def stop(self):
        self._stop.set()
        try:
            if self.sock:
                self.sock.close()
        except Exception as e:
            if self.log:
                self.log.debug(e)
        if self.log:
            self.log.info("RTP proxy stopped.")


# TODO MAY BE DEPRECATED
class RTPTextSender:
    """
    TO BE DEPRECATED
    RFC 4103 (RTP Payload for Text Conversation) minimal sender.
    Sends text as RTP packets (t140-like).
    """

    def __init__(self, log: logging.Logger | None = None):
        self.log = log or logging.getLogger("RTPText")

    def send_text(
        self,
        dst_ip: str,
        dst_port: int,
        text: str,
        payload_type: int = 98,
    ):
        """
        Send a single RTP packet with text payload.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        ssrc = os.getpid() & 0xFFFFFFFF
        seq = random.randint(0, 65535)
        timestamp = random.randint(0, 0xFFFFFFFF)

        payload = text.encode("utf-8")

        # RTP header:
        # V=2, P=0, X=0, CC=0
        # M=0, PT=dynamic (default 98 for text)
        header = struct.pack(
            ">BBHII",
            0x80,
            payload_type & 0x7F,
            seq,
            timestamp,
            ssrc,
        )

        try:
            sock.sendto(header + payload, (dst_ip, int(dst_port)))
            if self.log:
                self.log.info(
                    "RTP text sent to %s:%s payload_type=%s text=%r",
                    dst_ip,
                    dst_port,
                    payload_type,
                    text,
                )
        finally:
            sock.close()


class RTPTextStream:
    """
    RFC 4103 / RTT-like RTP text sender
    with SSRC and CSRC support.

    Guarantees:
      - Sequence Number increments by +1
      - Timestamp increments by +ts_step
      - Stable SSRC
      - Optional CSRC list
    """

    def __init__(
        self,
        src_ip: str,
        src_port: int,
        dst_ip: str,
        dst_port: int,
        payload_type: int = 98,
        ts_step: int = 20,
        ssrc: int | None = None,
        csrc_list: list[int] | None = None,
        log: logging.Logger | None = None,
    ):
        self.src_ip = src_ip
        self.src_port = int(src_port)
        self.dst = (dst_ip, int(dst_port))
        self.payload_type = int(payload_type)
        self.ts_step = int(ts_step)
        self.log = log or logging.getLogger("RTPTextStream")

        self.sock: socket.socket | None = None

        self.ssrc = ssrc if ssrc is not None else (os.getpid() & 0xFFFFFFFF)
        self.csrc_list = csrc_list or []

        if len(self.csrc_list) > 15:
            raise ValueError("RTP supports a maximum of 15 CSRC identifiers")

        self.seq = random.randint(0, 65535)
        self.timestamp = random.randint(0, 0xFFFFFFFF)

    def start(self):
        if self.sock:
            return

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception as e:
            self.log.debug(e)

        self.sock.bind((self.src_ip, self.src_port))
        actual = self.sock.getsockname()

        if self.log:
            self.log.info(
                "RTP RTT stream bound at %s:%s → %s:%s (pt=%s ts_step=%s ssrc=%s csrc=%s)",
                actual[0],
                actual[1],
                self.dst[0],
                self.dst[1],
                self.payload_type,
                self.ts_step,
                self.ssrc,
                self.csrc_list,
            )

    def stop(self):
        try:
            if self.sock:
                self.sock.close()
        except Exception as e:
            self.log.debug(e)
        self.sock = None

    def send_text_packet(self, text: str):
        if not self.sock:
            self.start()

        payload = (text or "").encode("utf-8")

        cc = len(self.csrc_list)
        b0 = 0x80 | cc  # V=2, CC=CSRC count
        b1 = self.payload_type & 0x7F

        header = struct.pack(
            ">BBHII",
            b0,
            b1,
            self.seq,
            self.timestamp,
            self.ssrc,
        )

        csrc_bytes = b"".join(struct.pack(">I", csrc) for csrc in self.csrc_list)

        try:
            if self.sock:
                self.sock.sendto(header + csrc_bytes + payload, self.dst)
        finally:
            self.seq = (self.seq + 1) & 0xFFFF
            self.timestamp = (self.timestamp + self.ts_step) & 0xFFFFFFFF

        if self.log:
            self.log.debug(
                "RTP RTT TX → %s:%s seq=%s ts=%s ssrc=%s csrc=%s text=%r",
                self.dst[0],
                self.dst[1],
                (self.seq - 1) & 0xFFFF,
                (self.timestamp - self.ts_step) & 0xFFFFFFFF,
                self.ssrc,
                self.csrc_list,
                text,
            )


class RTPAudioStream:
    """
    RTP audio sender for:
      - G.711 PCMU (payload type 0)
      - G.711 PCMA (payload type 8)

    WAV requirements:
      - PCM
      - mono
      - 8000 Hz
    """

    def __init__(
        self,
        src_ip: str,
        src_port: int,
        dst_ip: str,
        dst_port: int,
        audio_file: str,
        codec: str = "pcmu",
        payload_type: int | None = None,
        clock_rate: int = 8000,
        ptime: int = 20,
        ssrc: int | None = None,
        log: logging.Logger | None = None,
    ):
        self.src = (src_ip, int(src_port))
        self.dst = (dst_ip, int(dst_port))
        self.audio_file = audio_file
        self.codec = codec.lower()
        self.clock_rate = int(clock_rate)
        self.ptime = int(ptime)
        self.log = log or logging.getLogger("RTPAudio")

        if self.codec not in ("pcmu", "pcma"):
            raise ValueError("Unsupported codec (pcmu or pcma only)")

        self.payload_type = (
            payload_type
            if payload_type is not None
            else (0 if self.codec == "pcmu" else 8)
        )

        self.ssrc = ssrc if ssrc is not None else (os.getpid() & 0xFFFFFFFF)
        self.seq = random.randint(0, 65535)
        self.timestamp = random.randint(0, 0xFFFFFFFF)

        self.sock: socket.socket | None = None

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(self.src)

        if self.log:
            self.log.info(
                "RTP audio bound at %s:%s → %s:%s codec=%s pt=%s",
                self.src[0],
                self.src[1],
                self.dst[0],
                self.dst[1],
                self.codec,
                self.payload_type,
            )

    def stop(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    def play(self):
        if not self.sock:
            self.start()

        wf = wave.open(self.audio_file, "rb")

        if wf.getnchannels() != 1:
            raise ValueError("WAV must be mono")
        if wf.getframerate() != self.clock_rate:
            raise ValueError("WAV sample rate must match clock_rate")

        sample_width = wf.getsampwidth()
        samples_per_packet = int(self.clock_rate * self.ptime / 1000)

        while True:
            pcm = wf.readframes(samples_per_packet)
            if not pcm:
                break

            if self.codec == "pcmu":
                payload = audioop.lin2ulaw(pcm, sample_width)
            else:
                payload = audioop.lin2alaw(pcm, sample_width)

            header = struct.pack(
                ">BBHII",
                0x80,
                self.payload_type & 0x7F,
                self.seq,
                self.timestamp,
                self.ssrc,
            )

            self.sock.sendto(header + payload, self.dst)

            self.seq = (self.seq + 1) & 0xFFFF
            self.timestamp = (self.timestamp + samples_per_packet) & 0xFFFFFFFF

            time.sleep(self.ptime / 1000.0)

        wf.close()
