# Test Description: TD_BCF_001
## Overview
### Summary
Adding Emergency Call, Incident Tracking identifiers and Resource Priority

### Description
This test checks header fields added by O-BCF while routing SIP packets inside ESInet:
* Emergency Call Identifier
* Incident Tracking Identifier
* Resource Priority

Test covers following SIP message variants:
* SIP INVITE
* SIP MESSAGE

Test steps description:
* 'Test System OSP' simulates SIP packets heading to O-BCF
* O-BCF will route the same packets with added default headers to ESRP
* 'Test System ESRP' receives SIP packets with added identifiers same way as ESRP normally would do

### SIP transport types
Test can be performed with 2 different SIP transport types. Steps describing actions for specific one are marked as following:
- (TLS transport) - used by default inside ESInet on production environment
- (TCP transport) - used in lab for testing purposes only if default TLS is not possible

### References
* Requirements : RQ_BCF_001, RQ_BCF_045, RQ_BCF_046, RQ_BCF_002, RQ_BCF_003, RQ_BCF_005, RQ_BCF_006, RQ_BCF_007, RQ_BCF_008
* Test Case    : TC_BCF_001

### Requirements
IXIT config file for BCF

## Configuration
### Implementation Under Test Interface Connections
<!-- Identify each of the FEs that are part of the configuration and how they are connected -->
* Test System (OSP)
  * IF_OSP_O-BCF - connected to O-BCF IF_O-BCF_OSP
* O-BCF
  * IF_O-BCF_OSP - connected to Test System IF_OSP_O-BCF
  * IF_O-BCF_ESRP - connected to Test System IF_ESRP_O-BCF
* Test System (ESRP)
  * IF_ESRP_O-BCF - connected to IF_O-BCF_ESRP

### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* Test System (OSP)
  * IF_OSP_O-BCF - Active
* O-BCF
  * IF_O-BCF_OSP - Active
  * IF_O-BCF_ESRP - Monitor
* Test System (ESRP)
  * IF_ESRP_O-BCF - Monitor

 
### Connectivity Diagram
<!--
[![](https://mermaid.ink/img/pako:eNp1kU1PhDAQhv8KmTMQvlt68ODqJiaa3SyeDMmmQheICyWlRJHw3y2g7Iqxp-nbZ-ad6fSQ8JQBgdOZvyc5FVJ7PMSVps7D9riL9sedcbvZGsbNeB3DUbwAk3IfHfYzMUazOCNN-5oJWufaM2ukFnWNZKW2FFi7zCqr0lXy1eMv3z-Flm7-q3TdxoX7Tl83r9JBh5KJkhap-qJ-lGOQOStZDESFKRVvMcTVoDjaSh51VQJEipbp0NYpleyuoMq5BHKi50apNa1eOC9_IJYWkouneQXTJiYESA8fQFyMTeRgD4dBgJAbYB06IL5tmyG2XOxjxwpD7A46fE41LdN3PNv1Qw85DvKQ4gVvs3xxz8Q4yGwt1HhMbHhbSSB2MHwBFBKYzA?type=png)](https://mermaid.live/edit#pako:eNp1kU1PhDAQhv8KmTMQvlt68ODqJiaa3SyeDMmmQheICyWlRJHw3y2g7Iqxp-nbZ-ad6fSQ8JQBgdOZvyc5FVJ7PMSVps7D9riL9sedcbvZGsbNeB3DUbwAk3IfHfYzMUazOCNN-5oJWufaM2ukFnWNZKW2FFi7zCqr0lXy1eMv3z-Flm7-q3TdxoX7Tl83r9JBh5KJkhap-qJ-lGOQOStZDESFKRVvMcTVoDjaSh51VQJEipbp0NYpleyuoMq5BHKi50apNa1eOC9_IJYWkouneQXTJiYESA8fQFyMTeRgD4dBgJAbYB06IL5tmyG2XOxjxwpD7A46fE41LdN3PNv1Qw85DvKQ4gVvs3xxz8Q4yGwt1HhMbHhbSSB2MHwBFBKYzA)
-->

![image](https://github.com/user-attachments/assets/4a412d95-3a81-4bac-b0d2-b277dc67c925)


## Pre-Test Conditions

### Test System OSP
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* No active calls
* (TLS transport) Test System OSP has it's own certificate signed by PCA

### O-BCF
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Default configuration is loaded
* Device has configured `Test System ESRP` as a next hop
* Device is initialized with steps from IXIT config file
* Device is active
* Device is in normal operating state
* No active calls

### Test System ESRP
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* No active calls
* (TLS transport) Test System ESRP has it's own certificate signed by PCA

## Test Sequence
### Test Preamble
#### Test System OSP
* Install SIPp by following steps from documentation[^1]
* Copy following XML scenario files to local storage:
  ```
  SIP_INVITE_from_OSP.xml
  SIP_INVITE_from_OSP_incorrect_1.xml
  SIP_INVITE_from_OSP_incorrect_2.xml
  SIP_INVITE_from_OSP_incorrect_3.xml
  SIP_MESSAGE_from_OSP.xml
  SIP_MESSAGE_from_OSP_incorrect_1.xml
  SIP_MESSAGE_from_OSP_incorrect_2.xml
  SIP_MESSAGE_from_OSP_incorrect_3.xml
  ```
* (TLS transport) Copy to local storage PCA-signed certificate and private key files:
  > PCA-cacert.pem
  > PCA-cakey.pem
* (TLS transport) Copy to local storage PCA-signed certificate and private key files for O-BCF:
  > O-BCF-cacert.pem
  > O-BCF-cakey.pem


#### Test System ESRP
* Install SIPp by following steps from documentation[^1]
* Install Wireshark[^2]
* (TLS transport) Copy to local storage PCA-signed certificate and private key files:
  > PCA-cacert.pem
  > PCA-cakey.pem
* (TLS transport) Copy to local storage PCA-signed certificate and private key files for O-BCF:
  > O-BCF-cacert.pem
  > O-BCF-cakey.pem
* (TLSv1.2 transport) Configure Wireshark to decode SIP over TLS packets[^3]
* (TLSv1.3 transport) Configure Wireshark to decode SIP over TLS packets[^4]
* Using Wireshark on 'Test System ESRP' start packet tracing on IF_ESRP_O-BCF interface - run following filter:
     * (TLS transport)
       > ip.addr == IF_ESRP_O-BCF_IP_ADDRESS and tls
     * (TCP transport)
       > ip.addr == IF_ESRP_O-BCF_IP_ADDRESS and sip


### Test Body
#### Variations

1. SIP_INVITE_from_OSP.xml
2. SIP_INVITE_from_OSP_incorrect_1.xml - incorrect 'To' header field
3. SIP_INVITE_from_OSP_incorrect_2.xml - incorrect 'To' header field
4. SIP_INVITE_from_OSP_incorrect_3.xml - incorrect 'To' header field
5. SIP_MESSAGE_from_OSP.xml
6. SIP_MESSAGE_from_OSP_incorrect_1.xml - incorrect 'To' header field
7. SIP_MESSAGE_from_OSP_incorrect_2.xml - incorrect 'To' header field
8. SIP_MESSAGE_from_OSP_incorrect_3.xml - incorrect 'To' header field

#### Stimulus
Send SIP packet to O-BCF - run following SIPp command on Test System OSP, example:
* (TCP transport)
  ```
  sudo sipp -t t1 -sf SCENARIO_FILE -i IF_OSP_O-BCF IF_O-BCF_OSP:5060
  ```
* (TLS transport)
  ```
  sudo sipp -t l1 -tls_cert PCA-cacert.pem -tls_key PCA-cakey.pem -sf SCENARIO_FILE -i IF_OSP_O-BCF IF_O-BCF_OSP:5061
  ```

#### Response
Variations 1-8
*  Using Wireshark open SIP INVITE or SIP MESSAGE packet received from O-BCF on IF_ESRP_O-BCF for verification
*  Verify if Request-URI is rewritten to: 
   > To: urn:service:sos
*  Verify Emergency Call Identifier included in "Call-Info" header field:
  * if header field contains "urn:emergency:uid:callid:"
  * if "urn:emergency:uid:callid:" is followed by 10 to 32 alphanumeric characters (String ID)
  * if String ID is followed by ":" and O-BCF domain name
* Verify Incident Tracking Identifier included in "Call-Info" header field:
  * if header field contains "urn:emergency:uid:incidentid:"
  * if "urn:emergency:uid:incidentid:" is followed by 10 to 32 alphanumeric characters (String ID)
  * if String ID is followed by ":" and O-BCF domain name
* Verify Resource-Priority header field, default value should be added:
  > Resource-Priority: esnet.1

VERDICT:
* PASSED - if all checks passed for variation
* FAILED - all other cases


### Test Postamble
#### Test System OSP
* stop all SIPp processes (if still running)
* archive all logs generated
* remove all SIPp scenarios
* disconnect interfaces from O-BCF
* (TLS transport) remove certificates

#### O-BCF
* disconnect IF_O-BCF_OSP
* disconnect IF_O-BCF_ESRP
* reconnect interfaces back to default

#### Test System ESRP
* stop all SIPp processes (if still running)
* stop Wireshark (if still running)
* archive traced packets in Wireshark
* remove certificate files
* disconnect interfaces from O-BCF
* (TLS transport) remove certificates


## Post-Test Conditions
### Test System OSP
* Test tools stopped
* interfaces disconnected from O-BCF

### O-BCF
* device connected back to default
* device in normal operating state

### Test System ESRP
* Test tools stopped
* interfaces disconnected from O-BCF


## Sequence Diagram
<!--
[![](https://mermaid.ink/img/pako:eNp1kLFOAzEQRH9ltS1n0buIFOBAV4SccESB3Fj25mKB7bC2iyjKv3PngKCh25HejGb2jDY5QolCCB1tins_SR0BgmdOvLYlcZawNx-ZdGxQps9K0dKDNxObsMAAO8oF1CkXCrBVo1itbrbi7v5RghpGGJ5fh10Pt01seqXWT_3V16CF_hvQq5fxfyN2GIiD8W6ufV5iNJYDBdIo59MZfteo42XmTC1JnaJFWbhSh_XoTPkpjrKt6vBo4ltKv5qcn1dvrn9p7-mQU50O38TlC94CYnU?type=png)](https://mermaid.live/edit#pako:eNp1kLFOAzEQRH9ltS1n0buIFOBAV4SccESB3Fj25mKB7bC2iyjKv3PngKCh25HejGb2jDY5QolCCB1tins_SR0BgmdOvLYlcZawNx-ZdGxQps9K0dKDNxObsMAAO8oF1CkXCrBVo1itbrbi7v5RghpGGJ5fh10Pt01seqXWT_3V16CF_hvQq5fxfyN2GIiD8W6ufV5iNJYDBdIo59MZfteo42XmTC1JnaJFWbhSh_XoTPkpjrKt6vBo4ltKv5qcn1dvrn9p7-mQU50O38TlC94CYnU)
-->

![image](https://github.com/user-attachments/assets/71e2797b-0bb9-4207-8567-e394d47723f5)

## Comments

Version:  010.3d.3.2.15

Date:     20250728

## Footnotes
[^1]: SIPp - tool for SIP packet simulations. Official documentation: https://sipp.sourceforge.net/doc/reference.html#Getting+SIPp
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt SIP over TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^4]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518
