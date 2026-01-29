# SipService

This document explains how to use **SipService** with **XML SIP scenarios**.
It covers SIP messaging, variables, RTP, RTP Proxy, media control, and custom logic.

---

## 1. Running SipService

Example CLI:

```bash
python3 sip_entry.py \
  --bind-ip 192.168.0.53 \
  --bind-port 5060 \
  --remote-ip 192.168.0.151 \
  --remote-port 5060 \
  --protocol TCP \
  --scenario SIP_call.stub.xml \
  --scenario-type auto \
  --set IF_ESRP_BCF 192.168.0.152 \
  --set CALL_ID callidtest@bcf.test \
  --message-timeout 30 
```

## Useful flags

| Flag                           | Description                 |
|--------------------------------|-----------------------------|
| `--bind-ip`, `--bind-port`     | SIP listener address        |
| `--remote-ip`, `--remote-port` | Default outbound target     |
| `--protocol`                   | UDP/TCP                     |
| `--scenario`                   | XML or YAML scenario file   |
| `--scenario-type`              | `auto`, `sipp`, or `yaml`   |
| `--set VAR VALUE`              | Override scenario variables |

---

## 2. XML Scenario Structure

A scenario consists of sequential steps interpreted by **ScenarioRunner**.

Supported blocks:

- `<send>` — send SIP message
- `<recv>` — wait for message
- `<media>` — start RTP or RTP proxy
- `<stop_media>` — stop RTP
- `<label>` and `<goto>` — control flow
- `<label>` within `<send>` or `<recv>` — add custom business logic
- `<Set>` — set variables

---

## 3. Example: Basic SIP Call Scenario

```xml
<scenario name="BasicCall">

  <send>
    <![CDATA[
INVITE urn:service:sos SIP/2.0
Via: SIP/2.0/TCP [$local_ip]:[$local_port]
From: <sip:test@local>;tag=123
To: <sip:sos>
Call-ID: [$call_id]
CSeq: 1 INVITE
Contact: <sip:tester@[$local_ip]:[$local_port]>
Content-Type: application/sdp
Content-Length: 0
    ]]>
  </send>

  <recv response="200">
    <action>
      <ereg regexp="tag=([0-9A-Za-z]+)" assign="to_tag"/>
    </action>
  </recv>

  <send>
    <![CDATA[
ACK sip:sos SIP/2.0
Via: SIP/2.0/TCP [$local_ip]:[$local_port]
From: <sip:test@local>;tag=123
To: <sip:sos>[$peer_tag_param]
Call-ID: [$call_id]
CSeq: 1 ACK
Content-Length: 0
    ]]>
  </send>

</scenario>
```

---

## 4. Media Control

### Start simple RTP receiver:

```xml
<media
  type="rtp"
  src_ip="192.168.0.151"
  dst_ip="192.168.0.53"
  dst_port="5004"
/>
```

### Start RTP Proxy:

```xml
<media
  type="rtp_proxy"
  proxy_ip="192.168.0.53"
  proxy_port="5004"
  src_ip="192.168.0.151"
  dst_ip="192.168.0.152"
  dst_port="5004"
/>
```

### Stop media:

```xml
<stop_media
  type="rtp_proxy"
  proxy_ip="192.168.0.53"
  dst_ip="192.168.0.152"
  dst_port="5004"
/>
```

---

## 5. Using variables

Variables come from:

### CLI:

```
--set CALL_ID call123
--set ESRP_FQDN esrp.local
```

### XML:

```xml
<Set variable="ESRP_PORT" value="5061"/>
```

### Inside SIP messages:

```
Call-ID: [$call_id]
To: sip:sos[$peer_tag_param]
```

---

## 6. Custom Logic: `<operate>`

`<operate>` allows attaching custom Python logic to inbound and outbound SIP messages.

It can appear:

- inside `<recv> ... </recv>` — to process **incoming** messages  
- inside `<send> ... </send>` — to transform **outgoing** messages before sending


### 6.1. Supported attributes

Example:
```xml
<operate
  method_name="my_module.rewrite_invite"
  src_ip="192.168.0.151"
  dst_ip="192.168.0.152"
  dst_port="5060"
  auto_200_ok="true"
  send_back="false"
  custom_param="value"
/>
```

Attributes:

- `method_name` — full Python function name (e.g. `logic.rewrite_invite`)
  
  Function signature:

      def rewrite_invite(message_text: str, ctx: dict) -> str | None:
          ...

- `src_ip` — optional source IP filter  
  (if it does not match, this operate is skipped)

- `dst_ip`, `dst_port` — when set, the operate result is **forwarded** to that address

- `auto_200_ok="true"` — when forwarding and this is true:
  - send automatic 200 OK back to sender
  - then forward the modified message to `dst_ip`

- `send_back="true"` — only applies when **dst_ip is NOT provided**  
  → result is sent back to original sender

- Any additional attributes become:
  
      ctx["operate"]["params"][param_name]


### 6.2. Behavior Matrix

#### 1) `dst_ip` present, `auto_200_ok = false`

- Forward the modified message to `dst_ip:dst_port`
- Do NOT send anything back
- This operate is terminal (execution stops)

Example:
```xml
<recv request="INVITE">
  <operate
    method_name="logic.rewrite_for_esrp"
    dst_ip="[$IF_ESRP_BCF]"
    dst_port="5060"/>
</recv>
```


#### 2) `dst_ip` present, `auto_200_ok = true`

- Send automatic 200 OK back to sender
- Then forward the modified message to `dst_ip`
- Terminal

Example:
```xml
<recv request="INVITE">
  <operate
    method_name="logic.rewrite_and_forward"
    dst_ip="[$IF_ESRP_BCF]"
    dst_port="5060"
    auto_200_ok="true"/>
</recv>
```


#### 3) No `dst_ip`, `send_back = false`

- Do NOT send anything
- Output of this operate becomes input to the **next** operate
- Not terminal

Pipeline example:
```xml
<recv request="INVITE">
  <operate method_name="logic.normalize_invite"/>
  <operate method_name="logic.validate_invite"/>
  <operate
    method_name="logic.route"
    dst_ip="[$IF_ESRP_BCF]"
    dst_port="5060"/>
</recv>
```


#### 4) No `dst_ip`, `send_back = true`

- Send modified message back to the source
- Terminal

Example:
```xml
<recv request="INVITE">
  <operate
    method_name="logic.build_error_response"
    send_back="true"/>
</recv>
```


### 6.3. Chaining multiple `<operate>` handlers

`<operate>` entries can chain if:

1. They have **no dst_ip**
2. `send_back` is NOT true

The output of one becomes the input of the next.

Example:
```xml
<recv request="INVITE">
  <operate
    method_name="logic.extract_header"
    header="Call-ID"
    ctx_key="CALL_ID"/>

  <operate method_name="logic.rewrite_invite_for_esrp"/>

  <operate
    method_name="logic.final_forward"
    dst_ip="[$IF_OSP_BCF]"
    dst_port="5060"
    auto_200_ok="true"/>
</recv>
```

---

## 7. RTP Proxy Behavior

`RTPProxyTransport` forwards:

- anything from `src_ip` (if defined),
- otherwise all incoming RTP packets,

to:

```
(dst_ip, dst_port)
```

Bind IP and port selected via:

```
proxy_ip + proxy_port
```

Example:
```xml
<media
    type="rtp_proxy"
    proxy_ip="192.168.0.53"
    proxy_port="5004"
    src_ip="192.168.0.151"
    dst_ip="192.168.0.152"
    dst_port="5004"
/>
```

---

## 8. Notes

- One scenario file = one call flow
- ScenarioRunner executes steps sequentially
- Labels allow simple branching
- Supports SIPp XML 90% compatible syntax + New features


