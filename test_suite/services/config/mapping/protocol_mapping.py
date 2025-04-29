protocol_map = {
    "HTTP": "tcp",
    "HTTPS": "tcp",
    "TLS": "tcp",
    "TLSv1.2": "tcp",
    "TLSv1.3": "tcp",
    "SIP": "udp",  # Default to UDP unless specified
    "SIP-UDP": "udp",
    "SIP-TCP": "tcp",
}