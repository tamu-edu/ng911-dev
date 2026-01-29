SIP_VARIABLE_HEADER_FIELDS = [
    "Via",  # May be updated with current hop
    "Max-Forwards",  # Is decremented by each host
    "CSeq",  # Is incremented
    "Route",  # Can be modified or appended
    "Content-Length",  # Would change in case of message body updates
    "Content-Type"
]