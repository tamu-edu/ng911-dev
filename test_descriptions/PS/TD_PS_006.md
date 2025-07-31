# Test Description: TD_PS_006
## Overview
### Summary
Handling HTTP DELETE on /Policies entrypoint

### Description
Test covers Policy Store HTTP DELETE requests verification and sending response

### References
* Requirements : RQ_PS_021
* Test Case    : TC_PS_006

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

![image](https://github.com/user-attachments/assets/1f423edc-d8f3-4867-a735-5b01b82333b2)


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
* Device is active
* IUT is initialized with steps from IXIT config file
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
* Edit JSON file with policy to be stored. Adjust policyOwner to FQDN used in CN of test system certificate:

```
Policy_object_example_v010.3f.3.0.X.json
```

* Generate JWS object with prepared policy (from test_suite directory):

```
python3 -m main generate_jws Policy_object_example_v010.3f.3.0.X.json --cert test_system.crt --key test_system.key
```

* Send HTTP POST to store generated policy:

    - (TLSv1.2):
  
    `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.2 -X POST https://IF_PS_TS_IP_ADDRESS:PORT/Policies -H "Content-Type: application/json" -d JWS_OBJECT`

    - (TLSv1.3):
  
    `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.3 -X POST https://IF_PS_TS_IP_ADDRESS:PORT/Policies -H "Content-Type: application/json" -d JWS_OBJECT`

    - (TCP):
  
    `curl -X POST https://IF_PS_TS_IP_ADDRESS:PORT/Policies -H "Content-Type: application/json" -d JWS_OBJECT`

* For variation 16 use adjusted `Policy_object_example_v010.3f.3.0.X.json` file, add `"policyId": "\n"` parameter, then generate JWS and send in HTTP POST

* For variation 17 use adjusted `Policy_object_example_v010.3f.3.0.X.json` file, add `"policyId": "'"` parameter, then generate JWS and send in HTTP POST

* For variation 18 use adjusted `Policy_object_example_v010.3f.3.0.X.json` file, add `"policyId": "("` parameter, then generate JWS and send in HTTP POST

### Test Body

#### Variations
1. Validate 4xx error response for request without "policyOwner"
URL:
```
POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyType=OtherRoutePolicy&policyId=test_example_1
```

2. Validate 4xx error response for request without "policyType"
URL:
```
POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyId=test_example_1
```

3. Validate 4xx error response for request with "policyType": "OtherRoutePolicy" and without "policyId"
URL:
```
POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy
```
   
4. Validate 4xx error response for request with "policyType": "OriginationRoutePolicy" and without "policyQueueName"
URL:
```
POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OriginationRoutePolicy
```
5. Validate 4xx error response for request with incorrect 'policyOwner' parameter (special characters not allowed in FQDN):
URL:
```
POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=te$t%40example%2Ecom&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40example.com
```

6. Validate 4xx error response for request with incorrect 'policyOwner' parameter (missing '@'):
URL:
```
POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=testexample%2Ecom&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40example.com
```

7. Validate 4xx error response for request with incorrect 'policyOwner' parameter (double '@'):
URL:
```
POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=test%40%40example%2Ecom&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40example.com
```

8. Validate 4xx error response for request with incorrect 'policyOwner' parameter (leading period):
URL:
```
POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=%2Etest%40example%2Ecom&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40example.com
```

9. Validate 4xx error response for request with incorrect 'policyOwner' parameter (length exceeded):
URL:
```
POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=test%40example%2Ecomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcom&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40example.com
```

10. Validate 4xx error response for request with incorrect 'policyType' parameter:
URL:
```
POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyType=OtherRoutePolicyy&policyOwner=TEST_SYSTEM_POLICY_OWNER&policyId=test_example_1
```

11. Validate 4xx error response for request with incorrect "policyQueueName" (send without username), URL:
URL:
```
POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OriginationRoutePolicy&policyQueueName=sip%3A%40example%2Ecom%3A5060
```

12. Validate 4xx error response for request with incorrect "policyQueueName" (send without domain), URL:
URL:
```
POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40%3A5060
```

13. Validate 4xx error response for request with incorrect "policyQueueName" (send with not allowed characters), URL:
URL:
```
POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40example$%2Ecom%3A5060
```

14. Validate 4xx error response for request with incorrect "policyQueueName" (send invalid port), URL:
URL:
```
POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40example$%2Ecom%3A65536
```

15. Validate 4xx error response for request with incorrect "policyQueueName" (send invalid scheme), URL:
URL:
```
POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OriginationRoutePolicy&policyQueueName=zip%3Atest%40example$%2Ecom%3A5060
```

16. Validate 200 Policy Successfully Deleted response for request with "policyId": "\n":

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=%0A
  ```
  JWS: POLICY_JWS

17. Validate 200 Policy Successfully Deleted response for request with "policyId": "'":

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=%27
  ```
  JWS: POLICY_JWS

18. Validate 200 Policy Successfully Deleted response for request with "policyId": "(":

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=%28
  ```
  JWS: POLICY_JWS


#### Stimulus

Send HTTP DELETE to /Policies entrypoint of Policy Store:

   - (TLSv1.2):

    `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.2 -X DELETE https://URL`
    
   - (TLSv1.3):

   `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.3 -X DELETE https://URL`
    
   - (TCP):

   `curl -X DELETE http://URL`


#### Response

Variation 1-15
IUT responds with HTTP 4XX error message

Variation 16-18
IUT responds with HTTP 200 Policy Successfully Deleted

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
* delete stored policy
* disconnect interfaces from Test System
* reconnect interfaces back to default

## Post-Test Conditions
### Test System 
* Test tools stopped
* interfaces disconnected from IUT

### Policy Store
* all stored policies removed
* device connected back to default
* device in normal operating state

## Sequence Diagram
<!--
[![](https://mermaid.ink/img/pako:eNq1kU1Lw0AQhv_KMleTku9u91AQW_CgUmiQIrksm2kaTHbrfoix9L-bpLbWq-Ce9vA878zwHkCoEoGB7_uFFEpu64oVkpC21lrpW2GVNoxseWOwkCNk8M2hFLioeaV5O8CEPCmLRL2jJjkaS9adsdh6ZKWaWnRk3acgI89c19zWShoS-mF6Mod35fjz-c1v6z7PV2SxfFjmyx_jGhmUq4RvI9ls_rha5of0f3eLguBCOSHQmK1rmo4ssEGLJXjQom55XfbFHIbgAuwOWyyA9d-S69cCCnnsOe6sWndSALPaoQduX3J7rgbY2JsHey5flGrPEJZ1v9vjqfix_xEBdoAPYNNwEqQRjZMgiYIopYkHHbAwyyZpltA0ScKYplF29OBzzAwm0yiLE5rNaBjPwlkw9UArV-0u4ys9XHKarVGWqO-Uk7YPpfT4BeY6yjQ?type=png)](https://mermaid.live/edit#pako:eNq1kU1Lw0AQhv_KMleTku9u91AQW_CgUmiQIrksm2kaTHbrfoix9L-bpLbWq-Ce9vA878zwHkCoEoGB7_uFFEpu64oVkpC21lrpW2GVNoxseWOwkCNk8M2hFLioeaV5O8CEPCmLRL2jJjkaS9adsdh6ZKWaWnRk3acgI89c19zWShoS-mF6Mod35fjz-c1v6z7PV2SxfFjmyx_jGhmUq4RvI9ls_rha5of0f3eLguBCOSHQmK1rmo4ssEGLJXjQom55XfbFHIbgAuwOWyyA9d-S69cCCnnsOe6sWndSALPaoQduX3J7rgbY2JsHey5flGrPEJZ1v9vjqfix_xEBdoAPYNNwEqQRjZMgiYIopYkHHbAwyyZpltA0ScKYplF29OBzzAwm0yiLE5rNaBjPwlkw9UArV-0u4ys9XHKarVGWqO-Uk7YPpfT4BeY6yjQ)
-->

![image](https://github.com/user-attachments/assets/3b738d19-14c6-4391-874f-72ae7f62e421)


## Comments

Version:  010.3f.3.1.5

Date:     20250507

## Footnotes
[^1]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^2]: Wireshark configuration to decrypt TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^3]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518
