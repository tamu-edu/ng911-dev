# Test Description: TD_BCF_001
## Overview
### Summary
Incoming SIP messages handling by O-BCF

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
- (TCP transport) - used as a fallback if use of TLS is not possible

### References
* Requirements : BCF_1, BCF_2, BCF_3, BCF_5, BCF_6, BCF_7, BCF_8
* Test Purpose : TP_BCF_001, TP_BCF_002, TP_BCF_003
* Test Case    :

## Configuration
### Implementation Under Test Interface Connections
<!-- Identify each of the FEs that are part of the configuration and how they are connected -->
* O-BCF
  * IF_O-BCF_OSP - connected to Test System IF_OSP_O-BCF
  * IF_O-BCF_ESRP - connected to Test System IF_ESRP_O-BCF
* Test System (OSP)
  * IF_OSP_O-BCF - connected to O-BCF IF_O-BCF_OSP
* Test System (ESRP)
  * IF_ESRP_O-BCF - connected to IF_O-BCF_ESRP

### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* Test System (OSP)
  * IF_OSP_O-BCF - Active
* O-BCF
  * IF_O-BCF_OSP - Active
  * IF_O-BCF_ESRP - Active
  * IF_O-BCF_TBCF - Passive
* Test System (ESRP)
  * IF_ESRP_O-BCF - Active

 
### Connectivity Diagram
[![](https://mermaid.ink/img/pako:eNp9kdsKwjAMhl-l5Hp7gV144QkERXFeSUHiGt3QtqNrkTF8d1srHqbYq-Trn_xp00GhBUEGh7O-FCUay-Zrrpg_s-luma92y3Q4mqbpIKQhDPAluJNJvl5FRYgijJLG7Y8G65JtqLEsbxtLkj0b9F0iJSV6xW-XH75fjZ7T_MCbPwbv032V99_kyyEBSUZiJfzPdQFzsCVJ4pD5UKA5ceDq6nXorM5bVUBmjaMEXC3Q0rhC7ywhO-C58bRGtdX6lZOorDaLuJr7hhIw2h3Lh-J6A-jHgv4?type=png)](https://mermaid.live/edit#pako:eNp9kdsKwjAMhl-l5Hp7gV144QkERXFeSUHiGt3QtqNrkTF8d1srHqbYq-Trn_xp00GhBUEGh7O-FCUay-Zrrpg_s-luma92y3Q4mqbpIKQhDPAluJNJvl5FRYgijJLG7Y8G65JtqLEsbxtLkj0b9F0iJSV6xW-XH75fjZ7T_MCbPwbv032V99_kyyEBSUZiJfzPdQFzsCVJ4pD5UKA5ceDq6nXorM5bVUBmjaMEXC3Q0rhC7ywhO-C58bRGtdX6lZOorDaLuJr7hhIw2h3Lh-J6A-jHgv4)

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

* (TLS transport) Copy to local storage SIP TLS certificate and private key files used to decrypt SIP packets within ESInet:
  > cacert.pem
  > cakey.pem

#### Test System ESRP
* Install SIPp by following steps from documentation[^1]
* Copy following XML scenario file to local storage:
  ```
  Receive_SIP_INVITE_from_O-BCF_regex_check.xml
  Receive_SIP_MESSAGE_from_O-BCF_regex_check.xml
  ```
 
* Install Wireshark[^2]
* (TLS transport) Copy to local storage SIP TLS certificate and private key files used to decrypt SIP packets within ESInet:
  > cacert.pem
  > cakey.pem
* (TLS transport) Configure Wireshark to decode SIP over TLS packets[^3]


### Test Body
**Following steps should be performed for all SIPp scenario files:**
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

  1. Using Wireshark on 'Test System ESRP' start packet tracing on IF_ESRP_O-BCF interface - run following filter:
     * (TLS transport)
       > ip.addr == IF_ESRP_O-BCF_IP_ADDRESS and tls
     * (TCP transport)
       > ip.addr == IF_ESRP_O-BCF_IP_ADDRESS and sip
  2. Prepare 'Test System ESRP' to receive SIP message - run SIPp tool with one of following commands:
     * (TCP transport)
       ```
       sudo sipp -t t1 -sf ./Receive_SIP_INVITE_from_O-BCF_regex_check.xml -i IF_ESRP_O-BCF_IP_ADDRESS:5060 -trace_logs -trace_msg -timeout 10 -max_recv_loops 1
       sudo sipp -t t1 -sf ./Receive_SIP_INVITE_from_O-BCF_regex_check.xml -i IF_ESRP_O-BCF_IP_ADDRESS:5060 -trace_logs -trace_msg -timeout 10 -max_recv_loops 1
       ```
     * (TLS transport)
       ```
       sudo sipp -t l1 -sf ./Receive_SIP_INVITE_from_O-BCF_regex_check.xml -i IF_ESRP_O-BCF_IPv4:5060 -trace_logs -trace_msg -timeout 10 -max_recv_loops 1
       sudo sipp -t l1 -sf ./Receive_SIP_INVITE_from_O-BCF_regex_check.xml -i IF_ESRP_O-BCF_IPv4:5060 -trace_logs -trace_msg -timeout 10 -max_recv_loops 1
       ```
  3. Send SIP packet to O-BCF - run following SIPp command on Test System OSP, example:
     * (TCP transport)
       ```
       sudo sipp -t t1 -sf SIP_INVITE_from_OSP.xml IF_OSP_O-BCF_IPv4:5060
       sudo sipp -t t1 -sf SIP_MESSAGE_from_OSP.xml IF_OSP_O-BCF_IPv4:5060
       ```
     * (TLS transport)
       ```
       sudo sipp -t l1 -sf SIP_INVITE_from_OSP.xml IF_OSP_O-BCF_IPv4:5060
       sudo sipp -t l1 -sf SIP_MESSAGE_from_OSP.xml IF_OSP_O-BCF_IPv4:5060
       ```
  4. Once the message is sent, stop Wireshark on 'Test System ESRP'
  5. Verify if SIP packet has been received by 'Test System ESRP' - SIPp script should stop automatically after receiving correct packet
  6. Verify SIPp log file on 'Test System ESRP', file should be named like:
    > RECEIVE_SIP_INVITE_FROM_O-BCF_CHECK_(PID)_logs.log
  7. Log file should include successful result of all tests, example:
```
       -- RECEIVE_SIP_INVITE_FROM_O-BCF_CHECK ---

      TEST 1/7 ( PASSED ) - Emergency Identifier URN: urn:emergency:uid:callid
      TEST 2/7 ( PASSED ) - Emergency Identifier String ID: callid:123qweasdz123qweasdz123qweasdz12:
      TEST 3/7 ( PASSED ) - Emergency Identifier Domain: urn:emergency:uid:callid:123qweasdz123qweasdz123qweasdz12:test.com
      TEST 4/7 ( PASSED ) - Incident Tracking Identifier URN: urn:emergency:uid:incidentid
      TEST 5/7 ( PASSED ) - Emergency Identifier String ID: incidentid:123qweasdz123qweasdz123qweasdz12:
      TEST 6/7 ( PASSED ) - Emergency Identifier Domain: urn:emergency:uid:incidentid:123qweasdz123qweasdz123qweasdz12:test.com
      TEST 7/7 ( PASSED ) - Resource-Priority: esnet.1
```
  8. **If SIPp logs have not been generated, verify Wireshark packets:**
     *  Using Wireshark open SIP INVITE or SIP MESSAGE packet received from O-BCF on IF_ESRP_O-BCF for verification
     *  Verify if 'To:' header field has been fixed, correct format is:
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
 
**Conditions for TEST PASSED verdict:**
* All steps performed for all SIPp scenarios
* All steps performed for SIP INVITE and/or SIP MESSAGE
* Step 7 for all scenarios printed all 7 test messages as PASSED
* In case step 7 was improssible to check, then all checks from step 8 should be passed

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
[![](https://mermaid.ink/img/pako:eNp1kLFOAzEQRH9ltS1n0buIFOBAV4SccESB3Fj25mKB7bC2iyjKv3PngKCh25HejGb2jDY5QolCCB1tins_SR0BgmdOvLYlcZawNx-ZdGxQps9K0dKDNxObsMAAO8oF1CkXCrBVo1itbrbi7v5RghpGGJ5fh10Pt01seqXWT_3V16CF_hvQq5fxfyN2GIiD8W6ufV5iNJYDBdIo59MZfteo42XmTC1JnaJFWbhSh_XoTPkpjrKt6vBo4ltKv5qcn1dvrn9p7-mQU50O38TlC94CYnU?type=png)](https://mermaid.live/edit#pako:eNp1kLFOAzEQRH9ltS1n0buIFOBAV4SccESB3Fj25mKB7bC2iyjKv3PngKCh25HejGb2jDY5QolCCB1tins_SR0BgmdOvLYlcZawNx-ZdGxQps9K0dKDNxObsMAAO8oF1CkXCrBVo1itbrbi7v5RghpGGJ5fh10Pt01seqXWT_3V16CF_hvQq5fxfyN2GIiD8W6ufV5iNJYDBdIo59MZfteo42XmTC1JnaJFWbhSh_XoTPkpjrKt6vBo4ltKv5qcn1dvrn9p7-mQU50O38TlC94CYnU)


## Comments

Version:  010.3d.1.0.11

Date:     2024.07.24


## Footnotes
[^1]: SIPp - tool for SIP packet simulations. Official documentation: https://sipp.sourceforge.net/doc/reference.html#Getting+SIPp
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt SIP over TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream

