# Test Description: TD_ECRF-LVF_001

## Overview
### Summary
Accepting PCA signed certificates

### Description
This test checks for ECRF/LVF if PCA traceable certificates are accepted for establishing mTLS sessions.

### References
* Requirements : RQ_ECRF_009
* Test Case    : TC_ECRF_LVF_001


## Configuration
### Implementation Under Test Interface Connections
<!-- Identify each of the FEs that are part of the configuration and how they are connected -->
* Test System
  * IF_TS_ECRF - connected to IF_ECRF_TS
  * IF_TS_LVF - connected to IF_LVF_TS
* ECRF
  * IF_ECRF_TS - connected to IF_TS_ECRF 
* LVF
  * IF_LVF_TS - connected to IF_TS_LVF 

### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* Test System
  * IF_TS_ECRF - Active
  * IF_TS_LVF - Active
* ECRF
  * IF_ECRF_TS - Active
* LVF
  * IF_LVF_TS - Active


### Connectivity Diagram
<!--
[![](https://mermaid.ink/img/pako:eNplkMsKwkAMRX-lZF1_oIgbHyDUjS0uZEBiJ9piZ6bMAxHx341Wa1tnldx7uMnkDoWRBAmcanMtSrQ-SrdCR_zWq0OeHZbz7Wo6mcy4e5Us9d109zW56jwXjmeLTRnl5HyU3Zwn1TrD3LHGGa1EWo6S_vDBMv98F_XB--sxDTEosgoryV-_v2QBviRFAhIuJdqLAKEfzGHwJrvpAhJvA8UQGomeFhXyIAXJCWvHaoN6b8yvJ1l5Yzftbd8njsGacC4_xOMJt_ByeQ?type=png)](https://mermaid.live/edit#pako:eNplkMsKwkAMRX-lZF1_oIgbHyDUjS0uZEBiJ9piZ6bMAxHx341Wa1tnldx7uMnkDoWRBAmcanMtSrQ-SrdCR_zWq0OeHZbz7Wo6mcy4e5Us9d109zW56jwXjmeLTRnl5HyU3Zwn1TrD3LHGGa1EWo6S_vDBMv98F_XB--sxDTEosgoryV-_v2QBviRFAhIuJdqLAKEfzGHwJrvpAhJvA8UQGomeFhXyIAXJCWvHaoN6b8yvJ1l5Yzftbd8njsGacC4_xOMJt_ByeQ)
-->

![image](https://github.com/user-attachments/assets/f5827b15-4752-4325-bfe2-7a66066acc3d)


## Pre-Test Conditions

### Test System
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* Test System has it's own certificate signed by PCA

### ECRF/LVF
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Default configuration is loaded
* IUT is initialized with steps from IXIT config file
* IUT is active
* IUT is in normal operating state
* IUT is provisioned with following service boundaries:
```
Boundary1 - service SIP URI: sip:boundary1@example.com
40.717309464520554, -73.99120141285248
40.71672360940788, -73.9891917501422
40.71556789497267, -73.9898030924558
40.716159065144886, -73.9917916448061
```

```
Boundary2 - service SIP URI: sip:boundary2@example.com
40.71556789497267, -73.9898030924558
40.716159065144886, -73.9917916448061
40.715035291934925, -73.99236780617362
40.71443880503375, -73.99025982895066
```

## Test Sequence

### Test Preamble

#### Test System
* Install Openssl[^1]
* Install Wireshark[^2]
* Copy to local storage PCA-signed TLS certificate and private key files:
  > cacert.pem
  > cakey.pem
* Generate self-signed certificate:
  > openssl req -x509 -newkey rsa:4096 -keyout self-signed-key.pem -out self-signed-cert.pem -sha256 -days 365
* Configure Wireshark to decode HTTP over TLS packets[^3]
* Using Wireshark on 'Test System' start packet tracing on IF_TS_ECRF or IF_TS_LVF interface - run following filter:
     > ip.addr == IF_TS_ECRF_IP_ADDRESS and tls
     or
     > ip.addr == IF_TD_LVF_IP_ADDRESS and tls
     > 


### Test Body

**Variations**
1. Self-signed certificate
2. PCA-signed certificate

**Stimulus**

From 'Test System' send HTTP message with certificate:
     > cat HTTP_LoST_request | openssl s_client -connect IF_TS_ECRF_IP_ADDRESS:443 -CAfile CERTIFICATE_FILE -ign_eof

**Response**
Variation 1
Mutual TLS handshake fails due to certificate not signed by PSAP Credentialing Agency (PCA).
If handshake is successful and data transfer is started then behavior should be noted as a warning - test should be passed with remarks

Variation 2

1. Mutual TLS handshake was successfully finished
2. TLS session has started


**VERDICT:**
* PASSED - if all checks passed
* PASSED with remarks - if self-signed certificate was accepted

### Test Postamble
#### Test System
* stop all Openssl processes (if still running)
* archive all logs generated
* stop Wireshark (if still running)
* remove all HTTP scenarios
* disconnect interfaces from ECRF
* disconnect interfaces from LVF

#### ECRF
* disconnect IF_ECRF_TS
* reconnect interfaces back to default

#### LVF
* disconnect IF_LVF_TS
* reconnect interfaces back to default


## Post-Test Conditions 
### Test System 
* Test tools stopped
* interfaces disconnected from ECRF
* interfaces disconnected from LVF

### ECRF
* device connected back to default
* device in normal operating state

### LVF
* device connected back to default
* device in normal operating state

## Sequence Diagram
<!--
[![](https://mermaid.ink/img/pako:eNrlVEFvmzAY_SvWd62TlbhA8KFSRRpNWrdDqXKouFjwBayCTY2ZyqL89xmyLqnarmzXcQL7vfd97wm9HWQ6R-Awm81SlWm1lQVPFSG1NEabq8xq03KyFVWLqRpBLT52qDJcSVEYUQ_gw_NNWyT6Oxpyh60lSd9arCm5jm_Xn242a042wkhhpVbEO7JOsLPLy7MjOq4kKks-Y1XpI_z53mFPmJwkaIbJE9ExGiu3MhMW6ekHuR3MtZa-0CMrrXDKxkehj1e4u0mIqBzjnwJc_D8BfuTvC_bk-ikrhSr-cgbZoJHbfgppVCexbErnKWkwm0BaSyXbEvM30zx7Gecf9N8lvdZ_d5WrpqkGy8OvsxJWTFB_TQEKNZpayNz1xW6QSMGWWGMK3L3mwjykkKq9w4nO6qRXGXBrOqTQNbnL-1djAB_rhEIj1L3W9TMIc-na5uuhj8ZaGiHAd_AEfOHPI7YIzn1_GQUXLAyXFHp3HLC5z4LQj1h0EXmM7Sn8GEXP51GwYKG7Y5HnLwNGweiuKH-PL8zg5DDboMrRxLpTFrjnheH-J3nVkSI?type=png)](https://mermaid.live/edit#pako:eNrlVEFvmzAY_SvWd62TlbhA8KFSRRpNWrdDqXKouFjwBayCTY2ZyqL89xmyLqnarmzXcQL7vfd97wm9HWQ6R-Awm81SlWm1lQVPFSG1NEabq8xq03KyFVWLqRpBLT52qDJcSVEYUQ_gw_NNWyT6Oxpyh60lSd9arCm5jm_Xn242a042wkhhpVbEO7JOsLPLy7MjOq4kKks-Y1XpI_z53mFPmJwkaIbJE9ExGiu3MhMW6ekHuR3MtZa-0CMrrXDKxkehj1e4u0mIqBzjnwJc_D8BfuTvC_bk-ikrhSr-cgbZoJHbfgppVCexbErnKWkwm0BaSyXbEvM30zx7Gecf9N8lvdZ_d5WrpqkGy8OvsxJWTFB_TQEKNZpayNz1xW6QSMGWWGMK3L3mwjykkKq9w4nO6qRXGXBrOqTQNbnL-1djAB_rhEIj1L3W9TMIc-na5uuhj8ZaGiHAd_AEfOHPI7YIzn1_GQUXLAyXFHp3HLC5z4LQj1h0EXmM7Sn8GEXP51GwYKG7Y5HnLwNGweiuKH-PL8zg5DDboMrRxLpTFrjnheH-J3nVkSI)
-->

![image](https://github.com/user-attachments/assets/72da0b05-d50a-496a-b213-f8f98a5465c7)


## Comments

Version:  010.3d.3.1.3

Date:     20250428


## Footnotes
[^1]: Openssl for Linux https://www.openssl.org/docs/
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt SIP over TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream

