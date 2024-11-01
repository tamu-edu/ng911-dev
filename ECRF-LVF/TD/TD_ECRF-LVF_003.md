# Test Description: TD_ECRF-LVF_003

## Overview
### Summary
Service boundaries handling

### Description
This test checks if ECRF responds with correct service URN for a requests from location covering:
* fully one service boundary and another one partially
* fully two boundaries

Outgoing request to another ECRF is checked in case of location out of ECRF jurisdiction.

### SIP transport types
Test can be performed with 2 different HTTP transport types. Steps describing actions for specific one are marked as following:
- (TLS transport) - used by default inside ESInet on production environment
- (TCP transport) - used as a fallback if use of TLS is not possible

### References
* Requirements : ECRF-LIS_11, ECRF-LIS-43
* Test Purpose : TP_ECRF-LVF_003
* Test Case    : TC_ECRF-LVF_003


## Configuration
### Implementation Under Test Interface Connections
<!-- Identify each of the FEs that are part of the configuration and how they are connected -->
* Test System
  * IF_TS_ECRF - connected to IF_ECRF_TS
* ECRF
  * IF_ECRF_TS - connected to IF_TS_ECRF
  * IF_ECRF_ECRF2 - connected to IF_TS_ECRF

### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* Test System
  * IF_TS_ECRF - Active
* ECRF
  * IF_ECRF_TS - Active
  * IF_ECRF_ECRF2 - Monitor

### Connectivity Diagram
[![](https://mermaid.ink/img/pako:eNplUM0KwjAMfpWS8-bB4xAv6kDQi_MkhRHX6IZrO7oWGeK727pBZSYQ2u8PkhdUWhBkcGv1s6rRWHY4ccV89e56N9jV7Ey9ZcXQW5IjE2qfl-ei3G1O-YiREjNb5CZ9ALzpHwtjOYuJ-as0Xc_dv-wi0lNQ6KCCBCQZiY3wC74CxsHWJIlD5p8CzYMDV2-vQ2d1MagKMmscJeA6gZa2DfpdJGQ3bHuPdqguWsc_icZqcxwv-D1kAka7ez0p3h8L52qu?type=png)](https://mermaid.live/edit#pako:eNplUM0KwjAMfpWS8-bB4xAv6kDQi_MkhRHX6IZrO7oWGeK727pBZSYQ2u8PkhdUWhBkcGv1s6rRWHY4ccV89e56N9jV7Ey9ZcXQW5IjE2qfl-ei3G1O-YiREjNb5CZ9ALzpHwtjOYuJ-as0Xc_dv-wi0lNQ6KCCBCQZiY3wC74CxsHWJIlD5p8CzYMDV2-vQ2d1MagKMmscJeA6gZa2DfpdJGQ3bHuPdqguWsc_icZqcxwv-D1kAka7ez0p3h8L52qu)

## Pre-Test Conditions

### Test System
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* (TLS transport) Test System has it's own certificate signed by PCA

### ECRF
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Default configuration is loaded
* IUT is active
* IUT is in normal operating state
* Provisioning file provided - with multiple service boundaries configured


## Test Sequence

### Test Preamble

#### Test System
* (TLS transport) Install Openssl[^1]
* (TCP transport) Install Netcat[^4]
* Install Wireshark[^2]
* Copy following HTTP scenario files to local storage:
  ```
	findService_polygon_covering_fully_one_and_partialy_another_boundary
	findService_polygon_covering_fully_two_boundaries
  ```
* Configure scenario files with correct ECRF URL and host addresses
* Configure scenario files with polygons matching service boundaries provisioned on ECRF-LVF:
  - findService_polygon_covering_fully_one_and_partialy_another_boundary - cover fully one boundary and another partially
  - findService_polygon_covering_fully_two_boundaries - cover fully two service boundaries

* (TLS transport) Copy to local storage PCA-signed TLS certificate and private key files:
  ```
  PCA-cacert.pem
  PCA-cakey.pem
  ```
* (TLS transport) Copy to local storage TLS certificate and private key files used by ECRF:
  ```
  ECRF-cacert.pem
  ECRF-cakey.pem
  ```
* (TLS transport) Configure Wireshark to decode HTTP over TLS packets from Test System and ECRF as well[^3]
* Using Wireshark on 'Test System' start packet tracing on IF_TS_ECRF and IF_ECRF_ECRF2 interface - run following filter:
   * (TLS transport)
     > (ip.addr == IF_TS_ECRF_IP_ADDRESS or ip.addr == IF_ECRF_ECRF2_IP_ADDRESS) and tls
   * (TCP transport)
     > (ip.addr == IF_TS_ECRF_IP_ADDRESS or ip.addr == IF_ECRF_ECRF2_IP_ADDRESS) and http

#### ECRF
* Provision IUT with file provided


### Test Body
**Variations**
1. findService_polygon_covering_fully_one_and_partialy_another_boundary
2.	findService_polygon_covering_fully_two_boundaries

**Stimulus**

From 'Test System' send HTTP message to ECRF, example:
   * (TLS transport)
     > curl -X POST ECRF_URL -d "$(cat ../../Test_files/HTTP_messages/HTTP_LoST/findService_polygon_covering_fully_two_boundaries | sed -n '/<?xml/,$p' | tr -d '\n' | tr -d '\r')"

   * (TCP transport)
     > curl -X POST ECRF_URL -d "$(cat ../../Test_files/HTTP_messages/HTTP_LoST/findService_polygon_covering_fully_two_boundaries | sed -n '/<?xml/,$p' | tr -d '\n' | tr -d '\r')"

**Response**

Variation 1

Using Wireshark verify LoST response from ECRF if returned service URN is from boundary which was fully covered by the polygon


Variation 2

Using Wireshark verify LoST response from ECRF if returned service URN is one of boundaries covered by the polygon
  
**VERDICT:**
* PASSED - if all checks passed for variation
* FAILED - all other cases


### Test Postamble
#### Test System
* (TLS transport) stop all Openssl processes (if still running)
* (TCP transport) stop all Netcat processes (if still running)
* archive all logs generated
* stop Wireshark (if still running)
* remove all HTTP scenarios
* disconnect interfaces from ECRF
* (TLS transport) remove certificates

#### ECRF
* disconnect IF_ECRF_TS
* reconnect interfaces back to default


## Post-Test Conditions 
### Test System 
* Test tools stopped
* interfaces disconnected from ECRF

### ECRF
* device connected back to default
* device in normal operating state


## Sequence Diagram
[![](https://mermaid.ink/img/pako:eNrNks9OwzAMh1_F8omJ9gVymIT4Iw4gIdoTyiWk7hZttYuTIFXT3p20GxocuZGTo3z2L9LnA3rpCA3WdW3ZC_dhYywDDEFV9MYn0Wigd_tIlhco0kcm9nQX3EbdMMOn01JM0Ewx0VCv19f3t68PBh7b9gWepGlB576YLvwM1IX80febj6PwHPvPAuBqL96lIAySE0gPkfQzeIJ3ydw5nVZ_-MN5pGNJW9KFX2GFA-ngQlfMHOZhFsvrQBZNKUvEzqLlY-FcTtJM7NEkzVRhHjuXvt2gWcRVODp-E7ncqQtF7PNJ_bIBFarkzfZMHL8AAqerOw?type=png)](https://mermaid.live/edit#pako:eNrNks9OwzAMh1_F8omJ9gVymIT4Iw4gIdoTyiWk7hZttYuTIFXT3p20GxocuZGTo3z2L9LnA3rpCA3WdW3ZC_dhYywDDEFV9MYn0Wigd_tIlhco0kcm9nQX3EbdMMOn01JM0Ewx0VCv19f3t68PBh7b9gWepGlB576YLvwM1IX80febj6PwHPvPAuBqL96lIAySE0gPkfQzeIJ3ydw5nVZ_-MN5pGNJW9KFX2GFA-ngQlfMHOZhFsvrQBZNKUvEzqLlY-FcTtJM7NEkzVRhHjuXvt2gWcRVODp-E7ncqQtF7PNJ_bIBFarkzfZMHL8AAqerOw)


## Comments

Version:  010.3d.2.0.7

Date:     20241030


## Footnotes
[^1]: Openssl for Linux https://www.openssl.org/docs/
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt SIP over TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^4]: Netcat for Linux https://linux.die.net/man/1/nc
