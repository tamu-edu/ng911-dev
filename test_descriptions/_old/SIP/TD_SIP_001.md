# Test Description: TD_SIP_001
## Overview
### Summary
Incorrect SIP calls handling


### Description
This test checks handling of incoming calls that do not follow SIP standards. It is applicable to all SIP Functional Elements (FE).

Test description:
* 'Test System Sender' simulates different emergency SIP INVITE packets heading to FE
* FE should handle the call accordingly to it's function
* If FE routes the calls to another ones within ESInet, then 'Test System Receiver' should be attached to it's output interface

### SIP transport types
Test can be performed with 2 different SIP transport types. Steps describing actions for specific one are marked as following:
- (TLS transport) - used by default inside ESInet on production environment
- (TCP transport) - used in lab for testing purposes only if default TLS is not possible

### References
* Requirements : O-BCF_2
* Test Purpose : TP_BCF_002
* Test Case    : 


## Configuration
### Implementation Under Test Interface Connections
<!-- Identify each of the FEs that are part of the configuration and how they are connected -->
* Test System Sender
  * IF_SENDER_FE-INPUT - connected to input interface of FE for SIP packets
* Functional Element
  * IF_FE-INPUT_SENDER - connected to IF_SENDER_FE-INPUT
  * IF_FE-OUTPUT_RECEIVER - connected to IF_RECEIVER_FE-OUTPUT (if FE routes SIP packets further)
* Test System Receiver
  * IF_RECEIVER_FE-OUTPUT - connected to output interface of FE for SIP packets

### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* Test System Sender
  * IF_SENDER_FE - Active
* Functional Element
  * IF_FE_SENDER - Active
  * IF_FE_RECEIVER - Monitor
* Test System Receiver
  * IF_RECEIVER_FE - Monitor

 
### Connectivity Diagram
[![](https://mermaid.ink/img/pako:eNp1kcFuwjAMhl8l8rndA_TAZaQS0uCQThxQJOQ1hlaQpEoTEEK8-zwKAxWRU_z7i_07PkPtDUEBm70_1g2GKL6UdoLPrFxXcjGVal3KPJ9wWMqb8g-wouSnnC2lyj-uzD3k1ED16WcbsGvEN_VRVKc-khUVOUNhAMa9BpWB0ft75tH62cyroXd1nn0oqqk9jJy8jMA1IANLwWJr-K_Of7KG2JAlDQVfDYadBu0uzGGKvjq5GooYEmWQOoORpi1yewvFBvc9qx26lfePmEwbfZgPy7juJIPg07a5EZdfFbyCJQ?type=png)](https://mermaid.live/edit#pako:eNp1kcFuwjAMhl8l8rndA_TAZaQS0uCQThxQJOQ1hlaQpEoTEEK8-zwKAxWRU_z7i_07PkPtDUEBm70_1g2GKL6UdoLPrFxXcjGVal3KPJ9wWMqb8g-wouSnnC2lyj-uzD3k1ED16WcbsGvEN_VRVKc-khUVOUNhAMa9BpWB0ft75tH62cyroXd1nn0oqqk9jJy8jMA1IANLwWJr-K_Of7KG2JAlDQVfDYadBu0uzGGKvjq5GooYEmWQOoORpi1yewvFBvc9qx26lfePmEwbfZgPy7juJIPg07a5EZdfFbyCJQ)

## Pre-Test Conditions
### Test System Sender
<!-- Where FE# is the FE abbreviation (LIS, BCF, ESRP, ECRF, ...) -->
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* No active calls
* (TLS transport) Test System has it's own certificate signed by PCA

### Test System Receiver
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* No active calls
* (TLS transport) Test System has it's own certificate signed by PCA

* Installed SIPp by following steps from documentation[^1]
* Prepared following XML scenario files:
  > SIP_INVITE_INCORRECT_EMERGENCY_SINGLE_1.xml
  > SIP_INVITE_INCORRECT_EMERGENCY_SINGLE_2.xml
  > SIP_INVITE_INCORRECT_EMERGENCY_SINGLE_3.xml

### Test System Receiver
* Installed SIPp by following steps from documentation[^1]
* Preapared SIP TLS certificate and private key files used to encrypt SIP packets within ESInet
* Prepared following XML file:
  > SIP_INVITE_RECEIVE.xml
* Installed Wireshark[^2]
* Wireshark configured to decode SIP over TLS packets[^3]


## Test Sequence
### Test Preamble
#### Test System Sender
* Install SIPp by following steps from documentation[^1]
* Copy following XML scenario files to local storage:
  ```
  SIP_INVITE_INCORRECT_EMERGENCY_SINGLE_1.xml
  SIP_INVITE_INCORRECT_EMERGENCY_SINGLE_2.xml
  SIP_INVITE_INCORRECT_EMERGENCY_SINGLE_3.xml
  ```
* Install Wireshark[^2]
* (TLS transport) Copy to local storage PCA-signed TLS certificate and private key files:
  ```
  cacert.pem
  cakey.pem
  ```
* (TLS transport) Copy to local storage TLS certificate and private key files used by FE:
  ```
  FE-cacert.pem
  FE-cakey.pem
  ```
* (TLS transport) Configure Wireshark to decode SIP over TLS packets from Test System and FE as well[^3]
* Using Wireshark on 'Test System' start packet tracing on IF_SENDER_FE interface - run following filter:
   * (TLS transport)
     > ip.addr == IF_SENDER_FE_IP_ADDRESS and tls
   * (TCP transport)
     > ip.addr == IF_SENDER_FE_IP_ADDRESS and sip

#### Test System Receiver
* Install SIPp by following steps from documentation[^1]
* Copy following XML scenario files to local storage:
  ```
  SIP_INVITE_RECEIVE.xml
  ```
* Install Wireshark[^2]
* (TLS transport) Copy to local storage PCA-signed TLS certificate and private key files:
  ```
  cacert.pem
  cakey.pem
  ```
* (TLS transport) Copy to local storage TLS certificate and private key files used by FE:
  ```
  FE-cacert.pem
  FE-cakey.pem
  ```
* (TLS transport) Configure Wireshark to decode SIP over TLS packets from Test System and FE as well[^3]
* Using Wireshark on 'Test System' start packet tracing on IF_RECEIVER_FE interface - run following filter:
   * (TLS transport)
     > ip.addr == IF_RECEIVER_FE_IP_ADDRESS and tls
   * (TCP transport)
     > ip.addr == IF_RECEIVER_FE_IP_ADDRESS and sip
* Prepare Test System to receive SIP INVITE, run SIPp scenario:
   * (TLS transport)
     > sudo sipp -t l1 -sf SIP_INVITE_RECEIVE.xml -i IF_RECEIVER_FE_IP_ADDRESS:5061
   * (TCP transport)
     > sudo sipp -t t1 -sf SIP_INVITE_RECEIVE.xml -i IF_RECEIVER_FE_IP_ADDRESS:5060


### Test Body
#### Variations
1. SIP_INVITE_INCORRECT_EMERGENCY_SINGLE_1.xml
2. SIP_INVITE_INCORRECT_EMERGENCY_SINGLE_2.xml
3. SIP_INVITE_INCORRECT_EMERGENCY_SINGLE_3.xml

#### Stimulus
Send SIP packet to FE using scenario file for tested variation - run following SIPp command on Test System SENDER, example:
* (TCP transport)
 ```
 sudo sipp -t t1 -sf SIP_INVITE_INCORRECT_EMERGENCY_SINGLE_1.xml IF_SENDER_FE_IP_ADDRESS:5060
 ```
* (TLS transport)
 ```
 sudo sipp -t l1 -sf SIP_INVITE_INCORRECT_EMERGENCY_SINGLE_1.xml IF_SENDER_FE_IP_ADDRESS:5060
 ```

#### Response
Variations 1-3
* SIP INVITE sent to next hop FE has header fields fixed
* 'To:' header field should be rewritten to following:
  > To: urn:service:sos

VERDICT:
* PASSED - if all checks passed for variation
* FAILED - all other cases

### Test Postamble
#### Test System Sender
* stop Sipp process (if still running)
* archive all logs generated
* stop Wireshark (if still running)
* remove all scenario files
* disconnect interfaces from ESRP
* (TLS transport) remove certificates

#### Test System Receiver
* stop Sipp process (if still running)
* archive all logs generated
* stop Wireshark (if still running)
* remove all scenario files
* disconnect interfaces from ESRP
* (TLS transport) remove certificates


## Post-Test Conditions 
### Test System Sender
* Test tools stopped
* interfaces disconnected from FE

### Functional Element
* device connected back to default
* device in normal operating state

### Test System Receiver
* Test tools stopped
* interfaces disconnected from FE

## Sequence Diagram
[![](https://mermaid.ink/img/pako:eNptkLFqAzEQRH9l2TanH1BhCMSBK2xCzqQIaoS0PgufVs5KChjjf4_unBAX7naWNwMzF3TJE2pUShl2ifdh1IYBYhBJ8uxKkqxhb6dMhhco01cldvQS7Cg2zjDAjnKB4ZwLRRiIPYlarZ6G_g1eK7sSEtsJ1hNF4qJh_vfbj363vrkfc6pF3Oe-k6PwTXLvxw4jSbTBtw6XOc1gOTS7Qd1Ob-Vo0PC1cbaWNJzZoS5SqcN68rb8tUC9VOzwZPkzpX9NPrQJNreRlq06lFTHwy9x_QFAj2xl?type=png)](https://mermaid.live/edit#pako:eNptkLFqAzEQRH9l2TanH1BhCMSBK2xCzqQIaoS0PgufVs5KChjjf4_unBAX7naWNwMzF3TJE2pUShl2ifdh1IYBYhBJ8uxKkqxhb6dMhhco01cldvQS7Cg2zjDAjnKB4ZwLRRiIPYlarZ6G_g1eK7sSEtsJ1hNF4qJh_vfbj363vrkfc6pF3Oe-k6PwTXLvxw4jSbTBtw6XOc1gOTS7Qd1Ob-Vo0PC1cbaWNJzZoS5SqcN68rb8tUC9VOzwZPkzpX9NPrQJNreRlq06lFTHwy9x_QFAj2xl)
## Comments

Version:  010.3d.2.1.2

Date:     2024.09.26


## Footnotes
[^1]: SIPp - tool for SIP packet simulations. Official documentation: https://sipp.sourceforge.net/doc/reference.html#Getting+SIPp
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt SIP over TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream

