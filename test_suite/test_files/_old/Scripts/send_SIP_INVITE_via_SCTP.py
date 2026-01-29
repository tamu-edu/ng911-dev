import socket
import sctp

#############################
# CONFIG
#############################
remote_ip = '192.0.2.1'
remote_port = 5060
#############################

# Get the local IP address
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    finally:
        s.close()
    return local_ip

# Setup SCTP socket
s = sctp.sctpsocket_tcp(socket.AF_INET)

local_ip = get_local_ip()

# Optional: Bind to local IP and port
s.bind((local_ip, 0))

# Connect to remote SIP server
s.connect((remote_ip, remote_port))

sdp = (
    f"v=0\r\n"
    f"o=user1 53655765 2353687637 IN IP4 {local_ip}\r\n"
    f"s=-\r\n"
    f"t=0 0\r\n"
    f"c=IN IP4 {local_ip}\r\n"
    f"m=audio 49170 RTP/AVP 0\r\n"
    f"a=rtpmap:0 PCMU/8000\r\n"
)

content_length = len(sdp.encode('utf-8'))

# Craft a basic SIP INVITE message
invite_msg = (
    f"INVITE urn:service:sos SIP/2.0\r\n"
    f"Via: SIP/2.0/SCTP {local_ip}\r\n"
    "To: urn:service:sos\r\n"
    f"From: SENDER <sip:SENDER@{local_ip}:{remote_port}>\r\n"
    f"Call-ID: 1342352534dfregegq424tyjyj@{local_ip}\r\n"
    "CSeq: 1 INVITE\r\n"
    f"Contact: <sip:SENDER@{local_ip}:{remote_port}>\r\n"
    "Max-Forwards: 70\r\n"
    "Content-Type: application/sdp\r\n"
    f"Content-Length: {content_length}\r\n\r\n"

    f"{sdp}"
)

# Send the SIP INVITE
s.send(invite_msg.encode('utf-8'))

# Close the socket after sending
s.close()
