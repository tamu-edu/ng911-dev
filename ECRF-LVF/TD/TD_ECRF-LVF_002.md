# Test Description: TD_ECRF-LVF_002

## Overview
### Summary
Civic and geodetic locations handling by ECRF


### Description
This test checks for ECRF:
* if handles civic addresses
* if handles all types of geolocation shapes:
  - point
  - circle
  - ellipse
  - arc-band
  - polygon


### SIP transport types
Test can be performed with 2 different HTTP transport types. Steps describing actions for specific one are marked as following:
- (TLS transport) - used by default inside ESInet on production environment
- (TCP transport) - used in lab for testing purposes only if default TLS is not possible

### References
* Requirements : ECRF-LVF_46, ECRF-LVF_22, ECRF-LVF_53
* Test Purpose : TP_ECRF-LVF_002
* Test Case    : TC_ECRF-LVF_002


## Configuration
### Implementation Under Test Interface Connections
<!-- Identify each of the FEs that are part of the configuration and how they are connected -->
* Test System
  * IF_TS_ECRF - connected to IF_ECRF_TS
* ECRF
  * IF_ECRF_TS - connected to IF_TS_ECRF


### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* Test System
  * IF_TS_ECRF - Active
* ECRF
  * IF_ECRF_TS - Active


### Connectivity Diagram
[![](https://mermaid.ink/img/pako:eNpdUM0KgzAMfhXJWV9Axi7bhMF2UU-jIJmNP8y2UluGiO--agVxOeX7S0ImKBUniKHq1LdsUJvgkTIZuLonRZ4Vt0uanKLo7NDSOsqrg33XGvsmyGkwQTYOhoRXjlnPkeR_sV3b_Ifpqx9CEKQFttzdNy0CA9OQIAaxaznqDwMmZ-dDa1Q2yhJioy2FYHuOhq4tumUC4gq7wbE9ypdSOybeGqWf_gHrH0LQytbN5ph_zqhZ8g?type=png)](https://mermaid.live/edit#pako:eNpdUM0KgzAMfhXJWV9Axi7bhMF2UU-jIJmNP8y2UluGiO--agVxOeX7S0ImKBUniKHq1LdsUJvgkTIZuLonRZ4Vt0uanKLo7NDSOsqrg33XGvsmyGkwQTYOhoRXjlnPkeR_sV3b_Ifpqx9CEKQFttzdNy0CA9OQIAaxaznqDwMmZ-dDa1Q2yhJioy2FYHuOhq4tumUC4gq7wbE9ypdSOybeGqWf_gHrH0LQytbN5ph_zqhZ8g)

## Pre-Test Conditions

### Test System
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* (TLS transport) Test System has it's own certificate signed by PCA

### ECRF
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Default configuration is loaded
* IUT is active
* IUT is in normal operating state
* Provisioning file provided


## Test Sequence

### Test Preamble

#### Test System
* (TLS transport) Install Openssl[^1]
* (TCP transport) Install Netcat[^4]
* Install Wireshark[^2]
* Copy following HTTP scenario files to local storage:
  ```
	findService_geodetic_point
	findService_geodetic_circle
	findService_geodetic_ellipse
	findService_geodetic_arc-band
	findService_geodetic_polygon
	findService_civic_address
  ```
* Make sure that geodetic and civic locations in HTTP scenario files match service boundaries from ECRF provisioning file
* Configure scenario files with correct ECRF URL and host addresses
* (TLS transport) Copy to local storage PCA-signed TLS certificate and private key files:
  ```
  PCA-cacert.pem
  PCA-cakey.pem
  ```
* (TLS transport) Copy to local storage TLS certificate and private key files used by ECRF:
  ```
  ECRF-cacert.pem
  ECRF-cakey.pem
  ```
* (TLS transport) Configure Wireshark to decode HTTP over TLS packets from Test System and ECRF as well[^3]
* Using Wireshark on 'Test System' start packet tracing on IF_TS_ECRF interface - run following filter:
   * (TLS transport)
     > ip.addr == IF_TS_ECRF_IP_ADDRESS and tls
   * (TCP transport)
     > ip.addr == IF_TS_ECRF_IP_ADDRESS and http

#### ECRF
* Provision IUT with file provided

### Test Body

**Variations**

1. Point as a location in findService request, scenario file:
```
	findService_geodetic_point
```
2. Circle as a location in findService request, scenario file:
```
	findService_geodetic_circle
```

3. Ellipse as a location in findService request, scenario file:
```
	findService_geodetic_ellipse
```
4. Arc-band as a location in findService request, scenario file:
```
	findService_geodetic_arc-band
```
5. Polygon as a location in findService request, scenario file:
```
	findService_geodetic_polygon
```
6. Civic address as a location in findService request, scenario file:
```
	findService_civic_address
```


**Stimulus**

From 'Test System' send HTTP message to ECRF, example:
   * (TLS transport)
     > curl -X POST ECRF_URL -d "$(cat ../../Test_files/HTTP_messages/HTTP_LoST/findService_geodetic_polygon | sed -n '/<?xml/,$p' | tr -d '\n' | tr -d '\r')"
   * (TCP transport)
     > curl -X POST ECRF_URL -d "$(cat ../../Test_files/HTTP_messages/HTTP_LoST/findService_geodetic_polygon | sed -n '/<?xml/,$p' | tr -d '\n' | tr -d '\r')"


**Response**

1. Using Wireshark verify if ECRF sends correct LoST response (findServiceResponse) for the request.
2. Using Wireshark verify if findServiceResponse contain <serviceNumber>. When present, it's value must be "911"


**VERDICT:**
* PASSED - if all checks passed for variation
* FAILED - all other cases

### Test Postamble
#### Test System
* (TLS transport) stop all Openssl processes (if still running)
* (TCP transport) stop all Netcat processes (if still running)
* archive all logs generated
* stop Wireshark (if still running)
* remove all HTTP scenarios
* disconnect interfaces from ECRF
* (TLS transport) remove certificates

#### ECRF
* disconnect IF_ECRF_TS
* reconnect interfaces back to default

## Post-Test Conditions 
### Test System 
* Test tools stopped
* interfaces disconnected from ECRF

### ECRF
* device connected back to default
* device in normal operating state

## Sequence Diagram
[![](https://mermaid.ink/img/pako:eNpVkE1qAzEMha9itO34Al4ESn_IIoXSmVXxxtjKxLSWprK9CCF3rz1pSaKVBN-T9N4JPAcEA1prS55pH2djSakURVgefWHJRu3dd0ZLK5TxpyJ5fI5uFpc6fKkJc1HjMRdMerN5eHn6eDVqO03vasfjpKTrcrnyHdCNvNHd83lh6mdhgISSXAzt0VNfYKEcMKEF09rg5MuCpXPjXC08HsmDKVJxgLoEV_5fBbP6GGBx9Ml8nTHE5vPtksQayADCdT78EedfXT1hDQ?type=png)](https://mermaid.live/edit#pako:eNpVkE1qAzEMha9itO34Al4ESn_IIoXSmVXxxtjKxLSWprK9CCF3rz1pSaKVBN-T9N4JPAcEA1prS55pH2djSakURVgefWHJRu3dd0ZLK5TxpyJ5fI5uFpc6fKkJc1HjMRdMerN5eHn6eDVqO03vasfjpKTrcrnyHdCNvNHd83lh6mdhgISSXAzt0VNfYKEcMKEF09rg5MuCpXPjXC08HsmDKVJxgLoEV_5fBbP6GGBx9Ml8nTHE5vPtksQayADCdT78EedfXT1hDQ)


## Comments

Version:  010.3d.2.1.7

Date:     20241031


## Footnotes
[^1]: Openssl for Linux https://www.openssl.org/docs/
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt SIP over TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^4]: Netcat for Linux https://linux.die.net/man/1/nc
