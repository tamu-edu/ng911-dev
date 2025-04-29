# Test Description: TD_ESRP_004
## Overview
### Summary
Processing of SIP OPTIONS and SIP CANCEL

### Description
Test verifies processing of SIP OPTIONS, and SIP CANCEL as per RFC 3261


### SIP transport types
Test can be performed with 2 different SIP transport types. Steps describing actions for specific one are marked as following:
- (TLS transport) - used by default inside ESInet on production environment
- (TCP transport) - used in lab for testing purposes only if default TLS is not possible

### References
* Requirements : RQ_ESRP_033, RQ_ESRP_034
* Test Case    : 

### Requirements
IXIT config file for ESRP

## Configuration
### Implementation Under Test Interface Connections
<!-- Identify each of the FEs that are part of the configuration and how they are connected -->
* Test System U-ESRP (upstream ESRP)
  * IF_U-ESRP_ESRP - connected to IF_ESRP_U-ESRP
* ESRP
  * IF_ESRP_U-ESRP - connected to Test System U-ESRP IF_U-ESRP_ESRP
  * IF_ESRP_T-BCF - connected to Test System T-BCF IF_T-BCF_ESRP
* Test System T-BCF
  * IF_T-BCF_ESRP - connected to IF_ESRP_T-BCF


### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* Test System U-ESRP
  * IF_U-ESRP_ESRP - Active
* ESRP
  * IF_ESRP_U-ESRP - Active
  * IF_ESRP_T-BCF - Monitor
* Test System T-BCF
  * IF_T-BCF_ESRP - Monitor
 
 
### Connectivity Diagram
<!--
[![](https://mermaid.ink/img/pako:eNp1UdsKwjAM_ZWS5-0HhvjgDQQFcfoihRHX6Ia2HV2LiPjvxs3LcJiH0Jyec5I2N8itIkjgcLaXvEDnxWItjeCYz7JtPE3Xq-yZBjHHkLEGaS8-vAbbxKPx7M1qiuxLqsP-6LAqxIZqL9Jr7UmLrku_Y4uTUT8OPU1vot5U_6y6w3SIL_3vG1gPEWhyGkvFX3Z7whJ8QZokJHxU6E4SpLkzD4O36dXkkHgXKIJQKfQ0KZFba0gOeK4ZrdDsrP3WpEpv3bLdSbOaCJwNx-LFuD8AwxiCSA?type=png)](https://mermaid.live/edit#pako:eNp1UdsKwjAM_ZWS5-0HhvjgDQQFcfoihRHX6Ia2HV2LiPjvxs3LcJiH0Jyec5I2N8itIkjgcLaXvEDnxWItjeCYz7JtPE3Xq-yZBjHHkLEGaS8-vAbbxKPx7M1qiuxLqsP-6LAqxIZqL9Jr7UmLrku_Y4uTUT8OPU1vot5U_6y6w3SIL_3vG1gPEWhyGkvFX3Z7whJ8QZokJHxU6E4SpLkzD4O36dXkkHgXKIJQKfQ0KZFba0gOeK4ZrdDsrP3WpEpv3bLdSbOaCJwNx-LFuD8AwxiCSA)
-->

![image](https://github.com/user-attachments/assets/5011ad48-6c86-49fa-993a-fea68dbf2788)


## Pre-Test Conditions
### Test System U-ESRP
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* No active calls
* (TLS transport) Test System has it's own certificate signed by PCA

### ESRP
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* Device is in normal operating state
* No active calls
* Logging enabled

### Test System T-BCF
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* No active calls
* (TLS transport) Test System has it's own certificate signed by PCA

## Test Sequence

### Test Preamble

#### Test System U-ESRP
* Install SIPp by following steps from documentation[^1]
* Copy following XML scenario files to local storage:
  ```
  SIP_OPTIONS.xml
  SIP_INVITE_with_CANCEL.xml
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
* Using Wireshark on 'Test System' start packet tracing on IF_U-ESRP_ESRP interface - run following filter:
   * (TLS transport)
     > ip.addr == IF_U-ESRP_ESRP_IP_ADDRESS and tls
   * (TCP transport)
     > ip.addr == IF_U-ESRP_ESRP_IP_ADDRESS and sip

#### Test System T-BCF
* Install SIPp by following steps from documentation[^1]
* Copy following XML scenario files to local storage:
  ```
  SIP_RECEIVE.xml
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
* Using Wireshark on 'Test System' start packet tracing on IF_U-ESRP_ESRP interface - run following filter:
   * (TLS transport)
     > ip.addr == IF_T-BCF_ESRP_IP_ADDRESS and tls
   * (TCP transport)
     > ip.addr == IF_T-BCF_ESRP_IP_ADDRESS and sip

### Test Body

#### Variations
1. SIP_OPTIONS.xml
2. SIP_INVITE_with_CANCEL.xml

#### Stimulus
Send SIP packet to ESRP using scenario file for tested variation - run following SIPp command on Test System U-ESRP, example:
* (TCP transport
  ```
  sudo sipp -t t1 -sf SIP_OPTIONS.xml IF_U-ESRP_ESRP_IP_ADDRESS:5060
  ```
* (TLS transport)
  ```
  sudo sipp -t l1 -sf SIP_OPTIONS.xml IF_U-ESRP_ESRP_IP_ADDRESS:5060
  ```

#### Response
Variation 1
* verify if ESRP responds with SIP 200 OK including it's capabilities

Variation 2
* verify if ESRP responds with 200 OK to Test System U-ESRP
* verify if ESRP stops processing SIP INVITE which must not be sent further to Test System T-BCF

VERDICT:
* PASSED - if all checks passed for variation
* FAILED - all other cases
<!--
* INCONCLUSIVE - 
* ERROR - 
-->

### Test Postamble
#### Test System U-ESRP
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

#### Test System T-BCF
* stop Sipp process (if still running)
* archive all logs generated
* stop Wireshark (if still running)
* remove all scenario files
* disconnect interfaces from ESRP
* (TLS transport) remove certificates

## Post-Test Conditions
### Test System U-ESRP
* Test tools stopped
* interfaces disconnected from ESRP

### ESRP
* device connected back to default
* device in normal operating state

### Test System T-BCF
* Test tools stopped
* interfaces disconnected from ESRP

## Sequence Diagram
Variant 1
<!--
[![](https://mermaid.ink/img/pako:eNplkD-LAjEQxb9KmNYNLJYpBEELOe52uWgjaUIyrsFLsjdJCpH97u6fE4ubZmbg9-C99wATLYIAzrkKJoaL64QKjHlHFGlrcqQk2EX_JFRhhhL-FgwGd053pP0EL3PElJm8p4yenfhefrd8s1lNWzB5aFnTHg_Nl3wLXsh_4SJY1zVrPqACj-S1s6PNx6RWkK_oUYEYT6vppkCFYeR0yVHegwGRqWAFpbc6v4yCmFNU0OtwjvH9o3Vjys-lh7mOCiiW7vpHDE_qrF2B?type=png)](https://mermaid.live/edit#pako:eNplkD-LAjEQxb9KmNYNLJYpBEELOe52uWgjaUIyrsFLsjdJCpH97u6fE4ubZmbg9-C99wATLYIAzrkKJoaL64QKjHlHFGlrcqQk2EX_JFRhhhL-FgwGd053pP0EL3PElJm8p4yenfhefrd8s1lNWzB5aFnTHg_Nl3wLXsh_4SJY1zVrPqACj-S1s6PNx6RWkK_oUYEYT6vppkCFYeR0yVHegwGRqWAFpbc6v4yCmFNU0OtwjvH9o3Vjys-lh7mOCiiW7vpHDE_qrF2B)
-->

![image](https://github.com/user-attachments/assets/7d4bb746-ccee-4d55-97f8-c8f74523d29b)


Variant 2
<!--
[![](https://mermaid.ink/img/pako:eNqN0D2LAjEQBuC_EqZ1A2KZQhDdYrk7FVctJE1IxjVoEp0khYj_3f04sbjmpskEnine9wE6GAQBnHPpdfBH2wjpGXOWKNBMp0BRsKO6RJS-RxFvGb3GhVUNKdfhYbYYE6vvMaFjO17WmzWfTkfdK1hdrVm13Ffb8v9-PlvOy--Pf4u_d4OfjMds9QUFOCSnrGlTPbprCemEDiWIdjWKzhKkf7ZO5RTqu9cgEmUsIF-NSu9cIPrQBVyVP4Tw-aOxbSk_Q219ewVQyM3pVzxfqFdqKQ?type=png)](https://mermaid.live/edit#pako:eNqN0D2LAjEQBuC_EqZ1A2KZQhDdYrk7FVctJE1IxjVoEp0khYj_3f04sbjmpskEnine9wE6GAQBnHPpdfBH2wjpGXOWKNBMp0BRsKO6RJS-RxFvGb3GhVUNKdfhYbYYE6vvMaFjO17WmzWfTkfdK1hdrVm13Ffb8v9-PlvOy--Pf4u_d4OfjMds9QUFOCSnrGlTPbprCemEDiWIdjWKzhKkf7ZO5RTqu9cgEmUsIF-NSu9cIPrQBVyVP4Tw-aOxbSk_Q219ewVQyM3pVzxfqFdqKQ)
-->

![image](https://github.com/user-attachments/assets/9e44283b-a962-41c1-8363-9c4e2f0e1690)


## Comments

Version:  010.3d.3.0.3

Date:     20250428

## Footnotes
[^1]: SIPp - tool for SIP packet simulations. Official documentation: https://sipp.sourceforge.net/doc/reference.html#Getting+SIPp
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt SIP over TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
