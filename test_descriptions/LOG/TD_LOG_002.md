# Test Description: TD_LOG_002
## Overview
### Summary
Handling HTTP GET requests on /LogEvents entrypoint

### Description
Test covers Logging Service HTTP GET requests verification on /LogEvents entrypoint and sending response

### References
* Requirements : RQ_LOG_028
* Test Case    : TC_LOG_002

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

![image](https://github.com/user-attachments/assets/2cbc1b3d-b59d-473e-ac72-df8cc7cc1c3d)


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
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?limit=test
    ```
2. Validate 4xx error response for request with incorrect 'limit' parameter (send empty).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?limit=
    ```

3. Validate 4xx error response for request with incorrect 'limit' parameter (send space).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?limit=%20
    ```

4. Validate 4xx error response for request with incorrect 'limit' parameter (send value exceeding 64bit unsigned int).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?limit=18446744073709551616
    ```

5. Validate 4xx error response for request with incorrect 'limit' parameter (send negative value exceeding 64bit int).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?limit=-9223372036854775809
    ```

6. Validate 4xx error response for request with incorrect 'start' parameter (send string).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?start=test
    ```
7. Validate 4xx error response for request with incorrect 'start' parameter (send empty).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?start=
    ```

8. Validate 4xx error response for request with incorrect 'start' parameter (send space).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?start=%20
    ```

9. Validate 4xx error response for request with incorrect 'start' parameter (send value exceeding 64bit unsigned int).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?start=18446744073709551616
    ```

10. Validate 4xx error response for request with incorrect 'start' parameter (send value less than 1).

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?start=0
    ```

11. Validate 4xx error response for request with incorrect 'logEventType' parameter (send 'CallProcessLogEventt')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?logEventType=CallProcessLogEventt
    ```

12. Validate 4xx error response for request with incorrect 'startTime' parameter (send space)

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?startTime=%20
    ```

13. Validate 4xx error response for request with incorrect 'startTime' parameter (send with incorrect year '20155-08-21T12:58:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?startTime=20155-08-21T12%3A58%3A03.01%2D05%3A00
    ```

14. Validate 4xx error response for request with incorrect 'startTime' parameter (send with incorrect month '2015-13-21T12:58:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?startTime=2015-13-21T12%3A58%3A03.01%2D05%3A00
    ```

15. Validate 4xx error response for request with incorrect 'startTime' parameter (send with incorrect day '2015-12-32T12:58:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?startTime=2015-12-32T12%3A58%3A03.01%2D05%3A00
    ```

16. Validate 4xx error response for request with incorrect 'startTime' parameter (send with incorrect hour '2015-12-21T24:58:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?startTime=2015-12-21T24%3A58%3A03.01%2D05%3A00
    ```

17. Validate 4xx error response for request with incorrect 'startTime' parameter (send with incorrect minutes '2015-12-21T12:60:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?startTime=2015-12-21T12%3A60%3A03.01%2D05%3A00
    ```

18. Validate 4xx error response for request with incorrect 'startTime' parameter (send with incorrect seconds '2015-12-21T12:58:61.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?startTime=2015-12-21T12%3A58%3A61.01%2D05%3A00
    ```

19. Validate 4xx error response for request with incorrect 'startTime' parameter (send with exceeded time offset '2015-12-21T12:58:03.01-13:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?startTime=2015-12-21T12%3A58%3A61.01%2D13%3A00
    ```

20. Validate 4xx error response for request with incorrect 'startTime' parameter (send incorrect day in February '2015-02-30T12:58:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?startTime=2015-02-30T12%3A58%3A61.01%2D05%3A00
    ```
21. Validate 4xx error response for request with incorrect 'endTime' parameter (send space)

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?endTime=%20
    ```
    
22. Validate 4xx error response for request with incorrect 'endTime' parameter (send with incorrect year '20155-08-21T12:58:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?endTime=20155-08-21T12%3A58%3A03.01%2D05%3A00
    ```

23. Validate 4xx error response for request with incorrect 'endTime' parameter (send with incorrect month '2015-13-21T12:58:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?endTime=2015-13-21T12%3A58%3A03.01%2D05%3A00
    ```

24. Validate 4xx error response for request with incorrect 'endTime' parameter (send with incorrect day '2015-12-32T12:58:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?endTime=2015-12-32T12%3A58%3A03.01%2D05%3A00
    ```

25. Validate 4xx error response for request with incorrect 'endTime' parameter (send with incorrect hour '2015-12-21T24:58:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?endTime=2015-12-21T24%3A58%3A03.01%2D05%3A00
    ```

26. Validate 4xx error response for request with incorrect 'endTime' parameter (send with incorrect minutes '2015-12-21T12:60:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?endTime=2015-12-21T12%3A60%3A03.01%2D05%3A00
    ```

27. Validate 4xx error response for request with incorrect 'endTime' parameter (send with incorrect seconds '2015-12-21T12:58:61.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?endTime=2015-12-21T12%3A58%3A61.01%2D05%3A00
    ```

28. Validate 4xx error response for request with incorrect 'endTime' parameter (send with exceeded time offset '2015-12-21T12:58:03.01-13:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?endTime=2015-12-21T12%3A58%3A61.01%2D13%3A00
    ```

29. Validate 4xx error response for request with incorrect 'endTime' parameter (send incorrect day in February '2015-02-30T12:58:03.01-05:00')

    Send request with example URL:
    
    ```
    LOGGING_SERVICE_FQDN_OR_IP:PORT/LogEvents?endTime=2015-02-30T12%3A58%3A61.01%2D05%3A00
    ```

#### Stimulus
Send HTTP GET to /LogEvents entrypoint of Logging Service:

- (TLSv1.2):
  
  `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.2 -X GET https://URL`

- (TLSv1.3):
  
  `curl --cert test_system.crt --key test_system.key --cacert PCA.crt --tlsv1.3 -X GET https://URL`

- (TCP):
  
  `curl -X GET http://URL`

#### Response
Logging Service should respond with 4xx error message

VERDICT:
* PASSED - if Policy Store responded as expected
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
[![](https://mermaid.ink/img/pako:eNplkFFLwzAQx79KuFfTkbYzXfIwEBR9UBFWZEheQnvrgjaZaTqsY9_dtpt0aJ4ux-93x_0PULgSQUIURcoWzm5MJZUlpDbeO39TBOcbSTb6o0FlR6jBzxZtgbdGV17XA3x6zy4gcXv0JMcmkFXXBKwpeXRVZWxFVuj3pkBJXrU3OhhnSRwlYvIvrGi5vPrnPeT5C7m_yyfjDzJYF0POxny9Bgo1-lqbsr_0MPgKwhZrVCD7stT-XYGyx57TbXCrzhYgg2-RQrsrdfi9FeQYBIWdtm_OTX8sTR_U0ynKMdGRAXmAL5BxwmcxF0JkKRNiIbKEQgey76YsYXGyEIIxEc_5kcL3OHY-SzjnLMt4nC5Sdp1R8K6ttueFxx_diIiH?type=png)](https://mermaid.live/edit#pako:eNplkFFLwzAQx79KuFfTkbYzXfIwEBR9UBFWZEheQnvrgjaZaTqsY9_dtpt0aJ4ux-93x_0PULgSQUIURcoWzm5MJZUlpDbeO39TBOcbSTb6o0FlR6jBzxZtgbdGV17XA3x6zy4gcXv0JMcmkFXXBKwpeXRVZWxFVuj3pkBJXrU3OhhnSRwlYvIvrGi5vPrnPeT5C7m_yyfjDzJYF0POxny9Bgo1-lqbsr_0MPgKwhZrVCD7stT-XYGyx57TbXCrzhYgg2-RQrsrdfi9FeQYBIWdtm_OTX8sTR_U0ynKMdGRAXmAL5BxwmcxF0JkKRNiIbKEQgey76YsYXGyEIIxEc_5kcL3OHY-SzjnLMt4nC5Sdp1R8K6ttueFxx_diIiH)
-->

![image](https://github.com/user-attachments/assets/dafed665-7530-4415-987a-412ac440408e)


## Comments

Version:  010.3f.3.1.5

Date:     20250428

## Footnotes
[^1]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^2]: Wireshark configuration to decrypt TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^3]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518
