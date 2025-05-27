# Test Description: TD_LOG_003

## Overview
### Summary
LogEvent object verification on HTTP POST and sending response

### Description
Test covers LogEvent JWS object verification on HTTP POST request and sending a response with logEventId when correct

### References
* Requirements : RQ_LOG_026, RQ_LOG_036
* Test Case    : TC_LOG_003

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

![image](https://github.com/user-attachments/assets/f5ccc887-8701-4d5b-a5b2-f6e708948418)


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
* Using Wireshark on 'Test System' start packet tracing on IF_TS_PS interface - run following filter:
   * (TLS)
     > ip.addr == IF_TS_LOG_IP_ADDRESS and tls
   * (TCP)
     > ip.addr == IF_TS_LOG_IP_ADDRESS and http
* use `LogEvent_object_example_v010.3f.3.0.X.json` from test repository to prepare json files for each variation. Change in file one of parameters which is mentioned in variation, f.e. for Variation1 change `"clientAssignedIdentifier": "test"` to `"clientAssignedIdentifier": 123` and save as a separate file
* use prepared json files, and run script from test suite main directory to generate JWS object for each varation, example:

```
python -m main generate_jws LogEvent_object_example_v010.3f.3.0.X.json --cert test_system.crt --key test_system.key
```

* for variation #55 use `LogEvent_object_example_v010.3f.3.0.X.json` and adjust following fields:
    - set `"logEventType": "CallSignalingMessageLogEvent"`
    - add:
      ```
      "text": "INVITE urn:service:sos SIP/2.0\n
      Via: SIP/2.0/TLS 192.168.1.100:5061\n
      From: SENDER <sip:SENDER@192.168.1.100:5061>\n
      To: urn:service:sos\n
      Call-ID: 1234567890qwertyuiop@192.168.1.100\n
      Cseq: 1 INVITE\n
      Contact: sip:SENDER@192.168.1.100:5061\n
      Max-Forwards: 70\n"
      ``` 

* for variations #57-58 generate certificates which:
    1. is not signed by PCA
    2. 
    - does not contain 'elementId' in Subject Common Name (CN) (if used LogEvent_object_example_v010.3f.3.0.X.json, then CN should not be 'bcf.ng911.test')
    - **does not contain 'agencyAgentId' in subjectAltName (generate certificate without subjectAltName)**

* using generated certificate create signed JWS object for variation #57:

```
python -m main generate_jws LogEvent_object_example_v010.3f.3.0.X.json --cert not_PCA_signed.crt --key not_PCA_signed.key
```

* using generated certificate create signed JWS object for variation #58:

```
python -m main generate_jws LogEvent_object_example_v010.3f.3.0.X.json --cert without_elementId_and_agenctAgentId.crt --key without_elementId_and_agenctAgentId.key
```

### Test Body

#### Variations

1. Validate 4xx error response for request with incorrect 'clientAssignedIdentifier' parameter (send integer): `"clientAssignedIdentifier": 123`
2. Validate 201 created response for request with `"clientAssignedIdentifier": "\n"`
3. Validate 201 created response for request with `"clientAssignedIdentifier": "'"`
4. Validate 201 created response for request with `"clientAssignedIdentifier": "("`
5. Validate 4xx error response for request with incorrect 'logEventType' parameter (send 'CallStateChangeLogEventt'): `"logEventType": "CallStateChangeLogEventt"`
6. Validate 4xx error response for request without 'logEventType'
7. Validate 4xx error response for request with incorrect 'timestamp' parameter (incorrect year): `"timestamp": "20155-08-21T12:58:03.01-05:00"`
8. Validate 4xx error response for request with incorrect 'timestamp' parameter (incorrect month): `"timestamp": "2015-13-21T12:58:03.01-05:00"`
9. Validate 4xx error response for request with incorrect 'timestamp' parameter (incorrect day): `"timestamp": "2015-12-32T12:58:03.01-05:00"`
10. Validate 4xx error response for request with incorrect 'timestamp' parameter (incorrect hour): `"timestamp": "2015-12-21T24:58:03.01-05:00"`
11. Validate 4xx error response for request with incorrect 'timestamp' parameter (incorrect minute): `"timestamp": "2015-12-21T12:60:03.01-05:00"`
12. Validate 4xx error response for request with incorrect 'timestamp' parameter (incorrect second): `"timestamp": "2015-12-21T12:58:61.01-05:00"`
13. Validate 4xx error response for request with incorrect 'timestamp' parameter (incorrect time offset): `"timestamp": "2015-12-21T12:58:03.01-13:00"`
14. Validate 4xx error response for request with incorrect 'timestamp' parameter (incorrect day in February): `"timestamp": "2015-02-30T12:58:03.01-05:00"`
15. Validate 4xx error response for request without 'timestamp'
16. Validate 4xx error response for request with incorrect 'elementId' parameter (special characters not allowed in FQDN): `"elementId": "bcf#.ng911.te$t"`
17. Validate 4xx error response for request with incorrect 'elementId' parameter (consecutive periods): `"elementId": "bcf..ng911.test"`
18. Validate 4xx error response for request with incorrect 'elementId' parameter (length exceeded): `"elementId": "bcf.ng911.testtesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttest"`
19. Validate 4xx error response for request with incorrect 'elementId' parameter (leading period): `"elementId": ".ng911.test"`
20. Validate 4xx error response for request without 'elementId'
21. Validate 4xx error response for request with incorrect 'agencyId' parameter (special characters not allowed in FQDN): `"agencyId": "bcf#.ng911.te$t"`
22. Validate 4xx error response for request with incorrect 'agencyId' parameter (consecutive periods): `"agencyId": "bcf..ng911.test"`
23. Validate 4xx error response for request with incorrect 'agencyId' parameter (length exceeded): `"agencyId": "bcf.ng911.testtesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttest"`
24. Validate 4xx error response for request with incorrect 'agencyId' parameter (leading period): `"agencyId": ".ng911.test"`
25. Validate 4xx error response for request without 'agencyId'
26. Validate 4xx error response for request with incorrect 'agencyAgentId' parameter (special characters not allowed in FQDN): `"agencyAgentId": "tester@ng911.te$t"`
27. Validate 4xx error response for request with incorrect 'agencyAgentId' parameter (missing '@'): `"agencyAgentId": "testerng911.test"`
28. Validate 4xx error response for request with incorrect 'agencyAgentId' parameter (double '@'): `"agencyAgentId": "tester@@ng911.test"`
29. Validate 4xx error response for request with incorrect 'agencyAgentId' parameter (leading period): `"agencyAgentId": ".tester@ng911.test"`
30. Validate 4xx error response for request with incorrect 'agencyAgentId' parameter (length exceeded): `"agencyAgentId": "tester@ng911.testtesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttesttestt"`
31. Validate 4xx error response for request with incorrect 'agencyPositionId' parameter (send integer): `"agencyPositionId": 123`
32. Validate 201 created response for request with `"agencyPositionId": "\n"`
33. Validate 201 created response for request with `"agencyPositionId": "'"`
34. Validate 201 created response for request with `"agencyPositionId": "("`
35. Validate 4xx error response for request with incorrect 'callId' parameter (incorrect urn): `"callId": "urn:emergency:uid:callidd:123456789qwerty:bcf.ng911.test"`
36. Validate 4xx error response for request with incorrect 'callId' parameter (string ID below 10 characters): `"callId": "urn:emergency:uid:callid:123456789:bcf.ng911.test"`
37. Validate 4xx error response for request with incorrect 'callId' parameter (string ID exceeded 36 characters): `"callId": "urn:emergency:uid:callid:123456789qwertyuiop1234567890qwertyui:bcf.ng911.test"`
38. Validate 4xx error response for request with incorrect 'callId' parameter (incorrect FQDN): `"callId": "urn:emergency:uid:callid:123456789qwertyuiop:bcf.ng911..test"`
39. Validate 4xx error response for request with incorrect 'callId' parameter (doubled ':'): `"callId": "urn:emergency:uid:callid:123456789qwertyuiop::bcf.ng911.test"`
40. Validate 4xx error response for request without 'callId' for 'logEventType': 'CallStateChangeLogEvent'
41. Validate 4xx error response for request with incorrect 'incidentId' parameter (incorrect urn): `"incidentId": "urn:emergency:uid:incidentidd:123456789qwerty:bcf.ng911.test"`
42. Validate 4xx error response for request with incorrect 'incidentId' parameter (string ID below 10 characters): `"incidentId": "urn:emergency:uid:incidentid:123456789:bcf.ng911.test"`
43. Validate 4xx error response for request with incorrect 'incidentId' parameter (string ID exceeded 36 characters): `"incidentId": "urn:emergency:uid:incidentid:123456789qwertyuiop1234567890qwertyui:bcf.ng911.test"`
44. Validate 4xx error response for request with incorrect 'incidentId' parameter (incorrect FQDN): `"incidentId": "urn:emergency:uid:callid:123456789qwertyuiop:bcf.ng911..test"`
45. Validate 4xx error response for request with incorrect 'incidentId' parameter (doubled ':'): `"incidentId": "urn:emergency:uid:callid:123456789qwertyuiop::bcf.ng911.test"`
46. Validate 4xx error response for request without 'incidentId' for 'logEventType': 'CallStateChangeLogEvent'
47. Validate 4xx error response for request with incorrect 'callIdSIP' parameter (not allowed character): `"callIdSIP": "f81d4fae!-7dec-11d0-a765-00a0c91e6bf6@osp.test"`
48. Validate 4xx error response for request with incorrect 'callIdSIP' parameter (empty): `"callIdSIP": ""`
49. Validate 4xx error response for request with incorrect 'callIdSIP' parameter (length exceeded): `"callIdSIP": "f81d4fae-7dec-11d0-a765-00a0c91e6bf6f81d4fae-7dec-11d0-a765-00a0c91e6bf6f81d4fae-7dec-11d0-a765-00a0c91e6bf691e6b124789f@osp.test"`
50. Validate 4xx error response for request with incorrect 'callIdSIP' parameter (doubled '@'): `"callIdSIP": "f81d4fae-7dec-11d0-a765-00a0c91e6bf6f81d4fae-7dec-11d0-a765-00a0c91e6@@osp.test"
51. Validate 4xx error response for request without 'callIdSIP' for 'logEventType': 'CallStateChangeLogEvent'
52. Validate 4xx error response for request with incorrect 'ipAddressPort' parameter (double period): `"ipAddressPort": "192.168.64..15:8080"`
53. Validate 4xx error response for request with incorrect 'ipAddressPort' parameter (port number exceeded): `"ipAddressPort": "192.168.64.15:65536"`
54. Validate 4xx error response for request with `"ipAddressPort": "192.168.64.15:5061"` (send message with SIP INVITE - check Test Preamble steps)
55. Validate 4xx error response for request with incorrect 'extension' parameter (invalid json): `"extension": {"test": "test",}`
56. Validate 4xx error response for request with JWS signed by credentials not traceable to PCA
57. Validate 4xx error response for request with JWS Agent signature different than 'agencyAgentId' or 'elementId'
58. Validate JSON body from 201 Created response for request with correct JWS LogEvent object

#### Stimulus
Send HTTP POST to /LogEvents entrypoint of Logging Service with generated JWS object:

- (TLSv1.2):
  
  `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.2 -X POST https://IF_PS_TS_IP_ADDRESS:PORT/LogEvents -H "Content-Type: application/json" -d GENERATED_JWS_OBJECT`

- (TLSv1.3):
  
  `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.3 -X POST https://IF_PS_TS_IP_ADDRESS:PORT/LogEvents -H "Content-Type: application/json" -d GENERATED_JWS_OBJECT`

- (TCP):
  
  `curl -X POST https://IF_PS_TS_IP_ADDRESS:PORT/LogEvents -H "Content-Type: application/json" -d GENERATED_JWS_OBJECT`

#### Response
* Variations 1, 5-32, 36-58
  Logging Service responds with 4xx error message
* Variations 2-4, 33-35, 59
  Logging Service responds with 201 'LogEvent Successfully Logged' containing:
- JSON body with 'logEventId'
- 'logEventId' should have string value
- 'logEventId' should contain: 'urn:emergency:uid:logid:'
- 'logEventId' should contain unique string 10 to 36 characters long
- 'logEventId' should contain FQDN of Logging Service

Example:

`urn:emergency:uid:logid:0013344556677-231:logger.state.pa.us`

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
* remove created LogEvents
* disconnect interfaces from Test System
* reconnect interfaces back to default

## Post-Test Conditions
### Test System 
* Test tools stopped
* interfaces disconnected from IUT

### Logging Service
* created LogEvent removed
* device connected back to default
* device in normal operating state

## Sequence Diagram
<!--
[![](https://mermaid.ink/img/pako:eNq1UslqwzAU_BXxrpWDd0c6BAot9NAl4FBC8UXYL47aWEolOTQN-fcqTkpCeyzVScvMvBEzO6h1g8AhCIJK1VotZMsrRUgnjdHmunbaWE4WYmWxUgPI4nuPqsYbKVojugP4uB61Q6I3aMgMrSPl1jrsKLnXbStVS0o0G1kjJ8_CSOGkVpZElGRBElOS5EE2PktdCASTydUvibvZbEqmT-XsTPmBOdAuVE6UdD7_k984SL3XJEgyb5z9v984jA7A2w0q_9LXNVq76Fer7UDHhlyRV6sVUOjQdEI2PsndYUYFbokdVsD9thHmrYJK7T1O9E6XW1UDd6ZHCv26Ee47S-BD0BTWQr1ofT5jI30RHo5VGRozYIDv4AN4FOejKGeMFUnI2JgVMYUtcH-bhP4H8ZixMGRRmu8pfA6y6SjO8zwsijxKxkmYFRSM7tvlaeD-CwRgzYA?type=png)](https://mermaid.live/edit#pako:eNq1UslqwzAU_BXxrpWDd0c6BAot9NAl4FBC8UXYL47aWEolOTQN-fcqTkpCeyzVScvMvBEzO6h1g8AhCIJK1VotZMsrRUgnjdHmunbaWE4WYmWxUgPI4nuPqsYbKVojugP4uB61Q6I3aMgMrSPl1jrsKLnXbStVS0o0G1kjJ8_CSOGkVpZElGRBElOS5EE2PktdCASTydUvibvZbEqmT-XsTPmBOdAuVE6UdD7_k984SL3XJEgyb5z9v984jA7A2w0q_9LXNVq76Fer7UDHhlyRV6sVUOjQdEI2PsndYUYFbokdVsD9thHmrYJK7T1O9E6XW1UDd6ZHCv26Ee47S-BD0BTWQr1ofT5jI30RHo5VGRozYIDv4AN4FOejKGeMFUnI2JgVMYUtcH-bhP4H8ZixMGRRmu8pfA6y6SjO8zwsijxKxkmYFRSM7tvlaeD-CwRgzYA)
-->

![image](https://github.com/user-attachments/assets/10b9216d-427d-4b0a-8a06-9a60b85b263f)

## Comments

Version:  010.3f.3.1.10

Date:     20250429

## Footnotes
[^1]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^2]: Wireshark configuration to decrypt TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^3]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518
