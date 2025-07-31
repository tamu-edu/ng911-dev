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
* Requirements : RQ_ECRF_022, RQ_ECRF_046, RQ_ECRF_053
* Test Case    : TC_ECRF_LVF_002

### Requirements
IXIT config file for ECRF-LVF

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
<!--
[![](https://mermaid.ink/img/pako:eNpdUM0KgzAMfhXJWV9Axi7bhMF2UU-jIJmNP8y2UluGiO--agVxOeX7S0ImKBUniKHq1LdsUJvgkTIZuLonRZ4Vt0uanKLo7NDSOsqrg33XGvsmyGkwQTYOhoRXjlnPkeR_sV3b_Ifpqx9CEKQFttzdNy0CA9OQIAaxaznqDwMmZ-dDa1Q2yhJioy2FYHuOhq4tumUC4gq7wbE9ypdSOybeGqWf_gHrH0LQytbN5ph_zqhZ8g?type=png)](https://mermaid.live/edit#pako:eNpdUM0KgzAMfhXJWV9Axi7bhMF2UU-jIJmNP8y2UluGiO--agVxOeX7S0ImKBUniKHq1LdsUJvgkTIZuLonRZ4Vt0uanKLo7NDSOsqrg33XGvsmyGkwQTYOhoRXjlnPkeR_sV3b_Ifpqx9CEKQFttzdNy0CA9OQIAaxaznqDwMmZ-dDa1Q2yhJioy2FYHuOhq4tumUC4gq7wbE9ypdSOybeGqWf_gHrH0LQytbN5ph_zqhZ8g)
-->

![image](https://github.com/user-attachments/assets/4687d1e9-a486-43af-98d4-38e37c5aa48b)


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
* IUT is initialized with steps from IXIT config file
* IUT is active
* IUT is in normal operating state
* IUT is provisioned with service boundaries


## Test Sequence

### Test Preamble

#### Test System
* Install curl[^1]
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
     > curl -X POST https://ECRF_URL -H "Content-Type: application/xml" -d @SCENARIO_FILE_PATH
   * (TCP transport)
     > curl -X POST http://ECRF_URL -H "Content-Type: application/xml" -d @SCENARIO_FILE_PATH


**Response**

Variation 1-6

1. Using Wireshark verify if ECRF sends correct LoST response (XML body with findServiceResponse) for the request.
2. Using Wireshark verify if findServiceResponse contain `<serviceNumber>`. When present, it's value must be "911"


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
<!--
[![](https://mermaid.ink/img/pako:eNpVkF9LwzAUxb9KuE-K7WhrmtY8DGQqghsbrg8ieQntXVc0yUxTcI59d5POv3k6gd859557gNo0CBziOBa6NnrTtVxoQlRnrbHXtTO252QjX3sUeoR6fBtQ13jTydZKFeDTq7B3ZL3vHap4Or24nT3ecXJfVSuyWq4rcva0mJO58cqGhN6d_1oDGzx_Ir6sWZKQ5cM_c78zfgnvhggUWiW7xhc4hDQBbosKBXAvG2lfBAh99JwcnFnvdQ3c2QEjGHaNdN8VgI_9IthJ_WyM-oaw6Xz9xelA451GBPgB3oFnZTahBc3zMsuKNM_zIoI9cK8mJWNpwcqU-Q8tjhF8jKnJhJU0yTPKikvK0quURmDN0G5_Fmht6HKablE3aGdm0C6k0uMn5JiCnQ?type=png)](https://mermaid.live/edit#pako:eNpVkF9LwzAUxb9KuE-K7WhrmtY8DGQqghsbrg8ieQntXVc0yUxTcI59d5POv3k6gd859557gNo0CBziOBa6NnrTtVxoQlRnrbHXtTO252QjX3sUeoR6fBtQ13jTydZKFeDTq7B3ZL3vHap4Or24nT3ecXJfVSuyWq4rcva0mJO58cqGhN6d_1oDGzx_Ir6sWZKQ5cM_c78zfgnvhggUWiW7xhc4hDQBbosKBXAvG2lfBAh99JwcnFnvdQ3c2QEjGHaNdN8VgI_9IthJ_WyM-oaw6Xz9xelA451GBPgB3oFnZTahBc3zMsuKNM_zIoI9cK8mJWNpwcqU-Q8tjhF8jKnJhJU0yTPKikvK0quURmDN0G5_Fmht6HKablE3aGdm0C6k0uMn5JiCnQ)
-->

![image](https://github.com/user-attachments/assets/af2b3306-7af6-4bb8-aba9-fd103543fcd7)


## Comments

Version:  010.3d.3.1.9

Date:     20250425


## Footnotes
[^1]: Curl: https://curl.se/download.html
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt SIP over TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
