# SIP Service

## Overview

The SIP Service is a lightweight SIP scenario execution framework developed as part of the Test Suite.

Unlike SIPp, this implementation is written entirely in Python and is designed to support automated protocol conformance, interoperability, and integration testing while remaining easily extensible.

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

# Features

## SIP

Supported transports:

- UDP
- TCP
- TLS

Supported functionality:

- INVITE
- ACK
- BYE
- CANCEL
- OPTIONS
- REGISTER
- MESSAGE
- INFO
- NOTIFY
- REFER
- UPDATE
- PRACK
- arbitrary SIP methods

Supports:

- custom SIP headers
- dynamic variables
- automatic Content-Length calculation
- multipart messages
- SDP bodies
- XML templates
- message matching
- retransmissions
- receive timeouts

---

## Media

Supported media capabilities:

- RTP
- RTP Proxy
- RTP Text
- RTP Audio
- Standalone SRTP
- DTLS-SRTP

Supported codecs:

- PCMU (G.711 μ-law)
- PCMA (G.711 A-law)

Supported media security:

- RTP/AVP
- RTP/SAVP (SDES)
- UDP/TLS/RTP/SAVP (DTLS-SRTP)

Current DTLS implementation uses:

- OpenSSL 3.x
- libSRTP2

Media security is explicitly controlled from XML scenarios.

The framework intentionally does not automatically negotiate media security from SDP, allowing interoperability and negative test scenarios.

---

## XML Scenario Engine

Scenario execution supports:

- send
- receive
- pause
- labels
- goto
- variables
- conditions
- Python expressions
- custom operations
- media lifecycle

Example:

```xml
<label id="start"/>

<send>
...
</send>

<recv response="180"/>

<recv response="200"/>

<operate assign_to="call_established">
True
</operate>

<goto label="media"/>
```

---

## Variables

Variables may be referenced anywhere using:

```
${variable_name}
```

Variables can originate from:

- built-in runtime variables
- XML operations
- received SIP messages
- SDP parsing
- user-defined values

Example:

```
${call_id}

${local_ip}

${peer_ip}

${media_port}
```

---

# Project Structure

```
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

# Installation

Requirements

- Python 3.12+
- OpenSSL 3.x
- libSRTP2

Verified environment:

```
Python      3.12.3

OpenSSL     3.0.13

libSRTP2    2.5.0
```

Linux packages:

```
openssl

libsrtp2

libssl.so.3

libcrypto.so.3
```

The DTLS implementation is intentionally bound to the verified OpenSSL 3.x API.

Using different OpenSSL major versions may require updating the OpenSSL bindings.

---

# Running

Example:

```python
SipService(
    local_ip="10.0.0.1",
    local_port=5061,
    transport="TLS",
    certificate="server.crt",
    private_key="server.key",
)
```

Running a scenario:

```python
service.run_scenario(
    "invite.xml"
)
```

YAML scenarios:

```python
service.run_scenario(
    "invite.yaml"
)
```

---
# XML Scenarios

## Overview

The SIP Service executes scenarios described in XML.

The XML syntax is intentionally inspired by SIPp while extending it with additional capabilities required for automated interoperability testing.

A scenario consists of sequential execution steps.

Example:

```xml
<scenario>

    <send>
        <![CDATA[
        INVITE sip:${remote_ip} SIP/2.0
        ...
        ]]>
    </send>

    <recv response="100"/>

    <recv response="180"/>

    <recv response="200"/>

    <send>
        <![CDATA[
        ACK sip:${remote_ip} SIP/2.0
        ...
        ]]>
    </send>

</scenario>
```

---

# Supported Steps

The XML loader currently supports:

- send
- recv
- pause
- label
- goto
- operate
- media_start
- media_stop

Execution is strictly sequential unless redirected by a goto operation.

---

# Send

Sends a SIP message.

Example:

```xml
<send>

<![CDATA[
INVITE sip:${peer_ip} SIP/2.0
Via: SIP/2.0/${transport} ${local_ip}:${local_port};branch=${branch}
From: <sip:test@test.com>;tag=${from_tag}
To: <sip:test@test.com>
Call-ID: ${call_id}
CSeq: 1 INVITE
Content-Length: 0

]]>

</send>
```

Variables are expanded immediately before transmission.

---

# Receive

Waits for an incoming SIP message.

Example:

```xml
<recv response="200"/>
```

or

```xml
<recv request="INVITE"/>
```

Receive steps support:

- request matching
- response matching
- timeout
- optional receive
- regexp extraction
- variable assignment

---

# Pause

Pauses scenario execution.

Example:

```xml
<pause milliseconds="500"/>
```

---

# Labels

Creates a jump target.

```xml
<label id="retry"/>
```

---

# Goto

Transfers execution to another label.

```xml
<goto label="retry"/>
```

Goto may be unconditional or controlled by an expression.

---

# Operate

Executes Python expressions inside the scenario.

Operations may:

- assign variables
- evaluate expressions
- manipulate scenario state
- build dynamic values

Example:

```xml
<operate assign_to="next_cseq">

int(${cseq}) + 1

</operate>
```

Example:

```xml
<operate>

print("Incoming call established")

</operate>
```

Operations execute inside the scenario runtime and therefore have access to current variables.

---

# Variables

Variables use the syntax:

```
${variable}
```

Example:

```xml
Call-ID: ${call_id}

From: ${from_tag}

To: ${to_tag}

Contact: <sip:${local_ip}>
```

Variables may be generated by:

- runtime
- XML operations
- received SIP messages
- SDP parsing
- media sessions

---

# Media

Media is managed explicitly through XML.

The framework never automatically creates secure media sessions based solely on SDP.

This enables deterministic interoperability and negative testing.

Supported media types:

- rtp
- rtp_proxy
- srtp
- dtls_srtp

Supported media actions:

- media_start
- media_stop
- rtp_send_text
- srtp_send_text
- dtls_srtp_send_text
- rtp_play_audio
- srtp_play_audio
- dtls_srtp_play_audio

---

# RTP

Creates a plain RTP transport.

Example:

```xml
<media_start
    type="rtp"
    src_ip="${local_ip}"
    src_port="5004"
/>
```

---

# RTP Proxy

Creates an RTP forwarding proxy.

Example:

```xml
<media_start
    type="rtp_proxy"
    src_ip="..."
    src_port="..."
    dst_ip="..."
    dst_port="..."
/>
```

---

# Standalone SRTP (SDES)

Creates an SRTP transport using explicitly configured session keys.

Example:

```xml
<media_start
    type="srtp"
    dst_ip="${local_ip}"
    dst_port="5004"
    tx_key="${local_tx_key}"
    rx_key="${remote_tx_key}"
    profile="AES_CM_128_HMAC_SHA1_80"
/>
```

Supported profiles include:

- AES_CM_128_HMAC_SHA1_80
- AES_CM_128_HMAC_SHA1_32

---

# DTLS-SRTP

Creates a DTLS session and derives SRTP keys according to RFC 5764.

Example:

```xml
<media_start
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

Supported roles:

- client
- server

Role selection is explicit.

Automatic role negotiation is intentionally not implemented.

---

# Stopping Media

Media sessions may be explicitly terminated.

Example:

```xml
<media_stop
    type="rtp"
    dst_ip="${local_ip}"
    dst_port="5004"
/>
```

Supported media types:

- rtp
- rtp_proxy
- srtp
- dtls_srtp

# RTP

## Overview

The framework contains a lightweight RTP implementation intended for protocol testing rather than media processing.

Responsibilities include:

- RTP packet generation
- RTP packet reception
- RTP forwarding
- RFC 4103 text transport
- G.711 audio transport
- optional SRTP protection
- optional DTLS-SRTP protection

Media transports are independent from SIP transports.

---

# RTP Transport

`RTPTransport` implements a UDP-based RTP endpoint.

Responsibilities:

- socket management
- sending RTP packets
- receiving RTP packets
- receive loop
- optional SRTP processing

When an SRTP processor is attached, every transmitted RTP packet is encrypted before transmission and every received packet is decrypted before delivery.

The RTP packet generation logic remains unchanged regardless of whether media security is enabled.

---

# RTP Proxy

`RTPProxyTransport` forwards RTP packets without interpreting media contents.

Responsibilities:

- receive RTP packets
- forward packets
- preserve packet payload
- preserve timing as closely as possible

The proxy is protocol-transparent and does not perform RTP parsing, SRTP processing or DTLS negotiation.

---

# RTP Text

The framework supports RTP text transmission according to RFC 4103.

Capabilities:

- UTF-8 text payloads
- configurable payload type
- configurable timestamp increment
- configurable SSRC
- configurable CSRC list

Example:

```xml
<media_start
    type="rtp_send_text"
    src_ip="${local_ip}"
    src_port="6000"
    dst_ip="${peer_ip}"
    dst_port="6000"
    payload_type="98"
/>
```

The same XML step is available for secure media:

```xml
type="srtp_send_text"
```

and

```xml
type="dtls_srtp_send_text"
```

No XML changes other than the media type are required.

---

# RTP Audio

The framework supports streaming WAV audio using RTP.

Currently supported codecs:

- PCMU (Payload Type 0)
- PCMA (Payload Type 8)

Requirements:

- mono WAV
- matching sample rate
- PCM source

Example:

```xml
<media_start
    type="rtp_play_audio"
    audio_file="audio/test.wav"
    codec="pcmu"
    dst_ip="${peer_ip}"
    dst_port="5004"
/>
```

Secure variants:

```xml
type="srtp_play_audio"
```

```xml
type="dtls_srtp_play_audio"
```

The audio generator remains identical regardless of transport security.

---

# SRTP

## Overview

Standalone SRTP is implemented using libSRTP2.

The implementation supports Secure RTP using explicitly configured session keys (SDES).

Supported protection profiles:

- AES_CM_128_HMAC_SHA1_80
- AES_CM_128_HMAC_SHA1_32

The SRTP implementation is intentionally separated from RTP generation.

Packet flow:

```
RTP Packet

↓

SRTP Processor

↓

libSRTP

↓

UDP
```

---

# DTLS-SRTP

DTLS-SRTP is implemented according to RFC 5764.

The implementation performs:

- DTLS handshake
- certificate exchange
- fingerprint verification
- SRTP profile negotiation
- RFC 5764 key export
- SRTP context creation

Packet flow:

```
UDP

↓

DTLS

↓

RFC5764 Exporter

↓

SRTP Processor

↓

RTP
```

Supported DTLS roles:

- client
- server

Role selection is explicit in XML.

---

# OpenSSL

The DTLS implementation uses native OpenSSL through Python `ctypes`.

Verified implementation environment:

- OpenSSL 3.0.x

The bindings are intentionally implemented without additional Python wrapper libraries to minimise external runtime dependencies and maintain direct control over the OpenSSL API.

---

# libSRTP

SRTP processing uses native libSRTP2 through Python `ctypes`.

Verified implementation environment:

- libSRTP 2.5.x

The framework performs direct bindings to the required libSRTP API instead of depending on third-party Python packages.

---

# Architecture

Secure media components are separated by responsibility.

```
ScenarioRunner

        │

        ▼

RTPTransport

        │

        ├──────────── Plain RTP

        │

        └────── SRTPProcessor

                    │

               libSRTP2


DTLSSRTPTransport

        │

        ▼

OpenSSLDTLS

        │

        ▼

RFC5764 Exporter

        │

        ▼

SRTPProcessor

        │

        ▼

libSRTP2
```

The RTP implementation is shared by plain RTP, standalone SRTP and DTLS-SRTP.

Only the security layer changes.

---

# YAML Scenarios

The framework also supports YAML-based scenarios.

YAML scenarios provide the same execution capabilities as XML while offering a more compact syntax for generated or programmatically maintained test cases.

Both XML and YAML scenarios execute through the same Scenario Runner.

---

# Logging

The service produces detailed execution logs including:

- SIP messages
- RTP session lifecycle
- SRTP session lifecycle
- DTLS handshake
- certificate validation
- fingerprint verification
- media transmission
- scenario execution
- variable evaluation
- XML execution flow

The logging subsystem is intended to simplify interoperability debugging and protocol analysis.

---
# Built-in Variables

The SIP Service provides a set of runtime variables automatically available during scenario execution.

## SIP Variables

| Variable | Description |
|----------|-------------|
| `${call_id}` | SIP Call-ID |
| `${from_tag}` | Local From tag |
| `${to_tag}` | Remote To tag |
| `${cseq}` | Current CSeq |
| `${local_ip}` | Local SIP IP |
| `${local_port}` | Local SIP port |
| `${remote_ip}` | Remote SIP IP |
| `${remote_port}` | Remote SIP port |
| `${peer_ip}` | Current peer IP |
| `${peer_port}` | Current peer port |

---

## RTP Variables

| Variable | Description |
|----------|-------------|
| `${rtp_local_ip}` | Local RTP IP |
| `${rtp_local_port}` | Local RTP port |
| `${rtp_remote_ip}` | Remote RTP IP |
| `${rtp_remote_port}` | Remote RTP port |

---

## Generic Media Variables

| Variable | Description |
|----------|-------------|
| `${media_ip}` | Media IP |
| `${media_port}` | Media port |
| `${media_protocol}` | SDP media protocol |
| `${media_security_mode}` | rtp / sdes_srtp / dtls_srtp |
| `${media_formats}` | SDP payload types |
| `${media_rtcp_ip}` | RTCP IP |
| `${media_rtcp_port}` | RTCP port |
| `${media_rtcp_mux}` | RTCP multiplexing flag |

---

## SRTP Variables

These variables are intended for standalone SDES-SRTP scenarios.

| Variable | Description |
|----------|-------------|
| `${srtp_profile}` | Local SRTP protection profile |
| `${srtp_tx_key}` | Local transmit key |
| `${srtp_rx_key}` | Local receive key |
| `${srtp_remote_profile}` | Remote SDP crypto suite |
| `${srtp_remote_key}` | Remote SDP crypto key |
| `${srtp_crypto_tag}` | SDP crypto tag |

---

## DTLS Variables

These variables are intended for DTLS-SRTP scenarios.

| Variable | Description |
|----------|-------------|
| `${dtls_role}` | client or server |
| `${dtls_certificate_file}` | Local certificate |
| `${dtls_private_key_file}` | Local private key |
| `${dtls_remote_fingerprint}` | Expected remote fingerprint |
| `${dtls_fingerprint_algorithm}` | Fingerprint algorithm |
| `${dtls_remote_setup}` | SDP setup attribute |
| `${dtls_srtp_profiles}` | Advertised SRTP protection profiles |
| `${dtls_cipher_list}` | OpenSSL cipher list |
| `${dtls_handshake_timeout}` | Handshake timeout |

---

# Security

## TLS

Supported capabilities:

- TLS over TCP
- Mutual TLS
- Custom CA
- Certificate validation
- Private key validation

---

## Standalone SRTP

Standalone SRTP uses explicit session keys.

The framework does not generate SDES keys automatically.

The scenario author explicitly defines:

- SRTP profile
- transmit key
- receive key

allowing both positive and negative interoperability testing.

---

## DTLS-SRTP

DTLS-SRTP follows RFC 5764.

The implementation performs:

- DTLS handshake
- certificate exchange
- peer certificate validation
- fingerprint verification
- SRTP profile negotiation
- RFC5764 key export
- SRTP context creation

The resulting SRTP session is transparently attached to the RTP transport.

---

# Design Principles

The SIP Service follows several design principles.

## Explicit Behaviour

Nothing security-related happens automatically.

Scenarios explicitly decide:

- transport
- media type
- SRTP
- DTLS-SRTP
- certificates
- fingerprints
- keys

This makes interoperability testing deterministic and reproducible.

---

## Protocol Separation

Each protocol layer owns only its own responsibilities.

```
SIP

↓

SDP

↓

RTP

↓

SRTP

↓

DTLS
```

No layer is responsible for behaviour belonging to another layer.

---

## Native Implementations

Secure media intentionally uses native libraries instead of Python wrapper packages.

Current native dependencies:

- OpenSSL
- libSRTP2

Bindings are implemented through Python `ctypes`.

This approach minimizes external runtime dependencies while allowing precise control over the underlying APIs.

---

## Scenario Driven

The framework is scenario-driven.

Runtime behaviour is controlled by XML or YAML scenarios rather than hardcoded logic.

This allows:

- protocol conformance testing
- interoperability testing
- regression testing
- negative testing
- custom protocol experimentation

without modifying Python source code.

---

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

These capabilities may be added in future if required by interoperability test scenarios.

---

# Supported Environment

The implementation has been verified using:

| Component | Version |
|------------|---------|
| Python | 3.12.x |
| OpenSSL | 3.0.x |
| libSRTP2 | 2.5.x |

Using different OpenSSL major versions may require updating the native OpenSSL bindings.

---

# License

This project is part of the Test Suite framework.

It is intended for protocol conformance, interoperability and integration testing of SIP-based systems.

---

# Roadmap

Future enhancements may include:

- Additional audio codecs
- RTP video streams
- DTMF (RFC 4733)
- RTCP scenario actions
- ICE
- STUN
- TURN
- Additional SIP extensions
- Extended SIPp XML compatibility
- Performance improvements
- Additional interoperability scenarios

Feature implementation is driven by Test Suite requirements and interoperability testing needs rather than by protocol completeness.

---

# Contributing

When extending the SIP Service, follow these principles:

- Preserve deterministic scenario execution.
- Keep protocol layers separated.
- Prefer explicit XML/YAML configuration over implicit behaviour.
- Avoid introducing protocol-specific logic into unrelated components.
- Keep secure media independent from RTP packet generation.
- Minimize external runtime dependencies.
- Preserve backward compatibility with existing scenarios whenever possible.

---

# Support

This implementation is intended for protocol conformance, interoperability and integration testing within the Test Suite project.

For implementation details, examples and advanced scenario construction, refer to the project documentation and example scenarios.

