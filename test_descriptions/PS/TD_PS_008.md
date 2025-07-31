# Test Description: TD_PS_008
## Overview
### Summary
Storing policies byte-for-byte unaltered

### Description
Test covers if stored policies are byte-for-byte unaltered

### References
* Requirements : RQ_PS_039
* Test Case    : TC_PS_008

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

![image](https://github.com/user-attachments/assets/9af7e487-6909-40f5-9acb-e367d4ac17c1)


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

#### Variations
1. Policy with large ruleset - file Policy_object_with_large_ruleset_v010.3f.3.0.X.json
2. Policy with extra whitespaces - file Policy_object_with_extra_whitespaces_v010.3f.3.0.X.json
3. Policy with Windows-type line endings - file Policy_object_with_Windows_type_line_endings_v010.3f.3.0.X.json
4. Policy with Unix-type line endings - file Policy_object_with_Linux_type_line_endings_v010.3f.3.0.X.json

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
* store policies for all variations by sending HTTP POST, f.e.:

   - (TLSv1.2):

    `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.2 -X POST https://IF_PS_TS_IP_ADDRESS:PORT/Policies -H "Content-Type: application/json" -d GENERATED_JWS_OBJECT`
    
   - (TLSv1.3):

   `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.3 -X POST https://IF_PS_TS_IP_ADDRESS:PORT/Policies -H "Content-Type: application/json" -d GENERATED_JWS_OBJECT`
    
   - (TCP):

   `curl -X POST https://IF_PS_TS_IP_ADDRESS:PORT/Policies -H "Content-Type: application/json" -d GENERATED_JWS_OBJECT`


### Test Body

#### Variations
1. Policy with large ruleset - file Policy_object_with_large_ruleset_v010.3f.3.0.X.json
2. Policy with extra whitespaces - file Policy_object_with_extra_whitespaces_v010.3f.3.0.X.json
3. Policy with Windows-type line endings - file Policy_object_with_Windows_type_line_endings_v010.3f.3.0.X.json
4. Policy with Unix-type line endings - file Policy_object_with_Linux_type_line_endings_v010.3f.3.0.X.json

#### Stimulus

Send HTTP GET to /Policies entrypoint of Policy Store, add to URL policyOwner field matching the one use while storing, f.e.:

```
IF_PS_TS_IP_ADDRESS:PORT/Policies?policyOwner=tester@ng911.test.system.com
```

   - (TLSv1.2):

   `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.2 -X GET https://IF_PS_TS_IP_ADDRESS:PORT/Policies?policyOwner=`
    
   - (TLSv1.3):

   `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.3 -X POST https://IF_PS_TS_IP_ADDRESS:PORT/Policies?policyOwner=`
    
   - (TCP):

   `curl -X POST http://IF_PS_TS_IP_ADDRESS:PORT/Policies?policyOwner=`


#### Response
Verify if JWS objects are unaltered after fetching from Policy Store. For additional checking JWS objects can be decrypted, f.e.:

```
python3 -m main decrypt_jws JWS_OBJECT --key test_system.key
```

VERDICT:
* PASSED - if JWS objects fetched from Policy Store were unaltered
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
[![](https://mermaid.ink/img/pako:eNqdkV9LwzAUxb9KuE_K2pG2M13yMFAURVALLQiSl9jebcU1mWkqq2Pf3a6dbD7OPOXPOb97wtlCbgoEAb7vS50bPS8XQmpCqtJaY69zZ2wtyFytapS6F9X42aDO8bZUC6uqvXhYz8YhMV9oSYa1I2lbO6w8kphVmbck7UgohqfEoqreV0guJpvLI-DE5s9mo7_GhyxLSPKSZmREHl_To-tUtredUA6ukNL_pLwxRXt2wvu77Mxow3_AgwptpcqiK2O7R0hwS6xQgui2hbIfEqTedTrVOJO2OgfhbIMeNOtCud86QPRdebBW-s2Y4xmLsovxNLTdl95rQGxhAyII2ThgnPM4opxPeRx60ILobiMa0iCcck4pDyZs58F3j52MQ8YYjWMWRNOIXsUeWNMsloeBux-0pbis?type=png)](https://mermaid.live/edit#pako:eNqdkV9LwzAUxb9KuE_K2pG2M13yMFAURVALLQiSl9jebcU1mWkqq2Pf3a6dbD7OPOXPOb97wtlCbgoEAb7vS50bPS8XQmpCqtJaY69zZ2wtyFytapS6F9X42aDO8bZUC6uqvXhYz8YhMV9oSYa1I2lbO6w8kphVmbck7UgohqfEoqreV0guJpvLI-DE5s9mo7_GhyxLSPKSZmREHl_To-tUtredUA6ukNL_pLwxRXt2wvu77Mxow3_AgwptpcqiK2O7R0hwS6xQgui2hbIfEqTedTrVOJO2OgfhbIMeNOtCud86QPRdebBW-s2Y4xmLsovxNLTdl95rQGxhAyII2ThgnPM4opxPeRx60ILobiMa0iCcck4pDyZs58F3j52MQ8YYjWMWRNOIXsUeWNMsloeBux-0pbis)
-->

![image](https://github.com/user-attachments/assets/ba6a9cd7-d3ae-41a0-87ac-cb276c838cb2)


## Comments

Version:  010.3f.3.0.2

Date:     20250428

## Footnotes
[^1]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^2]: Wireshark configuration to decrypt TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^3]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518
