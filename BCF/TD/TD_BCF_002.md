# Test Description: TD_BCF_002
## Overview
### Summary
Discrepancy Reporting by O-BCF on incorrect SIP message from OSP

### Description
This test checks Discrepancy Report sending by O-BCF when incorrect SIP message is received from OSP:
* XML with all required fields
* incorrect resolution detection from DR server and appriopriate responding
* report resolution when correct message from DR server is received

### SIP and HTTP transport types
Test can be performed with 2 different SIP and HTTP transport types. Steps describing actions for specific one are marked as following:
- (TLS transport) - used by default inside ESInet on production environment
- (TCP transport) - used in lab for testing purposes only if default TLS is not possible

### References
* Requirements : RQ_BCF_009
* Test Case    :

### Requirements
IXIT config file for BCF

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
  * IF_O-BCF_ESRP - Monitor
* Test System (ESRP)
  * IF_ESRP_O-BCF - Monitor

 
### Connectivity Diagram
<!--
[![](https://mermaid.ink/img/pako:eNp9kdsKwjAMhl-l5Hp7gV144QkERXFeSUHiGt3QtqNrkTF8d1srHqbYq-Trn_xp00GhBUEGh7O-FCUay-Zrrpg_s-luma92y3Q4mqbpIKQhDPAluJNJvl5FRYgijJLG7Y8G65JtqLEsbxtLkj0b9F0iJSV6xW-XH75fjZ7T_MCbPwbv032V99_kyyEBSUZiJfzPdQFzsCVJ4pD5UKA5ceDq6nXorM5bVUBmjaMEXC3Q0rhC7ywhO-C58bRGtdX6lZOorDaLuJr7hhIw2h3Lh-J6A-jHgv4?type=png)](https://mermaid.live/edit#pako:eNp9kdsKwjAMhl-l5Hp7gV144QkERXFeSUHiGt3QtqNrkTF8d1srHqbYq-Trn_xp00GhBUEGh7O-FCUay-Zrrpg_s-luma92y3Q4mqbpIKQhDPAluJNJvl5FRYgijJLG7Y8G65JtqLEsbxtLkj0b9F0iJSV6xW-XH75fjZ7T_MCbPwbv032V99_kyyEBSUZiJfzPdQFzsCVJ4pD5UKA5ceDq6nXorM5bVUBmjaMEXC3Q0rhC7ywhO-C58bRGtdX6lZOorDaLuJr7hhIw2h3Lh-J6A-jHgv4)
-->

![image](https://github.com/user-attachments/assets/f293c609-456b-4982-bbb9-4dadc1e75c83)


## Pre-Test Conditions

### Test System OSP
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* No active calls

### O-BCF
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Default configuration is loaded
* Device is initialized with steps from IXIT config file
* Device is active
* Device is in normal operating state
* No active calls

### Test System ESRP
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* No active calls


## Test Sequence
### Test Preamble
#### Test System OSP
* Install SIPp by following steps from documentation[^2]
* Copy following XML scenario files to local storage:
  ```
  SIP_INVITE_from_OSP_incorrect_1.xml
  SIP_INVITE_from_OSP_incorrect_2.xml
  SIP_INVITE_from_OSP_incorrect_3.xml
  ```
* (TLS transport) Copy to local storage SIP TLS certificate and private key files used to decrypt SIP packets within ESInet:
  > cacert.pem
  > cakey.pem

#### O-BCF
* Configure Discrepancy Report server to 'Test System ESRP'
* Reload configuration (or reboot device)

#### Test System ESRP
* Install SIPp by following steps from documentation[^2]
* Install Netcat (NC)[^1]
* Copy following XML scenario file to local storage:
  > SIP_INVITE_RECEIVE.xml
* Install Wireshark[^3]
* (TLS transport) Copy to local storage SIP TLS certificate and private key files used to decrypt SIP packets within ESInet:
  > cacert.pem
  > cakey.pem
* (TLS transport) Configure Wireshark to decode SIP over TLS packets[^4]
* On 'Test System ESRP' Start simple HTTP server basing on netcat. Used to receive HTTP request and respond with 201 code
   * (TLS transport)
     > echo -e 'HTTP/1.1 201 Discrepancy Resolution successfully created\r\nContent-Length: 0\r\n' | nc -lp 443
   * (TCP transport)
     > echo -e 'HTTP/1.1 201 Discrepancy Resolution successfully created\r\nContent-Length: 0\r\n' | nc -lp 80

* Using Wireshark on 'Test System ESRP' start packet tracing on IF_ESRP_O-BCF interface - run following filter:
   * (TLS transport)
     > ip.addr == IF_TS_LIS_IP_ADDRESS and tls
   * (TCP transport)
     > ip.addr == IF_TS_LIS_IP_ADDRESS and http


### Test Body
#### Variations
1. SIP_INVITE_FROM_OSP_INCORRECT_1.xml + HTTP_Incorrect_Discrepancy_Resolution_JSON
2. SIP_INVITE_FROM_OSP_INCORRECT_2.xml + HTTP_Incorrect_Discrepancy_Resolution_JSON
3. SIP_INVITE_FROM_OSP_INCORRECT_3.xml + HTTP_Incorrect_Discrepancy_Resolution_JSON
4. SIP_INVITE_FROM_OSP_INCORRECT_1.xml + HTTP_Discrepancy_Resolution_JSON
5. SIP_INVITE_FROM_OSP_INCORRECT_2.xml + HTTP_Discrepancy_Resolution_JSON
6. SIP_INVITE_FROM_OSP_INCORRECT_3.xml + HTTP_Discrepancy_Resolution_JSON

#### Stimulus
1. Send SIP packet to O-BCF - run SIPp command with scenario file for variation being tested on Test System OSP, example:
* (TCP transport)
  ```
  sudo sipp -t t1 -sf SIP_INVITE_INCORRECT_EMERGENCY_SINGLE_1.xml IF_OSP_O-BCF_IPv4:5060
  ```
* (TLS transport)
  ```
  sudo sipp -t l1 -sf SIP_INVITE_INCORRECT_EMERGENCY_SINGLE_1.xml IF_OSP_O-BCF_IPv4:5060
  ```

2. Send HTTP response from Test System ESRP using message file for variation being tested, example:
* (TLS transport)
  ```
  cat HTTP_Incorrect_Discrepancy_Resolution_JSON | openssl s_client -connect IF_O-BCF_ESRP_IPv4:443 -CAfile cacert.pem -ign_eof
  ```
* (TCP transport)
  ```
  cat HTTP_Incorrect_Discrepancy_Resolution_JSON | nc IF_O-BCF_ESRP_IPv4 80
  ```

#### Response
Variations 1-3
* Using Wireshark open Discrepancy Report (HTTP packet) received from O-BCF on IF_ESRP_O-BCF for verification, following header fields and values should be included in JSON message:
  ```
  "resolutionUri": "http://TEST_SYSTEM_OSP_ADDRESS/Resolutions"
  "reportType": "OriginatingService"
  "discrepancyReportSubmittalTimeStamp": "MESSAGE_TIMESTAMP"
  "discrepancyReportId": "REPORT_ID"
  "reportingAgencyName": "TEST_SYSTEM_OSP_FQDN_ADDRESS"
  "reportingContactJcard": "TEST_SYSTEM_OSP_JCARD"
  "problemService": "OriginatingService"
  "problemSeverity": "Moderate"
  "problemComments": "SIP_INVITE_SENT_FROM_TEST_SYSTEM_OSP"
  "problem": "BadSIP"
  "callHeader": "TO_HEADER_OF_SIP_INVITE_SENT"
  ```
* After sending HTTP response from Test System ESRP, verify if O-BCF responds with error message:
  ```
  454 Unspecified Error
  ```
Variations 4-6
* Using Wireshark open Discrepancy Report (HTTP packet) received from O-BCF on IF_ESRP_O-BCF for verification, following header fields and values should be included in JSON message:
  ```
  "resolutionUri": "http://TEST_SYSTEM_OSP_ADDRESS/Resolutions"
  "reportType": "OriginatingService"
  "discrepancyReportSubmittalTimeStamp": "MESSAGE_TIMESTAMP"
  "discrepancyReportId": "REPORT_ID"
  "reportingAgencyName": "TEST_SYSTEM_OSP_FQDN_ADDRESS"
  "reportingContactJcard": "TEST_SYSTEM_OSP_JCARD"
  "problemService": "OriginatingService"
  "problemSeverity": "Moderate"
  "problemComments": "SIP_INVITE_SENT_FROM_TEST_SYSTEM_OSP"
  "problem": "BadSIP"
  "callHeader": "TO_HEADER_OF_SIP_INVITE_SENT"
  ```
* After sending HTTP response from Test System ESRP, verify if O-BCF responds with error message:
  ```
  201 Discrepancy Resolution successfully created
  ```

VERDICT:
* PASSED - if all checks passed for variation

**TEST CANNOT BE FAILED !**
**This test is based on requirement which is SHOULD - if any of steps has failed, then final verdict cannot be marked as failed!**


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
[![](https://mermaid.ink/img/pako:eNqdkl9LwzAUxb_K5b7agsp8ycNgthUL2pamCo68hPauK9qkpunDGPvupt1kBRXRp_z7nZyT3LvHUleEDH3fF6rUatPUTCiAtjFGm1VptekZbORbT0JNUE_vA6mSwkbWRrYjDFBQb4HvekstpDzzl8uL1L8N7hjwOIM4eY6L6EhO2-P5XBLxPPsTel8UGYQxD_IoWyXBC7gxzYuvYUbcd3ec0ky668srMNR3Wo2P-lZxzj8pYvc1xlBpIcydFU8fnoo4TeYxneSHmIubxe92c7d_eMyfhB62ZFrZVK6u-1Ev0G6pJYHMTStpXgUKdXCcHKzmO1Uis2YgD4eukvazssimsnvYSbXW-rymqnFt8XhsnKl_PDR6qLcn4vABhsW4wg?type=png)](https://mermaid.live/edit#pako:eNqdkl9LwzAUxb_K5b7agsp8ycNgthUL2pamCo68hPauK9qkpunDGPvupt1kBRXRp_z7nZyT3LvHUleEDH3fF6rUatPUTCiAtjFGm1VptekZbORbT0JNUE_vA6mSwkbWRrYjDFBQb4HvekstpDzzl8uL1L8N7hjwOIM4eY6L6EhO2-P5XBLxPPsTel8UGYQxD_IoWyXBC7gxzYuvYUbcd3ec0ky668srMNR3Wo2P-lZxzj8pYvc1xlBpIcydFU8fnoo4TeYxneSHmIubxe92c7d_eMyfhB62ZFrZVK6u-1Ev0G6pJYHMTStpXgUKdXCcHKzmO1Uis2YgD4eukvazssimsnvYSbXW-rymqnFt8XhsnKl_PDR6qLcn4vABhsW4wg)
-->

![image](https://github.com/user-attachments/assets/fadcda5f-c4e8-4c10-94e0-0858d30ab8b1)


## Comments

Version:  010.3d.3.1.5

Date:     20250428


## Footnotes
[^1]: Netcat for Linux https://linux.die.net/man/1/nc
[^2]: SIPp - tool for SIP packet simulations. Official documentation: https://sipp.sourceforge.net/doc/reference.html#Getting+SIPp
[^3]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^4]: Wireshark configuration to decrypt SIP over TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
