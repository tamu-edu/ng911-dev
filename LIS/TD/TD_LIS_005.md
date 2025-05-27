# Test Description: TD_LIS_005

## IMPORTANT!
**Current implementation of getting location URI will not work!**
Normally it is provided by OSP which is 3rd party for NG911 tests. Currently there is no way to stimulate OSP to send SIP INVITE with 'Geolocation' which includes location URI.


## Overview
### Summary
Location dereference authentication


### Description
This test checks if LIS accepts only PCA traceable certificates

### References
* Requirements : RQ_LIS_005. RQ_LIS_008
* Test Case    : TC_LIS_005


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
[![](https://mermaid.ink/img/pako:eNpdUMsKgzAQ_BXZs_6AlJ5KQbCX2lMJyNasD2oSiQlFxH_v1khfe5qdmX3OUBlJkELdm0fVonVRfhY64siO5aUo86zYJcmeE0ZMBG30t8bi0EYXGl1UTKMjFZSfykCRln9Vb2lzf7de3RCDIquwk7za_BIEuJYUCUgZSrR3AUIv7EPvTDHpClJnPcXgB4mODh3yKAVpjf3I7ID6aswnJ9k5Y0_h9vUFMVjjm3ZzLE9zz1ja?type=png)](https://mermaid.live/edit#pako:eNpdUMsKgzAQ_BXZs_6AlJ5KQbCX2lMJyNasD2oSiQlFxH_v1khfe5qdmX3OUBlJkELdm0fVonVRfhY64siO5aUo86zYJcmeE0ZMBG30t8bi0EYXGl1UTKMjFZSfykCRln9Vb2lzf7de3RCDIquwk7za_BIEuJYUCUgZSrR3AUIv7EPvTDHpClJnPcXgB4mODh3yKAVpjf3I7ID6aswnJ9k5Y0_h9vUFMVjjm3ZzLE9zz1ja)
-->

![image](https://github.com/user-attachments/assets/8c57e572-b6c6-4815-ba81-bb3109d6d3a7)

## Pre-Test Conditions

### Test System
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* Test System has it's own certificate signed by PCA (test_system_PCA.crt, test_system_PCA.key)

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
* Install Openssl[^1]
* Install Wireshark[^2]
* Install SIPp by following steps from documentation[^4]
* Copy following SIPp scenario file to local storage:
  > SIP_SUBSCRIBE_from_LIS.xml
* Copy to local storage PCA-signed TLS certificate and private key files:
  > cacert.pem
  > cakey.pem
* Generate self-signed certificate:
  > openssl req -x509 -newkey rsa:4096 -keyout self-signed.key -out self-signed.crt -sha256 -days 365
* Configure Wireshark to decode HTTP over TLS packets[^3]
* Using Wireshark on 'Test System' start packet tracing on IF_TS_LIS interface - run following filter:
     > ip.addr == IF_TS_LIS_IP_ADDRESS and tls

### Test Body

#### Variations 
1. Self-signed certificate

Use generated self-signed certificate and key files: self-signed.crt, self-signed.key

2. PCA-signed certificate

Use PCA signed certificate and key files: test_system_PCA.crt, test_system_PCA.key

#### Stimulus
From 'Test System' try to send HTTP message to LIS:

     > sudo sipp -t l1 -tls_cert CERTIFICATE_FILE -tls_key KEY_FILE -sf SIP_SUBSCRIBE_from_LIS.xml -i IF_TS_LIS IF_LIS_TS:5061

#### Response

Variation 1
Using Wireshark verify if Mutual TLS handshake fails due to certificate not signed by PSAP Credentialing Agency (PCA)

Variation 2
Using Wireshark verify:
   * if Mutual TLS handshake was successfully finished
   * if TLS session has started


**VERDICT:**
* PASSED - if LIS responsed as expected
* FAILED - all other cases


### Test Postamble
#### Test System
* stop all Openssl processes (if still running)
* archive all logs generated
* stop Wireshark (if still running)
* remove all SIPp scenarios
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
<!--
[![](https://mermaid.ink/img/pako:eNrdlMFvmzAUxv-Vp3etEzVxgeBDpSrZtGndDqPqYeJiwQtYA5sZM5VF-d9nSLeka0Xa6ziB_fP3-X3ivR1mJicUOJvNUp0ZvVWFSDVAraw19iZzxrYCtrJqKdUj1NKPjnRGGyULK-sBPjxfjCMwP8nCHbUOkr51VDO4_ZgIuJdWSaeMhsXxwAk2u76-GMF1pUg7-EBVZY6k3_LECS8gITtYnQfXZJ3aqkw6Yqcf8HUopHXsiRRsjKYzVzxqTBrf3SYgKw-_NaLl_xnRRC2fqId3D1kpdfF6Zbgnq7b9GX7UhLVqSn__pKFsmn-vtGpLyv_N6-JpYBOqL_HPVV_yvmmaaqhs-Ac20slpzec0MqzJ1lLlvqF3w-kUXUk1pSj8ay7t9xRTvfec7JxJep2hcLYjhl2T-0QfWxrF2O8MG6m_GVP_gShXfhx8PgyMcW6MCIodPqBYBvOYL8PLIFjF4RWPohXD3i-HfB7wMApiHl_FC873DH-NopfzOFzyyO_xeBGsQs7Qmq4o_9oXdqjk4G1J52TXptMORRztfwP7d3fl?type=png)](https://mermaid.live/edit#pako:eNrdlMFvmzAUxv-Vp3etEzVxgeBDpSrZtGndDqPqYeJiwQtYA5sZM5VF-d9nSLeka0Xa6ziB_fP3-X3ivR1mJicUOJvNUp0ZvVWFSDVAraw19iZzxrYCtrJqKdUj1NKPjnRGGyULK-sBPjxfjCMwP8nCHbUOkr51VDO4_ZgIuJdWSaeMhsXxwAk2u76-GMF1pUg7-EBVZY6k3_LECS8gITtYnQfXZJ3aqkw6Yqcf8HUopHXsiRRsjKYzVzxqTBrf3SYgKw-_NaLl_xnRRC2fqId3D1kpdfF6Zbgnq7b9GX7UhLVqSn__pKFsmn-vtGpLyv_N6-JpYBOqL_HPVV_yvmmaaqhs-Ac20slpzec0MqzJ1lLlvqF3w-kUXUk1pSj8ay7t9xRTvfec7JxJep2hcLYjhl2T-0QfWxrF2O8MG6m_GVP_gShXfhx8PgyMcW6MCIodPqBYBvOYL8PLIFjF4RWPohXD3i-HfB7wMApiHl_FC873DH-NopfzOFzyyO_xeBGsQs7Qmq4o_9oXdqjk4G1J52TXptMORRztfwP7d3fl)
-->

![image](https://github.com/user-attachments/assets/87e86017-cde4-44bc-a151-d8d61f54d1eb)


## Comments

Version:  010.3d.3.1.5

Date:     20250508


## Footnotes
[^1]: Openssl for Linux https://www.openssl.org/docs/
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt SIP over TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^4]: SIPp - tool for SIP packet simulations. Official documentation: https://sipp.sourceforge.net/doc/reference.html#Getting+SIPp
