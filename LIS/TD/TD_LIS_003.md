# Test Description: TD_LIS_003

## IMPORTANT !
Test requires simulation of moving object sent to LIS. Procedure is not clarified yet

## Overview
### Summary
SIP location filters


### Description
This test checks support of SIP location filters on LIS:
* if different type of filters are accepted
* if LIS sends SIP NOTIFY only when location change matches trigger set up in the filter

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

![image](https://github.com/user-attachments/assets/b52b5dd1-3f90-4a47-a010-4d95fd50a6de)


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
* Install Netcat[^3]
* Copy following XML scenario files to local storage:
  > SIP_SUBSCRIBE_distance_filter_with_NOTIFY_receive.xml
  > SIP_SUBSCRIBE_speed_filter_with_NOTIFY_receive.xml
  > SIP_SUBSCRIBE_civic_address_filter_with_NOTIFY_receive.xml
  > SIP_SUBSCRIBE_enter_area_filter_with_NOTIFY_receive.xml
  > SIP_SUBSCRIBE_location_type_change_filter_with_NOTIFY_receive.xml

<!--
* **!** Copy following HTTP scenario files to local storage:
  > TO DO
-->

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

**Variations**

1. Distance filter - object moved by distance below value set in filter.
Scenario file: SIP_SUBSCRIBE_distance_filter_with_NOTIFY_receive.xml

2. Distance filter - object moved by distance with higher than value set in filter.
Scenario file: SIP_SUBSCRIBE_distance_filter_with_NOTIFY_receive.xml

3. Speed filter - object speed change below value set in filter.
Scenario file: SIP_SUBSCRIBE_speed_filter_with_NOTIFY_receive.xml

4. Speed filter - object speed change higher than value set in filter.
Scenario file: SIP_SUBSCRIBE_speed_filter_with_NOTIFY_receive.xml

5. Address filter - object geolocation do not match civic address area set in the filter
Scenario file: SIP_SUBSCRIBE_civic_address_filter_with_NOTIFY_receive.xml

6. Address filter - object geolocation match civic address area set in the filter
Scenario file: SIP_SUBSCRIBE_civic_address_filter_with_NOTIFY_receive.xml

7. Area filter - object geolocation do not match area set in the filter
Scenario file: SIP_SUBSCRIBE_enter_area_filter_with_NOTIFY_receive.xml

8. Area filter - object geolocation match area set in the filter
Scenario file: SIP_SUBSCRIBE_enter_area_filter_with_NOTIFY_receive.xml

9. Location type filter - object change location type, not geolocation (f.e. from civic address to geolocation point)
Scenario file: SIP_SUBSCRIBE_location_type_change_filter_with_NOTIFY_receive.xml

**Stimulus**
1. Subscribe to object location on LIS - run following SIPp command on Test System, example:
    * (TCP transport)
      > sudo sipp -t t1 -sf SCENARIO_FILE IF_LIS_TS_IPv4:5060 -bg
    * (TLS transport)
      > sudo sipp -t l1 -sf SCENARIO_FILE IF_LIS_TS_IPv4:5061 -bg
2. Simulate change of subscribed object location according to variation 

**Response**
Variation 1, 3, 5, 7
Verify if change of subscribed object location has not yet triggered sending of SIP NOTIFY

Variation 2, 4, 6, 8, 9
Verify if change of subscribed object location triggered send of SIP NOTIFY


<!--
7. Configure HTTP location files accordingly to current scenario:
   * Distance filter scenario - leave object's distance still a bit lower than set in the filter. Sum with previous distance will exceed value which should trigger SIP NOTIFY
   * Speed filter scenario - leave object's speed still a bit lower than set in the filter. Sum with previous distance will exceed value which should trigger SIP NOTIFY
   * Civic address filter scenario - change object's civic address fields included in the filter
   * Enter area filter scenario - change object's gelocation which match area set in filter
   * Location type change filter scenario - simulate change of location which changes it's type (f.e. for civic change to geolocation only)
8. Update object location LIS - send HTTP messages from step 5 with configuration from step 7
9. Using Wireshark verify if location change on LIS triggered sending SIP NOTIFY to Test System.
10. Verify if received SIP NOTIFY has included correct PIDF-LO XML body
11. Configure HTTP location files accordingly to current scenario - if not mentioned then step should be skipped:
   * Distance filter scenario - configure object's distance a bit higher than set in the filter
   * Speed filter scenario - configure object's speed a bit higher than set in the filter
12. Update object location LIS - send HTTP messages from step 5 with configuration from step 11 (only for distance and speed scenarios)
13. Repeat steps 9 and 10 (only for distance and speed scenarios)
14. Stop SIPp process running in the background
-->

**Conditions for TEST PASSED verdict:**
* Test steps performed for all SIPp scenario files
* All steps passed


### Test Postamble
#### Test System
* stop all NC processes (if still running)
* stop all SIPp processes (if still running)
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

**Distance and speed filter scenarios:**
<!--
[![](https://mermaid.ink/img/pako:eNrFk8FOAjEQhl-lmZPGbQLGUw8koKtuBJbY9aDppXaHZaNtsdtNIIR3t-yiYFBOJhyatPN_yT8znVmBsjkCA0qpMMqaaVkwYQjRpXPW9ZW3rmJkKt8rFKaBKvyo0Si8KWXhpN7AhGRYecKXlUdNe72LYcIZ4cmE8KcBv35MBnGLhTgN-h7dYulDqztUnrji9azbvYq257yV_nK5z7IJGVolfWnNDv3NqUEvO51vOzS5MHuZLX7g45SMYs77dzE_LJIuGvcD5hQVHOvsOM2S2-fjn3TK7v9H7hCBRqdlmYdBXm14AX6GGgWwcM2lexMgzDpwsvaWL40C5l2NEdTzXPqvUQbWzHkEc2lerN29MS_DHozaTWkWJgJn62K2Jdaf3f_5DQ?type=png)](https://mermaid.live/edit#pako:eNrFk8FOAjEQhl-lmZPGbQLGUw8koKtuBJbY9aDppXaHZaNtsdtNIIR3t-yiYFBOJhyatPN_yT8znVmBsjkCA0qpMMqaaVkwYQjRpXPW9ZW3rmJkKt8rFKaBKvyo0Si8KWXhpN7AhGRYecKXlUdNe72LYcIZ4cmE8KcBv35MBnGLhTgN-h7dYulDqztUnrji9azbvYq257yV_nK5z7IJGVolfWnNDv3NqUEvO51vOzS5MHuZLX7g45SMYs77dzE_LJIuGvcD5hQVHOvsOM2S2-fjn3TK7v9H7hCBRqdlmYdBXm14AX6GGgWwcM2lexMgzDpwsvaWL40C5l2NEdTzXPqvUQbWzHkEc2lerN29MS_DHozaTWkWJgJn62K2Jdaf3f_5DQ)
-->

![image](https://github.com/user-attachments/assets/8b9f46c0-32cb-43a7-9940-2f830987cb71)


**Other filter scenarios:**
<!--
[![](https://mermaid.ink/img/pako:eNrFks9PwjAUx_-V5p00bgkYTz2QgE5d-DFix0HTS20fY9G22HUJhPC_WzYUDMrVQ5O275N832s_G5BWIVCI45gbac28LCg3hOjSOev60ltXUTIX7xVy00AVftRoJN6VonBC72BCcqw8YevKo457vatRyihh6ZSw2YDdPqWDpMXCfRzqR3SLZcO27lB64orXi273Jtqvy7b0V8pjnk_JyErhS2sO6G9JDXrd6XzHoVHcHHW2-oFPMjJOGOs_JOx0yHjVpJ8w_zHBuZedZHl6_3z-k7IhRKDRaVGqoMJmR3PwC9TIgYatEu6NAzfbwInaW7Y2Eqh3NUZQL5XwXzIAbUyJYCnMi7WHM6oymDRuXWuUi8DZuljsie0nuDTDnA?type=png)](https://mermaid.live/edit#pako:eNrFks9PwjAUx_-V5p00bgkYTz2QgE5d-DFix0HTS20fY9G22HUJhPC_WzYUDMrVQ5O275N832s_G5BWIVCI45gbac28LCg3hOjSOev60ltXUTIX7xVy00AVftRoJN6VonBC72BCcqw8YevKo457vatRyihh6ZSw2YDdPqWDpMXCfRzqR3SLZcO27lB64orXi273Jtqvy7b0V8pjnk_JyErhS2sO6G9JDXrd6XzHoVHcHHW2-oFPMjJOGOs_JOx0yHjVpJ8w_zHBuZedZHl6_3z-k7IhRKDRaVGqoMJmR3PwC9TIgYatEu6NAzfbwInaW7Y2Eqh3NUZQL5XwXzIAbUyJYCnMi7WHM6oymDRuXWuUi8DZuljsie0nuDTDnA)
-->

![image](https://github.com/user-attachments/assets/8af93341-2c0e-4b9b-b724-4f36cf57d83e)


## Comments

Version:  010.3d.3.1.4

Date:     20250429


## Footnotes
[^1]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^2]: Wireshark configuration to decrypt SIP over TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^3]: Netcat for Linux https://linux.die.net/man/1/nc

