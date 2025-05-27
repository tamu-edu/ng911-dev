# Test Description: TD_PS_002
## Overview
### Summary
Policy Object contents verification

### Description
Test covers Policy Object contents verification while sending HTTP POST

### References
* Requirements : RQ_PS_010, RQ_PS_025
* Test Case    : TC_PS_002

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

![image](https://github.com/user-attachments/assets/ba1b3495-e027-4a5a-a8b4-1770620a7a64)


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

* verify if JWS policy generate from default `Policy_object_example_v010.3f.3.0.X.json` is acceptable for Policy Store. Send HTTP POST and check if PS responded with "HTTP 201 Policy Successfully Created". Example HTTP POST command:

- (TLSv1.2):
  
  `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.2 -X POST https://IF_PS_TS_IP_ADDRESS:PORT/Policies -H "Content-Type: application/json" -d GENERATED_JWS_OBJECT`

- (TLSv1.3):
  
  `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.3 -X POST https://IF_PS_TS_IP_ADDRESS:PORT/Policies -H "Content-Type: application/json" -d GENERATED_JWS_OBJECT`

- (TCP):
  
  `curl -X POST https://IF_PS_TS_IP_ADDRESS:PORT/Policies -H "Content-Type: application/json" -d GENERATED_JWS_OBJECT`

* use `Policy_object_example_v010.3f.3.0.X.json` from test repository to prepare json files for each variation. Change in file parameters mentioned in variation f.e. for Variation 2 change `"policyOwner": "user@test.example"` to `"policyOwner": "tester@ng911.te$t"`
* use prepared json files, run script to generate JWS object for each varation, example:

```
python -m main generate_jws Policy_object_without_policyOwner_v010.3f.3.0.X.json --cert test_system.crt --key test_system.key
```

### Test Body

#### Variations
JWS with Policy Object:
1. Validate 4xx error response for request without 'policyOwner' parameter
2. Validate 4xx error response for request with incorrect 'policyOwner' parameter (special characters not allowed in FQDN): `"policyOwner": "tester@ng911.te$t"`
3. Validate 4xx error response for request with incorrect 'policyOwner' parameter (missing '@'): `"policyOwner": "testerng911.test"`
4. Validate 4xx error response for request with incorrect 'policyOwner' parameter (double '@'): `"policyOwner": "tester@@ng911.test"`
5. Validate 4xx error response for request with incorrect 'policyOwner' parameter (leading period): `"policyOwner": ".tester@ng911.test"`
6. Validate 4xx error response for request with incorrect 'policyOwner' parameter (length exceeded): `"policyOwner": "tester@ng911.testtesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttestt"`
7. Validate 4xx error response for request without 'policyType' parameter
8. Validate 4xx error response for request with incorrect 'policyType' parameter: `"policyType": "OtherRoutePolicyy"`
9. Validate 4xx error response for request without 'policyRules' parameter
10. Validate 4xx error response for request with `"policyType": "OtherRoutePolicy"` and without 'policyId' parameter
11. Validate 4xx error response for request with `"policyType": "OtherRoutePolicy"` and with incorrect 'policyId' parameter (send integer): `"policyId": 123`
12. Validate 201 created response for request with `"policyType": "OtherRoutePolicy"` and with incorrect 'policyId' parameter: `"policyId": "\n"`
13. Validate 201 created response for request with `"policyType": "OtherRoutePolicy"` and with incorrect 'policyId' parameter: `"policyId": "'"`
14. Validate 201 created response for request with `"policyType": "OtherRoutePolicy"` and with incorrect 'policyId' parameter: `"policyId": "("`
15. Validate 4xx error response for request with `"policyType": "OriginationRoutePolicy"` and with `"policyId": "test_123"`
16. Validate 4xx error response for request with `"policyType": "OriginationRoutePolicy"` or `"policyType": "NormalNextHopRoutePolicy"` and without 'policyQueueName'
17. Validate 4xx error response for request with `"policyType": "OtherRoutePolicy"` and with `"policyQueueName": "test"`
18. Validate 4xx error response for request with incorrect 'policyExpirationTime' parameter (incorrect year): `"policyExpirationTime": "21155-08-21T12:58:03.01-05:00"`
19. Validate 4xx error response for request with incorrect 'policyExpirationTime' parameter (incorrect month): `"timestamp": "2115-13-21T12:58:03.01-05:00"`
20. Validate 4xx error response for request with incorrect 'policyExpirationTime' parameter (incorrect day): `"policyExpirationTime": "2115-12-32T12:58:03.01-05:00"`
21. Validate 4xx error response for request with incorrect 'policyExpirationTime' parameter (incorrect hour): `"policyExpirationTime": "2115-12-21T24:58:03.01-05:00"`
22. Validate 4xx error response for request with incorrect 'policyExpirationTime' parameter (incorrect minute): `"policyExpirationTime": "2115-12-21T12:60:03.01-05:00"`
23. Validate 4xx error response for request with incorrect 'policyExpirationTime' parameter (incorrect second): `"policyExpirationTime": "2115-12-21T12:58:61.01-05:00"`
24. Validate 4xx error response for request with incorrect 'policyExpirationTime' parameter (incorrect time offset): `"policyExpirationTime": "2115-12-21T12:58:03.01-13:00"`
25. Validate 4xx error response for request with incorrect 'policyExpirationTime' parameter (incorrect day in February): `"policyExpirationTime": "2115-02-30T12:58:03.01-05:00"`
26. Validate 4xx error response for request with incorrect 'policyExpirationTime' parameter (date in the past): `"policyExpirationTime": "2015-04-30T12:58:03.01-05:00"`
27. Validate 4xx error response for request with incorrect 'description' parameter (send integer): `"description": 123`
28. Validate 201 created response for request with incorrect 'description' parameter: `"description": "\n"`
29. Validate 201 created response for request with incorrect 'description' parameter: `"description": "'"`
30. Validate 201 created response for request with incorrect 'description' parameter: `"description": "("`

#### Stimulus
Send HTTP POST to Policy Store with generated JWS object for tested variation:

- (TLSv1.2):
  
  `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.2 -X POST https://IF_PS_TS_IP_ADDRESS:PORT/Policies -H "Content-Type: application/json" -d JWS_OBJECT`

- (TLSv1.3):
  
  `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.3 -X POST https://IF_PS_TS_IP_ADDRESS:PORT/Policies -H "Content-Type: application/json" -d JWS_OBJECT`

- (TCP):
  
  `curl -X POST https://IF_PS_TS_IP_ADDRESS:PORT/Policies -H "Content-Type: application/json" -d JWS_OBJECT`

#### Response
Variations 1-11, 15-27
Policy Store responds with HTTP 4XX error message

Variations 12-14, 28-30
Policy Store responds with HTTP 201 Created message

VERDICT:
* PASSED - if Policy Store responded as expected
* FAILED - any other cases


### Test Postamble
#### Test System
* stop Wireshark (if still running)
* archive all logs generated
* remove all scenario files
* disconnect interfaces from IUT
* (TLS) remove certificates

#### FE storing policies or Policy Store
* disconnect interfaces from Test System
* reconnect interfaces back to default
* if sent policies were accepted, remove them

## Post-Test Conditions
### Test System 
* Test tools stopped
* interfaces disconnected from IUT

### Policy Store
* device connected back to default
* device in normal operating state
* policies added during testing are removed

## Sequence Diagram
<!--
[![](https://mermaid.ink/img/pako:eNrNk8FLwzAUxv-V8K42I2m7tslhIHrwog5aZEguoX3bimsy01SsY_-7XTfYvA4Uc0rC7_vex-O9HZS2QpBAKVWmtGZZr6QyhDS1c9bdlt66VpKl3rSozAi1-N6hKfG-1iunG2WerEdiP9CRAltP8r712ARkbjd12ZN8cEBJXrSrta-taQmnnB9KHM-Fhs5mNz9VD0UxJ_PnvDjzl8BBcKE_8fFicUWokPL4N1OFjJM7h9pjdUW6KQ3Tf9ezMKMR-6OeQQANukbX1TCsu4OJAr_GBhXI4Vpp96ZAmf3A6c7bvDclSO86DKDbVoPDaVxBjrMcwFabV2vPb6zqIcjjcRvGpRgZkDv4BMnDZMITIUQaMSEykYYB9CCH34gNKcNMCMYEj5N9AF-jbTwJkyRhaZrwKIvYNA3A2W61PhXcfwMqaBlU?type=png)](https://mermaid.live/edit#pako:eNrNk8FLwzAUxv-V8K42I2m7tslhIHrwog5aZEguoX3bimsy01SsY_-7XTfYvA4Uc0rC7_vex-O9HZS2QpBAKVWmtGZZr6QyhDS1c9bdlt66VpKl3rSozAi1-N6hKfG-1iunG2WerEdiP9CRAltP8r712ARkbjd12ZN8cEBJXrSrta-taQmnnB9KHM-Fhs5mNz9VD0UxJ_PnvDjzl8BBcKE_8fFicUWokPL4N1OFjJM7h9pjdUW6KQ3Tf9ezMKMR-6OeQQANukbX1TCsu4OJAr_GBhXI4Vpp96ZAmf3A6c7bvDclSO86DKDbVoPDaVxBjrMcwFabV2vPb6zqIcjjcRvGpRgZkDv4BMnDZMITIUQaMSEykYYB9CCH34gNKcNMCMYEj5N9AF-jbTwJkyRhaZrwKIvYNA3A2W61PhXcfwMqaBlU)
-->

![image](https://github.com/user-attachments/assets/522b21c6-6024-4a09-b95f-e717d1c2643c)

## Comments

Version:  010.3f.3.1.11

Date:     20250512

## Footnotes
[^1]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^2]: Wireshark configuration to decrypt TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^3]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518
