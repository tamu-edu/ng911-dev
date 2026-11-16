# GUIDE.md updates

## 1. Overview — update "The service supports"

Replace the current list with:

The service supports:

- SIP over UDP
- SIP over TCP
- SIP over TLS (mTLS supported)
- RTP
- RTP Proxy
- RTP Text (RFC 4103)
- RTP Audio (PCMU / PCMA)
- Standalone SRTP (SDES)
- DTLS-SRTP
- MSRP text messaging
- MSRPS text messaging over TLS/TCP
- XML scenario execution
- YAML scenario execution
- Variables
- Conditional execution
- Labels and jumps
- Embedded Python operations
- Automatic message correlation
- Dynamic message templating

The goal of the service is deterministic protocol testing rather than emulating a complete SIP endpoint.

---

## 2. Features -> Media

Replace the current `## Media` section near the beginning of the document with:

## Media

Supported media capabilities:

- RTP
- RTP Proxy
- RTP Text
- RTP Audio
- Standalone SRTP
- DTLS-SRTP
- MSRP
- MSRPS

Supported RTP codecs:

- PCMU (G.711 μ-law)
- PCMA (G.711 A-law)

Supported RTP media security:

- RTP/AVP
- RTP/SAVP (SDES)
- UDP/TLS/RTP/SAVP (DTLS-SRTP)

Supported MSRP transports:

- MSRP over TCP
- MSRPS over TLS/TCP

Current DTLS-SRTP implementation uses:

- OpenSSL 3.x
- libSRTP2

MSRPS uses TLS over TCP and does not depend on DTLS-SRTP or libSRTP.

Media transport and security are explicitly controlled from scenarios.

The framework intentionally does not automatically select runtime media behaviour from SDP.

This allows deterministic conformance, interoperability and negative testing.

SIP signalling transport and media transport are independently selectable.

---

## 3. Project Structure

Add the three MSRP modules.

Replace the current project structure block with:

# Project Structure

```text
sip_service/

    scenario_runner.py
    sip_transport.py
    sip_service.py

    sipp_loader.py
    yaml_loader.py

    message.py
    message_parser.py

    sdp_utils.py

    rtp_transport.py
    rtp_registry.py

    msrp_message.py
    msrp_transport.py
    msrp_session.py

    secure_media/
        dtls/
        libsrtp/
        openssl_dtls.py
        dtls_srtp_transport.py
        srtp.py
        srtp_processor.py

    templates/
```

---

## 4. Supported Steps

The current guide calls the XML elements `media_start` and `media_stop`.

The actual XML elements are `<media>` and `<stop_media>`.

Replace the section with:

# Supported Steps

The XML loader currently supports:

- send
- recv
- pause
- label
- goto
- operate
- media
- stop_media

Execution is strictly sequential unless redirected by a goto operation.

`media_start` and `media_stop` are internal ScenarioRunner step types and are not XML element names.

---

## 5. Main Media section

Replace the beginning of `# Media` with:

# Media

Media is managed explicitly through XML.

The framework does not automatically instantiate secure or connection-oriented media sessions based solely on SDP.

This enables deterministic conformance, interoperability and negative testing.

Supported `<media>` types include:

- rtp
- rtp_proxy
- srtp
- dtls_srtp
- rtp_send_text
- srtp_send_text
- dtls_srtp_send_text
- rtp_play_audio
- srtp_play_audio
- dtls_srtp_play_audio
- msrp_listen
- msrps_listen
- msrp_send_text
- msrps_send_text
- msrp_receive_text
- msrps_receive_text

MSRP/MSRPS actions are intentionally separate from RTP text actions.

RTP text uses RTP-specific concepts such as:

- payload type;
- SSRC;
- CSRC;
- RTP timestamps;
- packet-oriented text transmission.

MSRP does not use these concepts.

---

## 6. Correct existing XML media examples

Anywhere in this document where an XML example currently uses:

```xml
<media_start
```

change it to:

```xml
<media
```

For example, RTP should be represented as:

# RTP

Creates a plain RTP transport.

Example:

```xml
<media
    type="rtp"
    dst_ip="${local_ip}"
    dst_port="5004"
/>
```

RTP Proxy:

```xml
<media
    type="rtp_proxy"
    proxy_ip="..."
    proxy_port="..."
    src_ip="..."
    dst_ip="..."
    dst_port="..."
/>
```

Standalone SRTP:

```xml
<media
    type="srtp"
    dst_ip="${local_ip}"
    dst_port="5004"
    tx_key="${local_tx_key}"
    rx_key="${remote_tx_key}"
    profile="AES_CM_128_HMAC_SHA1_80"
/>
```

DTLS-SRTP:

```xml
<media
    type="dtls_srtp"
    src_ip="${local_ip}"
    src_port="5004"
    dst_ip="${peer_ip}"
    dst_port="5004"
    role="client"
    certificate_file="certs/client.crt"
    private_key_file="certs/client.key"
    remote_fingerprint="${expected_fp}"
/>
```

RTP text:

```xml
<media
    type="rtp_send_text"
    src_ip="${local_ip}"
    src_port="6000"
    dst_ip="${peer_ip}"
    dst_port="6000"
    payload_type="98"
    text="Test message"
/>
```

RTP audio:

```xml
<media
    type="rtp_play_audio"
    audio_file="audio/test.wav"
    codec="pcmu"
    src_ip="${local_ip}"
    src_port="0"
    dst_ip="${peer_ip}"
    dst_port="5004"
/>
```

---

## 7. Add MSRP / MSRPS after the DTLS-SRTP media section

Add this before `# Stopping Media`:

# MSRP / MSRPS

## Overview

The SIP Service supports instant-message media using MSRP and MSRPS.

MSRP is implemented as a dedicated connection-oriented media stack and is intentionally separate from RTP.

```text
Scenario XML
      │
      ▼
SIPp Loader
      │
      ▼
ScenarioRunner
      │
      ▼
MSRPSession
      │
      ▼
MSRPTransport
      │
      ├── TCP
      │     └── MSRP
      │
      └── TLS/TCP
            └── MSRPS
```

MSRP does not use:

- RTP packets;
- RTP payload types;
- SSRC;
- CSRC;
- RTP timestamps;
- SRTP;
- DTLS-SRTP;
- libSRTP.

The current implementation focuses on complete MSRP SEND transactions required by interoperability and conformance scenarios.

---

## MSRP Message Layer

`msrp_message.py` implements MSRP protocol framing and parsing.

Responsibilities include:

- MSRP message representation;
- transaction ID generation;
- message ID generation;
- SEND request construction;
- response construction;
- header parsing;
- body parsing;
- transaction delimiter handling;
- incremental extraction of complete messages from a TCP byte stream.

MSRP runs over a stream transport.

A single TCP `recv()` operation is therefore not assumed to contain exactly one complete MSRP message.

The parser maintains a receive buffer and extracts complete MSRP messages as data becomes available.

---

## MSRP Transport

`MSRPTransport` implements transport lifecycle for both MSRP and MSRPS.

Responsibilities include:

- TCP listener creation;
- outbound TCP connection establishment;
- passive TCP connection acceptance;
- TLS wrapping for MSRPS;
- background passive connection acceptance;
- TCP stream buffering;
- connection shutdown;
- listener shutdown.

Plain MSRP uses:

```text
MSRP
  ↓
TCP
```

MSRPS uses:

```text
MSRP
  ↓
TLS
  ↓
TCP
```

MSRPS does not use DTLS.

MSRPS does not use SRTP.

MSRPS does not use libSRTP.

---

## MSRP Session

`MSRPSession` provides the transaction-oriented layer above `MSRPTransport`.

Responsibilities include:

- sending SEND requests;
- receiving SEND requests;
- waiting for transaction responses;
- transaction ID correlation;
- expected response-status validation;
- automatic response generation;
- optional received-text validation;
- optional To-Path validation;
- optional From-Path validation;
- transport lifecycle ownership.

---

## MSRP Session Identifiers

MSRP runtime sessions are registered using scenario-defined identifiers.

Example:

```xml
session="msrp1"
```

The same identifier is used by subsequent actions that operate on the same TCP/TLS connection.

For example:

```xml
<media
    type="msrp_listen"
    session="msrp1"
    src_ip="${local_ip}"
    src_port="49172"
/>
```

followed by:

```xml
<media
    type="msrp_receive_text"
    session="msrp1"
    expected_text="Test message"
/>
```

Both actions operate on the same logical MSRP session.

Multiple MSRP sessions may exist simultaneously as long as they use different session identifiers.

---

## Passive MSRP Listener

A passive MSRP endpoint is created with:

```xml
<media
    type="msrp_listen"
    session="msrp1"
    src_ip="${local_ip}"
    src_port="49172"
/>
```

For MSRPS:

```xml
<media
    type="msrps_listen"
    session="msrp1"
    src_ip="${local_ip}"
    src_port="49172"
/>
```

The listening socket is created immediately.

Connection acceptance proceeds in the background instead of blocking sequential scenario execution.

This behaviour is particularly important for MSRPS.

A remote active endpoint may establish TCP and begin the TLS handshake immediately after receiving the SIP response that advertises the passive MSRP endpoint.

The listener must therefore be ready before the corresponding receive action is executed.

---

## Sending MSRP Text

Plain MSRP SEND example:

```xml
<media
    type="msrp_send_text"
    session="msrp1"
    src_ip="${local_ip}"
    src_port="0"
    dst_ip="${peer_ip}"
    dst_port="49172"
    from_path="msrp://${local_ip}:49172/local;tcp"
    to_path="msrp://${peer_ip}:49172/remote;tcp"
    text="Test message"
    content_type="text/plain"
    timeout="5"
    expected_status="200"
/>
```

The MSRPS equivalent uses:

```xml
<media
    type="msrps_send_text"
    ...
/>
```

and normally uses `msrps://` paths.

Supported send attributes:

```text
session
src_ip
src_port
dst_ip
dst_port
from_path
to_path
text
content_type
timeout
expect_response
expected_status
server_hostname
```

`session`, `from_path` and `to_path` are required.

When creating a new active session, `dst_ip` and `dst_port` are also required.

If the specified session does not yet exist, the action creates an active MSRP/MSRPS connection.

If the session already exists, the existing connection is reused.

This allows multiple SEND transactions to use the same persistent TCP/TLS connection.

---

## Receiving MSRP Text

Plain MSRP receive example:

```xml
<media
    type="msrp_receive_text"
    session="msrp1"
    expected_text="Test message"
    timeout="5"
    response_status="200"
    response_comment="OK"
/>
```

For MSRPS:

```xml
<media
    type="msrps_receive_text"
    session="msrp1"
    expected_text="Test message"
/>
```

Supported receive attributes:

```text
session
timeout
expected_text
expected_to_path
expected_from_path
response_status
response_comment
assign_to
```

`session` is required.

The following validation attributes are optional:

```text
expected_text
expected_to_path
expected_from_path
```

If an expected value is not supplied, that value is not validated.

After receiving a SEND request, the session sends an MSRP transaction response.

The default response is:

```text
200 OK
```

The response may be changed using:

```text
response_status
response_comment
```

---

## Assigning Received Text

The received text body may be assigned to a scenario variable.

Example:

```xml
<media
    type="msrp_receive_text"
    session="msrp1"
    assign_to="received_text"
/>
```

After successful reception:

```text
${received_text}
```

contains the received body.

---

## MSRP Network Endpoints and Protocol Paths

The physical TCP connection and the logical MSRP paths are intentionally independent.

Network connection parameters are:

```text
src_ip
src_port
dst_ip
dst_port
```

MSRP protocol routing parameters are:

```text
from_path
to_path
```

For example:

```xml
dst_ip="10.140.140.101"
dst_port="49172"

to_path="msrp://10.140.140.218:49172/session1;tcp"
```

is valid.

The runtime does not infer `To-Path` from `dst_ip` and `dst_port`.

Likewise, it does not use `To-Path` to determine the actual network connection target.

This separation supports:

- anchored media testing;
- proxy testing;
- interoperability testing;
- intentionally inconsistent protocol signalling;
- negative scenarios.

---

## MSRPS and SIP TLS Independence

MSRPS security is independent from SIP signalling security.

The following combinations are valid:

```text
SIP over UDP
+
MSRPS over TLS/TCP
```

```text
SIP over TCP
+
MSRPS over TLS/TCP
```

```text
SIP over TLS
+
MSRP over TCP
```

```text
SIP over TLS
+
MSRPS over TLS/TCP
```

Selecting SIP TLS does not automatically select MSRPS.

Selecting MSRPS does not require the SIP signalling connection itself to use TLS.

The two transports use independent runtime contexts.

---

## MSRP Lifecycle

A passive session lifecycle is:

```text
msrp_listen / msrps_listen
        │
        ▼
Create listener
        │
        ▼
Start background accept
        │
        ▼
Remote connects
        │
        ├── TCP
        │
        └── TLS handshake when MSRPS
        │
        ▼
msrp_receive_text / msrps_receive_text
        │
        ▼
Receive SEND
        │
        ▼
Send transaction response
```

An active session lifecycle is:

```text
msrp_send_text / msrps_send_text
        │
        ▼
Create session if necessary
        │
        ▼
Connect TCP/TLS
        │
        ▼
Send SEND request
        │
        ▼
Receive transaction response
```

Existing sessions may be reused for subsequent SEND transactions.

At normal scenario completion, remaining MSRP/MSRPS sessions are stopped and removed from the ScenarioRunner registry.

---

## 8. Stopping Media

The current explicit stop action applies to the RTP-family transports.

Replace the example:

```xml
<media_stop
```

with:

```xml
<stop_media
```

Use this section:

# Stopping Media

RTP-family media sessions may be explicitly terminated.

Example:

```xml
<stop_media
    type="rtp"
    dst_ip="${local_ip}"
    dst_port="5004"
/>
```

Supported explicit stop types currently include:

- rtp
- rtp_proxy
- srtp
- dtls_srtp

MSRP/MSRPS does not currently expose a dedicated `<stop_media>` action.

Remaining MSRP/MSRPS sessions are closed during normal scenario completion.

---

## 9. Architecture

Replace the current `# Architecture` section with:

# Architecture

Media components are separated by protocol responsibility.

```text
                           ScenarioRunner
                                │
                  ┌─────────────┴─────────────┐
                  │                           │
                  ▼                           ▼
            RTP Media Stack             MSRP Media Stack
                  │                           │
         ┌────────┴─────────┐                 ▼
         │                  │            MSRPSession
         ▼                  ▼                 │
   RTPTransport      DTLSSRTPTransport        ▼
         │                  │            MSRPTransport
         │                  │                 │
         │                  ▼          ┌──────┴──────┐
         │           OpenSSL DTLS      │             │
         │                  │          ▼             ▼
         │                  ▼         TCP           TLS
         │           RFC 5764 Export                  │
         │                  │                         ▼
         ▼                  ▼                        TCP
   SRTPProcessor      SRTPProcessor
         │                  │
         └────────┬─────────┘
                  ▼
              libSRTP2
```

The RTP stack supports plain RTP, standalone SRTP and DTLS-SRTP.

The MSRP stack is independent and connection-oriented.

MSRP/MSRPS does not pass through:

- `RTPTransport`;
- `SRTPProcessor`;
- `DTLSSRTPTransport`;
- libSRTP.

MSRPS uses ordinary TLS over TCP rather than DTLS.

Protocol-specific behaviour remains within the corresponding protocol stack.

---

## 10. Logging

Replace the logging capability list with:

# Logging

The service produces detailed execution logs including:

- SIP messages
- RTP session lifecycle
- SRTP session lifecycle
- DTLS handshake
- certificate validation
- fingerprint verification
- MSRP listener lifecycle
- MSRP/MSRPS connection lifecycle
- MSRP SEND transactions
- MSRP transaction responses
- MSRPS TLS connection lifecycle
- media transmission
- scenario execution
- variable evaluation
- XML execution flow

The logging subsystem is intended to simplify interoperability debugging and protocol analysis.

---

## 11. Built-in Variables

Do not add MSRP-specific built-in variables.

The current implementation does not automatically create variables such as:

```text
msrp_local_ip
msrp_local_port
msrp_remote_ip
msrp_remote_port
```

MSRP addressing is supplied explicitly through scenario attributes.

Keep the existing Built-in Variables sections unchanged.

---

## 12. Security

Add the following section after `## DTLS-SRTP`:

## MSRPS

MSRPS provides TLS protection for MSRP TCP connections.

MSRPS TLS is independent from SIP signalling transport.

The transport stack is:

```text
MSRP
  ↓
TLS
  ↓
TCP
```

MSRPS uses dedicated TLS contexts for media connections.

Configured certificate, private-key, CA and client-certificate requirements may be applied to MSRPS independently from the SIP signalling transport.

MSRPS supports:

- outbound TLS connection establishment;
- passive TLS connection acceptance;
- server certificates;
- optional client certificates;
- configured CA validation;
- configurable TLS cipher policy.

MSRPS does not use:

- DTLS;
- SRTP;
- RFC 5764;
- libSRTP.

---

## 13. Design Principles -> Explicit Behaviour

Replace the current section with:

## Explicit Behaviour

Protocol and security behaviour is scenario-controlled.

Scenarios explicitly decide:

- SIP transport;
- media type;
- RTP;
- SRTP;
- DTLS-SRTP;
- MSRP;
- MSRPS;
- certificates;
- fingerprints;
- SRTP keys;
- actual network endpoints;
- MSRP logical paths.

SDP does not automatically override these runtime decisions.

This makes interoperability testing deterministic and reproducible.

---

## 14. Design Principles -> Protocol Separation

Replace the current linear protocol diagram with:

## Protocol Separation

Each protocol layer owns only its own responsibilities.

SIP signalling and media execution are independent.

```text
                          SIP
                           │
                           ▼
                          SDP
                           │
                  Scenario behaviour
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
        RTP family                  MSRP family
             │                           │
      ┌──────┴──────┐                    ▼
      │             │                MSRPSession
      ▼             ▼                    │
     RTP           SRTP                  ▼
                    │              MSRPTransport
                    │                    │
                    ▼              ┌─────┴─────┐
                  DTLS             │           │
              key establishment    ▼           ▼
                                  TCP         TLS/TCP
```

SDP does not automatically instantiate or change media transport.

Scenario configuration remains authoritative for runtime media behaviour.

MSRP is not implemented as an RTP subtype.

MSRPS is not implemented as DTLS-SRTP.

SIP signalling TLS and MSRPS TLS are independently selectable.

No protocol layer is responsible for behaviour belonging to another layer.

---

## 15. Native Implementations

The current section says:

> Secure media intentionally uses native libraries instead of Python wrapper packages.

This is now too broad because MSRPS uses Python's TLS support rather than the native `ctypes` secure-media implementation.

Replace the beginning of that section with:

## Native Implementations

DTLS-SRTP and SRTP use native libraries instead of Python wrapper packages.

Current native dependencies for the RTP secure-media stack are:

- OpenSSL
- libSRTP2

Bindings are implemented through Python `ctypes`.

MSRPS is separate from this native secure-media stack and uses standard TLS over TCP.

This separation minimizes unnecessary dependencies while preserving precise control over RTP secure-media processing.

---

## 16. Current Limitations

Keep the existing limitations and append:

- MSRP support currently focuses on complete SEND transactions
- MSRP REPORT transactions are not currently exposed as scenario actions
- MSRP chunk continuation is not currently exposed as a high-level scenario action
- MSRP chunk abort is not currently exposed as a high-level scenario action
- no automatic MSRP/MSRPS selection from SDP
- no automatic MSRP active/passive role negotiation from SDP
- no explicit MSRP/MSRPS `<stop_media>` action
- MSRP/MSRPS sessions are currently terminated during normal scenario completion

The final section should therefore be:

# Current Limitations

The framework intentionally focuses on deterministic interoperability testing rather than implementing a complete SIP endpoint.

Current limitations include:

- no SIP registration database
- no SIP proxy implementation
- no SDP negotiation engine
- no ICE
- no STUN
- no TURN
- no SRTP key management beyond SDES and DTLS-SRTP
- no automatic DTLS role negotiation
- no video codecs
- no media transcoding
- no jitter buffer
- no packet loss concealment
- MSRP support currently focuses on complete SEND transactions
- MSRP REPORT transactions are not currently exposed as scenario actions
- MSRP chunk continuation is not currently exposed as a high-level scenario action
- MSRP chunk abort is not currently exposed as a high-level scenario action
- no automatic MSRP/MSRPS selection from SDP
- no automatic MSRP active/passive role negotiation from SDP
- no explicit MSRP/MSRPS `<stop_media>` action
- MSRP/MSRPS sessions are currently terminated during normal scenario completion

These capabilities may be added in future if required by interoperability test scenarios.

---

## 17. Contributing

Replace the current list with:

# Contributing

When extending the SIP Service, follow these principles:

- Preserve deterministic scenario execution.
- Keep protocol layers separated.
- Prefer explicit XML/YAML configuration over implicit behaviour.
- Avoid introducing protocol-specific logic into unrelated components.
- Keep SRTP security processing independent from RTP packet generation.
- Keep MSRP/MSRPS independent from RTP/SRTP/DTLS-SRTP.
- Do not introduce RTP-specific concepts into MSRP actions.
- Keep MSRP logical paths independent from TCP endpoint addressing.
- Preserve independent selection of SIP signalling security and media security.
- Passive connection-oriented media must not block sequential SIP scenario execution.
- Minimize external runtime dependencies.
- Preserve backward compatibility with existing scenarios whenever possible.

---

## 18. No changes required

The following existing sections do not require MSRP-specific changes:

- SIP
- Variables
- Send
- Receive
- Pause
- Labels
- Goto
- Operate
- RTP Transport
- RTP Proxy
- RTP Text
- RTP Audio
- SRTP
- DTLS-SRTP
- libSRTP
- YAML Scenarios
- SIP Variables
- RTP Variables
- SRTP Variables
- DTLS Variables
- Scenario Driven
- Supported Environment
- License
- Roadmap
- Support

The important point is to document MSRP/MSRPS as a separate connection-oriented protocol family rather than extending the existing RTP model.