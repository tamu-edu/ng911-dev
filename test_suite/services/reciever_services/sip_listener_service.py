from twisted.internet.protocol import DatagramProtocol, Protocol, Factory
from twisted.internet import reactor
from twisted.protocols.sip import Base, Response


class SIPUDPProtocol(Base, DatagramProtocol):
    def __init__(self, parent):
        self.parent = parent
        super().__init__()

    def datagramReceived(self, data, addr):
        """
        Handles the incoming UDP datagram and processes it as a SIP message.
        :param data: The raw data received.
        :param addr: The address from where the datagram was received.
        """
        try:
            message = self.parent.parse_request(data)
            self.parent.handle_request(message, addr, 'UDP', self)
        except Exception as e:
            print(f"Error parsing request via UDP: {e}")

    def send_response(self, code, reason, addr):
        """
        Sends a SIP response over UDP.
        :param code: Response code (e.g., 200 for OK).
        :param reason: Response reason (e.g., "OK" or "Method Not Allowed").
        :param addr: The address to send the response to.
        """
        response = Response(code, reason)
        response_string = response.toString().encode()
        self.transport.write(response_string, addr)


class SIPTCPProtocol(Base, Protocol):
    def __init__(self, parent):
        self.parent = parent
        super().__init__()

    def dataReceived(self, data):
        """
        Handles incoming TCP data, processes it as a SIP message.
        """
        addr = self.transport.getPeer()  # Get the client's address
        try:
            message = self.parent.parse_request(data)
            self.parent.handle_request(message, addr, 'TCP', self)
        except Exception as e:
            print(f"Error parsing request via TCP: {e}")

    def send_response(self, code, reason, addr):
        """
        Sends a SIP response over TCP.
        :param code: Response code (e.g., 200 for OK).
        :param reason: Response reason (e.g., "OK" or "Method Not Allowed").
        """
        response = Response(code, reason)
        response_string = response.toString().encode()
        print(f"Sending response to {addr}: {response_string}")
        self.transport.write(response_string)


class SIPListener:
    def __init__(self, port=5060):
        """
        Initializes the SIPListener on the specified port.
        :param port: UDP and TCP port to listen for SIP messages (default is 5060).
        """
        self.port = port
        print(f"SIPListener initialized on port {self.port}")

    def start(self):
        """
        Starts the SIPListener service for both UDP and TCP.
        """
        reactor.listenUDP(self.port, SIPUDPProtocol(self))  # UDP Listener
        reactor.listenTCP(self.port, SIPFactory(self))  # TCP Listener
        print(f"SIPListener running on UDP and TCP port {self.port}")
        reactor.run()

    def stop(self):
        """
        Stops the SIPListener service.
        """
        reactor.stop()
        print("SIPListener stopped")

    def handle_request(self, message, addr, protocol, transport_protocol):
        """
        Handles the incoming SIP request.
        :param message: The parsed SIP message as a dictionary.
        :param addr: The address from where the SIP message was received.
        :param protocol: The protocol used ('UDP' or 'TCP').
        :param transport_protocol: The protocol instance (either UDP or TCP).
        """
        print(f"Received {message['method']} request from {addr} via {protocol}")
        if message['method'] == 'INVITE':
            transport_protocol.send_response(200, b"OK", addr)
        else:
            transport_protocol.send_response(405, b"Method Not Allowed", addr)

    def parse_request(self, data):
        """
        Parses the raw SIP message and returns it as a structured dictionary.
        :param data: Raw SIP message data in bytes.
        :return: Parsed SIP message as a dictionary.
        """
        lines = data.decode('utf-8').split('\r\n')
        request_line = lines[0].split(' ')
        headers = {}
        for line in lines[1:]:
            if line:
                header_name, header_value = line.split(':', 1)
                headers[header_name.strip()] = header_value.strip()
        return {
            'method': request_line[0],
            'uri': request_line[1],
            'version': request_line[2],
            **headers
        }


class SIPFactory(Factory):
    def __init__(self, parent):
        self.parent = parent

    def buildProtocol(self, addr):
        """
        Builds the TCP protocol instance when a new connection is made.
        """
        return SIPTCPProtocol(self.parent)
