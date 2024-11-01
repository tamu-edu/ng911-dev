# Test Description: TD_ECRF-LVF_005


## Overview
### Summary
Support of recursive and iterative modes in findService requests


### Description
This test checks if ECRF and LVF support for findService requests:
* recursive mode
* iterative mode


### SIP transport types
Test can be performed with 2 different HTTP transport types. Steps describing actions for specific one are marked as following:
- (TLS transport) - used by default inside ESInet on production environment
- (TCP transport) - used as a fallback if use of TLS is not possible

### References
* Requirements : ECRF-LVF_50
* Test Purpose : TP_ECRF-LVF_004
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
* Provisioning file provided


## Test Sequence

### Test Preamble

#### Test System
* (TLS transport) Install Openssl[^1]
* (TCP transport) Install Netcat[^4]
* Install Wireshark[^2]
* Copy following HTTP scenario files to local storage:
  ```
	findService_recursive_mode_polygon_not_covering_boundaries
	findService_iterative_mode_polygon_not_covering_boundaries
  ```
* Change configuration in HTTP scenario files to be used:
  * change /LoST to ECRF URL for LoST
  * change IF_ECRF_TS to ECRF address (FQDN or IP)
  * change polygon location to one which do not match service boundary in provided provisioning file for ECRF
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
* Backup current configuration
* Provision IUT with file provided


### Test Body

**Variations**
1. findService_recursive_mode_polygon_not_covering_boundaries
2. findService_iterative_mode_polygon_not_covering_boundaries

**Stimulus**
From 'Test System' send request with recursion enabled to ECRF:
   * (TLS transport)
     > curl -X POST ECRF_URL -d "$(cat ../../Test_files/HTTP_messages/HTTP_LoST/findService_recursive_mode_polygon_not_covering_boundaries | sed -n '/<?xml/,$p' | tr -d '\n' | tr -d '\r')"
   * (TCP transport)
     > curl -X POST ECRF_URL -d "$(cat ../../Test_files/HTTP_messages/HTTP_LoST/findService_recursive_mode_polygon_not_covering_boundaries | sed -n '/<?xml/,$p' | tr -d '\n' | tr -d '\r')"

**Response**

Variation 1

Using Wireshark verify if ECRF tries to reach another ECRF's (by sending LoST requests on IF_ECRF_ECRF2) to get info about polygon from the request and responds with service from another ECRF


Variation 2

Using Wireshark verify if ECRF responds HTTP 30X message with Location containing URL of another ECRF


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
* disconnect IF_ECRF_ECRF2
* reconnect interfaces back to default
* restore previous configuration


## Post-Test Conditions 
### Test System 
* Test tools stopped
* interfaces disconnected from ECRF

### ECRF
* device connected back to default
* device in normal operating state


## Sequence Diagram
[![](https://mermaid.ink/img/pako:eNqlkU9LAzEQxb9KmKu7F48BC-IfPCiIuyfJJSTTbaiZWSeJUEq_u8m2UgU9mUsS-L15M2_24NgjaOj73pBjWodJG1IqBhGWa5dZklZr-5bQ0AIlfC9IDm-DncTGBh_PiCmrYZcyxn61uri7ebnX6mEcn9UjD6OSpquEoCuSwgdeZSl4lje-6b6V-U3eMJV5uS__YX4a6Yd7Vf7pnmamJoAOIkq0wdfU9q2AgbzBiAZ0fXorWwOGDpWzJfOwIwe6TdpBmb3NX7mBXjroYLb0ynz-ow819KfjWpbtdCBcps2JOHwCmE6Nhw?type=png)](https://mermaid.live/edit#pako:eNqlkU9LAzEQxb9KmKu7F48BC-IfPCiIuyfJJSTTbaiZWSeJUEq_u8m2UgU9mUsS-L15M2_24NgjaOj73pBjWodJG1IqBhGWa5dZklZr-5bQ0AIlfC9IDm-DncTGBh_PiCmrYZcyxn61uri7ebnX6mEcn9UjD6OSpquEoCuSwgdeZSl4lje-6b6V-U3eMJV5uS__YX4a6Yd7Vf7pnmamJoAOIkq0wdfU9q2AgbzBiAZ0fXorWwOGDpWzJfOwIwe6TdpBmb3NX7mBXjroYLb0ynz-ow819KfjWpbtdCBcps2JOHwCmE6Nhw)


## Comments

Version:  010.3d.2.0.5

Date:     20241031


## Footnotes
[^1]: Openssl for Linux https://www.openssl.org/docs/
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt SIP over TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^4]: Netcat for Linux https://linux.die.net/man/1/nc
