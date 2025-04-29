# Test Description: TD_LOG_008
## Overview
### Summary
Logging call status by call stateful functional elements

### Description
Test covers logging of CallStartLogEvent, CallEndLogEvent and CallSignallingMessageLogEvent by all functional elements which are processing a calls

### References
* Requirements : RQ_LOG_53, RQ_LOG_56, RQ_LOG_57, RQ_LOG_103
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
* SIP Test System (SIPTS)
  * IF_SIPTS_FE - connected to Call Stateful Functional Element IF_FE_SIPTS
* Call Stateful Functional Element (FE)
  * IF_FE_SIPTS - connected to SIP Test System IF_SIPTS_FE
  * IF_FE_LOGTS - connected to Logging Service Test System IF_LOGTS_FE
* Logging Service Test System (LOGTS)
  * IF_LOGTS_FE - connected to FE IF_FE_LOGTS

### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* SIP Test System (SIPTS)
  * IF_SIPTS_FE - Active
* Call Stateful Functional Element (FE)
  * IF_FE_SIPTS - Active
  * IF_FE_LOGTS - Active
* Logging Service Test System (LOGTS)
  * IF_LOGTS_FE - Active
 
### Connectivity Diagram
<!--
[![](https://mermaid.ink/img/pako:eNp1UVFPgzAQ_ivNPbOlwCxrY3zRzSzBaGRPhmSp0AER6FKKimT_3RPUKcn6dPd9d9991-sh0akCAftSvyW5NJaEj3FN8G3Wu2jzsI1269XlbHaF6Xo1Ir88AuH97TYa6SFEbKSb9jkz8pATbCFb1VgSdY1V1chOBoygqtNJ77UsS9JYadW-LclP3Wn6HzsTS-cUQ51lRZ2RSJnXIlFnnf1fBnXAgUqZShYp_lb_Bcdgc1WpGASGqTQvMcT1Eetka3XU1QkIa1rlQHtIcYObQqKFCsRelg2iB1k_aX3KVVpYbe7GcwxXGWpA9PAOwvXY3GWc88CnnC954DnQgUDUpx51vSXnlHJ3wY4OfAyyi7nHGKNBwFx_6dOLwAGj2yz_Hnj8BPUxlrY?type=png)](https://mermaid.live/edit#pako:eNp1UVFPgzAQ_ivNPbOlwCxrY3zRzSzBaGRPhmSp0AER6FKKimT_3RPUKcn6dPd9d9991-sh0akCAftSvyW5NJaEj3FN8G3Wu2jzsI1269XlbHaF6Xo1Ir88AuH97TYa6SFEbKSb9jkz8pATbCFb1VgSdY1V1chOBoygqtNJ77UsS9JYadW-LclP3Wn6HzsTS-cUQ51lRZ2RSJnXIlFnnf1fBnXAgUqZShYp_lb_Bcdgc1WpGASGqTQvMcT1Eetka3XU1QkIa1rlQHtIcYObQqKFCsRelg2iB1k_aX3KVVpYbe7GcwxXGWpA9PAOwvXY3GWc88CnnC954DnQgUDUpx51vSXnlHJ3wY4OfAyyi7nHGKNBwFx_6dOLwAGj2yz_Hnj8BPUxlrY)
-->

![image](https://github.com/user-attachments/assets/12918e90-c766-4c0a-ad39-aa8798a7a1a7)


## Pre-Test Conditions
### SIP/Logging Service Test System
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* ng911 repository cloned to local storage
* (TLS) Generated own PCA-signed certificate and private key files (test_system.crt, test_system.key)
* (TLS) Certificate and key used by FE copied to local storage
* (TLS) PCA certificate copied to local storage

### Call Stateful Functional Element (FE)
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device configured to use Logging Service Test System as a Logging Service
* IUT is initialized with steps from IXIT config file
* Device is active
* Device is in normal operating state
* IUT is initialized using IXIT config file

## Test Sequence

### Test Preamble

#### SIP Test System
* Install SIPp by following steps from documentation[^1]
* Copy following XML scenario file to local storage:
  `SIP_basic_call.xml`
* Install Wireshark[^2]
* (TLS v1.2) Configure Wireshark to decode HTTP over TLS, use tests system and FE certificate keys [^3]
* (TLS v1.3) Configure logging of session keys and configure Wireshark to decode HTTP over TLS [^4]
* Using Wireshark on 'Test System' start packet tracing on IF_SIPTS_FE interface - run following filter:
   * (TLS)
     > ip.addr == IF_SIPTS_FE_IP_ADDRESS and tls
   * (TCP)
     > ip.addr == IF_SIPTS_FE_IP_ADDRESS and sip

#### Logging Service Test System
* Install Wireshark[^2]
* (TLS v1.2) Configure Wireshark to decode HTTP over TLS, use tests system and FE certificate keys [^3]
* (TLS v1.3) Configure logging of session keys and configure Wireshark to decode HTTP over TLS [^4]
* Using Wireshark on 'Test System' start packet tracing on IF_LOGTS_FE interface - run following filter:
   * (TLS)
     > ip.addr == IF_LOGTS_FE_IP_ADDRESS and tls
   * (TCP)
     > ip.addr == IF_LOGTS_FE_IP_ADDRESS and http

### Test Body

#### Stimulus
Simulate basic call from SIP Test System to FE - run SIPp scenario by using following command on SIP Test System, example:
* (TCP transport)
  ```
  sudo sipp -t t1 -sf SIP_basic_call.xml IF_FE_SIPTS_IPv4:5060
  ```
* (TLS transport)
  ```
  sudo sipp -t l1 -tls_cert test_system.crt -tls_key test_system.key -sf SIP_basic_call.xml IF_FE_SIPTS_IPv4:5060
  ```

#### Response
Using traced packets on Wireshark from SIP and Logging Service Tests Systems verify:
* If FE sends HTTP POST to Logging Service Test System with signed JWS body containing:
  * "logEventType": "CallStartLogEvent"
  * "timestamp" with correct date-time format (f.e. 2020-03-10T11:00:01-05:00) and date-time match the time when SIP INVITE message has been received
  * "elementId" which has value with FQDN of FE
  * "agencyId" which has value with FQDN of an agency
  * "callId" which has value: `urn:emergency:uid:callid:1234567890:bcf.ng911.example` (if SIP_basic_call.xml used)
  * "incidentId" which has value: `urn:emergency:uid:incidentid:1234567890:bcf.ng911.example` (if SIP_basic_call.xml used)
  * "callIdSIP" which has value: `1234567890qwertyuiop@caller.example.com` (if SIP_basic_call.xml used)
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
* If FE sends HTTP POST to Logging Service Test System with signed JWS body containing:
  * "logEventType": "CallSignalingMessageLogEvent"
  * "timestamp" with correct date-time format (f.e. 2020-03-10T11:00:01-05:00) and date-time match the time when SIP INVITE message has been received
  * "elementId" which has value with FQDN of FE
  * "agencyId" which has value with FQDN of an agency
  * "callId" which has value: `urn:emergency:uid:callid:1234567890:bcf.ng911.example` (if SIP_basic_call.xml used)
  * "incidentId" which has value: `urn:emergency:uid:incidentid:1234567890:bcf.ng911.example` (if SIP_basic_call.xml used)
  * "callIdSIP" which has value: `1234567890qwertyuiop@caller.example.com` (if SIP_basic_call.xml used)
  * "direction" which has value: `incoming`
  * "text" which has string value containing SIP INVITE message received by FE from SIP Test System
  * "protocol" which has string value: `sip`
* If FE sends HTTP POST to Logging Service Test System with signed JWS body containing:
  * "logEventType": "CallEndLogEvent"
  * "timestamp" with correct date-time format (f.e. 2020-03-10T11:00:01-05:00) and date-time match SIP BYE message received by FE from SIP Test System
  * "elementId" which has value with FQDN of FE
  * "agencyId" which has value with FQDN of an agency
  * "callId" which has value: `urn:emergency:uid:callid:1234567890:bcf.ng911.example` (if SIP_basic_call.xml used)
  * "incidentId" which has value: `urn:emergency:uid:incidentid:1234567890:bcf.ng911.example` (if SIP_basic_call.xml used)
  * "callIdSIP" which has value: `1234567890qwertyuiop@caller.example.com` (if SIP_basic_call.xml used)
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
* If FE sends HTTP POST to Logging Service Test System with signed JWS body containing:
  * "logEventType": "CallSignalingMessageLogEvent"
  * "timestamp" with correct date-time format (f.e. 2020-03-10T11:00:01-05:00) and date-time match SIP BYE message received by FE from SIP Test System
  * "elementId" which has value with FQDN of FE
  * "agencyId" which has value with FQDN of an agency
  * "callId" which has value: `urn:emergency:uid:callid:1234567890:bcf.ng911.example` (if SIP_basic_call.xml used)
  * "incidentId" which has value: `urn:emergency:uid:incidentid:1234567890:bcf.ng911.example` (if SIP_basic_call.xml used)
  * "callIdSIP" which has value: `1234567890qwertyuiop@caller.example.com` (if SIP_basic_call.xml used)
  * "direction" which has value: `incoming`
  * "text" which has string value containing SIP BYE message received by FE from SIP Test System
  * "protocol" which has string value: `sip`

VERDICT:
* PASSED - if Logging Service responded as expected
* FAILED - any other cases


### Test Postamble
#### SIP Service Test System
* stop SIPp (if still running)
* stop Wireshark (if still running)
* archive all logs generated
* disconnect interfaces from IUT
* (TLS) remove certificates

#### Logging Service Test System
* stop Wireshark (if still running)
* archive all logs generated
* disconnect interfaces from IUT
* (TLS) remove certificates

#### Call Stateful Functional Element (FE)
* restore default configuration
* disconnect interfaces from Test System
* reconnect interfaces back to default

## Post-Test Conditions
### SIP/Logging Service Test System 
* Test tools stopped
* interfaces disconnected from IUT

### Call Stateful Functional Element (FE)
* device connected back to default
* device in normal operating state

## Sequence Diagram
<!--
[![](https://mermaid.ink/img/pako:eNrdVE1P4zAQ_SvWnKg2RU4KSe0DErsEUfHRioSVWOXiTYZg0djFcRCl6n_HSYFWrGCR4IQv9tjvPT_ZM7OAXBcIHPr9fqZyra5kyTNFSCWN0WY_t9rUnFyJaY2Z6kA13jaocjyQojSiasGrkYwmJMXakmReW6z6e3s_DmPebY_Ofo_SeA09jNvTE12WUpUkQXMnc9wkc3KUphMyGScp2folptPECmMdIb5DZXtrpXc0ng10SgGlZHz8KQeyVG5y8FOsa1Hi17ppz1-94OrtfIdNzbyV3dIzK7Vz0fsgdUjJuSO-w32L-trhX4PiZh2-3PwPebJ_kWz8NKriQxny8_JT6RGr4jsnx_9-CTyo0FRCFq6UFy01A3uNFWbA3bIQ5iaDTC0dTjRWJ3OVA7emQQ-aWSHsczED7yrdg5lQf7Rex1hI1wlOV72iaxkdBvgC7oH7Qbjth4yxaEAZG7Io8GAO3O0OaED9YMgYpczfCZcePHSyO9tBGIY0ikJ_MBzQ3cgDo5vy-unC5SMy615S?type=png)](https://mermaid.live/edit#pako:eNrdVE1P4zAQ_SvWnKg2RU4KSe0DErsEUfHRioSVWOXiTYZg0djFcRCl6n_HSYFWrGCR4IQv9tjvPT_ZM7OAXBcIHPr9fqZyra5kyTNFSCWN0WY_t9rUnFyJaY2Z6kA13jaocjyQojSiasGrkYwmJMXakmReW6z6e3s_DmPebY_Ofo_SeA09jNvTE12WUpUkQXMnc9wkc3KUphMyGScp2folptPECmMdIb5DZXtrpXc0ng10SgGlZHz8KQeyVG5y8FOsa1Hi17ppz1-94OrtfIdNzbyV3dIzK7Vz0fsgdUjJuSO-w32L-trhX4PiZh2-3PwPebJ_kWz8NKriQxny8_JT6RGr4jsnx_9-CTyo0FRCFq6UFy01A3uNFWbA3bIQ5iaDTC0dTjRWJ3OVA7emQQ-aWSHsczED7yrdg5lQf7Rex1hI1wlOV72iaxkdBvgC7oH7Qbjth4yxaEAZG7Io8GAO3O0OaED9YMgYpczfCZcePHSyO9tBGIY0ikJ_MBzQ3cgDo5vy-unC5SMy615S)
-->


![image](https://github.com/user-attachments/assets/5b0614d2-26e8-46a8-b0c4-bb18217095a4)

## Comments

Version:  010.3f.3.0.5

Date:     20250429

## Footnotes
[^1]: SIPp - tool for SIP packet simulations. Official documentation: https://sipp.sourceforge.net/doc/reference.html#Getting+SIPp
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^4]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518
