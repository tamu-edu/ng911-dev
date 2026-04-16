# Test Description: TD_BRIDGE_004
## Overview
### Summary
Logging the call status

### Description
Test covers logging of CallStartLogEvent, CallEndLogEvent and CallSignallingMessageLogEvent

### References
* Requirements : RQ_BRG_092, RQ_BRG_100, RQ_BRG_101, RQ_BRG_102
* Test Case    : 

### Requirements
IXIT config file for IUT

### HTTP transport types
Test can be performed with 2 different HTTP transport types. Steps describing actions for specific one are marked as following:
- (TLS) - used by default inside ESInet on production environment
- (TCP) - used if default TLS is not possible

## Configuration
### Implementation Under Test Interface Connections
<!-- Identify each of the FEs that are part of the configuration and how they are connected -->
* Test System ESRP
  * IF_ESRP_CHFE - connected to IF_CHFE_ESRP
* Test System CHFE
  * IF_CHFE_ESRP - connected to IF_ESRP_CHFE
  * IF_CHFE_TS-CA - connected to IF_TS-CA_CHFE
  * IF_CHFE_BRIDGE - connected to IF_BRIDGE_CHFE
* CONFERENCE APP
  * IF_TS-CA_CHFE - connected to IF_CHFE_TS-CA
* BRIDGE
  * IF_BRIDGE_CHFE - connected to IF_CHFE_BRIDGE
  * IF_BRIDGE_LOG - connected to IF_LOG_BRIDGE
* Test System Logging Service
  * IF_LOG_BRIDGE - connected to IF_BRIDGE_LOG

### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* Test System ESRP
  * IF_ESRP_CHFE - Active
* Test System CHFE
  * IF_CHFE_ESRP - Active
  * IF_CHFE_TS-CA - Active
  * IF_CHFE_BRIDGE - Active
* CONFERENCE APP
  * IF_TS-CA_CHFE - Active
* BRIDGE
  * IF_BRIDGE_CHFE - Active
  * IF_BRIDGE_LOG - Active
* Test System Logging Service
  * IF_LOG_BRIDGE - Active
 
### Connectivity Diagram
<!--
https://mermaid.live/edit#pako:eNp9U2trg0AQ_Cuyn01Qk7N6lEJqTBpIk6D5VIRw1YtKoxfOs20a8t_rIy-VVjjYHWZmZz3uCD4LKGDY7tiXHxEupLnjpVLxzSYb23VWG-tlYj_2ek9FX5YVeGVUyNrtWaMzpaoruMl5dmbj6cWnbpqsMzZfTmtOUZyxmpLl7yEn-0ha00xI7iETNJFuWdqJa5SmQUttLRcT27EXli2NVk1tO3pXfJ-nGfum6qzzl9n9HnMWhnEaSi7ln7FPG07tH_G_UydI684699aFW8NAhpDHAWDBcypDQnlCyhaOJcUDEdGEeoCLMiD8wwMvPRWaPUnfGEsuMs7yMAK8Jbus6PJ9QAQdx6RYILmivJhGucXyVAA2TL0yAXyEb8CqqvRVXTWGpoL0AUK6KcMBsGb2hwPDLI-qIFVD2kmGn2qu0jcMczAwENJMpBqq9iADyQVzD6l_SUWDWDD-Wj-B6iWcfgGxAuH2
-->

![image](../_assets/BRIDGE/TD_BRIDGE_004_Connectivity_Diagram.png)


## Pre-Test Conditions
### Test System ESRP/Test System CHFE/Test System Logging Service
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* ng911 repository cloned to local storage
* (TLS) Generated own PCA-signed certificate and private key files (test_system.crt, test_system.key)
* (TLS) Certificate and key used by BRIDGE copied to local storage
* (TLS) PCA certificate copied to local storage

### BRIDGE/CONFERENCE APP
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device configured to use Logging Service Test System as a Logging Service
* IUT is initialized with steps from IXIT config file
* Device is active
* Device is in normal operating state
* IUT is initialized using IXIT config file

## Test Sequence

### Test Preamble

#### Test System ESRP
* clone ng911 repository to local storage

#### Test System Logging Service
* Install Wireshark[^2]
* (TLS v1.2) Configure Wireshark to decode HTTP over TLS, use tests system and BRIDGE certificate keys [^3]
* (TLS v1.3) Configure logging of session keys and configure Wireshark to decode HTTP over TLS [^4]
* Using Wireshark on 'Test System' start packet tracing on IF_LOG_BRIDGE interface - run following filter:
   * (TLS)
     > ip.addr == IF_LOG_BRIDGE_IP_ADDRESS and tls
   * (TCP)
     > ip.addr == IF_LOG_BRIDGE_IP_ADDRESS and http
     
### Test Body

#### Stimulus
Simulate basic call from Test System ESRP to Test System CHFE - run SIPp scenario by using following command on Test System ESRP, example:
* (TCP transport)
  ```
  sudo sipp -t t1 -sf SIP_basic_call.xml IF_ESRP_CHFE_IPv4:5060
  ```
* (TLS transport)
  ```
  sudo sipp -t l1 -tls_cert test_system.crt -tls_key test_system.key -sf SIP_basic_call.xml IF_ESRP_CHFE_IPv4:5060
  ```

#### Response
Using traced packets on Wireshark from Test System Logging Service verify:
* If BRIDGE sends HTTP POST to Logging Service Test System with signed JWS body containing:
  * "logEventType": "CallStartLogEvent"
  * "timestamp" with correct date-time format (f.e. 2020-03-10T11:00:01-05:00) and date-time match the time when SIP INVITE message has been received
  * "elementId" which has value with FQDN of BRIDGE
  * "agencyId" which has value with FQDN of an agency
  * "callId" which has value f.e.: `urn:emergency:uid:callid:1234567890:BRIDGE.ng911.example`. Check:
    * if header field contains "urn:emergency:uid:callid:"
    * if "urn:emergency:uid:callid:" is followed by 10 to 32 alphanumeric characters (String ID)
    * if String ID is followed by ":" and domain name
  * "incidentId" which has value f.e.: `urn:emergency:uid:incidentid:1234567890:BRIDGE.ng911.example`. Check:
    * if header field contains "urn:emergency:uid:incidentid:"
    * if "urn:emergency:uid:incidentid:" is followed by 10 to 32 alphanumeric characters (String ID)
    * if String ID is followed by ":" and domain name
  * "callIdSIP" which has value f.e.: `1234567890qwertyuiop@caller.example.com` 
  * "direction" which has value: `incoming`
  * (optionally) zero or one "standardPrimaryCallType" with one of string values:
    - "emergency"
    - "nonEmergency"
    - "silentMonitoring"
    - "intervene"
    - "legacyWireline"
    - "legacyWireless"
    - "legacyVoip"
  * (optionally) zero or one "standardSecondaryCallType" with one of string values mentioned for "standardPrimaryCallType"
  * (optionally) zero or one "localCallType" with string value
  * (optionally) zero or one "localUse" with string value
  * (optionally) zero or one "clientAssignedIdentifier" with string value
  * (optionally) zero or one "extension" with string value
* If BRIDGE sends HTTP POST to Logging Service Test System with signed JWS body containing:
  * "logEventType": "CallSignalingMessageLogEvent"
  * "timestamp" with correct date-time format (f.e. 2020-03-10T11:00:01-05:00) and date-time match the time when SIP INVITE message has been received
  * "elementId" which has value with FQDN of BRIDGE
  * "agencyId" which has value with FQDN of an agency
  * "callId" which has value f.e.: `urn:emergency:uid:callid:1234567890:bcf.ng911.example`. Check:
    * if header field contains "urn:emergency:uid:callid:"
    * if "urn:emergency:uid:callid:" is followed by 10 to 32 alphanumeric characters (String ID)
    * if String ID is followed by ":" and domain name
  * "incidentId" which has value f.e.: `urn:emergency:uid:incidentid:1234567890:bcf.ng911.example`. Check:
    * if header field contains "urn:emergency:uid:incidentid:"
    * if "urn:emergency:uid:incidentid:" is followed by 10 to 32 alphanumeric characters (String ID)
    * if String ID is followed by ":" and domain name
  * "callIdSIP" which has value f.e.: `1234567890qwertyuiop@caller.example.com` 
  * "direction" which has value: `incoming`
  * "text" which has string value containing SIP INVITE message received by BRIDGE from Test System CHFE
  * (Optional) "protocol" which has string value: `sip`
* If BRIDGE sends HTTP POST to Logging Service Test System with signed JWS body containing:
  * "logEventType": "CallEndLogEvent"
  * "timestamp" with correct date-time format (f.e. 2020-03-10T11:00:01-05:00) and date-time match SIP BYE message received by BRIDGE from SIP Test System
  * "elementId" which has value with FQDN of BRIDGE
  * "agencyId" which has value with FQDN of an agency
  * "callId" which has value f.e.: `urn:emergency:uid:callid:1234567890:bcf.ng911.example`. Check:
    * if header field contains "urn:emergency:uid:callid:"
    * if "urn:emergency:uid:callid:" is followed by 10 to 32 alphanumeric characters (String ID)
    * if String ID is followed by ":" and domain name
  * "incidentId" which has value f.e.: `urn:emergency:uid:incidentid:1234567890:bcf.ng911.example`. Check:
    * if header field contains "urn:emergency:uid:incidentid:"
    * if "urn:emergency:uid:incidentid:" is followed by 10 to 32 alphanumeric characters (String ID)
    * if String ID is followed by ":" and domain name
  * "callIdSIP" which has value f.e.: `1234567890qwertyuiop@caller.example.com` 
  * "direction" which has value: `incoming`
  * (optionally) zero or one "standardPrimaryCallType" with one of string values:
    - "emergency"
    - "nonEmergency"
    - "silentMonitoring"
    - "intervene"
    - "legacyWireline"
    - "legacyWireless"
    - "legacyVoip"
  * (optionally) zero or one "standardSecondaryCallType" with one of string values mentioned for "standardPrimaryCallType"
  * (optionally) zero or one "localCallType" with string value
  * (optionally) zero or one "localUse" with string value
  * (optionally) zero or one "clientAssignedIdentifier" with string value
  * (optionally) zero or one "extension" with string value
* If BRIDGE sends HTTP POST to Logging Service Test System with signed JWS body containing:
  * "logEventType": "CallSignalingMessageLogEvent"
  * "timestamp" with correct date-time format (f.e. 2020-03-10T11:00:01-05:00) and date-time match SIP BYE message received by BRIDGE from Test System CHFE
  * "elementId" which has value with FQDN of BRIDGE
  * "agencyId" which has value with FQDN of an agency
  * "callId" which has value f.e.: `urn:emergency:uid:callid:1234567890:bcf.ng911.example`. Check:
    * if header field contains "urn:emergency:uid:callid:"
    * if "urn:emergency:uid:callid:" is followed by 10 to 32 alphanumeric characters (String ID)
    * if String ID is followed by ":" and domain name
  * "incidentId" which has value f.e.: `urn:emergency:uid:incidentid:1234567890:bcf.ng911.example`. Check:
    * if header field contains "urn:emergency:uid:incidentid:"
    * if "urn:emergency:uid:incidentid:" is followed by 10 to 32 alphanumeric characters (String ID)
    * if String ID is followed by ":" and domain name
  * "callIdSIP" which has value f.e.: `1234567890qwertyuiop@caller.example.com` 
  * "direction" which has value: `incoming`
  * "text" which has string value containing SIP BYE message received by BRIDGE from Test System CHFE
  * (Optional) "protocol" which has string value: `sip`

VERDICT:
* PASSED - if BRIDGE sent logs as expected
* FAILED - any other cases


### Test Postamble
#### Test System ESRP/Test System CHFE
* stop SIPp (if still running)
* stop Wireshark (if still running)
* archive all logs generated
* disconnect interfaces from IUT
* (TLS) remove certificates

#### Test System Logging Service
* stop Wireshark (if still running)
* archive all logs generated
* disconnect interfaces from IUT
* (TLS) remove certificates

#### BRIDGE/CONFERENCE APP
* restore default configuration
* disconnect interfaces from Test Systems
* reconnect interfaces back to default

## Post-Test Conditions
### Test System ESRP/Test System CHFE/Test System Logging Service
* Test tools stopped
* interfaces disconnected from IUT

### BRIDGE/CONFERENCE APP
* device connected back to default
* device in normal operating state

## Sequence Diagram
<!--
https://mermaid.live/edit#pako:eNrtVV9P2zAc_Co_-YmKlOUfbWohJEjD6FjbqKkmbcqLl7jBWmN3joPWIb77nGSlJQXG4GEvkyI1je7O5_Mlv1uUiJQijLrdbswTwRcswzEHyJmUQp4lSsgCw4IsCxrzGlTQ7yXlCR0ykkmSV2CAFZGKJWxFuII5LRRE60LRHIJoFu4jzmej4ftg_7k_nVwEs2DiB3AWhs8r-5cXWqHBtFfsnp4etrEYolEIo8mn0Tw4-SrfncJBNAxBWa7Z2VepGG2VSrlRsU0TplfPCjxpo-Kf-VePM05Oupq0b31MU0Y2u50IRUHcULnn2HgYIAZfUqJoAb4-WCqrU2skntpum7-NrN5sZ8t-iHw6cMe0YazNpnXm2ociiYKCrfDW02h4yIqFSMri793VUf4xl6ZwGD4Ixl-exoa1k0LbeL2rVjQNrR3JR5FljGcQUXnDEorhcj4PIZxGczjwyXIZKV10DQpuKFedx421NHY91mq2acFGAqIySWhRLMrlcl0zafpmjyzj-kdDxlqZZPQf-93WzPJMmOml9PVyUvMa7xYTv66Yu0W5f7dfAj7_HLz1TAKe_m_NK1vTFKD6fiADZZKlCCtZUgPlVOak-otuK7UYqWua0xhhfZsS-S1GMb_THD2VvgiRb2hSlNk1wvW0NFC5SvXH9_eYvH-qi5VS6YuSK4Rd0x3UKgjfoh8IWz3zyDw-Nns913bNvm33DbTWMO9oYHk9y7P7jus4A-_OQD_rda0j03Jty_X6jmM5A9PxDERKJaI1Tzau9OzQU3zczPl63N_9AtuUcrE
-->


![image](../_assets/BRIDGE/TD_BRIDGE_004_Sequence_Diagram.png)

## Comments

Version:  010.3f.5.0.3

Date:     20260402

## Footnotes
[^1]: SIPp - tool for SIP packet simulations. Official documentation: https://sipp.sourceforge.net/doc/reference.html#Getting+SIPp
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^4]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518
