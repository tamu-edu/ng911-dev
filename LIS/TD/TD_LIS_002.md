# Test Description: TD_LIS_002

## IMPORTANT!
**Current implementation of getting location URI will not work!**
Normally it is provided by OSP which is 3rd party for NG911 tests. Currently there is no way to stimulate OSP to send SIP INVITE with 'Geolocation' which includes location URI.


## Overview
### Summary
Getting locationURI from LIS


### Description
This test checks on LIS which supports location by reference:
* getting locationURI
* correct locationURI expiration time

### HTTP and SIP transport types
Test can be performed with 2 different SIP and HTTP transport types. Steps describing actions for specific one are marked as following:
- (TLS transport) - should be used by default
- (TCP transport) - used in lab for testing purposes only if default TLS is not possible

### References
* Requirements : LIS_6
* Test Purpose : TP_LIS_002
* Test Case    : TC_LIS_002


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
[![](https://mermaid.ink/img/pako:eNpdUNsKgkAQ_RWZZ_0BiZ4iEOwlfYoFmdzxQu6u7IUQ8d-b0oqapzPnnLnOUBtJkEIzmHvdofVRfhY64siOVVlUeVbskmTPCSMmhF5VF66txbGLSnI-KibnSa3KT-1KkZZ_VR9pc7-bb26IQZFV2EtebX7SAnxHigSkDCXamwChF_Zh8KaYdA2pt4FiCKNET4ceeZCCtMHBMTuivhjzzUn23tjTevvrBTFYE9pucywPiKlY2g?type=png)](https://mermaid.live/edit#pako:eNpdUNsKgkAQ_RWZZ_0BiZ4iEOwlfYoFmdzxQu6u7IUQ8d-b0oqapzPnnLnOUBtJkEIzmHvdofVRfhY64siOVVlUeVbskmTPCSMmhF5VF66txbGLSnI-KibnSa3KT-1KkZZ_VR9pc7-bb26IQZFV2EtebX7SAnxHigSkDCXamwChF_Zh8KaYdA2pt4FiCKNET4ceeZCCtMHBMTuivhjzzUn23tjTevvrBTFYE9pucywPiKlY2g)

## Pre-Test Conditions

### Test System
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active

### LIS
* location is supplied by reference
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Default configuration is loaded
* IUT is active
* IUT is in normal operating state


## Test Sequence

### Test Preamble

#### Test System
* Install CURL[^1]
* Install Wireshark[^2]
* Copy following HTTP scenario files to local storage:
  > Location_request_for_locationURI
* (TLS transport) Copy to local storage TLS certificate and private key files:
  > cacert.pem
  > cakey.pem
* (TLS transport) Configure Wireshark to decode HTTP over TLS packets[^3]
* Using Wireshark on 'Test System' start packet tracing on IF_TS_LIS interface - run following filter:
   * (TLS transport)
     > ip.addr == IF_TS_LIS_IP_ADDRESS and tls
   * (TCP transport)
     > ip.addr == IF_TS_LIS_IP_ADDRESS and http
* On 'Test System' change configuration in scenario file:
   > Location_request_for_locationURI
   * Change LOCATION_URI to '/Location'
   * Configure LIS_FQDN to IF_LIS_TS_IP_ADDRESS
   * (TCP transport) configure PORT to '80'
   * (TLS transport) configure PORT to '443'

### Test Body

**Stimulus**

From 'Test System' send HTTP message with HTTP GET to LIS:
   * (TLS transport)
     > curl -X POST LIS_URL -d "$(cat ../../Test_files/HTTP_messages/HTTP_HELD/Location_request_for_locationURI | sed -n '/<?xml/,$p' | tr -d '\n' | tr -d '\r')"
   * (TCP transport)
     > curl -X POST LIS_URL -d "$(cat ../../Test_files/HTTP_messages/HTTP_HELD/Location_request_for_locationURI | sed -n '/<?xml/,$p' | tr -d '\n' | tr -d '\r')"
 
 **Response**
 
Using Wireshark verify 200 OK response from LIS:
* if includes correct PIDF-LO XML body
* if includes HELD locationURI (if supported), example:
    > <locationURI>https://ls.example.com:9768/357yc6s64ceyoiuy5ax3o</locationURI>
* if includes SIP locationURI (if supported), example:
    > <locationURI>sip:9769+357yc6s64ceyoiuy5ax3o@ls.example.com</locationURI>
* if includes 'expires' parameter, example:
    > <locationUriSet expires="2006-01-01T13:00:00.0Z">
* if expire time is minimum 30 min and maximum 24h
* if expire time is in format defined in https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/

**VERDICT:**
* PASSED - if all checks passed for variation
* FAILED - all other cases


### Test Postamble
#### Test System
* stop all NC processes (if still running)
* archive all logs generated
* remove all HTTP scenarios
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
[![](https://mermaid.ink/img/pako:eNpNz8EKAiEQBuBXGebaCtHRQxB0KCoKdk_hRXTapNQa9RDRu2dbUTfH-Qb-_44mWkKJQggVTAwH10sVALxjjjwzOXKScNDnRCoMKNG1UDA0d7pn7V8YoKOUob2lTF5Mp6P1spWw6Lod7LZt9yb1T9Tdn_yQyXgM2xU26Im9dramub9OFOYjeVIo69NqPilU4VGdLjm2t2BQZi7UYLlYnb95UA5hG7zosI_xN5N1tczmXXdo3SDH0h8_4vEEwzFX6Q?type=png)](https://mermaid.live/edit#pako:eNpNz8EKAiEQBuBXGebaCtHRQxB0KCoKdk_hRXTapNQa9RDRu2dbUTfH-Qb-_44mWkKJQggVTAwH10sVALxjjjwzOXKScNDnRCoMKNG1UDA0d7pn7V8YoKOUob2lTF5Mp6P1spWw6Lod7LZt9yb1T9Tdn_yQyXgM2xU26Im9dramub9OFOYjeVIo69NqPilU4VGdLjm2t2BQZi7UYLlYnb95UA5hG7zosI_xN5N1tczmXXdo3SDH0h8_4vEEwzFX6Q)


## Comments

Version:  010.3d.2.1.4

Date:     20241031


## Footnotes
[^1]: CURL for Linux https://linux.die.net/man/1/curl
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt SIP over TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream

