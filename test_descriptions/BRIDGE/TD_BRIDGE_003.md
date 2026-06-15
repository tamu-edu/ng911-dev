# Test Description: TD_BRIDGE_003

## Overview
### Summary
Handling multi-party aware and unaware endpoints in the same session

### Description
This test checks if Bridge is capable of handling multi-party aware and multi-party unaware endpoints in the same session

### References
* Requirements : RQ_BRG_042
* Test Case    : 

### Requirements
IXIT config file for BRIDGE

### SIP transport types
Test can be performed with 2 different SIP transport types. Steps describing actions for specific one are marked as following:
- (TLS transport) - should be used by default
- (TCP transport) - used in lab for testing purposes only if default TLS is not possible

## Configuration
### Implementation Under Test Interface Connections
<!-- Identify each of the FEs that are part of the configuration and how they are connected -->
* Test System OSP
  * IF_OSP_BCF - connected to IF_BCF_OSP
  * IF_OSP_CHFE - connected to IF_CHFE_OSP
  * IF_OSP_BRIDGE - connected to IF_BRIDGE_OSP
* Test System BCF
  * IF_BCF_OSP - connected to IF_OSP_BCF
  * IF_BCF_ESRP - connected to IF_ESRP_BCF
* Test System ESRP
  * IF_ESRP_BCF - connected to IF_BCF_ESRP
  * IF_ESRP_CHFE - connected to IF_CHFE_ESRP
* BRIDGE
  * IF_BRIDGE_CHFE - connected to IF_CHFE_BRIDGE
  * IF_BRIDGE_OSP - connected to IF_OSP_BRIDGE
* Test System CHFE (Transfer-from) 
  * IF_CHFE_OSP - connected to IF_OSP_CHFE
  * IF_CHFE_ESRP - connected to IF_ESRP_CHFE
  * IF_CHFE_BRIDGE - connected to IF_BRIDGE_CHFE
  * IF_CHFE_TS-CA - connected to IF_TS-CA_CHFE
* CONFERENCE APP
  * IF_TS-CA_CHFE - connected to IF_CHFE_TS-CA


### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* Test System OSP
  * IF_OSP_BCF - Active
  * IF_OSP_CHFE - Active
  * IF_OSP_BRIDGE - Active
* Test System BCF
  * IF_BCF_OSP - Active
  * IF_BCF_ESRP - Active
* Test System ESRP
  * IF_ESRP_BCF - Active
  * IF_ESRP_CHFE - Active
* BRIDGE
  * IF_BRIDGE_CHFE - Active
  * IF_BRIDGE_OSP - Active
* Test System CHFE (Transfer-from)
  * IF_CHFE_OSP - Active
  * IF_CHFE_ESRP - Active
  * IF_CHFE_BRIDGE - Active
  * IF_CHFE_TS-CA - Active
* CONFERENCE APP
  * IF_TS-CA_CHFE - Active

### Connectivity Diagram
<!--
https://mermaid.live/edit#pako:eNqNVNtugkAQ_RUyz2qAVW5pmljU1qRNjfjUkJgtrGIqLFmWtNb4711WRC6mkaeZs2fOnJ0he4SAhgQc2OzpdxBhxpXXpZ8o4pvP1u_eYv3kzh76_UeRiahAqtMin3rLRXlchAVWnUvAfZlNS0IRSrCh3ybUO0hg5fXdccmQsYSvLpbzyfO0I3OG2ywhXpLk1UrOmZXln1uG00hZkYwr3iHjJFYqN82JdLCrpTqx5oEk4T9t2pKNUbfGfY_elVffRbtLtaB7JDs3bG6rDna6dzbS2W_NQcvDjbLaym_hladbco0r0WRDGEkCMk7ThlL7PxNK0IMt24XgcJaTHsSExbhI4VhQfOARiYkPjghDzL588JOTqElx8kFpfCljNN9G4GzwPhNZnoaYk8kOC29xhQpHIWEuzRMODrJ1KQLOEX7A0VRrgCwVoaFhI81WDdSDAzjGaGCOTH1oIts2kalppx78yrbqwDIM3ULqyNZ0VTMtIYdzTr1DElxMkXDHKXs7PwTyPTj9AeRbKcs
-->

![image](../_assets/BRIDGE/TD_BRIDGE_003_Connectivity_Diagram.png)


## Pre-Test Conditions
### Test System OSP, Test System BCF, Test System ESRP, Test System CHFE, CONFERENCE APP
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* ng911 repository cloned to local storage
* (TLS) Generated own PCA-signed certificate and private key files (test_system.crt, test_system.key)
* (TLS) Certificate and key used by BRIDGE copied to local storage
* (TLS) PCA certificate copied to local storage

### BRIDGE
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* IUT is active
* IUT is in normal operating state
* Default configuration is loaded
* IUT is initialized using IXIT config file
  
## Test Sequence

### Test Preamble

#### Test System OSP, Test System BCF, Test System ESRP, Test System CHFE, CONFERENCE APP
* Install SIPp by following steps from documentation[^1]
* Install Wireshark[^2]
* (TLS v1.2) Configure Wireshark to decode SIP over TLS, use Test Systems and IUT certificate keys [^3]
* (TLS v1.3) Configure logging of session keys and configure Wireshark to decode SIP over TLS [^4]
* Using Wireshark, start packet tracing on all local interfaces - run following filter (e.g. for IF_OSP_BRIDGE):
   * (TLS transport)
     > ip.addr == IF_OSP_BRIDGE_IP_ADDRESS and tls
   * (TCP transport)
     > ip.addr == IF_OSP_BRIDGE_IP_ADDRESS and sip

#### CONFERENCE APP

Prepare to receive call and redirect Test System CHFE (Transfer-from):
  * (TLS transport)
    >   sudo sipp -t l1 --tls_cert cert.crt --tls_key cert.key -sf SIP_INVITE_RECEIVE_302_Moved_Contact.xml \
    > -i IF_TS-CA_CHFE -p 5061 \
  -set conference_id CONFERENCE_ID_VALUE \
  -set BRIDGE_IP IF_BRIDGE_CHFE_IP \
  -set BRIDGE_port 5061 \
  -max_socket 1000 -m 1 IF_TS-CA_CHFE_IP_ADDRESS:5061
  * (TCP transport)
    >   sudo sipp -t t1 -sf SIP_INVITE_RECEIVE_302_Moved_Contact.xml \
    > -i IF_TS-CA_CHFE -p 5060 \
  -set conference_id CONFERENCE_ID_VALUE \
  -set BRIDGE_IP IF_BRIDGE_CHFE_IP \
  -set BRIDGE_port 5060 \
  -max_socket 1000 -m 1 IF_TS-CA_CHFE_IP_ADDRESS:5061

#### Test System BCF

Run custom SIP service using following command (replace names in {} with values):
  * (TLS transport)
    >   sudo python3 test_suite/services/stub_server/sip_service/sip_entry.py \
  --scenario test_suite/test_files/SIPp_scenarios/sip_service/CHFE_006/BCF_CHFE_006_var2.xml \
  --scenario-type auto --bind-ip {IF_BCF_OSP_IP} --bind-port 5061 \
  --remote-ip {IF_ESRP_BCF_IP} --remote-port 5061 \
  --tls-cert {BCF_CERT_FILE_PATH} --tls_key {BCF_KEY_FILE_PATH} \
  --tls-ca {PCA_CERT_FILE_PATH} \
  --set IF_OSP_BCF {IF_OSP_BCF_IP} \
  --set IF_ESRP_BCF {IF_ESRP_BCF_IP} \
  --protocol TLS
  * (TCP transport)
    >   sudo python3 test_suite/services/stub_server/sip_service/sip_entry.py \
  --scenario test_suite/test_files/SIPp_scenarios/sip_service/CHFE_006/BCF_CHFE_006_var2.xml \
  --scenario-type auto --bind-ip {IF_BCF_OSP_IP} --bind-port 5060 \
  --remote-ip {IF_ESRP_BCF_IP} --remote-port 5060 \
  --set IF_OSP_BCF {IF_OSP_BCF_IP} \
  --set IF_ESRP_BCF {IF_ESRP_BCF_IP} \
  --protocol TCP

#### Test System ESRP

Run custom SIP service using following command (replace names in {} with values):
  * (TLS transport)
    >   sudo python3 test_suite/services/stub_server/sip_service/sip_entry.py \
  --scenario test_suite/test_files/SIPp_scenarios/sip_service/FEs/ESRP_simple_call.xml \
  --scenario-type auto --bind-ip {IF_ESRP_BCF_IP} --bind-port 5061 \
  --remote-ip {IF_CHFE_ESRP_IP} --remote-port 5061 \
  --tls-cert {ESRP_CERT_FILE_PATH} --tls_key {ESRP_KEY_FILE_PATH} \
  --tls-ca {PCA_CERT_FILE_PATH} \
  --set IF_BCF_ESRP {IF_BCF_ESRP_IP} \
  --set IF_CHFE_ESRP_BCF {IF_CHFE_ESRP_IP} \
  --protocol TLS
  * (TCP transport)
    >   sudo python3 test_suite/services/stub_server/sip_service/sip_entry.py \
  --scenario test_suite/test_files/SIPp_scenarios/sip_service/FEs/ESRP_simple_call.xml \
  --scenario-type auto --bind-ip {IF_ESRP_BCF_IP} --bind-port 5060 \
  --remote-ip {IF_CHFE_ESRP_IP} --remote-port 5060 \
  --set IF_BCF_ESRP {IF_BCF_ESRP_IP} \
  --set IF_CHFE_ESRP_BCF {IF_CHFE_ESRP_IP} \
  --protocol TCP

#### Test System CHFE

Run custom SIP service using following command (replace names in {} with values):
  * (TLS transport)
    >   sudo python3 test_suite/services/stub_server/sip_service/sip_entry.py \
  --scenario test_suite/test_files/SIPp_scenarios/sip_service/BRIDGE_003/CHFE_BRIDGE_003.xml \
  --scenario-type auto --bind-ip {IF_CHFE_ESRP_IP} --bind-port 5061 \
  --remote-ip {IF_CHFE_BRIDGE_IP} --remote-port 5061 \
  --tls-cert {CHFE_CERT_FILE_PATH} --tls_key {CHFE_KEY_FILE_PATH} \
  --tls-ca {PCA_CERT_FILE_PATH} \
  --set conference_id {CONFERENCE_ID} \
  --set IF_OSP_CHFE {IF_OSP_CHFE_IP} \
  --set IF_CHFE_OSP {IF_CHFE_OSP_IP} \
  --set IF_TS-CA_CHFE {IF_TS-CA_CHFE_IP} \
  --set IF_CHFE_TS-CA {IF_CHFE_TS-CA_IP} \
  --set IF_BRIDGE_CHFE {IF_BRIDGE_CHFE_IP} \
  --set IF_CHFE_BRIDGE_BCF {IF_CHFE_BRIDGE_IP} \
  --protocol TLS
  * (TCP transport)
    >   sudo python3 test_suite/services/stub_server/sip_service/sip_entry.py \
  --scenario test_suite/test_files/SIPp_scenarios/sip_service/BRIDGE_003/CHFE_BRIDGE_003.xml \
  --scenario-type auto --bind-ip {IF_CHFE_ESRP_IP} --bind-port 5060 \
  --remote-ip {IF_CHFE_BRIDGE_IP} --remote-port 5060 \
  --set conference_id {CONFERENCE_ID} \
  --set IF_OSP_CHFE {IF_OSP_CHFE_IP} \
  --set IF_CHFE_OSP {IF_CHFE_OSP_IP} \
  --set IF_TS-CA_CHFE {IF_TS-CA_CHFE_IP} \
  --set IF_CHFE_TS-CA {IF_CHFE_TS-CA_IP} \
  --set IF_BRIDGE_CHFE {IF_BRIDGE_CHFE_IP} \
  --set IF_CHFE_BRIDGE_BCF {IF_CHFE_BRIDGE_IP} \
  --protocol TCP

### Test Body

#### Stimulus

Start text call with CHFE, then exchange text messages after receiving INVITE to conference from BRIDGE - run following SIPp command on Test System OSP.

Run custom SIP service using following command (replace names in {} with values):
  * (TLS transport)
    >   sudo python3 test_suite/services/stub_server/sip_service/sip_entry.py \
  --scenario test_suite/test_files/SIPp_scenarios/sip_service/BRIDGE_003/OSP_BRIDGE_003.xml \
  --scenario-type auto --bind-ip {IF_OSP_BCF_IP} --bind-port 5061 \
  --remote-ip {IF_BCF_OSP_IP} --remote-port 5061 \
  --tls-cert {OSP_CERT_FILE_PATH} --tls_key {OSP_KEY_FILE_PATH} \
  --tls-ca {PCA_CERT_FILE_PATH} \
  --set conference_id {CONFERENCE_ID} \
  --set IF_OSP_BCF {IF_OSP_BCF_IP} \
  --set IF_BCF_OSP {IF_BCF_OSP_IP} \
  --set IF_OSP_CHFE {IF_OSP_CHFE_IP} \
  --set IF_CHFE_OSP {IF_CHFE_OSP_IP} \
  --set IF_BRIDGE_OSP {IF_BRIDGE_OSP_IP} \
  --set IF_OSP_BRIDGE_BCF {IF_OSP_BRIDGE_IP} \
  --protocol TLS
  * (TCP transport)
    >   sudo python3 test_suite/services/stub_server/sip_service/sip_entry.py \
  --scenario test_suite/test_files/SIPp_scenarios/sip_service/BRIDGE_003/OSP_BRIDGE_003.xml \
  --scenario-type auto --bind-ip {IF_OSP_BCF_IP} --bind-port 5060 \
  --remote-ip {IF_BCF_OSP_IP} --remote-port 5060 \
  --set conference_id {CONFERENCE_ID} \
  --set IF_OSP_BCF {IF_OSP_BCF_IP} \
  --set IF_BCF_OSP {IF_BCF_OSP_IP} \
  --set IF_OSP_CHFE {IF_OSP_CHFE_IP} \
  --set IF_CHFE_OSP {IF_CHFE_OSP_IP} \
  --set IF_BRIDGE_OSP {IF_BRIDGE_OSP_IP} \
  --set IF_OSP_BRIDGE_BCF {IF_OSP_BRIDGE_IP} \
  --protocol TCP

#### Response

* BRIDGE accepts SDP offer from Test System CHFE (t140 media, multi-party aware). 200 OK response should contain:
  * 'a=rtpmap:98 t140/1000'
  * 'a=rtt-mixer' 
* BRIDGE sends SIP INVITE to Test System BCF (t140 media, multi-party unaware) containing in SDP body:
  * 'a=rtpmap:98 t140/1000'
* All text messages sent from Test System OSP are delivered through Test System BCF and BRIDGE to Test System CHFE
* All text messages sent from Test System CHFE are delivered through BRIDGE and Test System BCF to Test System OSP
* All RTP packets received by Test System OSP from Test System BCF contain one SSRC (Synchronization Source Identifier) which identify the Test System BCF
* All RTP packets received by Test System CHFE from BRIDGE contain one SSRC (Synchronization Source Identifier) which identify BRIDGE
* All RTP packets sent by BRIDGE to Test System CHFE contain CSRC (Contributing Source Identifiers) with SSRC values of Test System BCF and Test System CHFE
* All RTP packets sent by BRIDGE to Test System BCF and then Test System OSP do not contain any ids in CSRC (Contributing Source Identifiers) or this section is missing in packets

VERDICT:
* PASSED - All checks passed
* FAILED - any other cases

### Test Postamble
#### Test System OSP, Test System BCF, Test System ESRP, Test System CHFE, CONFERENCE APP
* stop all SIPp processes (if still running)
* archive all logs generated
* stop Wireshark (if still running)
* remove ng911 repository files
* disconnect interfaces from BRIDGE

#### BRIDGE
* reconnect interfaces back to default

## Post-Test Conditions 
### Test System OSP, Test System BCF, Test System ESRP, Test System CHFE, CONFERENCE APP
* Test tools stopped
* interfaces disconnected

### BRIDGE
* device connected back to default
* device in normal operating state

## Sequence Diagram
<!--
https://mermaid.live/edit#pako:eNqNVV1v2jAU_StXfmrVpEsIH8WqKkFIN1YVUEInbcqLGwy1SmzmOF1Z1f8-OymUzwyJh3B97r3nXB_bbygRE4owsm075ongUzbDMQdImZRCdhIlZIZhSuYZjXkByujvnPKE9hiZSZIaMMCCSMUStiBcwTAaAclgTDMF0TJTNDWhfVzXv93FmdBZt9Z96Jzv44Mo3CtsYgcqh_3e12A_7ndMvj8c3AZhMPAD6IwOZPvfboPdPkXsbCwJz6ZU2lMpUs2wzNXi7JubC80dR_0R9Ac_-mMNjnojUG7d-VCilw3KEK6CmXWDMw0xfAKvH-WXmz20Qa2rFuia48Dw7mhZQ7IK98FSS6qE7Uju-HeHRa4X9mVt5lxf23qxXAvHI7inE0ZAj588zln2RCeFetN_3b5MKeRUZ1iQ5nPFbLPDS8g5-UMkLcusNnAgFAXxQmUxT8vvYPAlJYpqr-gTQaWxewndHLrBVexkAe1si_acGtzrTiU9XVyRREHGFvizUb93wbKpSPLseMtieAfJl9bH8F0wXk1_hdyQsEukYHlIV5m7rc29ciBkfKZ_1cDSU5sTwMcmsE3AAqmUnbJXKs-r9azN9cnhdI9tO2bDL8e6RQ_dyA_73f0BnjIIqAYNhuP-7U8IXihXOFnXBre4s5bVzMoO_7FKJ3vOoCvZZEZBCWD8hWnczvVtVtQTPdlRYaDv2MOGCqm5QscCwziyzVEug4s5SWi2Ctr-t-CU6cUcWWimySOsZE4tlFKZEvMXvZn8GGnWKY0R1p8TIp9jFPN3naOv-l9CpKs0KfLZE8LFQ2ehfDHRx__jhVtHtYgJlb7IuULYrdVbRRWE39Arwlfty3rTbbccp15r1d26Z6Elwp536bU9r9Z0m9pZrtd8t9Dfoq1zeVVvNRqNWqvd8txWw2lYiORKREuerEhpi-r39758oYuH-v0fkFk2Qw
-->

![image](../_assets/BRIDGE/TD_BRIDGE_003_Sequence_Diagram_1a.png)


<!--
https://mermaid.live/edit#pako:eNqlVmFP2zAQ_SsnfwItYUnaNdRCSCWko5ooqOkmsXUfTOq21hq7cxxoh_jvsx1aoEkZsH5KnXfv3Tvf2blDqRhThJHruiOeCj5hUzziABmTUshOqoTMMUzIPKcjbkE5_V1QntJTRqaSZAYMsCBSsZQtCFdwkVwCyWFIcwXJKlc0M0tV3EnU3caZpb2T4ORrZ7-Kj5NBhdis1TAPeqef4-p61DHx0UW_Gw_ifhRD57ImOjrrxts6dm1vKAnPJ1S6EykynWEZ2xeKgrih0th0Sm0MPX7DFM1tNZQANaMQ6fJSaWpXBppfCXePjz9o7xiS3iX0-t96wxhytsCPEW7v9OhafjyGAV3MSUpzbPDRWbyVlAXtJada1G96DmTFXDHX2FtBwcktkXT_iXrUtdIPORt13_NgKFeMT-uSNHUocf2LYa97BfEN5QpLqhOw0nXhJmhbJtC4iy8vZlKBvCoLSIrrPJVsoZjgbqKIohgUlRnj-nFsk9xmflWC_1JPN3sFQdlPNH-vxKYXOlHl_dGRqyEWMRhewjkdMwK6Vcn1nOWzB4c7N7-uZUtDQ7pUkNE8J1PdtnSZzgif0oqDtQGjvZckgwi8Zcvz9jey2vtqLsgYwwjZETovOcH0p2UZoRrPG0Nr0uZ_kNpm0taeMwbvZ9RcdTn6r2c0R2AlxbpiBu_nXNey3NCtYjoQ6WcMP6yEU27bzzdK7W6f-KFh9Kw97aNbpmaMA4En4zEREj7lNF3TPRb4sfFPruIXD4fn76uDs-N8sT3x9P37Bty3A75623jXYXbYeMygJEEOmko2RljJgjoo08cZMX_RnYkeIX27ZHSEzNaNifxldupex-jr7LsQ2TpMimI6Q9he5g4qFmN9ID7c4ptV7W9MZSQKrhD226FvWRC-Q0uEg_Cg4Yfh4WHYaIR-q-G1HLRCuB0ctFqHfuA1w0az6bX9ewf9sbreQbvttYJmu9UMGmHgNzQdKZRIVjxdZ6XPL_2RcV5-htivkfu_Pb54Ag
-->

![image](../_assets/BRIDGE/TD_BRIDGE_003_Sequence_Diagram_1b.png)

## Comments

Version:  010.3f.5.1.3

Date:     20260413

## Footnotes
[^1]: SIPp - tool for SIP packet simulations. Official documentation: https://sipp.sourceforge.net/doc/reference.html#Getting+SIPp
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^4]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518
