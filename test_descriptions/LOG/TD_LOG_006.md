# Test Description: TD_LOG_006

## IMPORTANT
Some of the requirements covered by this document are not fully clarified! Affected parts are marked in **bold font**

## Overview
### Summary
Response for HTTP GET on /CallIds

### Description
Test covers Logging Service HTTP GET requests verification on /CallIds and sending a response

### References
* Requirements : RQ_LOG_042, RQ_LOG_044
* Test Case    : TC_LOG_006

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

![image](../_assets/LOG/TD_LOG_006_Connectivity_Diagram.png)

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

### Test Body

#### Variations

1. Validate 4xx error response for request with incorrect 'limit' parameter (send string).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?limit=test
    ```
2. Validate 4xx error response for request with incorrect 'limit' parameter (send empty).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?limit=
    ```

3. Validate 4xx error response for request with incorrect 'limit' parameter (send space).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?limit=%20
    ```

4. Validate 4xx error response for request with incorrect 'limit' parameter (send value exceeding 64bit unsigned int).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?limit=18446744073709551616
    ```

5. Validate 4xx error response for request with incorrect 'limit' parameter (send negative value exceeding 64bit int).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?limit=-9223372036854775809
    ```

6. Validate 4xx error response for request with incorrect 'start' parameter (send string).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?start=test
    ```
7. Validate 4xx error response for request with incorrect 'start' parameter (send empty).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?start=
    ```

8. Validate 4xx error response for request with incorrect 'start' parameter (send space).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?start=%20
    ```

9. Validate 4xx error response for request with incorrect 'start' parameter (send value exceeding 64bit unsigned int).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?start=18446744073709551616
    ```

10. Validate 4xx error response for request with incorrect 'start' parameter (send value less than 1).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?start=0
    ```

11. Validate 4xx error response for request with incorrect 'incidentid' parameter (incorrect urn `urn:emergency:uid:incidentidd:123456789qwerty:bcf.ng911.test`).

    Send request with example URL:
    
    `IF_LOG_TS_IP_ADDRESS:PORT/CallIds?incidentid=urn%3Aemergency%3Auid%3Aincidentidd%3A123456789qwerty%3Abcf%2Eng911%2Etest`

12. Validate 4xx error response for request with incorrect 'incidentid' parameter (string ID below 10 characters `urn:emergency:uid:incidentid:1:bcf.ng911.test`).

    Send request with example URL:
    
    `IF_LOG_TS_IP_ADDRESS:PORT/CallIds?incidentid=urn%3Aemergency%3Auid%3Aincidentid%3A1%3Abcf%2Eng911%2Etest`

13. Validate 4xx error response for request with incorrect 'incidentid' parameter (string ID exceeding 36 characters `urn:emergency:uid:incidentid:123456789qwertyuiop1234567890qwertyui:bcf.ng911.test`).

    Send request with example URL:
    
    `IF_LOG_TS_IP_ADDRESS:PORT/CallIds?incidentid=urn%3Aemergency%3Auid%3Aincidentid%3A123456789qwertyuiop1234567890qwertyui%3Abcf%2Eng911%2Etest`

14. Validate 4xx error response for request with incorrect 'incidentid' parameter (incorrect FQDN `urn:emergency:uid:incidentid:123456789qwerty:bcf.ng911..test`).

    Send request with example URL:
    
    `IF_LOG_TS_IP_ADDRESS:PORT/CallIds?incidentid=urn%3Aemergency%3Auid%3Aincidentid%3A123456789qwerty%3Abcf%2Eng911%2E%2Etest`
   
15. Validate 4xx error response for request with incorrect 'incidentid' parameter (doubled ':' `urn:emergency:uid:incidentid:123456789qwerty::bcf.ng911.test`).

    Send request with example URL:
    
    `IF_LOG_TS_IP_ADDRESS:PORT/CallIds?incidentid=urn%3Aemergency%3Auid%3Aincidentid%3A123456789qwerty%3A%3Abcf%2Eng911%2Etest`


16. Validate 4xx error response for request with incorrect 'startTime' parameter (send space)

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?startTime=%20
    ```

17. Validate 4xx error response for request with incorrect 'startTime' parameter (send with incorrect year '20155-08-21T12:58:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?startTime=20155-08-21T12%3A58%3A03.01%2D05%3A00
    ```

18. Validate 4xx error response for request with incorrect 'startTime' parameter (send with incorrect month '2015-13-21T12:58:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?startTime=2015-13-21T12%3A58%3A03.01%2D05%3A00
    ```

19. Validate 4xx error response for request with incorrect 'startTime' parameter (send with incorrect day '2015-12-32T12:58:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?startTime=2015-12-32T12%3A58%3A03.01%2D05%3A00
    ```

20. Validate 4xx error response for request with incorrect 'startTime' parameter (send with incorrect hour '2015-12-21T24:58:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?startTime=2015-12-21T24%3A58%3A03.01%2D05%3A00
    ```

21. Validate 4xx error response for request with incorrect 'startTime' parameter (send with incorrect minutes '2015-12-21T12:60:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?startTime=2015-12-21T12%3A60%3A03.01%2D05%3A00
    ```

22. Validate 4xx error response for request with incorrect 'startTime' parameter (send with incorrect seconds '2015-12-21T12:58:61.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?startTime=2015-12-21T12%3A58%3A61.01%2D05%3A00
    ```

23. Validate 4xx error response for request with incorrect 'startTime' parameter (send with exceeded time offset '2015-12-21T12:58:03.01-13:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?startTime=2015-12-21T12%3A58%3A61.01%2D13%3A00
    ```

24. Validate 4xx error response for request with incorrect 'startTime' parameter (send incorrect day in February '2015-02-30T12:58:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?startTime=2015-02-30T12%3A58%3A61.01%2D05%3A00
    ```

25. Validate 4xx error response for request with incorrect 'endTime' parameter (send space)

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?endTime=%20
    ```

26. Validate 4xx error response for request with incorrect 'endTime' parameter (send with incorrect year '20155-08-21T12:58:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?endTime=20155-08-21T12%3A58%3A03.01%2D05%3A00
    ```

27. Validate 4xx error response for request with incorrect 'endTime' parameter (send with incorrect month '2015-13-21T12:58:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?endTime=2015-13-21T12%3A58%3A03.01%2D05%3A00
    ```

28. Validate 4xx error response for request with incorrect 'endTime' parameter (send with incorrect day '2015-12-32T12:58:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?endTime=2015-12-32T12%3A58%3A03.01%2D05%3A00
    ```

29. Validate 4xx error response for request with incorrect 'endTime' parameter (send with incorrect hour '2015-12-21T24:58:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?endTime=2015-12-21T24%3A58%3A03.01%2D05%3A00
    ```

30. Validate 4xx error response for request with incorrect 'endTime' parameter (send with incorrect minutes '2015-12-21T12:60:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?endTime=2015-12-21T12%3A60%3A03.01%2D05%3A00
    ```

31. Validate 4xx error response for request with incorrect 'endTime' parameter (send with incorrect seconds '2015-12-21T12:58:61.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?endTime=2015-12-21T12%3A58%3A61.01%2D05%3A00
    ```

32. Validate 4xx error response for request with incorrect 'endTime' parameter (send with exceeded time offset '2015-12-21T12:58:03.01-13:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?endTime=2015-12-21T12%3A58%3A61.01%2D13%3A00
    ```

33. Validate 4xx error response for request with incorrect 'endTime' parameter (send incorrect day in February '2015-02-30T12:58:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/CallIds?endTime=2015-02-30T12%3A58%3A61.01%2D05%3A00
    ```

34. **Validate 4xx error response for request with incorrect 'area' parameter.**

    Send request with 'area' which is a string without PIDF-LO object, example URL:
    
    `IF_LOG_TS_IP_ADDRESS:PORT/CallIds?area=test`

35. Validate 200 OK + JSON response for any correct request.

    Send request without optional parameters, example URL:
    
    `IF_LOG_TS_IP_ADDRESS:PORT/CallIds`

#### Stimulus
Send HTTP GET to /CallIds entrypoint of Logging Service:

- (TLSv1.2):
  
  `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.2 -X GET https://URL`

- (TLSv1.3):
  
  `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.3 -X GET https://URL`

- (TCP):
  
  `curl -X GET http://URL`

#### Response
* Variation 1-34
  Logging Service responds with 4xx error message
* Variation 35
  Logging Service responds with 200 OK with JSON body containing:
- 'CallIdArray' which is an array with:
    - 'count' which is integer
    - 'totalCount' which is integer
    - 'callIds' which an array with zero or more entries
    - each element in 'callIds' must be a string in correct Call Identifier format (example: `urn:emergency:uid:callid:a56e556d871:bcf.state.pa.us`):
        - must contain `urn:emergency:uid:callid` at the beginning
        - then after `:` must contain 10 to 36 alphanumeric unique string ID
        - then after `:` must contain correct FQDN


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
[![](https://mermaid.ink/img/pako:eNq1kU1Lw0AQhv_KMtcmJR-bNN1DQVQU_ISGUiSXJZmmq2a3TjbFWvrfTVJrix7FPe3hed-Z4dlCbgoEAa7rZjo3eqFKkWnGKkVk6Cy3hmrBFvK1xkz3UI1vDeocL5QsSVYdvH_3xiIzaySWYm3ZdFNbrBx2a8pS6ZJNkdYqR8FmkpS0ymjmuyE_5k9S7mQy-JW7TtNHdnWZHhM_kC51UvKV4PP5X3YMo3_fMPA89nDDBuy5NhocqJAqqYrWyrZrysAuscIMRPstJL1kkOldy8nGmulG5yAsNehAsyqkPXgB0UtzYCX1kzHVAcJCtU7v9tZ7-T0CYgvvIEb-0IuCJOQeD7wgSrgDGxB-HA-jmCcR536YREG8c-Cj7_SGoyAOeRKPEz8c-2Nv5ACZplx-jy-pu2Q_m1AXSOem0RZEzHef2GPG0g?type=png)](https://mermaid.live/edit#pako:eNq1kU1Lw0AQhv_KMtcmJR-bNN1DQVQU_ISGUiSXJZmmq2a3TjbFWvrfTVJrix7FPe3hed-Z4dlCbgoEAa7rZjo3eqFKkWnGKkVk6Cy3hmrBFvK1xkz3UI1vDeocL5QsSVYdvH_3xiIzaySWYm3ZdFNbrBx2a8pS6ZJNkdYqR8FmkpS0ymjmuyE_5k9S7mQy-JW7TtNHdnWZHhM_kC51UvKV4PP5X3YMo3_fMPA89nDDBuy5NhocqJAqqYrWyrZrysAuscIMRPstJL1kkOldy8nGmulG5yAsNehAsyqkPXgB0UtzYCX1kzHVAcJCtU7v9tZ7-T0CYgvvIEb-0IuCJOQeD7wgSrgDGxB-HA-jmCcR536YREG8c-Cj7_SGoyAOeRKPEz8c-2Nv5ACZplx-jy-pu2Q_m1AXSOem0RZEzHef2GPG0g)
-->

![image](../_assets/LOG/TD_LOG_006_Sequence_Diagram.png)


## Comments

Version:  010.3f.3.1.6

Date:     20250505

## Footnotes
[^1]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^2]: Wireshark configuration to decrypt TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^3]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518
