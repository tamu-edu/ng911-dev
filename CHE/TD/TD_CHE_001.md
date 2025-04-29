# Test Description: TD_CHE_001
## Overview
### Summary
Dereferencing from LIS

### Description
This test checks CHE dereferencing from LIS:
- using SIP Presence Event Package
- using HELD

### References
* Requirements : RQ_CHE_11
* Test Case    : 

### Requirements
IXIT config file for CHE

### HTTP and SIP transport types
Test can be performed with 2 different SIP and HTTP transport types. Steps describing actions for specific one are marked as following:
- (TLS transport) - should be used by default
- (TCP transport) - used in lab for testing purposes only if default TLS is not possible

## Configuration
### Implementation Under Test Interface Connections
<!-- Identify each of the FEs that are part of the configuration and how they are connected -->
* Test System SIP
  * IF_TSSIP_CHE - connected to IF_CHE_TSSIP
* CHE
  * IF_CHE_TSSIP - connected to IF_TSSIP_CHE
  * IF_CHE_TSLIS - connected to IF_TSLIS_CHE
* Test System LIS
  * IF_TSLIS_CHE - connected to IF_CHE_TSLIS


### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* Test System SIP
  * IF_TSSIP_CHE - Active
* CHE
  * IF_CHE_TSSIP - Active
  * IF_CHE_TSLIS - Active
* Test System LIS
  * IF_TSLIS_CHE - Active


### Connectivity Diagram
<!--
[![](https://mermaid.ink/img/pako:eNplkW9rgzAQxr-K3Ou0RO2iCWNv9ocJHYzZV0MomUmrrBqJkc2J332pFutcXt398tw9l0sHqRISGBxO6ivNuDbO9i0pHXuip_0ujqPX_f3z42p1Z1MbjGgm2Ebxmd_OFZaNirr5OGpeZc5O1saJ29rIwpnqlyYjlaVYFE9Xl4LFGH_oZP2_zXyGSbZ8x1QMCAqpC54Lu5zujBMwmSxkAsyGguvPBJKytzreGBW3ZQrM6EYiaCrBjXzIufUtgB34qba04uW7Utdcitwo_TJuf_iEQQOsg29grkfWLqGUBj6mNKSBh6AFZqmPPex6IaUYU3dDegQ_Q9vN2iOE4CAgrh_6-CZAoFVzzC6G_S9tRo9H?type=png)](https://mermaid.live/edit#pako:eNplkW9rgzAQxr-K3Ou0RO2iCWNv9ocJHYzZV0MomUmrrBqJkc2J332pFutcXt398tw9l0sHqRISGBxO6ivNuDbO9i0pHXuip_0ujqPX_f3z42p1Z1MbjGgm2Ebxmd_OFZaNirr5OGpeZc5O1saJ29rIwpnqlyYjlaVYFE9Xl4LFGH_oZP2_zXyGSbZ8x1QMCAqpC54Lu5zujBMwmSxkAsyGguvPBJKytzreGBW3ZQrM6EYiaCrBjXzIufUtgB34qba04uW7Utdcitwo_TJuf_iEQQOsg29grkfWLqGUBj6mNKSBh6AFZqmPPex6IaUYU3dDegQ_Q9vN2iOE4CAgrh_6-CZAoFVzzC6G_S9tRo9H)
-->

![image](https://github.com/user-attachments/assets/fae9546a-3fdb-4ba4-a7ef-1cb7adf1dbce)


## Pre-Test Conditions

### Test System SIP
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* ng911 repository cloned to local storage
* (TLS) Generated own PCA-signed certificate and private key files (test_system_sip.crt, test_system_sip.key)
* (TLS) Certificate and key used by CHE copied to local storage
* (TLS) PCA certificate copied to local storage

### CHE
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* IUT is active
* IUT is in normal operating state
* Default configuration is loaded
* IUT is initialized using IXIT config file
* Test System SIP configured as default ESRP
* Test System LIS configured as default LIS
* Agent logged in (f.e. tester@psap.example.com)

### Test System LIS
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* ng911 repository cloned to local storage
* (TLS) Generated own PCA-signed certificate and private key files (test_system_lis.crt, test_system_lis.key)
* (TLS) Certificate and key used by CHE copied to local storage
* (TLS) PCA certificate copied to local storage

## Test Sequence

### Test Preamble

#### Test System SIP
* Install SIPp by following steps from documentation[^1]
* Install Wireshark[^2]
* (TLS v1.2) Configure Wireshark to decode SIP over TLS, use test system and CHE certificate keys [^3]
* (TLS v1.3) Configure logging of session keys and configure Wireshark to decode SIP over TLS [^4]
* Using Wireshark on 'Test System SIP' start packet tracing on IF_TSSIP_CHE interface - run following filter:
   * (TLS)
     > ip.addr == IF_TSSIP_CHE_IP_ADDRESS and tls
   * (TCP)
     > ip.addr == IF_TSSIP_CHE_IP_ADDRESS and http

#### Test System LIS
* Install SIPp by following steps from documentation[^1]
* Install Wireshark[^2]
* (TLS v1.2) Configure Wireshark to decode SIP and HTTP over TLS, use test system and CHE certificate keys [^3]
* (TLS v1.3) Configure logging of session keys and configure Wireshark to decode SIP and HTTP over TLS [^4]
* Using Wireshark on 'Test System LIS' start packet tracing on IF_TSLIS_CHE interface - run following filter:
   * (TLS)
     > ip.addr == IF_TSLIS_CHE_IP_ADDRESS and tls
   * (TCP)
     > ip.addr == IF_TSLIS_CHE_IP_ADDRESS and (http or sip)
* run following SIPp scenario to handle SIP Presence Event Package:
    * (TCP transport)
      ```
      sudo sipp -t t1 -sf SIP_SUBSCRIBE_LIS.xml IF_TSLIS_CHE_IPv4:5060
      ```
    * (TLS transport)
      ```
      sudo sipp -t l1 -tls_cert test_system.crt -tls_key test_system.key -sf SIP_SUBSCRIBE_LIS.xml IF_TSLIS_CHE_IPv4:5061
      ```

### Test Body

#### Variations
1. Validate HTTP POST sent to LIS after receiving SIP INVITE (HELD)

Use SIPp scenario file: `SIP_INVITE_geolocation_HELD.xml`

2. Validate SIP SUBSCRIBE sent to LIS after receiving SIP INVITE (SIP Presence Event Package)

Use SIPp scenario file: `SIP_INVITE_geolocation_SIP.xml`

#### Stimulus

Send SIP INVITE to CHE from Test System SIP, use SIP INVITE
* (TCP transport)
  ```
  sudo sipp -t t1 -sf SIPP_SCENARIO IF_TSSIP_CHE_IPv4:5060
  ```
* (TLS transport)
  ```
  sudo sipp -t l1 -tls_cert test_system.crt -tls_key test_system.key -sf SIPP_SCENARIO IF_TSSIP_CHE_IPv4:5061
  ```

#### Response
* Variation 1
    - CHE sends HTTP POST to Test System LIS
    - HTTP POST is addressed to URL from 'Geolocation' header field in received SIP INVITE
    - HTTP POST contains 'Content-Type: application/held+xml'
    - HTTP POST contains XML body with 'locationRequest', example:

     ```
     <?xml version="1.0"?>
         <locationRequest xmlns="urn:ietf:params:xml:ns:geopriv:held"/>
     ```

* Variation 2
    - CHE sends SIP SUBSCRIBE to Test System LIS
    - SIP SUBSCRIBE contains 'To' header field with SIP URI from 'Geolocation' header field in received SIP INVITE
    - SIP SUBSCRIBE contains 'Event: presence'
    - SIP SUBSCRIBE contains 'Accept: application/pidf+xml'
    - CHE responds with SIP 200 OK for each SIP NOTIFY sent by 'Test System LIS'

VERDICT:
* PASSED - if CHE sends correct message with expected header field values
* FAILED - any other cases


### Test Postamble
#### Test System SIP/LIS
* stop all SIPp processes (if still running)
* (TCP transport) stop all NC processes (if still running)
* (TLS transport) stop all Openssl processes (if still running)
* archive all logs generated
* stop Wireshark (if still running)
* remove all SIPp and HTTP scenarios
* (TLS transport) remove certificates
* disconnect interfaces from CHE

#### CHE
* reconnect interfaces back to default

## Post-Test Conditions 
### Test System 
* Test tools stopped
* interfaces disconnected from CHE

### CHE
* device connected back to default
* device in normal operating state

## Sequence Diagram
### Variation 1 (HELD)
<!--
[![](https://mermaid.ink/img/pako:eNplkF1rgzAUhv9KOLfTErWLJheFsRUq-6ig7GLkJmhqZTPpYoQ58b8v2pYNdnfOeZ_zno8RSl1JYOD7PlelVoemZlwh1DbGaHNXWm06hg7io5NcLVAnP3upSvnQiNqIdoYRKmRnUT50VrYoTzN_s7nfbdkcovTlNS22Z8wVnXTzl35Kc4Z2RZGhbJ8X_92cfnVbqBBjtH_kCjxopWlFU7ntx7mPgz3KVnJgLqyEeefA1eQ40VudD6oEZk0vPehPlbDX_YEtx3lwEupN699cVo07_vn8nuVLCwNshC9gQUhWAaGUxhGmNKFx6MEAzFUjHOIgTCjFmAZrMnnwvdiuVyEhBMcxCaIkwrexB0b39fEycPoBC0t36A?type=png)](https://mermaid.live/edit#pako:eNplkF1rgzAUhv9KOLfTErWLJheFsRUq-6ig7GLkJmhqZTPpYoQ58b8v2pYNdnfOeZ_zno8RSl1JYOD7PlelVoemZlwh1DbGaHNXWm06hg7io5NcLVAnP3upSvnQiNqIdoYRKmRnUT50VrYoTzN_s7nfbdkcovTlNS22Z8wVnXTzl35Kc4Z2RZGhbJ8X_92cfnVbqBBjtH_kCjxopWlFU7ntx7mPgz3KVnJgLqyEeefA1eQ40VudD6oEZk0vPehPlbDX_YEtx3lwEupN699cVo07_vn8nuVLCwNshC9gQUhWAaGUxhGmNKFx6MEAzFUjHOIgTCjFmAZrMnnwvdiuVyEhBMcxCaIkwrexB0b39fEycPoBC0t36A)
-->

![image](https://github.com/user-attachments/assets/d1866ffd-e029-4bad-bfcd-3d3f90a4f259)


### Variation 2 (SIP Presence Event Package)
<!--
[![](https://mermaid.ink/img/pako:eNqFkF1LwzAUhv9KOLe2I21nuuRi4GbFom5ip6DkJrRZV7TJTFNwjv73Za3iwIvdnY_nvAeePeS6kMDA932ucq3WVcm4QqiujNHmKrfaNAytxUcjueqhRn62UuXyuhKlEfURRmglG4uyXWNljbL00Z9O57cJO5YoXbykq2TA3NCtLk7p-zQbuOx5ls2f0lnyP9Exp4khxmh5dxZbLFfpzev5x0MceFBLU4uqcDb2xysOdiNryYG5shDmnQNXneNEa3W2Uzkwa1rpQbsthP31AayX5cFWqDet_3pZVE7mw6C7t94zwPbwBSwIySgglNI4wpROaBx6sAPmphEOcRBOKMWYBmPSefDdx45HISEExzEJokmEL2MPjG7Lzc_D7gCtjI4O?type=png)](https://mermaid.live/edit#pako:eNqFkF1LwzAUhv9KOLe2I21nuuRi4GbFom5ip6DkJrRZV7TJTFNwjv73Za3iwIvdnY_nvAeePeS6kMDA932ucq3WVcm4QqiujNHmKrfaNAytxUcjueqhRn62UuXyuhKlEfURRmglG4uyXWNljbL00Z9O57cJO5YoXbykq2TA3NCtLk7p-zQbuOx5ls2f0lnyP9Exp4khxmh5dxZbLFfpzev5x0MceFBLU4uqcDb2xysOdiNryYG5shDmnQNXneNEa3W2Uzkwa1rpQbsthP31AayX5cFWqDet_3pZVE7mw6C7t94zwPbwBSwIySgglNI4wpROaBx6sAPmphEOcRBOKMWYBmPSefDdx45HISEExzEJokmEL2MPjG7Lzc_D7gCtjI4O)
-->

![image](https://github.com/user-attachments/assets/c4cbbcae-7881-4912-86f0-e6701e7d708f)

## Comments

Version: 010.3f.3.0.5
Date: 20250429


## Footnotes
[^1]: SIPp - tool for SIP packet simulations. Official documentation: https://sipp.sourceforge.net/doc/reference.html#Getting+SIPp
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt SIP over TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^4]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518



