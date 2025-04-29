# Test Description: TD_LOG_007
## Overview
### Summary
Verification of CallStartLogEvent, CallEndLogEvent, RecCallStartLogEvent and RecCallEndLogEvent

### Description
Test covers LogEvent JWS object verification on HTTP POST requests containing:
- CallStartLogEvent
- CallEndLogEvent
- RecCallStartLogEvent
- RecCallEndLogEvent

### References
* Requirements : RQ_LOG_54, RQ_LOG_55, RQ_LOG_58, RQ_LOG_59
* Test Case    : TC_LOG_007

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
[![](https://mermaid.ink/img/pako:eNpdkEFPhDAQhf8KmTO7KbAW2hhPRmOCMZE9GZJNpbNAXCgpRUXCf3cETXbtad438-Y1M0FhNIKE48l8FJWyzkuf89aj93B32GeH9On-erO5IUEVgbXXD6-lVV3l7bF3Xjb2Dpu1c-FcEbb6nys1ZVm3pZehfa8LvHCex5ATfGjQNqrW9MnpB-fgKmwwB0mlVvYth7ydaU4NzmRjW4B0dkAfhk4rh7e1otDmD3aqfTGG5FGdetKoa2fs43qE5RbLDMgJPkEGId8GXAgRR0yIRMShDyNIohELWRAmQjAmgh2fffha1u62IeecxTEPoiRiV7EP1gxl9Rs4fwP4vG62?type=png)](https://mermaid.live/edit#pako:eNpdkEFPhDAQhf8KmTO7KbAW2hhPRmOCMZE9GZJNpbNAXCgpRUXCf3cETXbtad438-Y1M0FhNIKE48l8FJWyzkuf89aj93B32GeH9On-erO5IUEVgbXXD6-lVV3l7bF3Xjb2Dpu1c-FcEbb6nys1ZVm3pZehfa8LvHCex5ATfGjQNqrW9MnpB-fgKmwwB0mlVvYth7ydaU4NzmRjW4B0dkAfhk4rh7e1otDmD3aqfTGG5FGdetKoa2fs43qE5RbLDMgJPkEGId8GXAgRR0yIRMShDyNIohELWRAmQjAmgh2fffha1u62IeecxTEPoiRiV7EP1gxl9Rs4fwP4vG62)
-->

![image](https://github.com/user-attachments/assets/97a0b9d8-1827-4681-a9a3-eeced26df872)


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
* TD_LOG_003 tests passed

## Test Sequence

### Test Preamble

#### Test System
* Install Wireshark[^1]
* (TLS v1.2) Configure Wireshark to decode HTTP over TLS, use tests system and PS certificate keys [^2]
* (TLS v1.3) Configure logging of session keys and configure Wireshark to decode HTTP over TLS [^3]
* Using Wireshark on 'Test System' start packet tracing on IF_TS_PS interface - run following filter:
   * (TLS)
     > ip.addr == IF_TS_LOG_IP_ADDRESS and tls
   * (TCP)
     > ip.addr == IF_TS_LOG_IP_ADDRESS and http

* use `CallStartLogEvent_object_example_v010.3f.3.0.X.json`, `CallEndLogEvent_object_example_v010.3f.3.0.X.json`, `RecCallStartLogEvent_object_example_v010.3f.3.0.X.json` and `RecCallEndLogEvent_object_example_v010.3f.3.0.X.json` from test repository to prepare json files for each variation. Change in file one of parameters which is mentioned in variation, f.e. for Variation1 change `"direction": "incoming"` to `"direction": 123` and save as a separate file
* go to test_suite directory, run script to generate JWS object for each varation, example:

```
python -m main generate_jws CallStartLogEvent_object_example_v010.3f.3.0.X.json --cert test_system.crt --key test_system.key
```

### Test Body

#### Variations

1. Validate 4xx error response for CallStartLogEvent request with incorrect 'direction' parameter (send integer): `"direction": 123`
2. Validate 4xx error response for CallStartLogEvent request with incorrect 'direction' parameter (send 'incomingg'): `"direction": "incomingg"`
3. Validate 4xx error response for CallStartLogEvent request without 'direction' parameter.
4. Validate 4xx error response for CallStartLogEvent request with incorrect 'standardPrimaryCallType' parameter (send integer): `"standardPrimaryCallType": 123`
5. Validate 4xx error response for CallStartLogEvent request with incorrect 'standardPrimaryCallType' parameter: `"standardPrimaryCallType": "emergencyy"`
6. Validate 4xx error response for CallStartLogEvent request with incorrect 'standardSecondaryCallType' parameter (send integer): `"standardSecondaryCallType": 123`
7. Validate 4xx error response for CallStartLogEvent request with incorrect 'standardSecondaryCallType' parameter: `"standardSecondaryCallType": "emergencyy"`
8. Validate 4xx error response for CallStartLogEvent request with incorrect 'localCallType' parameter (send integer): `"localCallType": 123`
9. Validate 201 Created response for CallStartLogEvent request with: `"localCallType": "\n"`
10. Validate 201 Created response for CallStartLogEvent request with: `"localCallType": "'"`
11. Validate 201 Created response for CallStartLogEvent request with: `"localCallType": "("`
12. Validate 4xx error response for CallStartLogEvent request with incorrect 'localUse' parameter (send integer): `"localUse": 123`
13. Validate 4xx error response for CallStartLogEvent request with incorrect 'localUse' parameter (send incorrect JSON): `"localUse": {"test": "test",}`
14. Validate 4xx error response for CallEndLogEvent request with incorrect 'direction' parameter (send integer): `"direction": 123`
15. Validate 4xx error response for CallEndLogEvent request with incorrect 'direction' parameter (send 'incomingg'): `"direction": "incomingg"`
16. Validate 4xx error response for CallEndLogEvent request without 'direction' parameter.
17. Validate 4xx error response for CallEndLogEvent request with incorrect 'standardPrimaryCallType' parameter (send integer): `"standardPrimaryCallType": 123`
18. Validate 4xx error response for CallEndLogEvent request with incorrect 'standardPrimaryCallType' parameter: `"standardPrimaryCallType": "emergencyy"`
19. Validate 4xx error response for CallEndtLogEvent request with incorrect 'standardSecondaryCallType' parameter (send integer): `"standardSecondaryCallType": 123`
20. Validate 4xx error response for CallEndLogEvent request with incorrect 'standardSecondaryCallType' parameter: `"standardSecondaryCallType": "emergencyy"`
21. Validate 4xx error response for CallEndLogEvent request with incorrect 'localCallType' parameter (send integer): `"localCallType": 123`
22. Validate 201 Created response for CallEndLogEvent request with: `"localCallType": "\n"`
23. Validate 201 Created response for CallEndLogEvent request with: `"localCallType": "'"`
24. Validate 201 Created response for CallEndLogEvent request with: `"localCallType": "("`
25. Validate 4xx error response for CallEndLogEvent request with incorrect 'localUse' parameter (send integer): `"localUse": 123`
26. Validate 4xx error response for CallEndLogEvent request with incorrect 'localUse' parameter (send incorrect JSON): `"localUse": {"test": "test",}`
27. Validate 4xx error response for RecCallStartLogEvent request with incorrect 'direction' parameter (send integer): `"direction": 123`
28. Validate 4xx error response for RecCallStartLogEvent request with incorrect 'direction' parameter (send 'incomingg'): `"direction": "incomingg"`
29. Validate 4xx error response for RecCallStartLogEvent request without 'direction' parameter.
30. Validate 4xx error response for RecCallStartLogEvent request with incorrect 'standardPrimaryCallType' parameter (send integer): `"standardPrimaryCallType": 123`
31. Validate 4xx error response for RecCallStartLogEvent request with incorrect 'standardPrimaryCallType' parameter: `"standardPrimaryCallType": "emergencyy"`
32. Validate 4xx error response for RecCallStartLogEvent request with incorrect 'standardSecondaryCallType' parameter (send integer): `"standardSecondaryCallType": 123`
33. Validate 4xx error response for RecCallStartLogEvent request with incorrect 'standardSecondaryCallType' parameter: `"standardSecondaryCallType": "emergencyy"`
34. Validate 4xx error response for RecCallStartLogEvent request with incorrect 'localCallType' parameter (send integer): `"localCallType": 123`
35. Validate 201 Created response for RecCallStartLogEvent request with: `"localCallType": "\n"`
36. Validate 201 Created response for RecCallStartLogEvent request with: `"localCallType": "'"`
37. Validate 201 Created response for RecCallStartLogEvent request with: `"localCallType": "("`
38. Validate 4xx error response for RecCallStartLogEvent request with incorrect 'localUse' parameter (send integer): `"localUse": 123`
39. Validate 4xx error response for RecCallStartLogEvent request with incorrect 'localUse' parameter (send incorrect JSON): `"localUse": {"test": "test",}`
40. Validate 4xx error response for RecCallEndLogEvent request with incorrect 'direction' parameter (send integer): `"direction": 123`
41. Validate 4xx error response for RecCallEndLogEvent request with incorrect 'direction' parameter (send 'incomingg'): `"direction": "incomingg"`
42. Validate 4xx error response for RecCallEndLogEvent request without 'direction' parameter.
43. Validate 4xx error response for RecCallEndLogEvent request with incorrect 'standardPrimaryCallType' parameter (send integer): `"standardPrimaryCallType": 123`
44. Validate 4xx error response for RecCallEndLogEvent request with incorrect 'standardPrimaryCallType' parameter: `"standardPrimaryCallType": "emergencyy"`
45. Validate 4xx error response for RecCallEndLogEvent request with incorrect 'standardSecondaryCallType' parameter (send integer): `"standardSecondaryCallType": 123`
46. Validate 4xx error response for RecCallEndLogEvent request with incorrect 'standardSecondaryCallType' parameter: `"standardSecondaryCallType": "emergencyy"`
47. Validate 4xx error response for RecCallEndLogEvent request with incorrect 'localCallType' parameter (send integer): `"localCallType": 123`
48. Validate 201 Created response for RecCallEndLogEvent request with: `"localCallType": "\n"`
49. Validate 201 Created response for RecCallEndLogEvent request with: `"localCallType": "'"`
50. Validate 201 Created response for RecCallEndLogEvent request with: `"localCallType": "("`
51. Validate 4xx error response for RecCallEndLogEvent request with incorrect 'localUse' parameter (send integer): `"localUse": 123`
52. Validate 4xx error response for RecCallEndLogEvent request with incorrect 'localUse' parameter (send incorrect JSON): `"localUse": {"test": "test",}`


#### Stimulus
Send HTTP POST to /LogEvents entrypoint of Logging Service with generated JWS object:

- (TLSv1.2):
  
  `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.2 -X POST https://IF_PS_TS_IP_ADDRESS:PORT/LogEvents -H "Content-Type: application/json" -d GENERATED_JWS_OBJECT`

- (TLSv1.3):
  
  `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.3 -X POST https://IF_PS_TS_IP_ADDRESS:PORT/LogEvents -H "Content-Type: application/json" -d GENERATED_JWS_OBJECT`

- (TCP):
  
  `curl -X POST http://IF_PS_TS_IP_ADDRESS:PORT/LogEvents -H "Content-Type: application/json" -d GENERATED_JWS_OBJECT`

#### Response
* Variations  1-8, 12-21, 25-34, 38-47, 51-52
    Logging Service responds with 4xx error message
* Variations  9-11, 22-24, 35-37, 48-50
    Logging Service responds with 201 Created

VERDICT:
* PASSED - if Logging Service responded as expected
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
[![](https://mermaid.ink/img/pako:eNq1UstqwzAQ_BWx10rBkp_SIVDooYc-Ag4lFF-ErTiitZTKcmga8u-VnZaE9liqkyRmZmeYPUBtGwUCCCGVqa1Z61ZUBqFOO2fdde2t6wVay9deVWYC9eptUKZWN1q2TnYj-HQerFfI7pRDS9V7VO57rzqM7mzbatOiUrmdrpVAT9Jp6bU1PUKUFBhRRhjFiKUkTjCKC5LkGKWUpOwsfiFJ5vOrX6K3y-UCLR7L5ZnyAzPSLlS-KMlq9bcEnNDRe4gweg8RgvekIGn0_95ZRAFDp1wndRM6PIz8CvxGdaoCEa6NdC8VVOYYcHLwttybGoR3g8IwbBvpv1sEMVWMYSvNs7Xnt2p0WIH705JMuzJhQBzgHQRl2YxmnPM8jjgveM4w7EGE3zgK7ljBeRRxmmRHDB-TbDJjWZZFeZ7RuIijNMfg7NBuvgYePwEo0sXq?type=png)](https://mermaid.live/edit#pako:eNq1UstqwzAQ_BWx10rBkp_SIVDooYc-Ag4lFF-ErTiitZTKcmga8u-VnZaE9liqkyRmZmeYPUBtGwUCCCGVqa1Z61ZUBqFOO2fdde2t6wVay9deVWYC9eptUKZWN1q2TnYj-HQerFfI7pRDS9V7VO57rzqM7mzbatOiUrmdrpVAT9Jp6bU1PUKUFBhRRhjFiKUkTjCKC5LkGKWUpOwsfiFJ5vOrX6K3y-UCLR7L5ZnyAzPSLlS-KMlq9bcEnNDRe4gweg8RgvekIGn0_95ZRAFDp1wndRM6PIz8CvxGdaoCEa6NdC8VVOYYcHLwttybGoR3g8IwbBvpv1sEMVWMYSvNs7Xnt2p0WIH705JMuzJhQBzgHQRl2YxmnPM8jjgveM4w7EGE3zgK7ljBeRRxmmRHDB-TbDJjWZZFeZ7RuIijNMfg7NBuvgYePwEo0sXq)
-->

![image](https://github.com/user-attachments/assets/343bf36b-e349-4718-ae9b-b0bc0f7a7dd0)


## Comments

Version:  010.3f.3.1.6

Date:     20250428

## Footnotes
[^1]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^2]: Wireshark configuration to decrypt TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^3]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518
