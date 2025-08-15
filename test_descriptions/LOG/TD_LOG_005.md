# Test Description: TD_LOG_005
## Overview
### Summary
Response for HTTP GET on /LogEventIds

### Description
Test covers Logging Service HTTP GET requests verification on /LogEventIds and sending a response

### References
* Requirements : RQ_LOG_039, RQ_LOG_041
* Test Case    : TC_LOG_005

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

![image](https://github.com/user-attachments/assets/188af9ba-24b1-47d5-8db9-6b2cccd94878)


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

1. Validate 4xx error response for request with incorrect 'limit' parameter (send string).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEventIds?limit=test
    ```
2. Validate 4xx error response for request with incorrect 'limit' parameter (send empty).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEventIds?limit=
    ```

3. Validate 4xx error response for request with incorrect 'limit' parameter (send space).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEventIds?limit=%20
    ```

4. Validate 4xx error response for request with incorrect 'limit' parameter (send value exceeding 64bit unsigned int).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEventIds?limit=18446744073709551616
    ```

5. Validate 4xx error response for request with incorrect 'limit' parameter (send negative value exceeding 64bit int).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEventIds?limit=-9223372036854775809
    ```

6. Validate 4xx error response for request with incorrect 'start' parameter (send string).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEventIds?start=test
    ```
7. Validate 4xx error response for request with incorrect 'start' parameter (send empty).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEventIds?start=
    ```

8. Validate 4xx error response for request with incorrect 'start' parameter (send space).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEventIds?start=%20
    ```

9. Validate 4xx error response for request with incorrect 'start' parameter (send value exceeding 64bit unsigned int).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEventIds?start=18446744073709551616
    ```

10. Validate 4xx error response for request with incorrect 'start' parameter (send value less than 1).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEventIds?start=0
    ```

11. Validate 4xx error response for request with incorrect 'callid' parameter (incorrect urn `urn:emergency:uid:callidd:123456789qwerty:bcf.ng911.test`).

    Send request with example URL:
    
    `IF_LOG_TS_IP_ADDRESS:PORT/LogEventIds?callid=urn%3Aemergency%3Auid%3Acallidd%3A123456789qwerty%3Abcf%2Eng911%2Etest`

12. Validate 4xx error response for request with incorrect 'callid' parameter (string ID below 10 characters `urn:emergency:uid:callid:1:bcf.ng911.test`).

    Send request with example URL:
    
    `IF_LOG_TS_IP_ADDRESS:PORT/LogEventIds?callid=urn%3Aemergency%3Auid%3Acallid%3A1%3Abcf%2Eng911%2Etest`

13. Validate 4xx error response for request with incorrect 'callid' parameter (string ID exceeding 36 characters `urn:emergency:uid:callid:123456789qwertyuiop1234567890qwertyui:bcf.ng911.test`).

    Send request with example URL:
    
    `IF_LOG_TS_IP_ADDRESS:PORT/LogEventIds?callid=urn%3Aemergency%3Auid%3Acallid%3A123456789qwertyuiop1234567890qwertyui%3Abcf%2Eng911%2Etest`

14. Validate 4xx error response for request with incorrect 'callid' parameter (incorrect FQDN `urn:emergency:uid:callid:123456789qwerty:bcf.ng911..test`).

    Send request with example URL:
    
    `IF_LOG_TS_IP_ADDRESS:PORT/LogEventIds?callid=urn%3Aemergency%3Auid%3Acallid%3A123456789qwerty%3Abcf%2Eng911%2E%2Etest`
   
15. Validate 4xx error response for request with incorrect 'callid' parameter (doubled ':' `urn:emergency:uid:callid:123456789qwerty::bcf.ng911.test`).

    Send request with example URL:
    
    `IF_LOG_TS_IP_ADDRESS:PORT/LogEventIds?callid=urn%3Aemergency%3Auid%3Acallid%3A123456789qwerty%3A%3Abcf%2Eng911%2Etest`

16. Validate 4xx error response for request with incorrect 'incidentid' parameter (incorrect urn `urn:emergency:uid:incidentidd:123456789qwerty:bcf.ng911.test`).

    Send request with example URL:
    
    `IF_LOG_TS_IP_ADDRESS:PORT/LogEventIds?incidentid=urn%3Aemergency%3Auid%3Aincidentidd%3A123456789qwerty%3Abcf%2Eng911%2Etest`

17. Validate 4xx error response for request with incorrect 'incidentid' parameter (string ID below 10 characters `urn:emergency:uid:incidentid:1:bcf.ng911.test`).

    Send request with example URL:
    
    `IF_LOG_TS_IP_ADDRESS:PORT/LogEventIds?incidentid=urn%3Aemergency%3Auid%3Aincidentid%3A1%3Abcf%2Eng911%2Etest`

18. Validate 4xx error response for request with incorrect 'incidentid' parameter (string ID exceeding 36 characters `urn:emergency:uid:incidentid:123456789qwertyuiop1234567890qwertyui:bcf.ng911.test`).

    Send request with example URL:
    
    `IF_LOG_TS_IP_ADDRESS:PORT/LogEventIds?incidentid=urn%3Aemergency%3Auid%3Aincidentid%3A123456789qwertyuiop1234567890qwertyui%3Abcf%2Eng911%2Etest`

19. Validate 4xx error response for request with incorrect 'incidentid' parameter (incorrect FQDN `urn:emergency:uid:incidentid:123456789qwerty:bcf.ng911..test`).

    Send request with example URL:
    
    `IF_LOG_TS_IP_ADDRESS:PORT/LogEventIds?incidentid=urn%3Aemergency%3Auid%3Aincidentid%3A123456789qwerty%3Abcf%2Eng911%2E%2Etest`
   
20. Validate 4xx error response for request with incorrect 'incidentid' parameter (doubled ':' `urn:emergency:uid:incidentid:123456789qwerty::bcf.ng911.test`).

    Send request with example URL:
    
    `IF_LOG_TS_IP_ADDRESS:PORT/LogEventIds?incidentid=urn%3Aemergency%3Auid%3Aincidentid%3A123456789qwerty%3A%3Abcf%2Eng911%2Etest`

21. Validate 200 OK + JSON response for any correct request.

    Send request without optional parameters, example URL:
    
    `IF_LOG_TS_IP_ADDRESS:PORT/LogEventIds`

#### Stimulus
Send HTTP GET to /LogEventIds entrypoint of Logging Service:

- (TLSv1.2):
  
  `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.2 -X GET https://URL`

- (TLSv1.3):
  
  `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.3 -X GET https://URL`

- (TCP):
  
  `curl -X GET http://URL`

#### Response
* Variation 1-20
  Logging Service responds with 4xx error message
* Variation 21
  Logging Service responds with 200 'LogEvents Found' with JSON body containing 'logEventIdArray' with:
    - 'count' which is integer
    - 'totalCount' which is integer
    - 'logEventIds' which an array with zero or more entries
    - each element in 'logEventIds' must be a string

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
[![](https://mermaid.ink/img/pako:eNq1kV1LwzAUhv9KOLdrR5qmXZeLgago-AkrY0hvQnvWRW0y03Q4x_67befc0EsxV7l43vecw7OF3BQIAnzfz3Ru9EKVItOEVMpaY89yZ2wtyEK-1pjpHqrxrUGd44WSpZVVB-_fvXFIzBotSbF2ZLqpHVYeuTVlqXRJpmjXKkdBZtIq6ZTRJPAZPeZPUv5kMviVu07TR3J1mR4TP5AudVLyleDz-V92ZMG_b8goJQ83ZECea6PBgwptJVXRWtl2TRm4JVaYgWi_hbQvGWR613KycWa60TkIZxv0oFkV0h28gOilebCS-smY6gBhoVqnd3vrvfweAbGFdxCjYEgjloScckZZlHAPNiCCOB5GMU8izoMwiVi88-Cj76TDEYtDnsTjJAjHwZiOPLCmKZff40vbXbKfbVEXaM9Nox2IkO0-AcecxsM?type=png)](https://mermaid.live/edit#pako:eNq1kV1LwzAUhv9KOLdrR5qmXZeLgago-AkrY0hvQnvWRW0y03Q4x_67befc0EsxV7l43vecw7OF3BQIAnzfz3Ru9EKVItOEVMpaY89yZ2wtyEK-1pjpHqrxrUGd44WSpZVVB-_fvXFIzBotSbF2ZLqpHVYeuTVlqXRJpmjXKkdBZtIq6ZTRJPAZPeZPUv5kMviVu07TR3J1mR4TP5AudVLyleDz-V92ZMG_b8goJQ83ZECea6PBgwptJVXRWtl2TRm4JVaYgWi_hbQvGWR613KycWa60TkIZxv0oFkV0h28gOilebCS-smY6gBhoVqnd3vrvfweAbGFdxCjYEgjloScckZZlHAPNiCCOB5GMU8izoMwiVi88-Cj76TDEYtDnsTjJAjHwZiOPLCmKZff40vbXbKfbVEXaM9Nox2IkO0-AcecxsM)
-->

![image](https://github.com/user-attachments/assets/66c30896-1948-4245-ab9f-04c519f57330)


## Comments

Version:  010.3f.3.1.6

Date:     20250505

## Footnotes
[^1]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^2]: Wireshark configuration to decrypt TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^3]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518
