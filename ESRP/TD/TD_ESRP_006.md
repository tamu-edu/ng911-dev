# Test Description: TD_ESRP_006
## Overview
### Summary
SIP INVITE exiting ESRP

### Description
Test verifies SIP INVITE messages exiting ESRP:
- Via header field specifying ESRP
- Route header field containing URI of downstream queue receiving a call
- if Emergency Call Identifier is added
- if Incident Tracking ID is added
- if ESRP do not remove header fields received from upstream interface
- if ESRP has implemented LoST interface


### SIP transport types
Test can be performed with 2 different SIP transport types. Steps describing actions for specific one are marked as following:
- (TLS transport) - used by default inside ESInet on production environment
- (TCP transport) - used in lab for testing purposes only if default TLS is not possible

### References
* Requirements : RQ_ESRP_042, RQ_ESRP_043, RQ_ESRP_045, RQ_ESRP_046, RQ_ESRP_048, RQ_ESRP_049
* Test Case    : TC_ESRP_006

### Requirements
IXIT config file for ESRP

## Configuration
### Implementation Under Test Interface Connections
* Test System 1 (Upstream ESRP)
  * IF_TS1_ESRP - connected to IF_ESRP_TS1
* ESRP
  * IF_ESRP_TS1 - connected to Test System 1 IF_TS1_ESRP
  * IF_ESRP_TS2 - connected to Test System 2 IF_TS2_ESRP
  * IF_ESRP_TS-ECRF - connected to Test System ECRF IF_TS-ECRF_ESRP
* Test System ECRF
  * IF_TS-ECRF_ESRP - connected to IF_ESRP_TS-ECRF
* Test System 2 (Downstream ESRP)
  * IF_TS2_ESRP - connected to IF_ESRP_TS2


### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* Test System 1 (Upstream ESRP)
  * IF_TS1_ESRP - Active
* ESRP
  * IF_ESRP_TS1 - Active
  * IF_ESRP_TS2 - Monitor
  * IF_ESRP_TS-ECRF - Active
* Test System ECRF
  * IF_TS-ECRF_ESRP - Active
* Test System 2 (Downstream ESRP)
  * IF_TS2_ESRP - Active
 
 
### Connectivity Diagram
<!--
[![](https://mermaid.ink/img/pako:eNp9klFrgzAQx7-K3LOVJmo1Yeyla2Gwwah9GkLJNK2ymkiMbK70uy9a56p0y1Pun9_d_Y_LCRKZcqCwP8qPJGNKW0-bWFjmPK532wjtVtHmZWbOvYnbeysOQC_MVsvN-q6H-rB7m4J4NkD4Cqjqt4NiZWZteaWtqKk0L6y-y8TKReQinWT-vo07olsiviV2rv8qf21shA72pkP_XwNPsvE4E2wouCpYnprVnFo5Bp3xgsdAzTVl6j2GWJwNx2oto0YkQLWquQ11mTLNH3JmmhZA9-xYGbVk4lXK4gfiaa6ler6svvsBHQL0BJ9APeQgFxOP-GHghsibezY0QLHvO36w8IN5iAjxgkV4tuGrqzp3wpAsPBcRjAnCPiE2KFkfssHAQbWzXLorMyFXS1kLDRS5wfkb9z67ig?type=png)](https://mermaid.live/edit#pako:eNp9klFrgzAQx7-K3LOVJmo1Yeyla2Gwwah9GkLJNK2ymkiMbK70uy9a56p0y1Pun9_d_Y_LCRKZcqCwP8qPJGNKW0-bWFjmPK532wjtVtHmZWbOvYnbeysOQC_MVsvN-q6H-rB7m4J4NkD4Cqjqt4NiZWZteaWtqKk0L6y-y8TKReQinWT-vo07olsiviV2rv8qf21shA72pkP_XwNPsvE4E2wouCpYnprVnFo5Bp3xgsdAzTVl6j2GWJwNx2oto0YkQLWquQ11mTLNH3JmmhZA9-xYGbVk4lXK4gfiaa6ler6svvsBHQL0BJ9APeQgFxOP-GHghsibezY0QLHvO36w8IN5iAjxgkV4tuGrqzp3wpAsPBcRjAnCPiE2KFkfssHAQbWzXLorMyFXS1kLDRS5wfkb9z67ig)
-->

![image](https://github.com/user-attachments/assets/0f8fff20-d2cf-4d91-85d0-3b07936f6e12)


## Pre-Test Conditions
### Test System 1
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* No active calls
* Test System has it's own certificate signed by PCA

### ESRP
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* Device is in normal operating state
* Device is initialized with steps from IXIT config file
* No active calls
* Logging enabled
* Device is configured to use Test System ECRF for LoST requests on '/lost' URL entrypoint
* Device is configured to use Test System 2 as a next hop host

### Test System ECRF
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* Test System has it's own certificate signed by PCA

### Test System 2
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* No active calls
* Test System has it's own certificate signed by PCA

## Test Sequence

### Test Preamble

#### Test System 1
* Install SIPp by following steps from documentation[^1]
* Copy following XML scenario files to local storage:
  ```
  SIP_INVITE_location_PIDF-LO_Boundary1_without_identifiers.xml
  ```
* Install Wireshark[^2]
* (TLS transport) Copy to local storage PCA-signed TLS certificate and private key files:
  ```
  PCA-cacert.pem
  PCA-cakey.pem
  ```
* (TLS transport) Copy to local storage TLS certificate and private key files used by ESRP:
  ```
  ESRP-cacert.pem
  ESRP-cakey.pem
  ```
* (TLS transport) Configure Wireshark to decode SIP over TLS packets from Test System and ESRP as well[^3]
* Using Wireshark on 'Test System' start packet tracing on IF_TS1_ESRP interface - run following filter:
   * (TLS transport)
     > ip.addr == IF_TS1_ESRP_IP_ADDRESS and tls
   * (TCP transport)
     > ip.addr == IF_TS1_ESRP_IP_ADDRESS and sip

#### Test System 2
* Install SIPp by following steps from documentation[^1]
* Copy following XML scenario files to local storage:
  ```
  SIP_INVITE_RECEIVE.xml
  ```
* Install Wireshark[^2]
* (TLS transport) Copy to local storage PCA-signed TLS certificate and private key files:
  ```
  PCA-cacert.pem
  PCA-cakey.pem
  ```
* (TLS transport) Copy to local storage TLS certificate and private key files used by ESRP:
  ```
  ESRP-cacert.pem
  ESRP-cakey.pem
  ```
* (TLS transport) Configure Wireshark to decode SIP over TLS packets from Test System and ESRP as well[^3]
* Using Wireshark on 'Test System' start packet tracing on IF_TS2_ESRP interface - run following filter:
   * (TLS transport)
     > ip.addr == IF_TS2_ESRP_IP_ADDRESS and tls
   * (TCP transport)
     > ip.addr == IF_TS2_ESRP_IP_ADDRESS and sip


 #### Test System ECRF
* Install Wireshark[^2]
* Copy following scenario files to local storage:
  ```
  findServiceResponse
  ```
* (TLS transport) Copy to local storage PCA-signed TLS certificate and private key files:
  ```
  PCA-cacert.pem
  PCA-cakey.pem
  ```
* (TLS transport) Copy to local storage TLS certificate and private key files used by ESRP:
  ```
  ESRP-cacert.pem
  ESRP-cakey.pem
  ```
* (TLS transport) Configure Wireshark to decode HTTP over TLS packets from Test System and ESRP as well[^3]
* Using Wireshark on 'Test System' start packet tracing on IF_TS-ECRF_ESRP interface - run following filter:
   * (TLS transport)
     > ip.addr == IF_TS-ECRF_ESRP_IP_ADDRESS and tls
   * (TCP transport)
     > ip.addr == IF_TS-ECRF_ESRP_IP_ADDRESS and sip
* Rename PCA-signed certificate files for Test System ECRF to server.pem and server.key
* Start https server responding for HTTPS GET requests:
   ```
   echo -e "HTTP/1.1 200 OK\r\nContent-Type: application/lost+xml\r\nContent-Length: 1167\r\n\r\n$(cat findServiceResponse | sed -n  '/<?xml/,/findServiceResponse>/p')\r\n" | \
   openssl s_server -quiet -accept LOCAL_PORT -cert server.pem -key server.key
   ```

### Test Body

#### Stimulus
Send SIP packet to ESRP - run following SIPp command on Test System 1, example:
* (TCP transport)
  ```
  sudo sipp -t t1 -sf SIP_INVITE_location_PIDF-LO_Boundary1_without_identifiers.xml -i IF_TS1_ESRP_IP_ADDRESS:5060 IF_ESRP_TS1_IP_ADDRESS:5060 -max_recv_loops 1 -m 1
  ```
* (TLS transport)
  ```
  sudo sipp -t l1 -tls_cert PCA-cacert.pem -tls_key PCA-cakey.pem -sf SIP_INVITE_location_PIDF-LO_Boundary1_without_identifiers.xml -i IF_TS1_ESRP_IP_ADDRESS:5060 IF_ESRP_TS1_IP_ADDRESS:5060 -max_recv_loops 1 -m 1
  ```

#### Response
* ESRP sends HTTP LoST query to Test System ECRF with findService request
* findService request contains geolocation from received SIP INVITE
* SIP INVITE has 'Via' header field specifying ESRP
* SIP INVITE has 'Route' header field containing Test System 2 queue URI received from Test System ECRF
* SIP INVITE has 'Route' header field containing 'lr' parameter
* Verify Emergency Call Identifier included in "Call-Info" header field from SIP INVITE:
  * if header field contains "urn:emergency:uid:callid:"
  * if "urn:emergency:uid:callid:" is followed by 10 to 32 alphanumeric characters (String ID)
  * if String ID is followed by ":" and ESRP domain name
* Verify if Call-Info header field with CallId contains 'emergency-CallId' purpose
* Verify Incident Tracking Identifier included in "Call-Info" header field from SIP INVITE:
  * if header field contains "urn:emergency:uid:incidentid:"
  * if "urn:emergency:uid:incidentid:" is followed by 10 to 32 alphanumeric characters (String ID)
  * if String ID is followed by ":" and ESRP domain name
* Verify if Call-Info header field with IncidentId contains 'emergency-IncidentId' purpose
* verify if all header fields from SIP INVITE received from Test System 1 are included in SIP INVITE addressed to Test System 2

VERDICT:
* PASSED - if all checks passed for variation
* FAILED - all other cases
<!--
* INCONCLUSIVE - 
* ERROR - 
-->

### Test Postamble
#### Test System 1
* stop Sipp process (if still running)
* archive all logs generated
* stop Wireshark (if still running)
* remove all scenario files
* disconnect interfaces from ESRP
* (TLS transport) remove certificates

#### ESRP
* disconnect interfaces from Test Systems
* reconnect interfaces back to default
* restore previous configuration

#### Test System ECRF
* stop http server
* archive all logs generated
* stop Wireshark (if still running)
* remove all scenario files
* disconnect interfaces from ESRP
* (TLS transport) remove certificates

#### Test System 2
* stop Sipp process (if still running)
* archive all logs generated
* stop Wireshark (if still running)
* remove all scenario files
* disconnect interfaces from ESRP
* (TLS transport) remove certificates

## Post-Test Conditions
### Test System 1
* Test tools stopped
* interfaces disconnected from ESRP

### ESRP
* device connected back to default
* device in normal operating state

### Test System ECRF
* Test tools stopped
* interfaces disconnected from ESRP

### Test System 2
* Test tools stopped
* interfaces disconnected from ESRP

## Sequence Diagram
<!--
[![](https://mermaid.ink/img/pako:eNp9kF9PgzAUxb9Kc580wkILjLYPS8xEXfxHBvHB8NJAx4jSzlIS57LvLrDM7cHYp5v0d-655-yg0KUEDq7r5qrQalVXPFcINbUx2lwXVpuWo5X4aGWuRqiVn51UhbypRWVEM8CHl8nWonTbWtkg7M5mV3G6TDhKFwlaPL8usviEDj8DcS6J58tbju6zLEF3cYYuHnWaXf69fUBPBqOEeB56efjfgZwfAw400jSiLvv0u0GYg13LRubA-7EU5j2HXO17TnRWp1tVALemkw50m1LYY37gYzkObIR607o5QrKs--6eDu2OJY8I8B18AQ_wBPuEBSykkU9x4AUObIGTMJyE0TSMPIoZC6Ip3TvwPW71JpSyaeBjRgjDJGTUAaO7av17QGWGLAd3I1UpzVx3ygLH1N__ACelkNM?type=png)](https://mermaid.live/edit#pako:eNp9kF9PgzAUxb9Kc580wkILjLYPS8xEXfxHBvHB8NJAx4jSzlIS57LvLrDM7cHYp5v0d-655-yg0KUEDq7r5qrQalVXPFcINbUx2lwXVpuWo5X4aGWuRqiVn51UhbypRWVEM8CHl8nWonTbWtkg7M5mV3G6TDhKFwlaPL8usviEDj8DcS6J58tbju6zLEF3cYYuHnWaXf69fUBPBqOEeB56efjfgZwfAw400jSiLvv0u0GYg13LRubA-7EU5j2HXO17TnRWp1tVALemkw50m1LYY37gYzkObIR607o5QrKs--6eDu2OJY8I8B18AQ_wBPuEBSykkU9x4AUObIGTMJyE0TSMPIoZC6Ip3TvwPW71JpSyaeBjRgjDJGTUAaO7av17QGWGLAd3I1UpzVx3ygLH1N__ACelkNM)
-->

![image](https://github.com/user-attachments/assets/1933a96d-e026-4d0d-bacc-6a340ef450cb)


## Comments

Version:  010.3d.3.0.8

Date:     20250519

## Footnotes
[^1]: SIPp - tool for SIP packet simulations. Official documentation: https://sipp.sourceforge.net/doc/reference.html#Getting+SIPp
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt SIP over TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
