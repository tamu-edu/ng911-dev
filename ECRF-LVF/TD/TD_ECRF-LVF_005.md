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
* Requirements : RQ_ECRF-LVF_043, RQ_ECRF-LVF_050
* Test Case    : 

### Requirements
IXIT config file for ECRF-LVF

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
<!--
[![](https://mermaid.ink/img/pako:eNplUM0KwjAMfpWS8-bB4xAv6kDQi_MkhRHX6IZrO7oWGeK727pBZSYQ2u8PkhdUWhBkcGv1s6rRWHY4ccV89e56N9jV7Ey9ZcXQW5IjE2qfl-ei3G1O-YiREjNb5CZ9ALzpHwtjOYuJ-as0Xc_dv-wi0lNQ6KCCBCQZiY3wC74CxsHWJIlD5p8CzYMDV2-vQ2d1MagKMmscJeA6gZa2DfpdJGQ3bHuPdqguWsc_icZqcxwv-D1kAka7ez0p3h8L52qu?type=png)](https://mermaid.live/edit#pako:eNplUM0KwjAMfpWS8-bB4xAv6kDQi_MkhRHX6IZrO7oWGeK727pBZSYQ2u8PkhdUWhBkcGv1s6rRWHY4ccV89e56N9jV7Ey9ZcXQW5IjE2qfl-ei3G1O-YiREjNb5CZ9ALzpHwtjOYuJ-as0Xc_dv-wi0lNQ6KCCBCQZiY3wC74CxsHWJIlD5p8CzYMDV2-vQ2d1MagKMmscJeA6gZa2DfpdJGQ3bHuPdqguWsc_icZqcxwv-D1kAka7ez0p3h8L52qu)
-->

![image](https://github.com/user-attachments/assets/55f96fc1-65ac-4b7d-b935-641d5c333f84)


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
     > curl -X POST https://ECRF_URL -d @SCENARIO_FILE
   * (TCP transport)
     > curl -X POST http://ECRF_URL -d @SCENARIO_FILE

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
<!--
[![](https://mermaid.ink/img/pako:eNqlkVFLwzAUhf9KuK-2Y2vWdgk4kKn4oCCuTyMvob3rijaZt4k4x_67TedURJ_MS0LynXty7t1DaSsECXEcK1Nas25qqQxjbUNk6aJ0ljrJ1vqpQ2UGqMNnj6bEy0bXpNsAH1eBnWPLXeewjefzs6vFw7VkN0Vxz27tsmAUdD1BWHrqmhc8d-TxSx74oPtW5jd5wJizw578w_wj0g_3P827rTWBhwhapFY3Vd-0fdArcBtsUYHsj5WmRwXKHHpOe2eXO1OCDEEj8NtKu1PbQA4fiGCrzcra9gRh1fQtvzsOZZjNgIDcwyvIJB0JnmTjNJ2JbMrzfBbBrr_O-CjlWZ4KLqZiwvkhgreh6HgksoTn_RsXk3SW8QjI-nrzaV9TSHL0JjQV0sJ640BO-OEdcdqozg?type=png)](https://mermaid.live/edit#pako:eNqlkVFLwzAUhf9KuK-2Y2vWdgk4kKn4oCCuTyMvob3rijaZt4k4x_67TedURJ_MS0LynXty7t1DaSsECXEcK1Nas25qqQxjbUNk6aJ0ljrJ1vqpQ2UGqMNnj6bEy0bXpNsAH1eBnWPLXeewjefzs6vFw7VkN0Vxz27tsmAUdD1BWHrqmhc8d-TxSx74oPtW5jd5wJizw578w_wj0g_3P827rTWBhwhapFY3Vd-0fdArcBtsUYHsj5WmRwXKHHpOe2eXO1OCDEEj8NtKu1PbQA4fiGCrzcra9gRh1fQtvzsOZZjNgIDcwyvIJB0JnmTjNJ2JbMrzfBbBrr_O-CjlWZ4KLqZiwvkhgreh6HgksoTn_RsXk3SW8QjI-nrzaV9TSHL0JjQV0sJ640BO-OEdcdqozg)
-->

![image](https://github.com/user-attachments/assets/7b887317-d75e-48bf-8274-5e9f888ee59f)


## Comments

Version:  010.3d.3.0.7

Date:     20250428


## Footnotes
[^1]: Openssl for Linux https://www.openssl.org/docs/
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt SIP over TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^4]: Netcat for Linux https://linux.die.net/man/1/nc
