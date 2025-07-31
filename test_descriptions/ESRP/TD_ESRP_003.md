# Test Description: TD_ESRP_003
## Overview
### Summary
Default location handling

### Description
Test verifies for handling a default location:
- if original Geolocation header fields are preserved in SIP INVITE
- if original PIDF-LO body is preserved in SIP INVITE
- adding PIDF-LO default body and Geolocation header field when missing/garbled or unable to dereference
- if added Geolocation header field is the top-most entry in Geolocation field sequence


### SIP transport types
Test can be performed with 2 different SIP transport types. Steps describing actions for specific one are marked as following:
- (TLS transport) - used by default inside ESInet on production environment
- (TCP transport) - used in lab for testing purposes only if default TLS is not possible

### References
* Requirements : RQ_ESRP_024, RQ_ESRP_025, RQ_ESRP_026, RQ_ESRP_027
* Test Case    : TC_ESRP_003

### Requirements
IXIT config file for ESRP

## Configuration
### Implementation Under Test Interface Connections
<!-- Identify each of the FEs that are part of the configuration and how they are connected -->
* Test System O-BCF
  * IF_O-BCF_ESRP - connected to IF_ESRP_O-BCF
* ESRP
  * IF_ESRP_O-BCF - connected to Test System O-BCF IF_O-BCF_ESRP
  * IF_ESRP_T-BCF - connected to Test System T-BCF IF_T-BCF_ESRP
* Test System T-BCF
  * IF_T-BCF_ESRP - connected to IF_ESRP_T-BCF

### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* Test System O-BCF
  * IF_O-BCF_ESRP - Active
* ESRP
  * IF_ESRP_O-BCF - Active
  * IF_ESRP_T-BCF - Active
* Test System T-BCF
  * IF_T-BCF_ESRP - Active
 
### Connectivity Diagram
<!--
[![](https://mermaid.ink/img/pako:eNp1kd2KwjAQhV8lzHXzAr3Yi_UHCrus2FxJQMZmtEWTlDRBpPTdjUZsd8vmKvnmzJlDpofKKoIcjhd7rWp0nn1tpWHxFOv9D_9crPercrvhnJXFhnH-USSQam_lE4kH-qUUb4Ok7MLh5LCtmaDOs_LWedJs4jSbmzAZ9ad_rE0DzJ3GXP85TZOIWb-YJ4EMNDmNjYrf1j-wBF-TJgl5vCp0ZwnSDFGHwdvyZirIvQuUQWgVelo2GEdryI946SJt0eysHd-kGm_dd9rLcz0ZOBtO9Usx3AH5OIIb?type=png)](https://mermaid.live/edit#pako:eNp1kd2KwjAQhV8lzHXzAr3Yi_UHCrus2FxJQMZmtEWTlDRBpPTdjUZsd8vmKvnmzJlDpofKKoIcjhd7rWp0nn1tpWHxFOv9D_9crPercrvhnJXFhnH-USSQam_lE4kH-qUUb4Ok7MLh5LCtmaDOs_LWedJs4jSbmzAZ9ad_rE0DzJ3GXP85TZOIWb-YJ4EMNDmNjYrf1j-wBF-TJgl5vCp0ZwnSDFGHwdvyZirIvQuUQWgVelo2GEdryI946SJt0eysHd-kGm_dd9rLcz0ZOBtO9Usx3AH5OIIb)
-->

![image](https://github.com/user-attachments/assets/6bca46d5-b91a-4407-8d5e-f540a956bfe5)


## Pre-Test Conditions
### Test System O-BCF
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* No active calls
* (TLS transport) Test System has it's own certificate signed by PCA


### Test System T-BCF
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* No active calls
* (TLS transport) Test System has it's own certificate signed by PCA

### ESRP
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Default configuration is loaded
* Device is initialized with steps from IXIT config file
* Device configured to use Test System T-BCF as a next hop host
* Queue length and number of permitted dequeuers must be higher than 1
* Device is provisioned with policy allowing to subscribe for Queue and Service states from Test System
* Device is active
* Device is in normal operating state
* No active calls

## Test Sequence

### Test Preamble

#### Test System O-BCF
* Install SIPp by following steps from documentation[^1]
* Copy following XML scenario files to local storage:
  ```
  SIP_INVITE_from_OSP.xml
  SIP_INVITE_location_garbled_PIDF-LO_body.xml
  SIP_INVITE_incorrect_geolocation_for_dereference.xml
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
* (TLS transport) Configure Wireshark to decode SIP over TLS packets from Test System and ESRP as well[^3]
* Using Wireshark on 'Test System' start packet tracing on IF_O-BCF_ESRP interface - run following filter:
   * (TLS transport)
     > ip.addr == IF_O-BCF_ESRP_IP_ADDRESS and tls
   * (TCP transport)
     > ip.addr == IF_O-BCF_ESRP_IP_ADDRESS and sip


#### Test System T-BCF
* Install SIPp by following steps from documentation[^1]
* Copy following XML scenario files to local storage:
  ```
  SIP_INVITE_RECEIVE.xml
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
* (TLS transport) Configure Wireshark to decode SIP over TLS packets from Test System and ESRP as well[^3]
* Using Wireshark on 'Test System' start packet tracing on IF_T-BCF_ESRP interface - run following filter:
   * (TLS transport)
     > ip.addr == IF_T-BCF_ESRP_IP_ADDRESS and tls
   * (TCP transport)
     > ip.addr == IF_T-BCF_ESRP_IP_ADDRESS and sip

### Test Body

#### Variations
1. SIP_INVITE_EMERGENCY_SINGLE.xml (SIP INVITE without "Geolocation" header fields and PIDF-LO body)
2. SIP_INVITE_location_garbled_PIDF-LO_body.xml
3. SIP_INVITE_incorrect_geolocation_for_dereference.xml - with `Geolocation` configured to any incorrect address, for example: `<https://192.168.0.1/incorrect>`

#### Stimulus
Send SIP packet to ESRP using scenario file for tested variation - run following SIPp command on Test System O-BCF, example:
* (TCP transport)
 ```
 sudo sipp -t t1 -sf SIP_INVITE_EMERGENCY_SINGLE.xml -i IF_O-BCF_ESRP_IP_ADDRESS:5060 IF_ESRP_O-BCF_IP_ADDRESS:5060 -max_recv_loops 1 -m 1
 ```
* (TLS transport)
 ```
 sudo sipp -t l1 -tls_cert PCA-cacert.pem -tls_key PCA-cakey.pem -sf SIP_INVITE_EMERGENCY_SINGLE.xml -i IF_O-BCF_ESRP_IP_ADDRESS:5060 IF_ESRP_O-BCF_IP_ADDRESS:5060 -max_recv_loops 1 -m 1
 ```

#### Response
Variation 1
* verify if ESRP sends SIP INVITE to Test System T-BCF
* verify if SIP INVITE has added Geolocation header field pointing to PIDF-LO xml body, for example:
```
Geolocation: <cid:default@test.com>
```
* verify if SIP INVITE has added PIDF-LO xml body with default location properly placed in message, for example:
```
Content-Type: application/pidf+xml
Content-ID: <default@test.com>

PIDF-LO xml body
```

Variation 2
* verify if ESRP sends SIP INVITE to Test System T-BCF
* verify if SIP INVITE has added Geolocation header field pointing to PIDF-LO xml body, for example:
```
Geolocation: <cid:default@test.com>
```
* verify if added Geolocation header field is the top-most entry in Geolocation field sequence
* verify if original Geolocation header field was not removed
* verify if SIP INVITE has added PIDF-LO xml body with default location properly placed in message, for example:
```
Content-Type: application/pidf+xml
Content-ID: <default@test.com>

PIDF-LO xml body
```
* verify if original PIDF-LO body was not removed

Variation 3
* verify if ESRP sends SIP INVITE to Test System T-BCF
* verify if SIP INVITE has added Geolocation header field pointing to PIDF-LO xml body, for example:
```
Geolocation: <cid:default@test.com>
```
* verify if added Geolocation header field is the top-most entry in Geolocation field sequence
* verify if original Geolocation header field was not removed
* verify if SIP INVITE has added PIDF-LO xml body with default location properly placed in message, for example:
```
Content-Type: application/pidf+xml
Content-ID: <default@test.com>

PIDF-LO xml body
```

VERDICT:
* PASSED - if all checks passed for variation
* FAILED - all other cases
<!--
* INCONCLUSIVE - 
* ERROR - 
-->

### Test Postamble
#### Test System O-BCF
* stop Sipp process (if still running)
* archive all logs generated
* stop Wireshark (if still running)
* remove all scenario files
* disconnect interfaces from ESRP
* (TLS transport) remove certificates

#### Test System ECRF-LVF
* stop simple_http_server.py
* archive all logs generated
* stop Wireshark (if still running)
* remove all scenario files
* disconnect interfaces from ESRP
* (TLS transport) remove certificates

#### Test System T-BCF
* stop Sipp process (if still running)
* archive all logs generated
* stop Wireshark (if still running)
* remove all scenario files
* disconnect interfaces from ESRP
* (TLS transport) remove certificates

#### ESRP
* disconnect interfaces from Test Systems
* reconnect interfaces back to default
* restore previous configuration

## Post-Test Conditions
### Test System O-BCF/ECRF-LVF/T-BCF
* Test tools stopped
* interfaces disconnected from ESRP

### ESRP
* device connected back to default
* device in normal operating state

## Sequence Diagram
<!--
[![](https://mermaid.ink/img/pako:eNpNkM0KAjEMhF-l5Or2BXoQ_IU9-IO7eJBeShvXom01bQ8ivrvbVdGcEvINzMwDdDAIAjjn0uvgj7YT0jPmLFGgiU6BomBHdYko_QBFvGX0GudWdaRcgd_TYkysuceEjm34dLbk4_Fo0ey2gjX1ltXrfd0ufnj5FOJf1hbZPw4VOCSnrOk9PopYQjqhQwmiX42iswTpnz2ncgrN3WsQiTJWkK9Gpa9LEEOECq7KH0L43WhsH3H1LmHoogIKuTt9iOcL4zNcwg?type=png)](https://mermaid.live/edit#pako:eNpNkM0KAjEMhF-l5Or2BXoQ_IU9-IO7eJBeShvXom01bQ8ivrvbVdGcEvINzMwDdDAIAjjn0uvgj7YT0jPmLFGgiU6BomBHdYko_QBFvGX0GudWdaRcgd_TYkysuceEjm34dLbk4_Fo0ey2gjX1ltXrfd0ufnj5FOJf1hbZPw4VOCSnrOk9PopYQjqhQwmiX42iswTpnz2ncgrN3WsQiTJWkK9Gpa9LEEOECq7KH0L43WhsH3H1LmHoogIKuTt9iOcL4zNcwg)
-->

![image](https://github.com/user-attachments/assets/89457554-44e1-42c2-945d-0e5730290b8c)


## Comments

Version:  010.3d.3.0.8

Date:     20250425

## Footnotes
[^1]: SIPp - tool for SIP packet simulations. Official documentation: https://sipp.sourceforge.net/doc/reference.html#Getting+SIPp
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt SIP over TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
