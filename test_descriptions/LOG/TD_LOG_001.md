# Test Description: TD_LOG_001
## Overview
### Summary
Response for HTTP GET to /Versions entrypoint

### Description
Test verifies if Logging Service reponds as required on HTTP GET to /Versions entrypoint

### References
* Requirements : RQ_LOG_002, RQ_LOG_003
* Test Case    : TC_LOG_001

### Requirements
IXIT config file for Logging Service

### HTTP transport types
Test can be performed with 2 different HTTP transport types. Steps describing actions for specific one are marked as following:
- (TLS) - used by default inside ESInet on production environment
- (TCP) - used if default TLS is not possible

## Configuration
### Implementation Under Test Interface Connections
<!-- Identify each of the FEs that are part of the configuration and how they are connected -->
* Logging Service (LOG)
  * IF_LOG_TS - connected to Test System IF_TS_LOG
* Test System
  * IF_TS_LOG - connected to FE IF_LOG_TS

### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* Test System 
  * IF_TS_LOG - Active
* Logging Service (LOG)
  * IF_LOG_TS - Active
 
### Connectivity Diagram
<!--
[![](https://mermaid.ink/img/pako:eNpdkFFPhDAMx7_K0mfuMuAcbDE-GY0JxkTuyZBcJusB8djIGCoSvrsTTLyzT-2v_fffdILSKAQBx5P5KGtpHcmeC018PNwd9vkhe7q_3mxufOEzD9ZeP7xWVnY12WPvSD72Dtu1c6FcEWr1T5WZqmp0RXK0702JF8pzG6-EAFq0rWyUP3L6wQW4GlssQPhUSftWQKFnPycHZ_JRlyCcHTCAoVPS4W0jvWkL4ihPvaed1C_G_NWoGmfs4_qF5RnLDIgJPkGEEduGjHOexJTzlCdRACMIT2Ma0TBKOaeUhzs2B_C1rN1tI8YYTRIWxmlMr5IArBmq-tdw_gZptW8B?type=png)](https://mermaid.live/edit#pako:eNpdkFFPhDAMx7_K0mfuMuAcbDE-GY0JxkTuyZBcJusB8djIGCoSvrsTTLyzT-2v_fffdILSKAQBx5P5KGtpHcmeC018PNwd9vkhe7q_3mxufOEzD9ZeP7xWVnY12WPvSD72Dtu1c6FcEWr1T5WZqmp0RXK0702JF8pzG6-EAFq0rWyUP3L6wQW4GlssQPhUSftWQKFnPycHZ_JRlyCcHTCAoVPS4W0jvWkL4ihPvaed1C_G_NWoGmfs4_qF5RnLDIgJPkGEEduGjHOexJTzlCdRACMIT2Ma0TBKOaeUhzs2B_C1rN1tI8YYTRIWxmlMr5IArBmq-tdw_gZptW8B)
-->

![image](https://github.com/user-attachments/assets/15c86987-911b-488e-8a8b-af52a2083ba8)


## Pre-Test Conditions
### Test System
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* ng911 repository cloned to local storage
* (TLS) Generated own PCA-signed certificate and private key files (test_system.crt, test_system.key)
* (TLS) Certificate and key used by Logging Service copied to local storage
* (TLS) PCA certificate copied to local storage

### Logging Service (LOG)
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
* Using Wireshark on 'Test System' start packet tracing on IF_TS_LOG interface - run following filter:
   * (TLS)
     > ip.addr == IF_TS_LOG_IP_ADDRESS and tls
   * (TCP)
     > ip.addr == IF_TS_LOG_IP_ADDRESS and http

### Test Body

#### Stimulus
Send HTTP GET to /Versions entrypoint of Logging Service:

- (TLSv1.2):
  
  `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.2 -X GET https://IF_LOG_TS_IP_ADDRESS_OR_FQDN:PORT/Versions`

- (TLSv1.3):
  
  `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.3 -X GET https://IF_LOG_TS_IP_ADDRESS_OR_FQDN:PORT/Versions`

- (TCP):
  
  `curl -X GET http://IF_LOG_TS_IP_ADDRESS_OR_FQDN:PORT/Versions`

#### Response
Logging Service should respond with HTTP 200 OK with JSON body containing:
1. 'fingerprint' with string value
2. 'versions' which is array.
3. Each of 'versions' element should contain 'major' and 'minor' integer values
4. Each of 'versions' element should contain 'serviceInfo' element containing "requiredAlgorithms with array of string describing accepted JWS algorithms

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

#### Logging Service
* disconnect interfaces from Test System
* reconnect interfaces back to default

## Post-Test Conditions
### Test System 
* Test tools stopped
* interfaces disconnected from IUT

### Logging Service
* device connected back to default
* device in normal operating state

## Sequence Diagram
<!--
[![](https://mermaid.ink/img/pako:eNpdkMtOwzAQRX_FmhWIpHKS4sReVEICgXi1UrJC3ljJNLEgdnEcoFT9d5K0qIhZzYzOvfPYQWkrBAFhGEpTWrPWtZCGkFY7Z91V6a3rBFmrtw6lmaAO33s0JV5rVTvVjvAhCuw8ybedxzZcLC4ebV1rU5Mc3YcuUZC7oliR25vipPiHjKo_JkdFTClZPpCzT-0bcp8vn88hgBZdq3Q1LL4b7ST4BluUIIa0Uu5VgjT7gVO9t_nWlCC86zGAflMp_7s6iOmuADbKvFh7qrHSw91Ph89MD5oYEDv4AhHFbBYxznmaUM4znsYBbEEM3YTGNIozzinl0ZztA_iebOezmDFG05RFSZbQyzQAZ_u6OQ7c_wAkzHfh?type=png)](https://mermaid.live/edit#pako:eNpdkMtOwzAQRX_FmhWIpHKS4sReVEICgXi1UrJC3ljJNLEgdnEcoFT9d5K0qIhZzYzOvfPYQWkrBAFhGEpTWrPWtZCGkFY7Z91V6a3rBFmrtw6lmaAO33s0JV5rVTvVjvAhCuw8ybedxzZcLC4ebV1rU5Mc3YcuUZC7oliR25vipPiHjKo_JkdFTClZPpCzT-0bcp8vn88hgBZdq3Q1LL4b7ST4BluUIIa0Uu5VgjT7gVO9t_nWlCC86zGAflMp_7s6iOmuADbKvFh7qrHSw91Ph89MD5oYEDv4AhHFbBYxznmaUM4znsYBbEEM3YTGNIozzinl0ZztA_iebOezmDFG05RFSZbQyzQAZ_u6OQ7c_wAkzHfh)
-->

![image](https://github.com/user-attachments/assets/88e236bd-3863-4555-b380-6912db83e657)


## Comments

Version:  010.3f.3.0.2

Date:     20250428

## Footnotes
[^1]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^2]: Wireshark configuration to decrypt TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^3]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518
