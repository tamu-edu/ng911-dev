# Test Description: TD_LOG_004

## IMPORTANT
Some of the requirements covered by this document are not fully clarified! Affected parts are marked in **bold font**

## Overview
### Summary
Response for HTTP GET on /LogEvents and /LogEvents/{logEventId}

### Description
Test covers Logging Service HTTP GET requests verification on /LogEvents/ and /LogEvents/{logEventId} and sending a response

### References
* Requirements : RQ_LOG_030, RQ_LOG_032, RQ_LOG_034
* Test Case    : TC_LOG_004

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

![image](../_assets/LOG/TD_LOG_004_Connectivity_Diagram.png)

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
* Device is active
* Device is in normal operating state
* Devices stores some Log Events with CallSignallingMessageLogEvent type

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

### Test Body

#### Variations

1. Validate 4xx error response for HTTP GET request with incorrect logEventId.

    Send request with URL example:
    
    `IF_LOG_TS_IP_ADDRESS:PORT/LogEvents/test123`

2. Validate JSON body from HTTP 200 OK response for HTTP GET request to /LogEvents entrypoint

    Send request with URL example:
    
    `IF_LOG_TS_IP_ADDRESS:PORT/LogEvents`

3. Validate JWS body from HTTP 200 OK response for HTTP GET request with correct logEventId.

    Send request with one of logEventId (with CallSignallingMessageLogEvent) received in response for HTTP GET in Variation 2, example URL:
    
    `IF_LOG_TS_IP_ADDRESS:PORT/LogEvents/LOG_EVENT_ID`

#### Stimulus
Send HTTP POST to /LogEvents entrypoint of Logging Service with generated JWS object:

- (TLSv1.2):
  
  `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.2 -X GET https://URL`

- (TLSv1.3):
  
  `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.3 -X GET https://URL`

- (TCP):
  
  `curl -X GET https://URL`

#### Response
* Variation 1
  Logging Service responds with 4xx error message
  
* Variation 2
  Logging service responds with 200 OK with JSON body containing:
- 'count' which is integer
- 'totalCount' which is integer
- 'logEventContainers' which is array of zero or more objects
- each element in 'logEventContainers' consits:
  - one 'logEventId' which is a string consisting of `urn:emergency:uid:logid:`, 10 to 36 alphanumeric unique string and FQDN, f.e. `urn:emergency:uid:logid:0013344556677-231:logger.state.pa.us`
  - zero or one 'rtsp'
  - 'rtsp' if present is an array of string values which are in RTSP URI format, example: "rtsp://user:password@192.168.1.1:8080/camera?channel=12"
  - each RTSP URI shall be unique
  - 'logEvent' which is JWS string with flattened JSON. Use checklist from Variation 3 to verify if JWS is correct.
    
* Variation 3
  Logging Service responds with 200 'LogEvents Found' with JWS string body:
  * which is signed by certificate traceable to the PCA
  * **if 'agencyAgentId' is present then JWS shall be signed by certificate where CN match FQDN from this header field**
  * **if 'agencyAgentId' is not present then JWS shall be signed by certificate where CN match FQDN from 'elementId'**
  * JWS payload JSON body shall contain:
    
      - zero or one 'clientAssignedIdentifier' which is a string
      - 'logEventType' which has one of following values:
          - CallProcessLogEvent
          - CallStartLogEvent
          - CallEndLogEvent
          - RecCallStartLogEvent
          - RecCallEndLogEvent
          - CallTransferLogEvent
          - RouteLogEvent
          - MediaStartLogEvent
          - MediaEndLogEvent
          - RecMediaStartLogEvent
          - RecordingFailedLogEvent
          - MessageLogEvent
          - AdditionalAgencyLogEvent
          - IncidentMergeLogEvent
          - IncidentUnMergeLogEvent
          - IncidentSplitLogEvent
          - IncidentLinkLogEvent
          - IncidentUnLinkLogEvent
          - IncidentClearLogEvent
          - IncidentReopenLogEvent
          - LostQueryLogEvent
          - LostResponseLogEvent
          - CallSignalingMessageLogEvent
          - SipRecMetadataLogEvent
          - NonRtpMediaMessageLogEvent
          - AliLocationQueryLogEvent
          - AliLocationResponseLogEvent
          - MalformedMessageLogEvent
          - EidoLogEvent
          - DiscrepancyReportLogEvent
          - ElementStateChangeLogEvent
          - ServiceStateChangeLogEvent
          - AdditionalDataQueryLogEvent
          - AdditionalDataResponseLogEvent
          - LocationQueryLogEvent
          - LocationResponseLogEvent
          - CallStateChangeLogEvent
          - GatewayCallLogEvent
          - HookflashLogEvent
          - LegacyDigitsLogEvent
          - AgentStateChangeLogEvent
          - QueueStateChangeLogEvent
          - KeepAliveFailureLogEvent
          - RouteRuleMsgLogEvent
          - PolicyChangeLogEvent
          - VersionsLogEvent
          - SubscribeLogEvent
      - 'timestamp' with string date-time value, example: "2020-03-10T10:00:00-05:00"
      - 'elementId' which has string value with FQDN
      - 'agencyId' which has string value with FQDN
      - 'agencyAgentId' which has string value  with agent identifier, example "agent@agency.gov"
      - zero or one 'agencyPositionId' which is a string
      - 'callId' - can be added to any 'logEventType', but is required for:
         ```
           CallProcessLogEvent
           CallStartLogEvent
           CallEndLogEvent
           RecCallStartLogEvent
           RecCallEndLogEvent
           CallTransferLogEvent
           RouteLogEvent
           MessageLogEvent
           AdditionalAgencyLogEvent
           CallSignalingMessageLogEvent
           SipRecMetadataLogEvent
           CallStateChangeLogEvent
         ```
      - 'callId' - if exist should have following format:
          - should contain: 'urn:emergency:uid:callid:'
          - should contain unique string 10 to 36 characters long
          - should contain FQDN
     <!-- - 'callId' should be the same as in `Call-Info` header field of SIP message included within `"text"` parameter of Log Event -->
      - 'incidentId' - can be added to any 'logEventType', but is required for:
         ```
           IncidentMergeLogEvent
           IncidentUnMergeLogEvent
           IncidentSplitLogEvent
           IncidentLinkLogEvent
           IncidentUnLinkLogEvent
           IncidentClearLogEvent
           IncidentReopenLogEvent
         ```
      - 'incidentId' - if exist should have following format:
          - should contain: 'urn:emergency:uid:incidentid:'
          - should contain unique string 10 to 36 characters long
          - should contain FQDN
     <!-- - 'incidentId' should be the same as in `Call-Info` header field of SIP message included within `"text"` parameter of Log Event -->
      - 'callIdSIP' - can be added to any 'logEventType', but is required for:
         ```
           CallProcessLogEvent
           CallStartLogEvent
           CallEndLogEvent
           RecCallStartLogEvent
           RecCallEndLogEvent
           CallTransferLogEvent
           RouteLogEvent
           MessageLogEvent
           AdditionalAgencyLogEvent
           CallSignalingMessageLogEvent (when "protocol" is "sip")
           SipRecMetadataLogEvent
           CallStateChangeLogEvent
         ```
      - 'callIdSIP' - if exist should be a string conformant with Call-ID format (RFC 3261)
      <!-- - 'callIdSIP' should be the same as in `Call-ID` header field of SIP message included within `"text"` parameter of Log Event -->
      - 'ipAddressPort' - value should be a string with standarized IP address/FQDN with port number
      - 'ipAddressPort' should be the same as IP in `From` header field of SIP message included within `"text"` parameter of Log Event
      - zero or one 'extension' which is a JSON object
      - zero or one 'rtsp' which is a string, example: "rtsp://user:password@192.168.1.1:8080/camera?channel=12"


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
[![](https://mermaid.ink/img/pako:eNq9kl1LwzAUhv9KOLdrR5rOdsnFQFAUv6FFh_QmtGdd1CYzTYdz7L_bdpMNvRyaqyS8zznvxbOG3BQIAnzfz3Ru9EyVItOEVMpaY09zZ2wtyEy-1ZjpPlTje4M6xzMlSyurLrw9d8YhMUu0JMXakWRVO6w8cmPKUumSJGiXKkdBHqVV0imjSbCHDxB_Mhn8gi7T9IFcnKd74kekow6G7IjRdHpMQfbnBRml5P6aDMhLbfQxVcP_q3r1lIAHFdpKqqJ1Z90NysDNscIMRHstpH3NINObNicbZ5KVzkE426AHzaKQ7tseEL1aHiykfjZm_8ZCterdbuXsHe0zINbwASJg0TCIOOdxSDkf85h5sALR_oaU0YCNOaeUB6No48FnP3Y0ZFEU0TiOgnAc0pPYA2uacr5buPkCsebxHA?type=png)](https://mermaid.live/edit#pako:eNq9kl1LwzAUhv9KOLdrR5rOdsnFQFAUv6FFh_QmtGdd1CYzTYdz7L_bdpMNvRyaqyS8zznvxbOG3BQIAnzfz3Ru9EyVItOEVMpaY09zZ2wtyEy-1ZjpPlTje4M6xzMlSyurLrw9d8YhMUu0JMXakWRVO6w8cmPKUumSJGiXKkdBHqVV0imjSbCHDxB_Mhn8gi7T9IFcnKd74kekow6G7IjRdHpMQfbnBRml5P6aDMhLbfQxVcP_q3r1lIAHFdpKqqJ1Z90NysDNscIMRHstpH3NINObNicbZ5KVzkE426AHzaKQ7tseEL1aHiykfjZm_8ZCterdbuXsHe0zINbwASJg0TCIOOdxSDkf85h5sALR_oaU0YCNOaeUB6No48FnP3Y0ZFEU0TiOgnAc0pPYA2uacr5buPkCsebxHA)
-->

![image](../_assets/LOG/TD_LOG_004_Sequence_Diagram.png)


## Comments

Version:  010.3f.3.0.12-requirements-under-clarification

Date:     20250430

## Footnotes
[^1]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^2]: Wireshark configuration to decrypt TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^3]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518
