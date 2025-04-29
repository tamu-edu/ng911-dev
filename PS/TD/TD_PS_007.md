# Test Description: TD_PS_007
## Overview
### Summary
Rulesets verification

### Description
Test covers rulesets verification by Policy Store

### References
* Requirements : RQ_PS_027, RQ_PS_031, RQ_PS_034, RQ_PS_035, RQ_PS_044
* Test Case    : 

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

![image](https://github.com/user-attachments/assets/664493f9-a570-4527-a32b-a6a37dda1c70)


## Pre-Test Conditions
### Test System
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* ng911 repository cloned to local storage
* (TLS) Generated own PCA-signed certificate and private key files (test_system.crt, test_system.key)
* (TLS) Certificate and key used by Policy Store copied to local storage
* (TLS) PCA certificate copied to local storage

### Policy Store (PS)
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Default configuration is loaded
* IUT is initialized with steps from IXIT config file
* Device is active
* Device is in normal operating state
* some policies are already stored

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
* generate JWS objects for all variations, use adequate JSON files f.e.:

```
Policy_object_without_unique_id_v010.3f.3.0.X.json
```
edit each JSON file to set policyOwner matching CN of test_system.crt, then run script to generate JWS object:

```
python3 -m main generate_jws Policy_object_without_unique_id_v010.3f.3.0.X.json --cert test_system.crt --key test_system.key
```

### Test Body

#### Variations
1. Validate 4xx error response for HTTP POST request with policy ruleset missing unique ID's
Generate JWS from file:
`Policy_object_without_unique_id_v010.3f.3.0.X.json`
2. Validate 4xx error response for HTTP PUT request with policy ruleset missing unique ID's
Generate JWS from file:
`Policy_object_without_unique_id_v010.3f.3.0.X.json`
3. Validate 4xx error response for HTTP POST request with policy ruleset missing 'id'
Generate JWS from file:
`Policy_object_without_id_member_v010.3f.3.0.X.json`
4. Validate 4xx error response for HTTP POST request with policy ruleset missing 'priority'
Generate JWS from file:
`Policy_object_without_priority_member_v010.3f.3.0.X.json`
5. Validate 4xx error response for HTTP POST request with policy ruleset missing 'actions'
Generate JWS from file:
`Policy_object_without_actions_member_v010.3f.3.0.X.json`
6. Validate 4xx error response for HTTP POST request with policy ruleset missing unique 'priority' for each rule
Generate JWS from file:
`Policy_object_without_unique_priority_v010.3f.3.0.X.json`
7. Validate 4xx error response for HTTP POST request with policy containing incorrect 'dateStart' in 'TimePeriodCondition' (incorrect year)
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "20130-08-10T12:58:03.01-05:00",
"policyRules_0_conditions_0_dateEnd": "2030-08-11T12:58:03.01-05:00",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`
8. Validate 4xx error response for HTTP POST request with policy containing incorrect 'dateStart' in 'TimePeriodCondition' (incorrect month)
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "2030-13-10T12:58:03.01-05:00",
"policyRules_0_conditions_0_dateEnd": "2030-08-11T12:58:03.01-05:00",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`
9. Validate 4xx error response for HTTP POST request with policy containing incorrect 'dateStart' in 'TimePeriodCondition' (incorrect day)
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "2030-08-32T12:58:03.01-05:00",
"policyRules_0_conditions_0_dateEnd": "2030-08-11T12:58:03.01-05:00",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`
10. Validate 4xx error response for HTTP POST request with policy containing incorrect 'dateStart' in 'TimePeriodCondition' (incorrect hour)
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "2030-08-10T24:58:03.01-05:00",
"policyRules_0_conditions_0_dateEnd": "2030-08-11T12:58:03.01-05:00",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`
11. Validate 4xx error response for HTTP POST request with policy containing incorrect 'dateStart' in 'TimePeriodCondition' (incorrect minute)
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "2030-08-10T12:60:03.01-05:00",
"policyRules_0_conditions_0_dateEnd": "2030-08-11T12:58:03.01-05:00",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`
12. Validate 4xx error response for HTTP POST request with policy containing incorrect 'dateStart' in 'TimePeriodCondition' (incorrect second)
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "2030-08-10T12:58:60.01-05:00",
"policyRules_0_conditions_0_dateEnd": "2030-08-11T12:58:03.01-05:00",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`
13. Validate 4xx error response for HTTP POST request with policy containing incorrect 'dateStart' in 'TimePeriodCondition' (incorrect time offset)
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "2030-08-10T12:58:03.01-13:00",
"policyRules_0_conditions_0_dateEnd": "2030-08-11T12:58:03.01-05:00",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`
14. Validate 4xx error response for HTTP POST request with policy containing incorrect 'dateStart' in 'TimePeriodCondition' (incorrect day in February)
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "2030-02-30T12:58:03.01-05:00",
"policyRules_0_conditions_0_dateEnd": "2030-08-11T12:58:03.01-05:00",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`
15. Validate 4xx error response for HTTP POST request with policy containing incorrect 'dateEnd' in 'TimePeriodCondition' (incorrect year)
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "2030-08-10T12:58:03.01-05:00",
"policyRules_0_conditions_0_dateEnd": "20130-08-10T12:58:03.01-05:00",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`
16. Validate 4xx error response for HTTP POST request with policy containing incorrect 'dateEnd' in 'TimePeriodCondition' (incorrect month)
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "2030-08-10T12:58:03.01-05:00",
"policyRules_0_conditions_0_dateEnd": "2030-13-11T12:58:03.01-05:00",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`
17. Validate 4xx error response for HTTP POST request with policy containing incorrect 'dateEnd' in 'TimePeriodCondition' (incorrect day)
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "2030-08-10T12:58:03.01-05:00",
"policyRules_0_conditions_0_dateEnd": "2030-08-11T12:58:03.01-05:00",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`
18. Validate 4xx error response for HTTP POST request with policy containing incorrect 'dateEnd' in 'TimePeriodCondition' (incorrect hour)
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "2030-08-10T12:58:03.01-05:00",
"policyRules_0_conditions_0_dateEnd": "2030-08-11T24:58:03.01-05:00",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`
19. Validate 4xx error response for HTTP POST request with policy containing incorrect 'dateEnd' in 'TimePeriodCondition' (incorrect minute)
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "2030-08-10T12:58:03.01-05:00",
"policyRules_0_conditions_0_dateEnd": "2030-08-11T12:60:03.01-05:00",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`
20. Validate 4xx error response for HTTP POST request with policy containing incorrect 'dateEnd' in 'TimePeriodCondition' (incorrect second)
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "2030-08-10T12:58:03.01-05:00",
"policyRules_0_conditions_0_dateEnd": "2030-08-11T12:58:60.01-05:00",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`
21. Validate 4xx error response for HTTP POST request with policy containing incorrect 'dateEnd' in 'TimePeriodCondition' (incorrect time offset)
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "2030-08-10T12:58:03.01-05:00",
"policyRules_0_conditions_0_dateEnd": "2030-08-11T12:58:03.01-13:00",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`
22. Validate 4xx error response for HTTP POST request with policy containing incorrect 'dateEnd' in 'TimePeriodCondition' (incorrect day in February)
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "2030-01-10T12:58:03.01-05:00",
"policyRules_0_conditions_0_dateEnd": "2030-02-30T12:58:03.01-05:00",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`
23. Validate 4xx error response for HTTP POST request with policy containing incorrect TimePeriodCondition (dateEnd earlier than dateStart)
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "2030-03-30T12:58:03.01-05:00",
"policyRules_0_conditions_0_dateEnd": "2030-01-30T12:58:03.01-05:00",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`
24. Validate 4xx error response for HTTP POST request with policy containing incorrect 'timeStart' in 'TimePeriodCondition' (incorrect hour)
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "2030-01-30T12:58:03.01-05:00",
"policyRules_0_conditions_0_dateEnd": "2030-03-30T12:58:03.01-05:00",
"policyRules_0_conditions_0_timeStart": "24:10:00",
"policyRules_0_conditions_0_timeEnd": "20:24:12",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`
25. Validate 4xx error response for HTTP POST request with policy containing incorrect 'timeStart' in 'TimePeriodCondition' (incorrect minute)
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "2030-01-30T12:58:03.01-05:00",
"policyRules_0_conditions_0_dateEnd": "2030-03-30T12:58:03.01-05:00",
"policyRules_0_conditions_0_timeStart": "12:61:00",
"policyRules_0_conditions_0_timeEnd": "20:24:12",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`
26. Validate 4xx error response for HTTP POST request with policy containing incorrect 'timeStart' in 'TimePeriodCondition' (incorrect second)
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "2030-01-30T12:58:03.01-05:00",
"policyRules_0_conditions_0_dateEnd": "2030-03-30T12:58:03.01-05:00",
"policyRules_0_conditions_0_timeStart": "12:10:61",
"policyRules_0_conditions_0_timeEnd": "20:24:12",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`
27. Validate 4xx error response for HTTP POST request with policy containing incorrect 'timeEnd' in 'TimePeriodCondition' (incorrect hour)
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "2030-01-30T12:58:03.01-05:00",
"policyRules_0_conditions_0_dateEnd": "2030-03-30T12:58:03.01-05:00",
"policyRules_0_conditions_0_timeStart": "12:10:00",
"policyRules_0_conditions_0_timeEnd": "24:24:12",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`
28. Validate 4xx error response for HTTP POST request with policy containing incorrect 'timeEnd' in 'TimePeriodCondition' (incorrect minute)
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "2030-01-30T12:58:03.01-05:00",
"policyRules_0_conditions_0_dateEnd": "2030-03-30T12:58:03.01-05:00",
"policyRules_0_conditions_0_timeStart": "12:11:00",
"policyRules_0_conditions_0_timeEnd": "20:61:12",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`
29. Validate 4xx error response for HTTP POST request with policy containing incorrect 'timeEnd' in 'TimePeriodCondition' (incorrect second)
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "2030-01-30T12:58:03.01-05:00",
"policyRules_0_conditions_0_dateEnd": "2030-03-30T12:58:03.01-05:00",
"policyRules_0_conditions_0_timeStart": "12:10:11",
"policyRules_0_conditions_0_timeEnd": "20:24:61",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`

30. Validate 4xx error response for HTTP POST request with policy containing incorrect 'weekdayList' in 'TimePeriodCondition'
Parameters to set:
```
"policyRules_0_conditions_0_conditionType": "TimePeriodCondition",
"policyRules_0_conditions_0_dateStart": "2030-01-30T12:58:03.01-05:00",
"policyRules_0_conditions_0_dateEnd": "2030-03-30T12:58:03.01-05:00",
"policyRules_0_conditions_0_timeStart": "12:10:11",
"policyRules_0_conditions_0_timeEnd": "20:24:11",
"policyRules_0_conditions_0_weekdayList_0": "test",
```
Generate JWS from file:
`Policy_object_with_incorrect_TimePeriodCondition_1_v010.3f.3.0.X.json`


#### Stimulus

1. For HTTP PUT (Variation 2) use URL containing data matching one of policies already stored, f.e.:

```
IF_PS_TS_IP_ADDRESS:PORT/Policies?policyOwner=tester@ng911.test.system.com
```

2. For HTTP POST (other variations) use URL:

```
IF_PS_TS_IP_ADDRESS:PORT/Policies
```

Send HTTP POST/PUT to /Policies entrypoint of Policy Store:

   - (TLSv1.2):

   `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.2 -X PUT/POST https://URL -H "Content-Type: application/json" -d GENERATED_JWS_OBJECT`
    
   - (TLSv1.3):

   `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.3 -X PUT/POST https://URL -H "Content-Type: application/json" -d GENERATED_JWS_OBJECT`
    
   - (TCP):

   `curl -X PUT/POST https://URL -H "Content-Type: application/json" -d GENERATED_JWS_OBJECT`


#### Response
IUT responds with HTTP 4XX error message

VERDICT:
* PASSED - if Policy Store responded as expected
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
[![](https://mermaid.ink/img/pako:eNq9Ut9LwzAQ_lfCvZqOtJ3pkoeB4IMI6qBVh-QltLctuCYzTcU69r_bdZPNRxHM0-X4fhz33RZKVyFIiKJI2dLZhVlKZQmpjffOX5XB-UaShV43qOwAavCtRVvitdFLr-s9-PAKbALJuyZgHU2nFzO3NmVH8l4BJbkpihmZPeQFuSC3z_mJdQ7b085UjqzxfP4rk8e_ety7gMS9oz93o-Sn15P2RgfjbEPSKGX_vAagUKOvtan67Lb7voKwwhoVyL6stH9VoOyux-k2uLyzJcjgW6TQbiodvtMDOURLYaPti3OnP1amH-XucBzDjQwYkFv4ABknfBRzIUSWMiEmIksodCD7bsoSFicTIRgT8ZjvKHwOsuNRwjlnWcbjdJKyy4yCd-1ydTTcfQGRQMTf?type=png)](https://mermaid.live/edit#pako:eNq9Ut9LwzAQ_lfCvZqOtJ3pkoeB4IMI6qBVh-QltLctuCYzTcU69r_bdZPNRxHM0-X4fhz33RZKVyFIiKJI2dLZhVlKZQmpjffOX5XB-UaShV43qOwAavCtRVvitdFLr-s9-PAKbALJuyZgHU2nFzO3NmVH8l4BJbkpihmZPeQFuSC3z_mJdQ7b085UjqzxfP4rk8e_ety7gMS9oz93o-Sn15P2RgfjbEPSKGX_vAagUKOvtan67Lb7voKwwhoVyL6stH9VoOyux-k2uLyzJcjgW6TQbiodvtMDOURLYaPti3OnP1amH-XucBzDjQwYkFv4ABknfBRzIUSWMiEmIksodCD7bsoSFicTIRgT8ZjvKHwOsuNRwjlnWcbjdJKyy4yCd-1ydTTcfQGRQMTf)
-->

![image](https://github.com/user-attachments/assets/257d8507-3e4f-44b7-98e5-97307a360858)

## Comments

Version:  010.3f.3.1.4

Date:     20250428

## Footnotes
[^1]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^2]: Wireshark configuration to decrypt TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^3]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518
