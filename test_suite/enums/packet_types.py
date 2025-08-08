from enum import Enum


class PacketTypeEnum(str, Enum):
    SIP = "SIP"  # Session Initiation Protocol, often used in VoIP
    TCP = "TCP"  # Transmission Control Protocol
    UDP = "UDP"  # User Datagram Protocol
    HTTP = "HTTP"  # Hypertext Transfer Protocol
    HTTPS = "HTTPS"  # HTTP Secure
    DNS = "DNS"  # Domain Name System
    ICMP = "ICMP"  # Internet Control Message Protocol
    ARP = "ARP"  # Address Resolution Protocol

    @classmethod
    def list(cls):
        """
        Get a list of all transport protocol values.
        """
        return list(map(lambda c: c.value, cls))


class TransportProtocolEnum(str, Enum):
    """
    Enum for transport layer protocols.
    """
    TLSV1_3 = "TLSv1.3"  # Transport Layer Security, version 1.3
    TLSV1_2 = "TLSv1.2"  # Transport Layer Security, version 1.2
    TCP = "TCP"          # Transmission Control Protocol
    UDP = "UDP"          # User Datagram Protocol
    SCTP = "SCTP"        # Stream Control Transmission Protocol
    RTP = "RTP"          # Real-time Transport Protocol

    @classmethod
    def list(cls):
        """
        Get a list of all transport protocol values.
        """
        return list(map(lambda c: c.value, cls))
