# Test Description: TD_PS_005
## Overview
### Summary
Handling HTTP PUT on /Policies entrypoint

### Description
Test covers Policy Store HTTP PUT requests verification and sending response

### References
* Requirements : RQ_PS_019, RQ_PS_029, RQ_PS_032
* Test Case    : TC_PS_005

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

![image](https://github.com/user-attachments/assets/0d876339-c3d4-43f6-bf39-3cfed7edadfe)


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
* Edit JSON file with policy to be stored. Adjust policyOwner to FQDN used in CN of test system certificate (replace 'user@test.example'):

```
Policy_object_example_v010.3f.3.0.X.json
```

* change used policyOwner field values also for in URLs for all test varations (replace in URL TEST_SYSTEM_POLICY_OWNER with CN from Test System certificate decoded for URL params format)

* Generate JWS object (to be used where POLICY_JWS mentioned) with prepared policy (from test_suite directory):

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

* Make a copy of JSON file and adjust for 'OriginationRoutePolicy' policyType:
    - remove policyId
    - change policyType to 'OriginationRoutePolicy'
    - add "policyQueueName": "sip:test@example.com"

* Generate new JWS (to be used where POLICY_ORIGNATIONROUTE_JWS mentioned) using prepared JSON file and send policy using HTTP POST

* For Variations 19-27 generate JWS objects using `Policy_object_example_v010.3f.3.0.X.json` JSON file with changed one of parameters (as mentioned in description of each variation)

* For Variation 28 generate JWS object using `Policy_object_example_v010.3f.3.0.X.json` JSON file and then replace signature part (JWS: {header}.{payload}.{signature}) with f.e.:

```
GciOiJFZERTQSIsI
```

### Test Body

#### Variations
1. Validate 4xx error response for request without "policyOwner"

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyType=OtherRoutePolicy&policyId=test_example_1
  ```
  JWS: POLICY_JWS

2. Validate 4xx error response for request without "policyType"

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyId=test_example_1
  ```
  JWS: POLICY_JWS

3. Validate 4xx error response for request with "policyType": "OtherRoutePolicy" and without "policyId"

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy
  ```
  JWS: POLICY_JWS

4. Validate 4xx error response for request with "policyType": "OriginationRoutePolicy" and without "policyQueueName"

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OriginationRoutePolicy
  ```
  JWS: POLICY_ORIGINATIONROUTE_JWS

5. Validate 4xx error response for request with incorrect 'policyOwner' parameter (special characters not allowed in FQDN):

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=te$t%40example%2Ecom&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40example.com
  ```
  JWS: POLICY_ORIGINATIONROUTE_JWS

6. Validate 4xx error response for request with incorrect 'policyOwner' parameter (missing '@'):

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=testexample%2Ecom&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40example.com
  ```
  JWS: POLICY_ORIGINATIONROUTE_JWS

7. Validate 4xx error response for request with incorrect 'policyOwner' parameter (double '@'):

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=test%40%40example%2Ecom&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40example.com
  ```
  JWS: POLICY_ORIGINATIONROUTE_JWS

8. Validate 4xx error response for request with incorrect 'policyOwner' parameter (leading period):

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=%2Etest%40example%2Ecom&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40example.com
  ```
  JWS: POLICY_ORIGINATIONROUTE_JWS

9. Validate 4xx error response for request with incorrect 'policyOwner' parameter (length exceeded):

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=test%40example%2Ecomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcom&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40example.com
  ```
  JWS: POLICY_ORIGINATIONROUTE_JWS

10. Validate 4xx error response for request with incorrect 'policyType' parameter:

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyType=OtherRoutePolicyy&policyOwner=TEST_SYSTEM_POLICY_OWNER&policyId=test_example_1
  ```
  JWS: POLICY_JWS

11. Validate 4xx error response for request with incorrect "policyQueueName" (send without username)

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OriginationRoutePolicy&policyQueueName=sip%3A%40example%2Ecom%3A5060
  ```
  JWS: POLICY_ORIGINATIONROUTE_JWS

12. Validate 4xx error response for request with incorrect "policyQueueName" (send without domain)

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40%3A5060
  ```
  JWS: POLICY_ORIGINATIONROUTE_JWS

13. Validate 4xx error response for request with incorrect "policyQueueName" (send with not allowed characters)

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40example$%2Ecom%3A5060
  ```
  JWS: POLICY_ORIGINATIONROUTE_JWS

14. Validate 4xx error response for request with incorrect "policyQueueName" (send invalid port)

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40example$%2Ecom%3A65536
  ```
  JWS: POLICY_ORIGINATIONROUTE_JWS

15. Validate 4xx error response for request with incorrect "policyQueueName" (send invalid scheme)

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OriginationRoutePolicy&policyQueueName=zip%3Atest%40example$%2Ecom%3A5060
  ```
  JWS: POLICY_ORIGINATIONROUTE_JWS


16. Validate 201 created response for request with "policyId": "\n":

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=%0A
  ```
  JWS: POLICY_JWS

17. Validate 201 created response for request with "policyId": "'":

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=%27
  ```
  JWS: POLICY_JWS

18. Validate 201 created response for request with "policyId": "(":

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=%28
  ```
  JWS: POLICY_JWS


19. Validate 4xx error response for request with incorrect 'policyExpirationTime' parameter in JWS (incorrect year): `"policyExpirationTime": "21155-08-21T12:58:03.01-05:00"`

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=test_example_1
  ```
  
  JWS: generated in Test Preamble with incorrect parameter in JSON payload

20. Validate 4xx error response for request with incorrect 'policyExpirationTime' parameter in JWS (incorrect month): `"policyExpirationTime": "2115-13-21T12:58:03.01-05:00"`

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=test_example_1
  ```
  
  JWS: generated in Test Preamble with incorrect parameter in JSON payload

21. Validate 4xx error response for request with incorrect 'policyExpirationTime' parameter in JWS (incorrect day): `"policyExpirationTime": "2115-12-32T12:58:03.01-05:00"`

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=test_example_1
  ```
  
  JWS: generated in Test Preamble with incorrect parameter in JSON payload

22. Validate 4xx error response for request with incorrect 'policyExpirationTime' parameter in JWS (incorrect hour): `"policyExpirationTime": "2115-12-21T24:58:03.01-05:00"`

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=test_example_1
  ```
  
  JWS: generated in Test Preamble with incorrect parameter in JSON payload

23. Validate 4xx error response for request with incorrect 'policyExpirationTime' parameter in JWS (incorrect minute): `"policyExpirationTime": "2115-12-21T12:60:03.01-05:00"`

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=test_example_1
  ```
  
  JWS: generated in Test Preamble with incorrect parameter in JSON payload

24. Validate 4xx error response for request with incorrect 'policyExpirationTime' parameter in JWS (incorrect second): `"policyExpirationTime": "2115-12-21T12:58:61.01-05:00"`

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=test_example_1
  ```
  
  JWS: generated in Test Preamble with incorrect parameter in JSON payload

25. Validate 4xx error response for request with incorrect 'policyExpirationTime' parameter in JWS (incorrect time offset): `"policyExpirationTime": "2115-12-21T12:58:03.01-13:00"`

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=test_example_1
  ```
  
  JWS: generated in Test Preamble with incorrect parameter in JSON payload

26. Validate 4xx error response for request with incorrect 'policyExpirationTime' parameter in JWS (incorrect day in February): `"policyExpirationTime": "2115-02-30T12:58:03.01-05:00"`

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=test_example_1
  ```
  
  JWS: generated in Test Preamble with incorrect parameter in JSON payload

27. Validate 4xx error response for request with incorrect 'policyExpirationTime' parameter in JWS (date in the past): `"policyExpirationTime": "2015-02-20T12:58:03.01-05:00"`

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=test_example_1
  ```
  
  JWS: generated in Test Preamble with incorrect parameter in JSON payload

28. Validate 4xx error response for request with incorrect signature (check Test Preamble)

  URL:
  ```
  POLICY_STORE_FQDN_OR_IP:PORT/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=test_example_1
  ```
  
  JWS: generated in Test Preamble with incorrect signature

#### Stimulus

JWS_OBJECT = 'POLICY_JWS' or 'POLICY_ORIGINATIONROUTE_JWS' or 'JWS object generated for variation 19-28'

Send HTTP PUT to /Policies entrypoint of Policy Store:

   - (TLSv1.2):

   `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.2 -X PUT https://URL -H "Content-Type: application/json" -d JWS_OBJECT`
    
   - (TLSv1.3):

   `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.3 -X PUT https://URL -H "Content-Type: application/json" -d JWS_OBJECT`
    
   - (TCP):

   `curl -X PUT https://URL -H "Content-Type: application/json" -d JWS_OBJECT`


#### Response
Variations 1-15, 19-28
IUT responds with HTTP 4XX error message

Variations 16-18
IUT responds with HTTP 201 Created message

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
[![](https://mermaid.ink/img/pako:eNq1klFrgzAUhf9KuK_TYjTamIfC6B72slGoG2X4EvTWhtWki3HMlf73qe267rXQPAXynXvODWcPhSkRBPi-n-vC6LWqRK4JqZW1xt4XzthGkLXcNpjrEWrwo0Vd4IOSlZX1ABPybBwS84mWZNg4suwah7VHFmario4s-ykoyKu0SjplNKE-jY_C4VxI_Nns7r_oMcsWZPGS_eGX7wN_IT_hbLW6LlbiU37DXGFAydyidFhely_1Q37bfwMParS1VGVfiv0gzsFtsMYcRH8tpX3PIdeHnpOtM8tOFyCcbdGDdlf2m51qAWLsjAc7qd-MqX8hLFXv_3Qs3di9EQGxhy8QUzoJ4pBHLGBhEMacedCBoEkyiRPGY8ZoxOMwOXjwPc4MJtMwiRhPUk6jlKbB1ANr2mpztq_ssMnR26Iu0c5Nqx2IODr8APTC73E?type=png)](https://mermaid.live/edit#pako:eNq1klFrgzAUhf9KuK_TYjTamIfC6B72slGoG2X4EvTWhtWki3HMlf73qe267rXQPAXynXvODWcPhSkRBPi-n-vC6LWqRK4JqZW1xt4XzthGkLXcNpjrEWrwo0Vd4IOSlZX1ABPybBwS84mWZNg4suwah7VHFmario4s-ykoyKu0SjplNKE-jY_C4VxI_Nns7r_oMcsWZPGS_eGX7wN_IT_hbLW6LlbiU37DXGFAydyidFhely_1Q37bfwMParS1VGVfiv0gzsFtsMYcRH8tpX3PIdeHnpOtM8tOFyCcbdGDdlf2m51qAWLsjAc7qd-MqX8hLFXv_3Qs3di9EQGxhy8QUzoJ4pBHLGBhEMacedCBoEkyiRPGY8ZoxOMwOXjwPc4MJtMwiRhPUk6jlKbB1ANr2mpztq_ssMnR26Iu0c5Nqx2IODr8APTC73E)
-->

![image](https://github.com/user-attachments/assets/659b44d1-6364-45e8-9b44-e4988c20ccf6)



## Comments

Version:  010.3f.3.2.10

Date:     20250512

## Footnotes
[^1]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^2]: Wireshark configuration to decrypt TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^3]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518
