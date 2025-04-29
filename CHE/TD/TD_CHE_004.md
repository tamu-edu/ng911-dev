# Test Description: TD_CHE_004

## Overview
### Summary
SIP INVITE for callbacks and other outbound calls

### Description
This test covers SIP INVITE validation for callbacks and other outbound calls

### References
* Requirements : RQ_CHE_3, RQ_CHE_4, RQ_CHE_5
* Test Case    : 

### Requirements
IXIT config file for CHE

### SIP transport types
Test can be performed with 2 different SIP transport types. Steps describing actions for specific one are marked as following:
- (TLS transport) - should be used by default
- (TCP transport) - used in lab for testing purposes only if default TLS is not possible

## Configuration
### Implementation Under Test Interface Connections
<!-- Identify each of the FEs that are part of the configuration and how they are connected -->
* Test System
  * IF_TS_CHE - connected to IF_CHE_TS
* CHE
  * IF_CHE_TS - connected to IF_TS_CHE 

### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* Test System
  * IF_TS_CHE - Active
* CHE
  * IF_CHE_TS - Active

### Connectivity Diagram
<!--
[![](https://mermaid.ink/img/pako:eNpdUEsLgkAQ_isyZ_0DEl16UFCX9BQLMrmTSu6u7IMQ8b83pQY1p_ke8xygNJIghXtrnmWN1keni9ARx3Ff5FmxOexWSbJmwBkTQk-qC7fKYldHOTkfZb3zpCblp3aiSMu_qq80u5fmsxtiUGQVNpJXG960AF-TIgEppxLtQ4DQI_sweJP1uoTU20AxhE6ip22DPEgtZIf6agzDO7aOMcnGG3ueTv98IAZrQlXPjvEF1-xYFw?type=png)](https://mermaid.live/edit#pako:eNpdUEsLgkAQ_isyZ_0DEl16UFCX9BQLMrmTSu6u7IMQ8b83pQY1p_ke8xygNJIghXtrnmWN1keni9ARx3Ff5FmxOexWSbJmwBkTQk-qC7fKYldHOTkfZb3zpCblp3aiSMu_qq80u5fmsxtiUGQVNpJXG960AF-TIgEppxLtQ4DQI_sweJP1uoTU20AxhE6ip22DPEgtZIf6agzDO7aOMcnGG3ueTv98IAZrQlXPjvEF1-xYFw)
-->

![image](https://github.com/user-attachments/assets/cba5a1bc-7188-4e67-b2a7-f69599ba68aa)


## Pre-Test Conditions
### Test System
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* ng911 repository cloned to local storage
* (TLS) Generated own PCA-signed certificate and private key files (test_system.crt, test_system.key)
* (TLS) Certificate and key used by CHE copied to local storage
* (TLS) PCA certificate copied to local storage

### CHE
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* IUT is active
* IUT is in normal operating state
* Default configuration is loaded
* IUT is initialized using IXIT config file
* Test System configured as default ESRP
* Agent logged in (f.e. tester@psap.example.com)

## Test Sequence

### Test Preamble

#### Test System
* Install SIPp by following steps from documentation[^1]
* Install Wireshark[^2]
* (TLS v1.2) Configure Wireshark to decode HTTP over TLS, use tests system and FE certificate keys [^3]
* (TLS v1.3) Configure logging of session keys and configure Wireshark to decode HTTP over TLS [^4]
* Using Wireshark on 'Test System' start packet tracing on IF_TS_CHE interface - run following filter:
   * (TLS transport)
     > ip.addr == IF_TS_CHE_IP_ADDRESS and tls
   * (TCP transport)
     > ip.addr == IF_TS_CHE_IP_ADDRESS and sip
* Generate call for callback test. Send SIP INVITE to CHE - run following SIPp command on Test System, example:
    * (TLS transport)
      > sudo sipp -t l1 -sf SIP_INVITE_SDP_with_audio_required.xml IF_TS_CHE_IP_ADDRESS:5060
    * (TCP transport)
      > sudo sipp -t t1 -sf SIP_INVITE_SDP_with_audio_required.xml IF_TS_CHE_IP_ADDRESS:5061


### Test Body

#### Variations

1. Validate SIP INVITE sent by CHE for callbacks
2. Validate SIP INVITE sent by CHE for outbound calls

#### Stimulus
* Variation 1
  
  On CHE trigger callback to incoming call sent earlier - follow steps described in IXIT config file
  
* Variation 2
  
  On CHE trigger outbound call to any target outside ESInet - follow steps described in IXIT config file

#### Response
* Variation 1
  - CHE should send SIP INVITE to Test System
  - SIP INVITE should contain:
    - Request-URI containing SIP URI value of 'P-Asserted-Identity' or 'From' header field from initial incoming SIP INVITE
    - 'To' header field containing SIP URI value of 'P-Asserted-Identity' or 'From' header field from initial incoming SIP INVITE
    - 'From' header field containing 'sip:TEL_NUMBER@CHE_FQDN;user=phone' where TEL_NUMBER is 10-digit NANP number or E.164 number (f.e. '+5511912345678') and CHE_FQDN shall be correct domain name
    - 'Via' header field with SIP protocol version, transport type and CHE ip address + port, f.e. `Via: SIP/2.0/TCP 192.0.2.1:5060;branch=z9hG4bK23423`
    - 'Call-ID' with unique string
    - 'CSeq' with string value f.e. `1 INVITE`
    - 'Contact' with SIP URI of CHE
    - 'Route' header field with FQDN or IP address and 'lr' parameter (f.e. `Route: <sip:esrp.example.com;lr>`)
    - 'Priority' header field with value 'psap-callback'
    - 'Resource-Priority' header field with value 'esnet.0'
    - 'P-Asserted-Identity' containing the same values as 'From' header field
    - Second 'P-Asserted-Identity' containing identity of an Agent logged in to CHE (f.e. `P-Asserted-Identity: sip:<tester@psap.example.com>`
    - 'Content-Type' header field with value 'application/sdp'
    - 'Content-Length' header field with int value
  - SIP INVITE should contain SDP body with:
    - all required media supported, f.e.:
      
        ```
          a=rtpmap:0 PCMU/8000
          a=rtpmap:8 PCMA/8000
        ```
        
    - language tags, f.e.:
      
       ```
        a=hlang-send:es eu en
        a=hlang-recv:es eu en
       ```

* Variation 2
  - CHE should send SIP INVITE to Test System
  - SIP INVITE should contain:
    - Request-URI containing 10-digit NANP number (f.e. 'tel:1234567890') or E.164 number (f.e. 'tel:+5511912345678') or SIP URI with FQDN of target's home network (f.e. `sip:target@example.com`)
    - 'To' header field containing 10-digit NANP number (f.e. 'tel:1234567890') or E.164 number (f.e. 'tel:+5511912345678') or SIP URI with FQDN of target's home network (f.e. `sip:target@example.com`)
    - 'From' header field containing one of following:
      - 'sip:TEL_NUMBER@CHE_FQDN;user=phone' where TEL_NUMBER is 10-digit NANP number or E.164 number (f.e. '+5511912345678') and CHE_FQDN shall be correct domain name
      - 'sip:anonymous@anonymous.invalid'
    - 'Via' header field with SIP protocol version, transport type and CHE ip address + port, f.e. `Via: SIP/2.0/TCP 192.0.2.1:5060;branch=z9hG4bK23423`
    - 'Call-ID' with unique string
    - 'CSeq' with string value f.e. `1 INVITE`
    - 'Contact' with SIP URI of CHE
    - 'Route' header field with FQDN or IP address and 'lr' parameter (f.e. `Route: <sip:esrp.example.com;lr>`)
    - 'Resource-Priority' header field with one of values: 'esnet.0', 'esnet.1' or 'esnet.2'
    - 'P-Asserted-Identity' containing 'sip:TEL_NUMBER@CHE_FQDN;user=phone' where TEL_NUMBER is 10-digit int and CHE_FQDN shall be correct domain name
    - Second 'P-Asserted-Identity' containing identity of an Agent logged in to CHE (f.e. `P-Asserted-Identity: sip:<tester@psap.example.com>`
    - 'Privacy' with value 'user' only when 'From' header field is 'sip:anonymous@anonymous.invalid'
    - 'Content-Type' header field with value 'application/sdp'
    - 'Content-Length' header field with int value
  - SIP INVITE should contain SDP body with:
    - all required media supported, f.e.:
      
        ```
          a=rtpmap:0 PCMU/8000
          a=rtpmap:8 PCMA/8000
        ```
        
    - language tags, f.e.:
      
       ```
        a=hlang-send:es eu en
        a=hlang-recv:es eu en
       ```



VERDICT:
* PASSED - if CHE sends language tags as expected
* FAILED - any other cases


### Test Postamble
#### Test System
* stop all SIPp processes (if still running)
* archive all logs generated
* stop Wireshark (if still running)
* remove ng911 repository files
* disconnect interfaces from CHE

#### CHE
* disconnect IF_CHE_TS
* reconnect interfaces back to default

## Post-Test Conditions 
### Test System 
* Test tools stopped
* interfaces disconnected from CHE

### CHE
* device connected back to default
* device in normal operating state

## Sequence Diagram
<!--
[![](https://mermaid.ink/img/pako:eNqNkc1uwjAQhF9ltVcSlB-aYB-QqoJUDkVIQRwqX1zHBAtiU8epShHvXuO2KlJ74La2v5m1Zk4oTC2RYhzHTAujN6qhTAO0ylpj74UztqOw4ftOMh2gTr72Ugs5VbyxvGV6YZwE8yYtrGTnoDp2TrYRPDzOKKy5VdwpoyG9uMI1Ek8mgwBV8yXMF-v5agYDqKbLv2Q8CeDKqqbxewTf7-GFix14Y__yJfDDxfJK95_1bb_NbrfECFtpW65qH-PpomPotrKVDKkfa253DJk-e473zlRHLZA628sI-0PN3U-QSEPKER64fjbm9yxr5Vt4-uop1BUYpCd8R5pmxTAtCCFlnhAyJmUW4RGpv82TLEmzMSFJQtJRcY7wI9iOhllRFElZFmk-zpO7MkJr-mb7vfD8CQs9pFw?type=png)](https://mermaid.live/edit#pako:eNqNkc1uwjAQhF9ltVcSlB-aYB-QqoJUDkVIQRwqX1zHBAtiU8epShHvXuO2KlJ74La2v5m1Zk4oTC2RYhzHTAujN6qhTAO0ylpj74UztqOw4ftOMh2gTr72Ugs5VbyxvGV6YZwE8yYtrGTnoDp2TrYRPDzOKKy5VdwpoyG9uMI1Ek8mgwBV8yXMF-v5agYDqKbLv2Q8CeDKqqbxewTf7-GFix14Y__yJfDDxfJK95_1bb_NbrfECFtpW65qH-PpomPotrKVDKkfa253DJk-e473zlRHLZA628sI-0PN3U-QSEPKER64fjbm9yxr5Vt4-uop1BUYpCd8R5pmxTAtCCFlnhAyJmUW4RGpv82TLEmzMSFJQtJRcY7wI9iOhllRFElZFmk-zpO7MkJr-mb7vfD8CQs9pFw)
-->

![image](https://github.com/user-attachments/assets/5279d276-9796-4c42-a9a3-6bff011f9f0f)

## Comments

Version:  010.3f.3.0.6

Date:     20250429

## Footnotes
[^1]: SIPp - tool for SIP packet simulations. Official documentation: https://sipp.sourceforge.net/doc/reference.html#Getting+SIPp
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^4]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518
