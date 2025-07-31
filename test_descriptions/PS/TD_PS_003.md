# Test Description: TD_PS_003
## Overview
### Summary
Response for HTTP GET to /Versions entrypoint

### Description
Test verifies if Policy Store reponds as required on HTTP GET to /Versions entrypoint

### References
* Requirements : RQ_PS_013, RQ_PS_014
* Test Case    : TC_PS_003

### Requirements
IXIT config file for Policy Store

### HTTP transport types
Test can be performed with 2 different HTTP transport types. Steps describing actions for specific one are marked as following:
- (TLS) - used by default inside ESInet on production environment
- (TCP) - used if default TLS is not possible

## Configuration
### Implementation Under Test Interface Connections
<!-- Identify each of the FEs that are part of the configuration and how they are connected -->
* Policy Store (PS)
  * IF_PS_TS - connected to Test System IF_TS_PS
* Test System
  * IF_TS_PS - connected to FE IF_PS_TS

### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* Test System 
  * IF_TS_PS - Active
* Policy Store (PS)
  * IF_PS_TS - Active
 
### Connectivity Diagram
<!--
[![](https://mermaid.ink/img/pako:eNpdUM0KwjAMfpWS8_YCQzyJICgMu5MURlwzN1zb0bXIGHt3oxOc5pR8P3xJJqicJsig7tyjatAHcTwrK7gO-7KQZS43abrlPpc8LswQrzePfSMKGoKQ4xDILMzatyBk9Z8pd11bjUIG5-nHtUpgFyRgyBtsNW83vWAFoSFDCjJuNfq7AmVn1mEMTo62giz4SAnEXmOgXYscaCCrsRsY7dFenPvOpFte4bSc__5CAt7FW_NRzE8do1qx?type=png)](https://mermaid.live/edit#pako:eNpdUM0KwjAMfpWS8_YCQzyJICgMu5MURlwzN1zb0bXIGHt3oxOc5pR8P3xJJqicJsig7tyjatAHcTwrK7gO-7KQZS43abrlPpc8LswQrzePfSMKGoKQ4xDILMzatyBk9Z8pd11bjUIG5-nHtUpgFyRgyBtsNW83vWAFoSFDCjJuNfq7AmVn1mEMTo62giz4SAnEXmOgXYscaCCrsRsY7dFenPvOpFte4bSc__5CAt7FW_NRzE8do1qx)
-->

![image](https://github.com/user-attachments/assets/08807cca-2224-4976-9a72-da9f4922cce4)


## Pre-Test Conditions
### Test System
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* ng911 repository cloned to local storage
* (TLS) Generated own PCA-signed certificate and private key files (test_system.crt, test_system.key)
* (TLS) Certificate and key used by FE/Policy Store copied to local storage
* (TLS) PCA certificate copied to local storage

### Policy Store (PS)
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Default configuration is loaded
* IUT is initialized with steps from IXIT config file
* Device is active
* Device is in normal operating state

## Test Sequence

### Test Preamble

#### Test System
* Install Wireshark[^1]
* (TLS v1.2) Configure Wireshark to decode HTTP over TLS, use tests system and PS certificate keys [^2]
* (TLS v1.3) Configure logging of session keys and configure Wireshark to decode HTTP over TLS [^3]
* Using Wireshark on 'Test System' start packet tracing on IF_TS_PS interface - run following filter:
   * (TLS)
     > ip.addr == IF_TS_PS_IP_ADDRESS and tls
   * (TCP)
     > ip.addr == IF_TS_PS_IP_ADDRESS and http

### Test Body

#### Stimulus
Send HTTP GET to /Versions entrypoint of Policy Store:

- (TLSv1.2):
  
  `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.2 -X GET https://IF_PS_TS_IP_ADDRESS:PORT/Versions`

- (TLSv1.3):
  
  `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.3 -X GET https://IF_PS_TS_IP_ADDRESS:PORT/Versions`

- (TCP):
  
  `curl -X GET http://IF_PS_TS_IP_ADDRESS:PORT/Versions`

#### Response
Policy Store should respond with HTTP 200 OK with JSON body containing:
1. 'fingerprint' with string value
2. 'versions' which is array.
3. Each of 'versions' element should contain 'major' and 'minor' integer values
4. Each of 'versions' element should contain 'serviceInfo' element containing "requiredAlgorithms with array of string describing accepted JWS algorithms
5. 'vendor' if present shall be a string

Example:

```
{
    "fingerprint": "Woof-FurrySuite-v8-8c439e",
    "versions": [
    {
        "major": 6, "minor": 3,
        "vendor": "burby-magic",
        "serviceInfo": {
            "requiredAlgorithms": [ "EdDSA" ]
        }
    }
    ]
}
```


VERDICT:
* PASSED - if response has correct JSON body
* FAILED - any other cases


### Test Postamble
#### Test System
* stop Wireshark (if still running)
* archive all logs generated
* disconnect interfaces from IUT
* (TLS) remove certificates

#### Policy Store
* disconnect interfaces from Test System
* reconnect interfaces back to default

## Post-Test Conditions
### Test System 
* Test tools stopped
* interfaces disconnected from IUT

### Policy Store
* device connected back to default
* device in normal operating state

## Sequence Diagram
<!--
[![](https://mermaid.ink/img/pako:eNpNkE9rAkEMxb9KyKniLojHOQiFlkpLq7B7krkMM3F3qDOx8wdZxO_u7GrRnBLyy-PlnVGzIRRY17X0mv3edkJ6AGdD4PCqE4coYK8OkaSfoEh_mbymN6u6oNwI36qlmKAZYiJXr1bzLR-sHqApCiRg3bZb-HhvH_jzfuSfzu_4crGAzRe8nGzq4bPZ_MywQkfBKWuK5fOoJTH15EiiKK1R4Vei9JfCqZy4GbxGkUKmCvPRqPRvGsX0UYVH5XfMj5mMLX6-b5lM0VQYOHf9nbhcAeRpY3I?type=png)](https://mermaid.live/edit#pako:eNpNkE9rAkEMxb9KyKniLojHOQiFlkpLq7B7krkMM3F3qDOx8wdZxO_u7GrRnBLyy-PlnVGzIRRY17X0mv3edkJ6AGdD4PCqE4coYK8OkaSfoEh_mbymN6u6oNwI36qlmKAZYiJXr1bzLR-sHqApCiRg3bZb-HhvH_jzfuSfzu_4crGAzRe8nGzq4bPZ_MywQkfBKWuK5fOoJTH15EiiKK1R4Vei9JfCqZy4GbxGkUKmCvPRqPRvGsX0UYVH5XfMj5mMLX6-b5lM0VQYOHf9nbhcAeRpY3I)
-->

![image](https://github.com/user-attachments/assets/62338a2c-35ad-497c-ac61-6d649181c8b7)


## Comments

Version:  010.3f.3.0.5

Date:     20250428

## Footnotes
[^1]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^2]: Wireshark configuration to decrypt TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^3]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518
