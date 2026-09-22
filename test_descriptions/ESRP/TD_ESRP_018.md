# Test Description: TD_ESRP_018

<!-- MULTIPLE TDs already exist - review & consolidate
Existing TD(s) - TD_ECRF-LVF_010 (from RQ_ECRF-LVF_065 / ECRF-LVF); TD_ESRP_018 (from RQ_ESRP_122 / ESRP) 
TD_ECRF-LVF_010 (from RQ_ECRF-LVF_064 / ECRF-LVF); TD_ESRP_018 (from RQ_ESRP_121 / ESRP) -->

## Overview
### Summary
Logging of ServiceStateChangeLogEvent on ESRP service state change

### Description
Verify that ESRP logs a valid ServiceStateChangeLogEvent when reporting service state changes(including Security Posture).

### HTTP transport types
Test can be performed with 2 different HTTP transport types. Steps describing actions for specific one are marked as following:
- (TLS transport) - used by default inside ESInet on production environment
- (TCP transport) - used as a fallback if use of TLS is not possible

### References
* Requirements : RQ_ESRP_121, RQ_ESRP_122
* Test Case    : TC_ESRP_018

### Requirements
IXIT config file for ESRP

## Configuration
### Implementation Under Test Interface Connections
<!-- Identify each of the FEs that are part of the configuration and how they are connected -->
* Test System BCF
  * IF_BCF_ESRP - connected to IF_ESRP_BCF
* ESRP
  * IF_ESRP_BCF - connected to IF_BCF_ESRP
  * IF_ESRP_LOG - connected to IF_LOG_ESRP
* Test System Logging Service
  * IF_LOG_ESRP - connected to IF_ESRP_LOG


### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* Test System BCF
  * IF_BCF_ESRP - Active
* ESRP
  * IF_ESRP_BCF - Active
  * IF_ESRP_LOG - Active
* Test System Logging Service
  * IF_LOG_ESRP - Active

### Connectivity Diagram
<!--
https://mermaid.live/edit#pako:eNp1Ul1PwjAU_SvNfR6ErftsjA-iGJIZDePJLCF1u2yLrCVdpyLhv9ttgkBin27P6flo2j1kMkdgsN7Iz6zkSpN4kQpi1ny2upvOVg_J4uVmNLqdD2OHnfgeiJ8ff3kz9dDAN-1bofi2JEtsNEl2jcaanNRXCQOIIr_S_nHnkdcuxx7_uZw3iGVRVKIgCaqPKsMLn8sL9D5gQaGqHJhWLVpQo6p5t4V9dygFXWKNKTAz5ly9p5CKg9FsuXiVsj7KlGyLEtiabxqza7c513hfcdOuPqHK5KGaylZoYIE36U2A7eELGHXHtm-H1LFd13Ejz7dgB8x3xi4NI9ef2JTSMKAHC7771Mk4DCMDeZ4TeXZoO4EFvNUy2Yns2AnzSkv1NDx__wsOP5winDk
-->

![image](../_assets/ESRP/TD_ESRP_018_Connectivity_Diagram.png)


## Pre-Test Conditions

### Test System BCF/Test System Logging Service
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* No active calls
* (TLS transport) Test System has it's own certificate signed by PCA

### ESRP
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Default configuration is loaded
* IUT is configured with planned changes
* IUT is initialized with steps from IXIT config file
* IUT is active
* IUT is in normal operating state(serviceState: Normal)
* IUT is provisioned with policy allowing ServiceState subscriptions from Test System ESRP
* Optionally, if Security Posture is supported by the IUT, the "newSecurityPosture" field shall contain one of the following values `Green`, `Yellow`, `Orange`, `Red`.

## Test Sequence

### Test Preamble

#### Test System BCF
* Install SIPp by following steps from documentation[^1]
* Copy following XML scenario files to local storage:
  ```
  SIP_SUBSCRIBE_ServiceState.xml
  ```
* Install Wireshark[^2]
* (TLS transport) Copy to local storage PCA-signed TLS certificate and private key files:
  ```
  PCA-cacert.pem
  PCA-cakey.pem
  ```
* (TLS transport) Copy to local storage TLS certificate and private key files used by ESRP:
  ```
  ESRP-cacert.pem
  ESRP-cakey.pem
  ```
* (TLS transport) Configure Wireshark to decode HTTP over TLS packets from Test System ESRP as well[^3]
* Using Wireshark on Test System BCF start packet tracing on IF_BCF_ESRP interface - run following filter:
  * (TLS transport)
    >   ip.addr == IF_BCF_ESRP_IP_ADDRESS and tls
  * (TCP transport)
    >   ip.addr == IF_BCF_ESRP_IP_ADDRESS and sip
* On Test System BCF start subscription for ServiceState - run SIPp tool with following command:
   * (TCP transport)
     > sudo sipp -t t1 -sf SIP_SUBSCRIBE_ServiceState.xml -i IF_BCF_ESRP_IP_ADDRESS:5060 IF_ESRP_BCF_IP_ADDRESS:5060 -timeout 10 -max_recv_loops 1
   * (TLS transport)
     > sudo sipp -t l1 -tls_cert PCA-cacert.pem -tls_key PCA-cakey.pem -sf SIP_SUBSCRIBE_ServiceState.xml -i IF_BCF_ESRP_IP_ADDRESS:5061 IF_ESRP_BCF_IP_ADDRESS:5061 -timeout 10 -max_recv_loops 1
* Verify if ESRP sends SIP NOTIFY messages with ServiceState="Normal" status

#### Test System Logging Service
* Install Wireshark[^2]
* (TLS v1.2) Configure Wireshark to decode HTTP over TLS, use tests system and ESRP certificate keys [^3]
* (TLS v1.3) Configure logging of session keys and configure Wireshark to decode HTTP over TLS [^4]
* Using Wireshark on 'Test System' start packet tracing on IF_LOG_ESRP interface - run following filter:
   * (TLS)
     > ip.addr == IF_LOG_ESRP_IP_ADDRESS and tls
   * (TCP)
     > ip.addr == IF_LOG_ESRP_IP_ADDRESS and http
* The Logging Service must be configured to accept and process HTTP POST requests. To verify this manually, you can simulate a listening HTTP endpoint on port 8080 using command in the terminal:
    * Step 1 - Prepare logEventId and JSON body
      ```
      ID="urn:emergency:uid:logid:$(date +%s%N):logger.state.pa.us"
      BODY="{\"logEventId\":\"$ID\"}"
      ```
    * Step 2 - Run server:
      * (TLS)
      ```
      python3 http_entry.py --ip IF_LOG_ESRP --port 443 --role RECEIVER --path /LogEvents --method POST \
      --body "$BODY" --content_type application/json --response_code 201 --server_cert /tmp/cert.crt --server_key /tmp/cert.key
      ```
      * (TCP)
      ```
      python3 http_entry.py --ip IF_LOG_ESRP --port 8080 --role RECEIVER --path /LogEvents --method POST \
      --body "$BODY" --content_type application/json --response_code 201
      ```
    * Step 3 - In another terminal, send a POST request to verify it is working:
      * (TLS)
      ```
      curl -k -X POST http://localhost:8080 -d '{"log":"test"}'
      ```   
      * (TCP)
      ```
      curl -X POST http://localhost:8080 -d '{"log":"test"}'


### Test Body
### Stimulus
#### Variation 1
Trigger a Security Posture change on ESRP to "Orange"
#### Variation 2
Trigger a ServiceState change on ESRP to "Down"

### Response
**Variation 1** (Security Posture change on ESRP to "Orange")

Using traced packets on Wireshark on IF_LOG_ESRP interface verify:
* If ESRP sends an HTTP POST to the Test System Logging Service with a JWS body containing a JSON payload with a LogEvent:
  * "logEventType": "ServiceStateChangeLogEvent"
  * "timestamp" with correct date-time format (e.g. 2020-03-10T11:00:01-05:00)
  * "elementId" which has value with FQDN of ESRP
  * "agencyId" which has value with FQDN of an agency
  * "direction" which has value: `outgoing` or `incoming`
  * "newState" with the new serviceState value - `Normal`
  * “affectedServiceIdentifier” with the FQDN of the ESRP service whose state changed
  * “newSecurityPosture”  with one of the following values `Orange`
  * (optional) "clientAssignedIdentifier" field with string value
  * (optional) "agencyAgentId" field with string value
  * (optional) "agencyPositionId" field with string value
  * (optional) "extension" field with string value


**Variation 2** (ServiceState change on ESRP to "Down")

Using traced packets on Wireshark on IF_LOG_ESRP interface verify:
* If ESRP sends an HTTP POST to the Test System Logging Service with a JWS body containing a JSON payload with a LogEvent:
  * "logEventType": "ServiceStateChangeLogEvent"
  * "timestamp" with correct date-time format (e.g. 2020-03-10T11:00:01-05:00)
  * "elementId" which has value with FQDN of ESRP
  * "agencyId" which has value with FQDN of an agency
  * "direction" which has value: `outgoing` or `incoming`
  * "newState" with the new serviceState value - `Down`
  * “affectedServiceIdentifier” with the FQDN of the ESRP service whose state changed
  * (optional) “newSecurityPosture”  with one of the following values `Green`, `Yellow`, `Orange`, `Red`
  * (optional) "clientAssignedIdentifier" field with string value
  * (optional) "agencyAgentId" field with string value
  * (optional) "agencyPositionId" field with string value
  * (optional) "extension" field with string value


VERDICT:
* PASSED - if all checks passed
* FAILED - all other cases

### Test Postamble
#### Test System BCF/Test System Logging Service
* (TCP transport) stop all Netcat processes (if still running)
* archive all logs generated
* stop Wireshark (if still running)
* remove all HTTP scenarios
* disconnect interfaces from ESRP
* (TLS transport) remove certificates

#### ESRP
* reconnect interfaces back to default
* restore previous configuration

## Post-Test Conditions 
### Test System BCF/Test System Logging Service
* Test tools stopped
* interfaces disconnected from ESRP

### ESRP
* device connected back to default
* device in normal operating state


## Sequence Diagram
<!--
https://mermaid.live/edit#pako:eNq1VNtu2kAQ_ZXRPhHJUF8wl1WFVAhJURNAsVOplaVqaw_GKt6l6zWpi3jtB_QT-yVd2ziiIXmp2jd7z5xzZo49uyehiJBQ0m63Ax4KvkpiGnCANJFSyDehEjKjsGKbDANeFWX4NUce4mXCYsnSgG-ZVEmYbBlX4HufxpMrYBn4mCnwikxhCvroz7LZvV_WTL275Rn_ZnH9lH8j4jjhMXgod0moG6lt2qORFqLgzZbg3Y-9yd1sPIXWdIdcUcAUZawbLdpHmqeYwouAa45m1hI12TZNWLx7Dpkv_NnVh9ef5ah1qkJhLmTKNkaJeBjmMlEFLEWmcqnBa4nIL55rs3GaC4Ugdiihgt4zmTCVCA5WqXjLeM428FQYwjXjMeqKV6MWduJObQS_fvyEhSyh0-l0jhTe-v4SlgvPPxthUmnpZKu4SjggHB8az6NlQGhAau2A1BNp3WaiSt02LWhkwMvDELNslW82RfXZMHo5VmidR_c4x19kZ59kl5UzngdWf7YqsUvxwP9BXiVWpVTq_Z-MTv-7Y9cvpUMMEsskIlTJHA2iVyBl5SvZl0sdELXWa6Hb1Y8Rk18CEvCD5ujd-yhE2tCkyOM1odXWGyTfRtr6uO6PpxJ5hHIicq4ItZ1Kg9A9-UZoz-n0LMfsd3vusGt3batrkEIfDzvOwHZd03WGA8txDwb5XpmanUHPtXtWf-hYjub0-gZhuRJewcOmJYwSfRXd1pdVdWcdfgNsDYwq
-->

![image](../_assets/ESRP/TD_ESRP_018_Sequence_Diagram.png)


## Comments

Version:  010.3d.5.0.0

Date:     20260703


## Footnotes
[^1]: SIPp - tool for SIP packet simulations. Official documentation: https://sipp.sourceforge.net/doc/reference.html#Getting+SIPp
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt SIP over TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^4]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518
