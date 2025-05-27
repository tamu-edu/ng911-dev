# Test Description: TD_LIS_004

## IMPORTANT !
Test requires simulation of moving object sent to LIS. Procedure is not clarified yet

## Overview
### Summary
SIP event rate control


### Description
This test checks support of SIP event rate control on LIS:
- min-rate
- max-rate
- adaptive-min-rate

### HTTP and SIP transport types
Test can be performed with 2 different SIP and HTTP transport types. Steps describing actions for specific one are marked as following:
- (TLS transport) - should be used by default
- (TCP transport) - used in lab for testing purposes only if default TLS is not possible

### References
* Requirements : RQ_LIS_003
* Test Case    : 

### Requirements
IXIT config file for LIS

## Configuration
### Implementation Under Test Interface Connections
<!-- Identify each of the FEs that are part of the configuration and how they are connected -->
* Test System
  * IF_TS_LIS - connected to IF_LIS_TS
* LIS
  * IF_LIS_TS - connected to IF_TS_LIS


### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* Test System
  * IF_TS_LIS - Active
* LIS
  * IF_LIS_TS - Active


### Connectivity Diagram
<!--
[![](https://mermaid.ink/img/pako:eNpdUNsKgkAQ_RWZZ_0BiZ4iEOwlfYoFmdzxQu6u7IUQ8d-b0oqapzPnnLnOUBtJkEIzmHvdofVRfhY64siOVVlUeVbskmTPCSMmhF5VF66txbGLSnI-KibnSa3KT-1KkZZ_VR9pc7-bb26IQZFV2EtebX7SAnxHigSkDCXamwChF_Zh8KaYdA2pt4FiCKNET4ceeZCCtMHBMTuivhjzzUn23tjTevvrBTFYE9pucywPiKlY2g?type=png)](https://mermaid.live/edit#pako:eNpdUNsKgkAQ_RWZZ_0BiZ4iEOwlfYoFmdzxQu6u7IUQ8d-b0oqapzPnnLnOUBtJkEIzmHvdofVRfhY64siOVVlUeVbskmTPCSMmhF5VF66txbGLSnI-KibnSa3KT-1KkZZ_VR9pc7-bb26IQZFV2EtebX7SAnxHigSkDCXamwChF_Zh8KaYdA2pt4FiCKNET4ceeZCCtMHBMTuivhjzzUn23tjTevvrBTFYE9pucywPiKlY2g)
-->

![image](https://github.com/user-attachments/assets/370a16a0-66cb-4545-aa4b-a1b3b83dc22d)


## Pre-Test Conditions

### Test System
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active

### LIS
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Default configuration is loaded
* IUT is initialized using IXIT config file
* IUT is active
* IUT is in normal operating state


## Test Sequence

### Test Preamble

#### Test System
* Install Wireshark[^1]
* Copy following XML scenario files to local storage:
  > SIP_SUBSCRIBE_minimum_rate_with_NOTIFY_receive.xml
  > SIP_SUBSCRIBE_maximum_rate_with_NOTIFY_receive.xml
  > SIP_SUBSCRIBE_adaptive_min_rate_with_NOTIFY_receive.xml

* (TLS transport) Copy to local storage TLS certificate and private key files:
  > cacert.pem
  > cakey.pem

* (TLS transport) Configure Wireshark to decode SIP over TLS packets[^2]
* Using Wireshark on 'Test System' start packet tracing on IF_TS_LIS interface - run following filter:
   * (TLS transport)
     > ip.addr == IF_TS_LIS_IP_ADDRESS and tls
   * (TCP transport)
     > ip.addr == IF_TS_LIS_IP_ADDRESS and sip

### Test Body

#### Variations
1. SIP_SUBSCRIBE_minimum_rate_with_NOTIFY_receive.xml
2. SIP_SUBSCRIBE_maximum_rate_with_NOTIFY_receive.xml
3. SIP_SUBSCRIBE_adaptive_min_rate_with_NOTIFY_receive.xml


#### Stimulus
1. Run SIPp XML scenario, execute following SIPp command on Test System, example:
    * (TCP transport)
      > sudo sipp -t t1 -sf SCENARIO_FILE IF_LIS_TS_IPv4:5060
    * (TLS transport)
      > sudo sipp -t l1 -sf SCENARIO_FILE IF_LIS_TS_IPv4:5061
 
Variation 2

Update object location multiple times within short time slot (to exceed maximum rate per second)

Variation 3
Update object's location with different frequency (f.e. couple messages -> pause -> multiple messages)

#### Response
Variation 1
Minimum_rate - time between SIP NOTIFY sent by LIS cannot be lower than configured in XML scenario file

Variation 2
Maximum_rate - despite location was changing dynamically, SIP NOTIFY messages sent by LIS are sent no more often than configured in XML scenario file.

Variation 3
Adaptive_min_rate - SIP NOTIFY messages sent by LIS timing shall follow frequency of location updates


VERDICT:
* PASSED - if LIS responded as expected
* FAILED - any other cases


### Test Postamble
#### Test System
* stop all NC processes (if still running)
* stop all SIPp processes (if still running)
* stop Wireshark (if still running)
* archive all logs generated
* remove all HTTP scenarios
* remove all SIP scenarios
* disconnect interfaces from LIS
* (TLS transport) remove certificates

#### LIS
* disconnect IF_LIS_TS
* reconnect interfaces back to default

## Post-Test Conditions 
### Test System 
* Test tools stopped
* interfaces disconnected from LIS

### LIS
* device connected back to default
* device in normal operating state

## Sequence Diagram

**Minimum rate scenario:**
<!--
[![](https://mermaid.ink/img/pako:eNqtkb1uAjEQhF_F2jbnF3CBBPmRTiQcikmRyI1lL4cFtmFtFwjx7vHdJUoqKrrdnU-z0swFTLQIAjjnKpgYtq4XKjDmHVGkucmRkmBbfUiowgglPBUMBp-c7kn7AWZsgykzeU4ZPZ_NHl5bKZhs10x-LOTje7t4nrB651X_R09Yt7ytr7pN-_J5-1W3HNR7-NzDAxrwSF47W8O9DLSCvEOPCkQdraa9AhWuldMlR3kOBkSmgg2Uo9X5N14QY_YNHHX4ivFvR-tqN29Te2OJDVAs_e6HuH4DLdeT8A?type=png)](https://mermaid.live/edit#pako:eNqtkb1uAjEQhF_F2jbnF3CBBPmRTiQcikmRyI1lL4cFtmFtFwjx7vHdJUoqKrrdnU-z0swFTLQIAjjnKpgYtq4XKjDmHVGkucmRkmBbfUiowgglPBUMBp-c7kn7AWZsgykzeU4ZPZ_NHl5bKZhs10x-LOTje7t4nrB651X_R09Yt7ytr7pN-_J5-1W3HNR7-NzDAxrwSF47W8O9DLSCvEOPCkQdraa9AhWuldMlR3kOBkSmgg2Uo9X5N14QY_YNHHX4ivFvR-tqN29Te2OJDVAs_e6HuH4DLdeT8A)
-->

![image](https://github.com/user-attachments/assets/23b3b8af-c601-4af4-b9ff-cc34de9c9e94)

**Maximum rate scenario:**
<!--
[![](https://mermaid.ink/img/pako:eNrFkltLAzEQhf_KME-Ku7gr-pKHgvWCi9UWsz4oeYnZ6XaxSWqSBUvpf3cvvShYXx0IzOR8DCfhrFDZgpBhHMfCKGumVcmEAdCVc9ZdqmCdZzCVc0_CdJCnj5qMoutKlk7qFgbIyQfgSx9Ix4PBySjjDHg2Af485FdP2fCmx5r7uNG_0T02vu_1ubULSJNPBhegyXtZEpxC6kn1eluOVABXvh2l6Xm0Ocd7-ZCbuzyfwMgqGSprfuK_uerwsyTZWWuLTNEPu-bQgx7HeXb78vffbDf__w6MUJPTsiqaJKxaWmCYkSaBrGkL6d4FCrNuOFkHy5dGIQuupgjrRSHDNgvIuqBEuJDm1dr9TEXVBOmhj1qXuAidrcvZhlh_AWMzwi0?type=png)](https://mermaid.live/edit#pako:eNrFkltLAzEQhf_KME-Ku7gr-pKHgvWCi9UWsz4oeYnZ6XaxSWqSBUvpf3cvvShYXx0IzOR8DCfhrFDZgpBhHMfCKGumVcmEAdCVc9ZdqmCdZzCVc0_CdJCnj5qMoutKlk7qFgbIyQfgSx9Ix4PBySjjDHg2Af485FdP2fCmx5r7uNG_0T02vu_1ubULSJNPBhegyXtZEpxC6kn1eluOVABXvh2l6Xm0Ocd7-ZCbuzyfwMgqGSprfuK_uerwsyTZWWuLTNEPu-bQgx7HeXb78vffbDf__w6MUJPTsiqaJKxaWmCYkSaBrGkL6d4FCrNuOFkHy5dGIQuupgjrRSHDNgvIuqBEuJDm1dr9TEXVBOmhj1qXuAidrcvZhlh_AWMzwi0)
-->

![image](https://github.com/user-attachments/assets/5c56395c-7b43-4c2f-ad31-b5b536d9027e)


**Adaptive minimum rate scenario:**
<!--
[![](https://mermaid.ink/img/pako:eNrtk01LAzEQhv_KMCfFXeyKveRQsH7gYrXFXQ9KLjE73S42SU2yYCn97-5Hu61gvQkeHAhk8j4MkxfeFUqTETIMw5BrafS0yBnXAKqw1tgL6Y11DKZi7ojrBnL0XpKWdFWI3ApVwwApOQ_J0nlS4WBwMooTBkk8geRpmFw-xsPrFqvew0rfo1tsfNfqc2MW0P9gEIEi50ROcAp9R7KV67IkPdj89SiKzoPNOd7Jh5a5TdMJjIwUvjD6K_7dUg1-1ut1m9VFOmub7nLoPw_jNL55_tma7eS_MqPzvr_nffTv_e_OwAAVWSWKrArhqqY5-hkp4siqaybsG0eu1xUnSm-SpZbIvC0pwHKRCb-NIbImowEuhH4xZtdTVlQZvm9T3oQ9QGvKfLYh1p-pVSwm?type=png)](https://mermaid.live/edit#pako:eNrtk01LAzEQhv_KMCfFXeyKveRQsH7gYrXFXQ9KLjE73S42SU2yYCn97-5Hu61gvQkeHAhk8j4MkxfeFUqTETIMw5BrafS0yBnXAKqw1tgL6Y11DKZi7ojrBnL0XpKWdFWI3ApVwwApOQ_J0nlS4WBwMooTBkk8geRpmFw-xsPrFqvew0rfo1tsfNfqc2MW0P9gEIEi50ROcAp9R7KV67IkPdj89SiKzoPNOd7Jh5a5TdMJjIwUvjD6K_7dUg1-1ut1m9VFOmub7nLoPw_jNL55_tma7eS_MqPzvr_nffTv_e_OwAAVWSWKrArhqqY5-hkp4siqaybsG0eu1xUnSm-SpZbIvC0pwHKRCb-NIbImowEuhH4xZtdTVlQZvm9T3oQ9QGvKfLYh1p-pVSwm)
-->

![image](https://github.com/user-attachments/assets/191863fd-c14a-4921-a8f0-4cb1172c4211)

## Comments

Version:  010.3f.3.1.3

Date:     20250429


## Footnotes
[^1]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^2]: Wireshark configuration to decrypt SIP over TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
