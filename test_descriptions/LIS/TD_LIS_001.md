# Test Description: TD_LIS_001
## Overview
### Summary
Location URI dereferencing


### Description
This test checks for LIS supplying location by reference (locationURI) at least one of following methods:
* HELD
* SIP Presence Event Package

### HTTP and SIP transport types
Test can be performed with 2 different SIP and HTTP transport types. Steps describing actions for specific one are marked as following:
- (TLS transport) - should be used by default
- (TCP transport) - used in lab for testing purposes only if default TLS is not possible

### References
* Requirements : RQ_LIS_001, RQ_LIS_002, RQ_LIS_007, RQ_LIS_010
* Test Case    : TC_LIS_001

### Requirements
IXIT config file for LIS

## Configuration
### Implementation Under Test Interface Connections
<!-- Identify each of the FEs that are part of the configuration and how they are connected -->
* Test System
  * IF_TS_LIS - connected to IF_LIS_TS
* LIS
  * IF_LIS_TS - connected to IF_TS_LIS 


### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* Test System
  * IF_TS_LIS - Active
* LIS
  * IF_LIS_TS - Active


### Connectivity Diagram
<!--
[![](https://mermaid.ink/img/pako:eNpdUNsKgkAQ_RWZZ_0BiZ4iEOwlfYoFmdzxQu6u7IUQ8d-b0oqapzPnnLnOUBtJkEIzmHvdofVRfhY64siOVVlUeVbskmTPCSMmhF5VF66txbGLSnI-KibnSa3KT-1KkZZ_VR9pc7-bb26IQZFV2EtebX7SAnxHigSkDCXamwChF_Zh8KaYdA2pt4FiCKNET4ceeZCCtMHBMTuivhjzzUn23tjTevvrBTFYE9pucywPiKlY2g?type=png)](https://mermaid.live/edit#pako:eNpdUNsKgkAQ_RWZZ_0BiZ4iEOwlfYoFmdzxQu6u7IUQ8d-b0oqapzPnnLnOUBtJkEIzmHvdofVRfhY64siOVVlUeVbskmTPCSMmhF5VF66txbGLSnI-KibnSa3KT-1KkZZ_VR9pc7-bb26IQZFV2EtebX7SAnxHigSkDCXamwChF_Zh8KaYdA2pt4FiCKNET4ceeZCCtMHBMTuivhjzzUn23tjTevvrBTFYE9pucywPiKlY2g)
-->

![image](https://github.com/user-attachments/assets/471b08e8-cce9-449b-b10c-0dbbfcc2896a)


## Pre-Test Conditions

### Test System
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* (TLS transport) Test System has it's own certificate signed by PCA
* locationURI received from LIS

### LIS
* location is supplied by reference
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Default configuration is loaded
* IUT is initialized with steps from IXIT config file
* IUT is active
* IUT is in normal operating state


## Test Sequence

### Test Preamble

#### Test System
* Install SIPp by following steps from documentation[^1]
* Install CURL[^2]
* Install Wireshark[^3]
* Copy following scenario files to local storage:
```
Location_request
SIP_SUBSCRIBE_from_LIS.xml
```
* Prepare at least one of locationURI received from LIS:
   * SIP locationURI - in example
     > 'sip:9769+357yc6s64ceyoiuy5ax3o@ls.example.com'
     
     received from LIS, following part should be used to pass as '-s' parameter:
     > 9769+357yc6s64ceyoiuy5ax3o
   * HELD locationURI - example
     > https://ls.example.com:9768/357yc6s64ceyoiuy5ax3o
* (TLS transport) Copy to local storage TLS certificate and private key files:
  > cacert.pem
  > cakey.pem
* (TLS transport) Configure Wireshark to decrypt TLS packets[^4]
* Using Wireshark on 'Test System' start packet tracing on IF_TS_LIS interface - run following filter:
   * (TLS transport)
     > ip.addr == IF_TS_LIS_IP_ADDRESS and tls
   * (TCP transport)
     > ip.addr == IF_TS_LIS_IP_ADDRESS and (http or sip)


### Test Body

**Variations**
1. Sending HTTP request to LIS using Location_request file:
   * (TLS transport)
     > curl -X POST https://LIS_URL -H "Content-Type: application/xml"-d @Location_request
   * (TCP transport)
     > curl -X POST http://LIS_URL -H "Content-Type: application/xml"-d @Location_request

2. Sending SIP SUBSCRIBE and then receiving SIP NOTIFY:
   * (TCP transport)
     > sudo sipp -t t1 -sf SIP_SUBSCRIBE_from_LIS.xml -i IF_TS_LIS_IP_ADDRESS:5060 -timeout 10 -max_recv_loops 1 -s SIP_LOCATION_URI
   * (TLS transport)
     > sudo sipp -t l1 -tls_cert cacert.pem -tls_key cakey.pem -sf SIP_SUBSCRIBE_from_LIS.xml -i IF_TS_LIS_IP_ADDRESS:5061 -trace_logs -trace_msg -timeout 10 -max_recv_loops 1 -s SIP_LOCATION_URI

**Stimulus**

Run HTTP/SIP scenario to request locationURI dereference from LIS

**Response**

Variation 1

Using Wireshark verify 200 OK response from LIS:
   * if includes 'Content-Type: application/pidf+xml'
   * if 200 OK message includes XML with locationResponse
   * if XML body with location is correct PIDF-LO (RFC5491, RFC5139)

Variation 2

Using Wireshark verify SIP NOTIFY received from LIS:
   * if includes 'Content-Type: application/pidf+xml'
   * if SIP NOTIFY message includes XML with locationResponse
   * if XML body with location is correct PIDF-LO (RFC5491, RFC5139)


**VERDICT:**
* PASSED - if all checks passed for variation
* FAILED - all other cases


### Test Postamble
#### Test System
* stop all SIPp processes (if still running)
* stop all NC processes (if still running)
* archive all logs generated
* remove all SIPp and HTTP scenarios
* disconnect interfaces from LIS

#### LIS
* disconnect IF_LIS_TS
* reconnect interfaces back to default

## Post-Test Conditions 
### Test System 
* Test tools stopped
* interfaces disconnected from LIS

### LIS
* device connected back to default
* device in normal operating state

## Sequence Diagram
### HELD
<!--
[![](https://mermaid.ink/img/pako:eNpNz8EKAiEQBuBXGebaCtHRQxB0KCoKdk_hRXTapNQa9RDRu2dbUTfH-Qb-_44mWkKJQggVTAwH10sVALxjjjwzOXKScNDnRCoMKNG1UDA0d7pn7V8YoKOUob2lTF5Mp6P1spWw6Lod7LZt9yb1T9Tdn_yQyXgM2xU26Im9dramub9OFOYjeVIo69NqPilU4VGdLjm2t2BQZi7UYLlYnb95UA5hG7zosI_xN5N1tczmXXdo3SDH0h8_4vEEwzFX6Q?type=png)](https://mermaid.live/edit#pako:eNpNz8EKAiEQBuBXGebaCtHRQxB0KCoKdk_hRXTapNQa9RDRu2dbUTfH-Qb-_44mWkKJQggVTAwH10sVALxjjjwzOXKScNDnRCoMKNG1UDA0d7pn7V8YoKOUob2lTF5Mp6P1spWw6Lod7LZt9yb1T9Tdn_yQyXgM2xU26Im9dramub9OFOYjeVIo69NqPilU4VGdLjm2t2BQZi7UYLlYnb95UA5hG7zosI_xN5N1tczmXXdo3SDH0h8_4vEEwzFX6Q)
-->

![image](https://github.com/user-attachments/assets/021593a8-7eae-423d-a9e9-21318f4e128b)


### SIP Presence Event Package
<!--
[![](https://mermaid.ink/img/pako:eNp90M9uAiEQBvBXIXPt8gIcTGpbk41_tin2YMOFwLiSCtgBDsb47uKuxp68McwvmXzfCUy0CAI45yqYGLauFyow5h1RpFeTIyXBtnqfUIUBJfwrGAy-O92T9lfM2BpTZvKYMno-mbwsWimYbD-Z_J7Kt692-jGy-s_r_p8eWTd_vl9163a2eX6qm0MDHslrZ2ug01UryDv0qEDUp9X0q0CFc3W65CiPwYDIVLCBcrA63yOBGPI2cNDhJ8bHjNbVPpZjY0NxDVAs_e4mzhcAZ2vC?type=png)](https://mermaid.live/edit#pako:eNp90M9uAiEQBvBXIXPt8gIcTGpbk41_tin2YMOFwLiSCtgBDsb47uKuxp68McwvmXzfCUy0CAI45yqYGLauFyow5h1RpFeTIyXBtnqfUIUBJfwrGAy-O92T9lfM2BpTZvKYMno-mbwsWimYbD-Z_J7Kt692-jGy-s_r_p8eWTd_vl9163a2eX6qm0MDHslrZ2ug01UryDv0qEDUp9X0q0CFc3W65CiPwYDIVLCBcrA63yOBGPI2cNDhJ8bHjNbVPpZjY0NxDVAs_e4mzhcAZ2vC)
-->

![image](https://github.com/user-attachments/assets/9e574ae9-988c-41e9-9683-d057bfeb7a45)



## Comments

Version:  010.3d.3.1.6

Date:     20250425


## Footnotes
[^1]: SIPp - tool for SIP packet simulations. Official documentation: https://sipp.sourceforge.net/doc/reference.html#Getting+SIPp
[^2]: CURL for Linux https://linux.die.net/man/1/curl
[^3]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^4]: Wireshark configuration to decrypt SIP over TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream



