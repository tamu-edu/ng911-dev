# Test Description: TD_BRIDGE_999

## Overview
### Summary
Outgoing SIP INVITE for call transfer to another PSAP

### Description
This test validates outgoing SIP INVITE for Bridge used for call transfer to another PSAP
Test includes verification if SIP INVITE sent to the target contains:
- caller location and its other additional data
- Emergency Call Identifier
- Incident Tracking Identifier
- service URN in the Request-URI
- 'Route' header field with URI from 'Refer-To' header field of SIP REFER
- 'Route' header field with 'lr' parameter
- 'Referred-By' header field with URI of the PSAP which transferred the call
- 'Refer-To' header field with SIP URI of target PSAP

### References
* Requirements : RQ_BRIDGE_006, RQ_BRIDGE_007, RQ_BRIDGE_010, RQ_BRIDGE_011, RQ_BRIDGE_012, RQ_BRIDGE_018
* Test Purpose : 
* Test Case    :

### Requirements
IXIT config file for BRIDGE

### SIP transport types
Test can be performed with 2 different SIP transport types. Steps describing actions for specific one are marked as following:
- (TLS transport) - should be used by default
- (TCP transport) - used in lab for testing purposes only if default TLS is not possible

## Configuration
### Implementation Under Test Interface Connections
<!-- Identify each of the FEs that are part of the configuration and how they are connected -->
* Test System PSAP1
  * IF_TS-PSAP1_CALLER - connected to IF_CALLER_TS-PSAP1
  * IF_TS-PSAP1_BRIDGE - connected to IF_BRIDGE_TS-PSAP1
* Test System CALLER
  * IF_CALLER_TS-PSAP1 - connected to IF_TS-PSAP1
  * IF_CALLER_BRIDGE - connected to IF_BRIDGE_CALLER
* Test System PSAP2
  * IF_TS-PSAP2_BRIDGE - connected to IF_BRIDGE_TS-PSAP2
* BRIDGE
  * IF_BRIDGE_TS-PSAP1 - connected to IF_TS-PSAP1_BRIDGE
  * IF_BRIDGE_TS-PSAP2 - connected to IF_TS-PSAP2_BRIDGE
  * IF_BRIDGE_CALLER - connected to IF_CALLER_BRIDGE


### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* Test System PSAP1
  * IF_TS-PSAP1_CALLER - Active
  * IF_TS-PSAP1_BRIDGE - Active
* Test System CALLER
  * IF_CALLER_TS-PSAP1 - Active
  * IF_CALLER_BRIDGE - Active
* Test System PSAP2
  * IF_TS-PSAP2_BRIDGE - Active
* BRIDGE
  * IF_BRIDGE_TS-PSAP1 - Active
  * IF_BRIDGE_TS-PSAP2 - Active
  * IF_BRIDGE_CALLER - Active

### Connectivity Diagram
[![](https://mermaid.ink/img/pako:eNqFUmFrwjAU_Cvlfa6SpC41YQzcdENwMKyfRkEyG63MNpKmbE7878ts59oubP3Ud3fc3SPvCCuVSOCw3qm3VSq08WbzOPfsN71f3o1ms8l8uYh6T9HoCV_3ejcW_R5r-qK-4Lfz6fhhUqur4UJ2vV3ajm_bgbRKkJqtxEX5stFin3oLWRgvOhRGZl4jtlu0GeReouJknnQCmqyzJv6DIy6u2eV3Xnch4ipN_indNHGs3noRF9NezfqDD5nUmdgm9oKOX3AMJpWZjIHb30To1xji_GR1ojQqOuQr4EaX0odynwgjx1thq2XA12JXWHQv8melfmaZbI3Sj9WJni_1rAF-hHfgmNA-poyxMECMDVlIfDgAt2iACMJkyBhCDA_oyYePs-2gTyilKAwpDoYBugp90KrcpHXg6RNhcN2i?type=png)](https://mermaid.live/edit#pako:eNqFUmFrwjAU_Cvlfa6SpC41YQzcdENwMKyfRkEyG63MNpKmbE7878ts59oubP3Ud3fc3SPvCCuVSOCw3qm3VSq08WbzOPfsN71f3o1ms8l8uYh6T9HoCV_3ejcW_R5r-qK-4Lfz6fhhUqur4UJ2vV3ajm_bgbRKkJqtxEX5stFin3oLWRgvOhRGZl4jtlu0GeReouJknnQCmqyzJv6DIy6u2eV3Xnch4ipN_indNHGs3noRF9NezfqDD5nUmdgm9oKOX3AMJpWZjIHb30To1xji_GR1ojQqOuQr4EaX0odynwgjx1thq2XA12JXWHQv8melfmaZbI3Sj9WJni_1rAF-hHfgmNA-poyxMECMDVlIfDgAt2iACMJkyBhCDA_oyYePs-2gTyilKAwpDoYBugp90KrcpHXg6RNhcN2i)

## Pre-Test Conditions
### Test System PSAP1, Test System PSAP2, Test System CALLER
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* ng911 repository cloned to local storage
* (TLS) Generated own PCA-signed certificate and private key files (test_system.crt, test_system.key)
* (TLS) Certificate and key used by BRIDGE copied to local storage
* (TLS) PCA certificate copied to local storage

### BRIDGE
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* IUT is active
* IUT is in normal operating state
* Default configuration is loaded
* IUT is initialized using IXIT config file

## Test Sequence

### Test Preamble

#### Test System PSAP1
* Install SIPp by following steps from documentation[^1]
* Install Wireshark[^2]
* (TLS v1.2) Configure Wireshark to decode HTTP over TLS, use tests system and FE certificate keys [^3]
* (TLS v1.3) Configure logging of session keys and configure Wireshark to decode HTTP over TLS [^4]
* Using Wireshark on 'Test System' start packet tracing on IF_TS_CHE interface - run following filter:
   * (TLS transport)
     > ip.addr == IF_TS1_BRIDGE_IP_ADDRESS and tls
   * (TCP transport)
     > ip.addr == IF_TS1_BRIDGE_IP_ADDRESS and sip

#### Test System PSAP2
* Install SIPp by following steps from documentation[^1]
* Install Wireshark[^2]
* (TLS v1.2) Configure Wireshark to decode HTTP over TLS, use tests system and FE certificate keys [^3]
* (TLS v1.3) Configure logging of session keys and configure Wireshark to decode HTTP over TLS [^4]
* Using Wireshark on 'Test System' start packet tracing on IF_TS_CHE interface - run following filter:
   * (TLS transport)
     > ip.addr == IF_TS2_BRIDGE_IP_ADDRESS and tls
   * (TCP transport)
     > ip.addr == IF_TS2_BRIDGE_IP_ADDRESS and sip

#### Test System CALLER
* Install SIPp by following steps from documentation[^1]
* Install Wireshark[^2]
* (TLS v1.2) Configure Wireshark to decode HTTP over TLS, use tests system and FE certificate keys [^3]
* (TLS v1.3) Configure logging of session keys and configure Wireshark to decode HTTP over TLS [^4]
* Using Wireshark on 'Test System' start packet tracing on IF_TS_CHE interface - run following filter:
   * (TLS transport)
     > ip.addr == IF_TS2_BRIDGE_IP_ADDRESS and tls
   * (TCP transport)
     > ip.addr == IF_TS2_BRIDGE_IP_ADDRESS and sip

#### Setup calls
* Prepare PSAP1 to receive call from CALLER
  On Test System PSAP1 run following SIPp scenario, example:
    * (TLS transport)
      > sudo sipp -t l1 -sf SIP_receive_call.xml IF_CALLER_TS-PSAP1_IP_ADDRESS:5060
    * (TCP transport)
      > sudo sipp -t t1 -sf SIP_receive_call.xml IF_CALLER_TS-PSAP1_IP_ADDRESS:5061
* Make call from CALLER to PSAP1
  On Test System CALLER run following SIPp scenario, example:
    * (TLS transport)
      > sudo sipp -t l1 -sf SIP_call_PSAP-CALLER.xml IF_CALLER_TS-PSAP1_IP_ADDRESS:5060
    * (TCP transport)
      > sudo sipp -t t1 -sf SIP_call_PSAP-CALLER.xml IF_CALLER_TS-PSAP1_IP_ADDRESS:5061
* On PSAP1 get Conference ID from 'Contact' header field in SIP 302 Moved Contact BRIDGE response
  On Test System PSAP1 run following SIPp scenario, example:
    * (TLS transport)
      > sudo sipp -t l1 -sf PSAP_get_Conference_ID_from_BRIDGE.xml IF_TS-PSAP1_BRIDGE_IP_ADDRESS:5060
    * (TCP transport)
      > sudo sipp -t t1 -sf PSAP_get_Conference_ID_from_BRIDGE.xml IF_TS-PSAP1_BRIDGE_IP_ADDRESS:5061
* Prepare CALLER to receive conference invitation from the BRIDGE:
  On Test System CALLER run following SIPp scenario, example:
    * (TLS transport)
      > sudo sipp -t l1 -sf CALLER_receive_conference_from_BRIDGE.xml IF_CALLER_BRIDGE_IP_ADDRESS:5060
    * (TCP transport)
      > sudo sipp -t t1 -sf CALLER_receive_conference_from_BRIDGE.xml IF_CALLER_BRIDGE_IP_ADDRESS:5061
* On PSAP1 create Conference with BRIDGE and transfer CALLER, for CONFERENCE_ID use SIP URI from 'Contact' header field in received SIP 302 Moved Contact response
  On Test System PSAP1 run following SIPp scenario, example:
    * (TLS transport)
      > sudo sipp -t l1 -s CONFERENCE_ID -sf PSAP_transfer_CALLER_to_conference_with_BRIDGE.xml IF_TS-PSAP1_BRIDGE_IP_ADDRESS:5060
    * (TCP transport)
      > sudo sipp -t t1 -s CONFERENCE_ID -sf PSAP_transfer_CALLER_to_conference_with_BRIDGE.xml IF_TS-PSAP1_BRIDGE_IP_ADDRESS:5061


### Test Body

#### Stimulus
Ask BRIDGE to invite PSAP2 to the conference. Send SIP REFER to BRIDGE - run following SIPp command on Test System PSAP1, example:
  * (TLS transport)
    > sudo sipp -t l1 -sf SIP_REFER_PSAP.xml IF_TS-PSAP1_BRIDGE_IP_ADDRESS:5060
  * (TCP transport)
    > sudo sipp -t t1 -sf SIP_REFER_PSAP.xml IF_TS-PSAP1_BRIDGE_IP_ADDRESS:5061

#### Response
* BRIDGE sends SIP INVITE to PSAP2
* SIP INVITE contains:
    - all SIP INVITE bodies from CALLER
    - CALLER location info (PIDF-LO xml body or location reference in 'Geolocation' header field)
    - Emergency Call Identifier copied from PSAP1 SIP REFER sent to BRIDGE
    - Incident Tracking Identifier copied from PSAP1 SIP REFER sent to BRIDGE
    - Request URI with service URN, f.e. `urn:service:sos`
    - 'Route' with SIP URI copied from 'Refer-To' of PSAP1 SIP REFER sent to BRIDGE
    - 'Route' shall contain 'lr' parameter
    - 'Referred-By' with PSAP1 SIP URI
    - 'Refer-To' with SIP URI of PSAP2

VERDICT:
* PASSED - if BRIDGE sends SIP INVITE to PSAP2 with expected contents
* FAILED - any other cases


### Test Postamble
#### Test System PSAP1, Test System PSAP2, Test System CALLER
* stop all SIPp processes (if still running)
* archive all logs generated
* stop Wireshark (if still running)
* remove ng911 repository files
* disconnect interfaces

#### BRIDGE
* reconnect interfaces back to default

## Post-Test Conditions 
#### Test System PSAP1, Test System PSAP2, Test System CALLER
* Test tools stopped
* interfaces disconnected from BRIDGE

### BRIDGE
* device connected back to default
* device in normal operating state

## Sequence Diagram
[![](https://mermaid.ink/img/pako:eNqlVF1vmzAU_SvWfR1UhnQQ_FApTdiEmqQI6KRNvFjgpGjBzoyZlkX573OgH8kSmtG9cc059577uYVM5AwImKaZ8kzwRbEkKUeoLKQUcpQpISuCFnRVsZQ3oIr9qBnP2KSgS0nLPRihhFUKxZtKsRKNR9OpH5k3N4ePYTwKLYLiIETB_EuQ-OgDiifhKbsBmn-xW5ct3cIYJXJT8OV7yEOMIk19g91NtnXk-7v-CY_Gd93BbqNg8tnvqkz7t9v1ANtoJn6yHI0FVzRTBFXFmmhjYQaTf4vaV95BgDNSu7We1P5Scm29-ycU-Z_86EhmxBZMmokgY7paMant9YpmrHqyzcZLH1FvYA8n5kzFzobuWoaXyTpMr5eCs829NLC3X_33b8dcKIb0SMpTtoFe8kiC2cP0If7vhu7hdr_OdQu0XwVGfhzez2P_gmv7qM_PO3i0HWBAyWRJi1yf2e3eXwrqkZUsBaI_cyq_p5DyncbRWol4wzMgStbMgHqdU_V8aIE0V9iANeXfhHi1WV7oKz1r73hzzhsMkC38AmLZzpXleJ7nDrDnDT3XNmADRL_q24Ete-h5GHvWtbMz4Hfj9vrKdhwHu65jDYYD_NE1QIp6-fgUcPcHpO3aeQ?type=png)](https://mermaid.live/edit#pako:eNqlVF1vmzAU_SvWfR1UhnQQ_FApTdiEmqQI6KRNvFjgpGjBzoyZlkX573OgH8kSmtG9cc059577uYVM5AwImKaZ8kzwRbEkKUeoLKQUcpQpISuCFnRVsZQ3oIr9qBnP2KSgS0nLPRihhFUKxZtKsRKNR9OpH5k3N4ePYTwKLYLiIETB_EuQ-OgDiifhKbsBmn-xW5ct3cIYJXJT8OV7yEOMIk19g91NtnXk-7v-CY_Gd93BbqNg8tnvqkz7t9v1ANtoJn6yHI0FVzRTBFXFmmhjYQaTf4vaV95BgDNSu7We1P5Scm29-ycU-Z_86EhmxBZMmokgY7paMant9YpmrHqyzcZLH1FvYA8n5kzFzobuWoaXyTpMr5eCs829NLC3X_33b8dcKIb0SMpTtoFe8kiC2cP0If7vhu7hdr_OdQu0XwVGfhzez2P_gmv7qM_PO3i0HWBAyWRJi1yf2e3eXwrqkZUsBaI_cyq_p5DyncbRWol4wzMgStbMgHqdU_V8aIE0V9iANeXfhHi1WV7oKz1r73hzzhsMkC38AmLZzpXleJ7nDrDnDT3XNmADRL_q24Ete-h5GHvWtbMz4Hfj9vrKdhwHu65jDYYD_NE1QIp6-fgUcPcHpO3aeQ)

## Comments

Version:  010.3f.3.0.2

Date:     20250326

## Footnotes
[^1]: SIPp - tool for SIP packet simulations. Official documentation: https://sipp.sourceforge.net/doc/reference.html#Getting+SIPp
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^4]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518
