# Test Description: TD_ALL_001
## Overview
### Summary
Discrepancy Report receiving by all Functional Elements

### Description
This test checks receiving of Discrepancy Reports by all Functional Elements:
- receiving and responding with confirmation
- responding with error message if report message is incorrect

### HTTP transport types
Test can be performed with 2 different HTTP transport types. Steps describing actions for specific one are marked as following:
- (TLS transport) - used by default (HTTPS) inside ESInet on production environment
- (TCP transport) - used in lab for testing purposes only if default TLS is not possible

### References
* Requirements : O-BCF_9
* Test Purpose : 
* Test Case    : 

## Configuration
### Implementation Under Test Interface Connections
<!-- Identify each of the FEs that are part of the configuration and how they are connected -->
* Functional Element
  * IF_FE_TS - connected to Test System IF_TS_FE
* Test System
  * IF_TS_FE - connected to Functional Element IF_FE_TS

### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* Test System
  * IF_TS_FE - Active
* Functional Element
  * IF_O-BCF_OSP - Active


### Connectivity Diagram
[![](https://mermaid.ink/img/pako:eNpdkE0KwkAMha8yZF0vUMSVLQi6sV3JgMRO-oOdmTLNICK9u9EKVrNKXvLxwntA5Q1BCnXvb1WLgdX-qJ2S2uXnsjjn2Xq12kifZzLOmzFemoBDq0oaWRX3kcnOmyU3K-TMH5RHV3HnHfYq68mS4x924SMsJGApWOyM_Ph4yRq4FUpDKq3BcNWg3SR3GNkXd1dByiFSAnEwyLTtUGwtpDX2o6gDupP335lMxz4c5hDeWSQQfGzaz8X0BDspXLE?type=png)](https://mermaid.live/edit#pako:eNpdkE0KwkAMha8yZF0vUMSVLQi6sV3JgMRO-oOdmTLNICK9u9EKVrNKXvLxwntA5Q1BCnXvb1WLgdX-qJ2S2uXnsjjn2Xq12kifZzLOmzFemoBDq0oaWRX3kcnOmyU3K-TMH5RHV3HnHfYq68mS4x924SMsJGApWOyM_Ph4yRq4FUpDKq3BcNWg3SR3GNkXd1dByiFSAnEwyLTtUGwtpDX2o6gDupP335lMxz4c5hDeWSQQfGzaz8X0BDspXLE)


## Pre-Test Conditions

### Test System
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active

### Functional Element
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Default configuration is loaded
* Device is active
* Device is in normal operating state


## Test Sequence
### Test Preamble
#### Test System
* Install netcat tool[^1]
* Install Wireshark[^2]
* (TLS transport) Configure Wireshark to decode HTTPS packets[^3]
* Copy following HTTP messages to local storage:
  > HTTP_Discrepancy_Report/HTTP_DR_Policy_Store_Incorrect_Unspecified_Error
  > HTTP_Discrepancy_Report/HTTP_DR_Policy_Store_Incorrect_Unknown_Service
  > HTTP_Discrepancy_Report/HTTP_DR_Policy_Store_Incorrect_Unauthorized_Reporter
  > HTTP_Discrepancy_Report/HTTP_DR_Policy_Store
  > HTTP_Discrepancy_Report/HTTP_DR_BCF_Incorrect_Unspecified_Error
  > HTTP_Discrepancy_Report/HTTP_DR_BCF_Incorrect_Unknown_Service
  > HTTP_Discrepancy_Report/HTTP_DR_BCF_Incorrect_Unauthorized_Reporter
  > HTTP_Discrepancy_Report/HTTP_DR_BCF
* (TLS transport) Copy to local storage certificate and private key files used to decrypt HTTPS packets within ESInet:
  > cacert.pem
  > cakey.pem
* Using Wireshark on Test System start packet tracing on IF_TS_FE interface - use following filter:

    (TCP transport)
    > ip.addr == IF_TS_FE_IP_ADDRESS and http
    
    (TLS transport)
    > ip.addr == IF_TS_FE_IP_ADDRESS and tls

### Test Body

#### Variations
1. HTTP_Discrepancy_Report/HTTP_DR_Policy_Store_Incorrect_Unspecified_Error
2. HTTP_Discrepancy_Report/HTTP_DR_Policy_Store_Incorrect_Unknown_Service
3. HTTP_Discrepancy_Report/HTTP_DR_Policy_Store_Incorrect_Unauthorized_Reporter
4. HTTP_Discrepancy_Report/HTTP_DR_Policy_Store
5. HTTP_Discrepancy_Report/HTTP_DR_BCF_Incorrect_Unspecified_Error
6. HTTP_Discrepancy_Report/HTTP_DR_BCF_Incorrect_Unknown_Service
7. HTTP_Discrepancy_Report/HTTP_DR_BCF_Incorrect_Unauthorized_Reporter
8. HTTP_Discrepancy_Report/HTTP_DR_BCF

#### Stimulus

From Test System send HTTP message for tested variation and stop NC (ctrl+C in the console), example:

  (TCP transport)
  > cat Scenarios/HTTP_Discrepancy_Report/HTTP_DR_FE_CLIENT_Incorrect_Unspecified_Error | nc IF_TS_FE_IP_ADDRESS 80

  (TLS transport)
  > cat Scenarios/HTTP_Discrepancy_Report/HTTP_DR_FE_CLIENT_Incorrect_Unspecified_Error | openssl s_client -connect IF_TS_FE_IP_ADDRESS:443 -CAfile cacert.pem -ign_eof

#### Response
Variations 1,5
* verify if FE responds with correct error message:
  > 454 Unspecified Error

Variations 2,6
* verify if FE responds with correct error message:
  > 470 Unknown Service/Database

Variations 3,7
* verify if FE responds with correct error message:
  > 471 Unauthorized Reporter

Variations 4,8
* verify if FE responds with correct error message:
  > 201 Report successfully created
* verify if message includes following required fields in the body:
    ```
    "respondingAgencyName": "FE_FQDN"
    "respondingContactJcard": "FE_jCard"
    ```
* (OPTIONAL) verify if message includes following optional fields in the body:
    ```
    "respondingAgentId": "FE_USER_ID"
    "responseEstimatedReturnTime": "ESTIMATED_RESPONSE_TIMESTAMP"
    "responseComments": "TEXT_COMMENT"
    ```

VERDICT:
* PASSED - if all mandatory checks passed for variation
* FAILED - all other cases


### Test Postamble
#### Test System
* stop all Netcat processes (if still running)
* archive all logs generated
* remove all HTTP message files
* disconnect interface from Functional Element

#### Functional Element
* disconnect interface from Test System
* reconnect interfaces back to default


## Post-Test Conditions
### Test System
* Test tools stopped
* interfaces disconnected from Functional Element

### Functional Element
* device connected back to default
* device in normal operating state

## Sequence Diagram
[![](https://mermaid.ink/img/pako:eNqtk19LwzAUxb_KJU-KLU6ZDPIwENfhQEW2-iKBEpPbLaxNav4oc-y7m3aFCb443FsC5_7OyeVkS4SRSChJ05RpYXSplpRpgFpZa-yt8MY6CiWvHDLdiRy-B9QCJ4ovLa9bMUCOzsNi4zzW6Xh8MQ1aeGU0ryCrsEbtKdzn-XMxmRdn06y4e5hlT_l5MYuW1qLwxYt2DQpVKpRF1lrvub9BaeSnP-woDG-GkMIPAPSAk0Vba_OpiwXaDyXwiGCjQResG4d-_HLCPX_j7TpPlo8HvzJWfcXdzbEx1uMx6xtddSkPEDhA_hPx7xGuB22EvSu4IAQ6V4aq2oCwyD1KpklCarQ1VzKWdduiGfGryGOExqPkds0I07uoiw8xi40WhHobMCGhkZHR15XQrssJabh-NeZwR6li1x_3v6H7FAmxJixXvWL3DYegFS4?type=png)](https://mermaid.live/edit#pako:eNqtk19LwzAUxb_KJU-KLU6ZDPIwENfhQEW2-iKBEpPbLaxNav4oc-y7m3aFCb443FsC5_7OyeVkS4SRSChJ05RpYXSplpRpgFpZa-yt8MY6CiWvHDLdiRy-B9QCJ4ovLa9bMUCOzsNi4zzW6Xh8MQ1aeGU0ryCrsEbtKdzn-XMxmRdn06y4e5hlT_l5MYuW1qLwxYt2DQpVKpRF1lrvub9BaeSnP-woDG-GkMIPAPSAk0Vba_OpiwXaDyXwiGCjQResG4d-_HLCPX_j7TpPlo8HvzJWfcXdzbEx1uMx6xtddSkPEDhA_hPx7xGuB22EvSu4IAQ6V4aq2oCwyD1KpklCarQ1VzKWdduiGfGryGOExqPkds0I07uoiw8xi40WhHobMCGhkZHR15XQrssJabh-NeZwR6li1x_3v6H7FAmxJixXvWL3DYegFS4)


## Comments

Version:  010.3d.2.1.6

Date:     2024.09.26


## Footnotes
[^1]: Netcat for Linux https://linux.die.net/man/1/nc
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt SIP over TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
