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
* Requirements : ESRP_42, ESRP_43, ESRP_45, ESRP_46, ESRP_48, ESRP_49
* Test Purpose : TP_ESRP_003
* Test Case    : TC_ESRP_003

## Configuration
### Implementation Under Test Interface Connections
* Test System U-ESRP (Upstream ESRP)
  * IF_U-ESRP_ESRP - connected to IF_ESRP_U-ESRP
* ESRP
  * IF_ESRP_U-ESRP - connected to Test System U-ESRP IF_U-ESRP_ESRP
  * IF_ESRP_D-ESRP - connected to Test System D-ESRP IF_D-ESRP_ESRP
  * IF_ESRP_ECRF-LVF - connected to Test System ECRF-LVF IF_ECRF-LVF_ESRP
* Test System ECRF-LVF
  * IF_ECRF-LVF_ESRP - connected to IF_ESRP_ECRF-LVF
* Test System D-ESRP (Downstream ESRP)
  * IF_D-ESRP_ESRP - connected to IF_ESRP_D-ESRP


### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* Test System U-ESRP (Upstream ESRP)
  * IF_U-ESRP_ESRP - Active
* ESRP
  * IF_ESRP_U-ESRP - Active
  * IF_ESRP_D-ESRP - Monitor
  * IF_ESRP_ECRF-LVF - Active
* Test System ECRF-LVF
  * IF_ECRF-LVF_ESRP - Active
* Test System D-ESRP (Downstream ESRP)
  * IF_D-ESRP_ESRP - Monitor
 
 
### Connectivity Diagram
[![](https://mermaid.ink/img/pako:eNp9UtFqwjAU_ZVwn9sfKLKX1cJAYbTbHiRQrs3VlpmkpAlDxH83GjurcctDyD2cnHNucg_QaEGQwWanf5oWjWWLkivm11tRf6bzqnyvz1vq14uHLkDAf2mB9FoW6eKrmI3Ea13H1DydKuY3k0Ab3HprsG_ZBw2WVfvBkmRTyzhdwEmJB4XoThQ_zhXjYyt_uUxz3nNHlfgt_ld5kiR_0i0kIMlI7IT_wcMZ5mBbksQh80eB5psDV0fPQ2d1tVcNZNY4SsD1Ai3lHXpzCdkGd4NHe1QrrW81ic5qswwjcpmUBIx22_bKOJ4AUiiqlw?type=png)](https://mermaid.live/edit#pako:eNp9UtFqwjAU_ZVwn9sfKLKX1cJAYbTbHiRQrs3VlpmkpAlDxH83GjurcctDyD2cnHNucg_QaEGQwWanf5oWjWWLkivm11tRf6bzqnyvz1vq14uHLkDAf2mB9FoW6eKrmI3Ea13H1DydKuY3k0Ab3HprsG_ZBw2WVfvBkmRTyzhdwEmJB4XoThQ_zhXjYyt_uUxz3nNHlfgt_ld5kiR_0i0kIMlI7IT_wcMZ5mBbksQh80eB5psDV0fPQ2d1tVcNZNY4SsD1Ai3lHXpzCdkGd4NHe1QrrW81ic5qswwjcpmUBIx22_bKOJ4AUiiqlw)

## Pre-Test Conditions
### Test System U-ESRP
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
* No active calls
* Logging enabled

### ECRF-LVF
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* No active calls
* Test System has it's own certificate signed by PCA

### Test System D-ESRP
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* No active calls
* Test System has it's own certificate signed by PCA

## Test Sequence

### Test Preamble

#### Test System U-ESRP
* Install SIPp by following steps from documentation[^1]
* Copy following XML scenario files to local storage:
  ```
  SIP_INVITE_EMERGENCY_SINGLE.xml
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
* Using Wireshark on 'Test System' start packet tracing on IF_U-ESRP_ESRP interface - run following filter:
   * (TLS transport)
     > ip.addr == IF_U-ESRP_ESRP_IP_ADDRESS and tls
   * (TCP transport)
     > ip.addr == IF_U-ESRP_ESRP_IP_ADDRESS and sip

#### Test System D-ESRP
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
* Using Wireshark on 'Test System' start packet tracing on IF_U-ESRP_ESRP interface - run following filter:
   * (TLS transport)
     > ip.addr == IF_D-ESRP_ESRP_IP_ADDRESS and tls
   * (TCP transport)
     > ip.addr == IF_D-ESRP_ESRP_IP_ADDRESS and sip


 #### Test System ECRF-LVF
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
* Using Wireshark on 'Test System' start packet tracing on IF_LIS_ESRP interface - run following filter:
   * (TLS transport)
     > ip.addr == IF_ECRF-LVF_ESRP_IP_ADDRESS and tls
   * (TCP transport)
     > ip.addr == IF_ECRF-LVF_ESRP_IP_ADDRESS and sip
* Rename PCA-signed certificate files for Test System ECRF-LVF to server.pem and server.key
* Start https server responding for HTTPS GET requests:
   ```
   echo -e "HTTP/1.1 200 OK\r\nContent-Type: application/xml\r\nContent-Length: 1167\r\n\r\n$(cat findServiceResponse | sed -n  '/<?xml/,/findServiceResponse>/p')\r\n" | \
   openssl s_server -quiet -accept LOCAL_PORT -cert server.pem -key server.key
   ```

### Test Body

#### Stimulus
Send SIP packet to ESRP using scenario file for tested variation - run following SIPp command on Test System U-ESRP, example:
* (TCP transport)
  ```
  sudo sipp -t t1 -sf SIP_INVITE_EMERGENCY_SINGLE.xml -i IF_U-ESRP_ESRP_IP_ADDRESS:5060 IF_ESRP_U-ESRP_IP_ADDRESS:5060 -max_recv_loops 1 -m 1
  ```
* (TLS transport)
  ```
  sudo sipp -t l1 -tls_cert PCA-cacert.pem -tls_key PCA-cakey.pem -sf SIP_INVITE_EMERGENCY_SINGLE.xml -i IF_U-ESRP_ESRP_IP_ADDRESS:5060 IF_ESRP_U-ESRP_IP_ADDRESS:5060 -max_recv_loops 1 -m 1
  ```

#### Response
* ESRP sends LoST query via HTTP to provisioned Test System ECRF-LVF with default location
* ESRP sends SIP INVITE to Test System D-ESRP
* SIP INVITE has 'Via' header field specifying ESRP
* SIP INVITE has 'Route' header field containing D-ESRP queue URI received from ECRF-LVF
* Verify Emergency Call Identifier included in "Call-Info" header field from SIP INVITE:
  * if header field contains "urn:emergency:uid:callid:"
  * if "urn:emergency:uid:callid:" is followed by 10 to 32 alphanumeric characters (String ID)
  * if String ID is followed by ":" and ESRP domain name
* Verify Incident Tracking Identifier included in "Call-Info" header field from SIP INVITE:
  * if header field contains "urn:emergency:uid:incidentid:"
  * if "urn:emergency:uid:incidentid:" is followed by 10 to 32 alphanumeric characters (String ID)
  * if String ID is followed by ":" and ESRP domain name
* verify if all header fields from SIP INVITE received from U-ESRP are included in SIP INVITE addressed to D-ESRP

VERDICT:
* PASSED - if all checks passed for variation
* FAILED - all other cases
<!--
* INCONCLUSIVE - 
* ERROR - 
-->

### Test Postamble
#### Test System U-ESRP
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

#### Test System ECRF-LVF
* stop simple_http_server.py
* archive all logs generated
* stop Wireshark (if still running)
* remove all scenario files
* disconnect interfaces from ESRP
* (TLS transport) remove certificates

#### Test System D-ESRP
* stop Sipp process (if still running)
* archive all logs generated
* stop Wireshark (if still running)
* remove all scenario files
* disconnect interfaces from ESRP
* (TLS transport) remove certificates

## Post-Test Conditions
### Test System U-ESRP
* Test tools stopped
* interfaces disconnected from ESRP

### ESRP
* device connected back to default
* device in normal operating state

### Test System ECRF-LVF
* Test tools stopped
* interfaces disconnected from ESRP

### Test System D-ESRP
* Test tools stopped
* interfaces disconnected from ESRP

## Sequence Diagram
[![](https://mermaid.ink/img/pako:eNp9kEFLwzAUx7_K450UGxgecxiI67Q4taxxB8klNG9d0CQzTQ5j7LvbdpaKDN8lL_D783_8jlh7TciRMSZd7d3WNFw6AGtC8OGujj60HLbqsyXpBqilr0SupoVRTVC2h88jqI1QHdpIFt5YXq1LNp_f9C-HqiiheNkUIp_4kfidy-_XS7baLDk8ClHCQy7gauUrcX25ZsSnoiF2O5vB69P_TQv29zLM0FKwyujOx7FPS4w7siSRd6tW4UOidKeOUyn66uBq5DEkyjDttYqjEeSDrgz3yr17P_1Jm07n81n44D3D4FOz-yFO34JUee0?type=png)](https://mermaid.live/edit#pako:eNp9kEFLwzAUx7_K450UGxgecxiI67Q4taxxB8klNG9d0CQzTQ5j7LvbdpaKDN8lL_D783_8jlh7TciRMSZd7d3WNFw6AGtC8OGujj60HLbqsyXpBqilr0SupoVRTVC2h88jqI1QHdpIFt5YXq1LNp_f9C-HqiiheNkUIp_4kfidy-_XS7baLDk8ClHCQy7gauUrcX25ZsSnoiF2O5vB69P_TQv29zLM0FKwyujOx7FPS4w7siSRd6tW4UOidKeOUyn66uBq5DEkyjDttYqjEeSDrgz3yr17P_1Jm07n81n44D3D4FOz-yFO34JUee0)


## Comments

Version:  010.3d.2.0.5

Date:     20241028

## Footnotes
[^1]: SIPp - tool for SIP packet simulations. Official documentation: https://sipp.sourceforge.net/doc/reference.html#Getting+SIPp
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt SIP over TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
