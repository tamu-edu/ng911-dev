# Test Description: TD_CHE_999

## Overview
### Summary
All media types support

### Description
This test checks if all types of media are supported by CHE:
- audio
- video
- text

### References
* Requirements : RQ_CHE_6
* Test Case    : TC_CHE_002

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

![image](https://github.com/user-attachments/assets/ccb77ae6-d311-4b5b-9679-509f615bd66d)

<!--
[![](https://mermaid.ink/img/pako:eNpdUEsLgkAQ_isyZ_0DEl16UFCX9BQLMrmTSu6u7IMQ8b83pQY1p_ke8xygNJIghXtrnmWN1keni9ARx3Ff5FmxOexWSbJmwBkTQk-qC7fKYldHOTkfZb3zpCblp3aiSMu_qq80u5fmsxtiUGQVNpJXG960AF-TIgEppxLtQ4DQI_sweJP1uoTU20AxhE6ip22DPEgtZIf6agzDO7aOMcnGG3ueTv98IAZrQlXPjvEF1-xYFw?type=png)](https://mermaid.live/edit#pako:eNpdUEsLgkAQ_isyZ_0DEl16UFCX9BQLMrmTSu6u7IMQ8b83pQY1p_ke8xygNJIghXtrnmWN1keni9ARx3Ff5FmxOexWSbJmwBkTQk-qC7fKYldHOTkfZb3zpCblp3aiSMu_qq80u5fmsxtiUGQVNpJXG960AF-TIgEppxLtQ4DQI_sweJP1uoTU20AxhE6ip22DPEgtZIf6agzDO7aOMcnGG3ueTv98IAZrQlXPjvEF1-xYFw)
-->

## Pre-Test Conditions
### Test System
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* ng911 repository cloned to local storage
* (TLS) Generated own PCA-signed certificate and private key files (test_system.crt, test_system.key)
* (TLS) Certificate and key used by CHE copied to local storage

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


### Test Body

#### Variations

1. Validate SIP 200 OK response for SIP INVITE with g711alaw audio media

Use SIPp scenario: `SIP_INVITE_SDP_with_g711alaw_audio.xml`

2. Validate SIP 200 OK response for SIP INVITE with g711ulaw audio media

Use SIPp scenario: `SIP_INVITE_SDP_with_g711ulaw_audio.xml`

3. Validate SIP 200 OK response for SIP INVITE with H.264 video media with baseline profile level 1b

Use SIPp scenario: `SIP_INVITE_SDP_with_H.264_video_level_1b.xml`

4. Validate SIP 200 OK response for SIP INVITE with H.264 video media with baseline profile level 1.1

Use SIPp scenario: `SIP_INVITE_SDP_with_H.264_video_level_1.1.xml`

5. Validate SIP 200 OK response for SIP INVITE with H.264 video media with baseline profile level 2.0

Use SIPp scenario: `SIP_INVITE_SDP_with_H.264_video_level_2.0.xml`

6. Validate SIP 200 OK response for SIP INVITE with H.264 video media with baseline profile level 3.0

Use SIPp scenario: `SIP_INVITE_SDP_with_H.264_video_level_3.0.xml`

7. Validate SIP 200 OK response for SIP INVITE with t140 text media

Use SIPp scenario: `SIP_INVITE_SDP_with_text.xml`


#### Stimulus

1. Send SIP INVITE to CHE - run following SIPp command on Test System, example:
  * (TLS transport)
    > sudo sipp -t l1 -sf SIPP_SCENARIO_FILE IF_CHE_TS:5060
  * (TCP transport)
    > sudo sipp -t t1 -sf SIPP_SCENARIO_FILE IF_CHE_TS:5061

2. On CHE accept incoming call

#### Response
* after accepting a call CHE responds with SIP 200 OK
* SIP 200 OK SDP body contains the same codec as offered in SIP INVITE

VERDICT:
* PASSED - if CHE responded as expected
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

![image](https://github.com/user-attachments/assets/12cc1e28-d035-4a57-8580-bbc1683e7908)

<!--
[![](https://mermaid.ink/img/pako:eNqFkFFLwzAQx79KuCdl7UjbmTZ5GIgbOEQ31uGD5CW0WRdck5mmYB377qad4h4U33J3v3_u-B2hMKUEBmEYcl0YvVUV4xqhWllr7G3hjG0Y2op9I7keoEa-tVIXcqZEZUXdwwhtZONQ3jVO1uF0Orq7nzOUL1Zo8fS82MzRCOWz1Zn0o7BHLhJnNMIYbWyndIWulgenjBb76_8yGUZrn_gr9Fsm9nuWD5cnQQC1tLVQpRdx7Hsc3E7WkgPzz1LYVw5cnzwnWmfyThfAnG1lAO2hFO5bBbDBUwAHoV-M-allqbzHx7PpQfjAADvCO7AoJuOIUErTBFOa0TQOoAPmuwmOcRRnlGJMowk5BfAxfDsZx4QQnKYkSrIE36QBWNNWu6-Fp0_S0o1u?type=png)](https://mermaid.live/edit#pako:eNqFkFFLwzAQx79KuCdl7UjbmTZ5GIgbOEQ31uGD5CW0WRdck5mmYB377qad4h4U33J3v3_u-B2hMKUEBmEYcl0YvVUV4xqhWllr7G3hjG0Y2op9I7keoEa-tVIXcqZEZUXdwwhtZONQ3jVO1uF0Orq7nzOUL1Zo8fS82MzRCOWz1Zn0o7BHLhJnNMIYbWyndIWulgenjBb76_8yGUZrn_gr9Fsm9nuWD5cnQQC1tLVQpRdx7Hsc3E7WkgPzz1LYVw5cnzwnWmfyThfAnG1lAO2hFO5bBbDBUwAHoV-M-allqbzHx7PpQfjAADvCO7AoJuOIUErTBFOa0TQOoAPmuwmOcRRnlGJMowk5BfAxfDsZx4QQnKYkSrIE36QBWNNWu6-Fp0_S0o1u)
-->

## Comments

Version:  010.3f.3.0.4

Date:     20250417

## Footnotes
[^1]: SIPp - tool for SIP packet simulations. Official documentation: https://sipp.sourceforge.net/doc/reference.html#Getting+SIPp
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^4]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518
