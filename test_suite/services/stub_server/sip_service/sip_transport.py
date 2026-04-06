import socket
import ssl
import select
from typing import Optional, Tuple


class SIPTransport:
    """
    Unified SIP transport:
      - UDP: bind and recvfrom/sendto
      - TCP/TLS: always bind+listen for inbound; optional outbound client to 'remote' (lazy connect on first send)
    """

    def __init__(
        self,
        protocol,
        bind,
        ssl_context: Optional[ssl.SSLContext] = None,
        log=None,
        remote: Optional[Tuple[str, int]] = None,
    ):
        """
        protocol: "UDP" | "TCP" | "TLS"
        bind: (ip, port) we always bind to this tuple
        remote: (ip, port) default destination for outbound sends (optional)
        """
        self.protocol = protocol.upper()
        self.bind = bind
        self.remote = remote
        self.ssl_context = ssl_context
        self.log = log

        # Sockets
        self.sock: socket.SocketType | None = (
            None  # UDP socket OR TCP/TLS listening socket
        )
        self.conn = None  # accepted server-side TCP/TLS connection (single peer)
        self.out_conn = None  # optional outbound TCP client connection to remote

    # ----------------------
    # Lifecycle
    # ----------------------
    def start(self):
        if self.protocol == "UDP":
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(self.bind)
            self.sock = s
            if self.log:
                self.log.info("UDP bound at %s:%s", *self.bind)
            return

        # TCP / TLS: ALWAYS bind + listen (server mode), regardless of 'remote'
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(self.bind)
        s.listen(5)
        self.sock = s
        if self.log:
            self.log.info("%s listening at %s:%s", self.protocol, *self.bind)

        # Do NOT connect to remote here. We will lazily connect on send() if needed.
        # This ensures listening is available immediately and avoids blocking startup.

    def stop(self):
        """Idempotent, race-safe shutdown of all sockets."""
        # Close accepted inbound connection
        try:
            conn = getattr(self, "conn", None)
            if conn is not None:
                try:
                    conn.shutdown(socket.SHUT_RDWR)
                except Exception as e:
                    self.log.debug(e)
                try:
                    conn.close()
                except Exception as e:
                    self.log.debug(e)
        finally:
            self.conn = None

        # Close outbound client connection (if any)
        try:
            out_conn = getattr(self, "out_conn", None)
            if out_conn is not None:
                try:
                    out_conn.shutdown(socket.SHUT_RDWR)
                except Exception as e:
                    self.log.debug(e)
                try:
                    out_conn.close()
                except Exception as e:
                    self.log.debug(e)
        finally:
            self.out_conn = None

        # Close listening/UDP socket
        try:
            sock = getattr(self, "sock", None)
            if sock is not None:
                try:
                    # For TCP listeners this is harmless; for UDP it simply closes.
                    sock.close()
                except Exception as e:
                    self.log.debug(e)
        finally:
            self.sock = None

    # ----------------------
    # Helpers
    # ----------------------
    def _accept_if_needed(self):
        """Accept a pending inbound TCP/TLS connection if any; non-blocking."""
        if self.protocol == "UDP" or self.sock is None:
            return
        r, _, _ = select.select([self.sock], [], [], 0)
        if not r:
            return
        conn, addr = self.sock.accept()
        if self.ssl_context and self.protocol == "TLS":
            conn = self.ssl_context.wrap_socket(conn, server_side=True)
        self.conn = conn
        if self.log:
            self.log.info("Accepted %s connection from %s", self.protocol, addr)

    def _ensure_outbound_connected(self):
        """Lazy-connect outbound TCP client to 'remote' if configured."""
        if self.remote is None:
            return
        if self.out_conn:
            return
        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        c.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind to our local bind IP with ephemeral port to preserve source IP if needed
        try:
            c.bind((self.bind[0], 0))
        except Exception as e:
            self.log.debug(e)
            # If bind fails (e.g., bind[0] not assigned), skip; OS will choose interface automatically
        c.settimeout(3.0)
        c.connect(self.remote)
        c.settimeout(None)
        # NOTE: If you need TLS client mode in future, wrap here with client-side SSL:
        # if self.protocol == "TLS" and self.ssl_context:
        #     c = self.ssl_context.wrap_socket(c, server_hostname=self.remote[0])
        self.out_conn = c
        if self.log:
            self.log.info("Outbound %s connected to %s", self.protocol, self.remote)

    # ----------------------
    # I/O
    # ----------------------
    def send(self, data: bytes, addr: Optional[Tuple[str, int]]):
        if self.protocol == "UDP":
            # Prefer explicit addr, else remote, else error
            target = addr or self.remote
            if not target:
                raise RuntimeError(
                    "UDP send: no target address provided and no remote configured"
                )
            if self.sock:
                self.sock.sendto(data, target)
            return

        # TCP / TLS:
        # Priority:
        # 1) If addr equals current accepted peer -> use self.conn
        # 2) Else if addr equals remote or addr is None -> use/establish self.out_conn
        # 3) Else fallback: if we have any connection (conn or out_conn), use it
        used = False

        if addr and self.conn:
            try:
                peer = self.conn.getpeername()
                if peer[0] == addr[0] and peer[1] == addr[1]:
                    self.conn.sendall(data)
                    used = True
            except Exception as e:
                self.log.debug(e)
                self.conn = None

        if not used:
            # When addr is remote or unspecified, try outbound path
            if (
                (addr is None and self.remote)
                or (addr and self.remote and addr == self.remote)
                or (self.remote and not self.conn)
            ):
                try:
                    self._ensure_outbound_connected()
                    if self.out_conn:
                        self.out_conn.sendall(data)
                        used = True
                except Exception as e:
                    raise RuntimeError(
                        f"TCP send: outbound connect/send to {self.remote} failed: {e}"
                    )

        if not used:
            # try sending to the addr
            if addr:
                # Try a one-off client connect to addr (does not replace listening)
                c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    c.settimeout(3.0)
                    c.connect(addr)
                    c.sendall(data)
                finally:
                    try:
                        c.close()
                    except Exception as e:
                        self.log.debug(e)
                used = True

        if not used:
            # Fallback to accepted conn if available and everything else failed
            if self.conn:
                try:
                    self.conn.sendall(data)
                    used = True
                except Exception:
                    self.conn = None

        if not used:
            raise RuntimeError(
                "TCP/TLS send: no available connection (no peer and no remote)"
            )

    def reset_listening_socket(self):
        """
        Fully restart the LISTEN socket (TCP/TLS only):
          - close accepted conn + outbound conn
          - close listening socket
          - create a new listening socket and bind/listen again

        No-op for UDP.
        """
        if self.protocol == "UDP":
            return

        # 1) Drop active conns first
        self.reset_connections()

        # 2) Close listener
        try:
            if self.sock is not None:
                try:
                    self.sock.close()
                except Exception as e:
                    self.log.debug(e)
        finally:
            self.sock = None

        # 3) Re-create listener
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(self.bind)
        s.listen(5)
        self.sock = s

        if self.log:
            self.log.info(
                "SIPTransport: listening socket restarted on %s:%s", *self.bind
            )

    def reset_connections(self):
        """
        Reset TCP/TLS connections (both inbound accepted conn and outbound client conn).
        Keeps listening socket alive.
        No-op for UDP.
        """
        if self.protocol == "UDP":
            return

        # Close accepted inbound connection
        try:
            if self.conn is not None:
                try:
                    self.conn.shutdown(socket.SHUT_RDWR)
                except Exception as e:
                    self.log.debug(e)
                try:
                    self.conn.close()
                except Exception as e:
                    self.log.debug(e)
        finally:
            self.conn = None

        # Close outbound connection (if any)
        try:
            if self.out_conn is not None:
                try:
                    self.out_conn.shutdown(socket.SHUT_RDWR)
                except Exception as e:
                    self.log.debug(e)
                try:
                    self.out_conn.close()
                except Exception as e:
                    self.log.debug(e)
        finally:
            self.out_conn = None

        if self.log:
            self.log.info("SIPTransport: connections reset (conn/out_conn closed).")

    def recv(self, timeout=0.2):
        if self.protocol == "UDP":
            self.sock.settimeout(timeout)
            try:
                data, addr = self.sock.recvfrom(65535)
                return data, addr
            except socket.timeout:
                return None, None

        # TCP / TLS:
        # Accept new inbound connection if any
        self._accept_if_needed()

        # Build readable set among accepted conn and outbound conn
        read_list = []
        src_map = {}  # map socket -> address tuple
        if self.conn:
            try:
                src_map[self.conn] = self.conn.getpeername()
                read_list.append(self.conn)
            except Exception:
                self.conn = None
        if self.out_conn:
            src_map[self.out_conn] = self.remote
            read_list.append(self.out_conn)

        if not read_list:
            # No connections yet; wait a bit for incoming accept
            r, _, _ = select.select([self.sock], [], [], timeout)
            if r:
                # accept and try one immediate read pass
                self._accept_if_needed()
                if self.conn:
                    read_list = [self.conn]
                    try:
                        src_map[self.conn] = self.conn.getpeername()
                    except Exception:
                        src_map[self.conn] = None
                else:
                    return None, None
            else:
                return None, None

        # Wait for data on any established connection
        r, _, _ = select.select(read_list, [], [], timeout)
        if not r:
            return None, None

        for s in r:
            try:
                data = s.recv(65535)
            except Exception:
                # treat as closed
                data = b""
            if not data:
                # connection closed
                if s is self.conn:
                    try:
                        self.conn.close()
                    except Exception as e:
                        self.log.debug(e)
                    self.conn = None
                if s is self.out_conn:
                    try:
                        self.out_conn.close()
                    except Exception as e:
                        self.log.debug(e)
                    self.out_conn = None
                continue
            # Return first readable packet
            return data, src_map.get(s) or self.remote

        return None, None
