# Test Description: TD_PS_009
## Overview
### Summary
FE's sending of HTTP GET /Versions to Policy Store

### Description
Test verifies if any Functional Element using Policy Store sends HTTP GET to /Versions entrypoint

### References
* Requirements : PS_015
* Test Purpose : 
* Test Case    : 

### HTTP transport types
Test can be performed with 2 different HTTP transport types. Steps describing actions for specific one are marked as following:
- (TLS) - used by default inside ESInet on production environment
- (TCP) - used if default TLS is not possible

## Configuration
### Implementation Under Test Interface Connections
<!-- Identify each of the FEs that are part of the configuration and how they are connected -->
* Functional Element using Policy Store (FE)
  * IF_FE_TS - connected to Test System IF_TS_FE
* Test System
  * IF_TS_FE - connected to FE IF_FE_TS

### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* Test System 
  * IF_TS_FE - Active
* Functional Element using Policy Store (FE)
  * IF_FE_TS - Active
 
### Connectivity Diagram
[![](https://mermaid.ink/img/pako:eNpdUNFqhDAQ_JWwz94R9RpNKH2qQqGFUu-pCEdqcirVRGJCa8V_b6qF3nWfZmd2dpadodJCAoNzpz-qhhuLHl9KhXw95Kdjccqz293uzuM88-2mjO6tNnxo0FGOFhXTaGW_KZe-jZFK_DPlGXJjq2r0rLu2mlBhtZFX9osob4cAeml63gp_5vxDl2Ab2csSmIeCm_cSSrX4Oe6sLiZVAbPGyQDcILiV9y33yT2wM-9Gzw5cvWr910vR-hOetj-s71hngM3wCSyMyD4klNIkxpSmNIkCmIB5NsYRDqOUUoxpeCBLAF_r2sM-IoTgJCFhnMb4JgnAaFc3v4HLNyS5b3s?type=png)](https://mermaid.live/edit#pako:eNpdUNFqhDAQ_JWwz94R9RpNKH2qQqGFUu-pCEdqcirVRGJCa8V_b6qF3nWfZmd2dpadodJCAoNzpz-qhhuLHl9KhXw95Kdjccqz293uzuM88-2mjO6tNnxo0FGOFhXTaGW_KZe-jZFK_DPlGXJjq2r0rLu2mlBhtZFX9osob4cAeml63gp_5vxDl2Ab2csSmIeCm_cSSrX4Oe6sLiZVAbPGyQDcILiV9y33yT2wM-9Gzw5cvWr910vR-hOetj-s71hngM3wCSyMyD4klNIkxpSmNIkCmIB5NsYRDqOUUoxpeCBLAF_r2sM-IoTgJCFhnMb4JgnAaFc3v4HLNyS5b3s)

## Pre-Test Conditions
### Test System
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* ng911 repository cloned to local storage
* (TLS) Generated own PCA-signed certificate and private key files (test_system.crt, test_system.key)
* (TLS) Certificate and key used by FE copied to local storage
* (TLS) PCA certificate copied to local storage

### Functional Element using Policy Store (FE)
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Default configuration is loaded
* Device is active
* Device is in normal operating state
* do backup of current configuration
* FE has configured Test System as it's Policy Store

## Test Sequence

### Test Preamble

#### Test System
* Install Wireshark[^1]
* (TLS v1.2) Configure Wireshark to decode HTTP over TLS, use tests system and PS certificate keys [^2]
* (TLS v1.3) Configure logging of session keys and configure Wireshark to decode HTTP over TLS [^3]
* Using Wireshark on 'Test System' start packet tracing on IF_TS_FE interface - run following filter:
   * (TLS)
     > ip.addr == IF_TS_FE_IP_ADDRESS and tls
   * (TCP)
     > ip.addr == IF_TS_FE_IP_ADDRESS and http

### Test Body

#### Stimulus
Restart Functional Element

#### Response
Using Wireshark verify if Functional Element sent HTTP GET to /Verions entrypoint to Test System

VERDICT:
* PASSED - if FE sent HTTP GET /Versions to Test System
* FAILED - any other cases


### Test Postamble
#### Test System
* stop Wireshark (if still running)
* archive all logs generated
* disconnect interfaces from IUT
* (TLS) remove certificates

#### Functional Element using Policy Store (FE)
* disconnect interfaces from Test System
* reconnect interfaces back to default
* restore previous configuration

## Post-Test Conditions
### Test System 
* Test tools stopped
* interfaces disconnected from IUT

### Functional Element using Policy Store (FE)
* device connected back to default
* device in normal operating state
* configuration is restored

## Sequence Diagram
[![](https://mermaid.ink/img/pako:eNpFj0FvgzAMhf9K5OugCtAFkkOlSeu2y6RKcJpyicClUUvShUQaQ_z3pXTTfLKtz37vzdDaDkFAmqbStNYcdS-kIWTQzln31HrrRkGO6jKiNCs04mdA0-KzVr1Tww2-18uehFGbnhzsRbcTqeMtprvdQ4OjJ_U0ehwEeWuaA3ndN5DAgG5Quovq8-2LBH_CASWI2HbKnSVIs0ROBW_rybQgvAuYQLh2yv_pg1jNJXBV5sPa_xk7HQ283-OtKVcGxAxfILKcbTLGOS8LynnFyzyBCUTcFjSnWV5xTinPtmxJ4Ht9u93kjDFaliwrqoI-lgk4G_rTr-DyA6l_Zo8?type=png)](https://mermaid.live/edit#pako:eNpFj0FvgzAMhf9K5OugCtAFkkOlSeu2y6RKcJpyicClUUvShUQaQ_z3pXTTfLKtz37vzdDaDkFAmqbStNYcdS-kIWTQzln31HrrRkGO6jKiNCs04mdA0-KzVr1Tww2-18uehFGbnhzsRbcTqeMtprvdQ4OjJ_U0ehwEeWuaA3ndN5DAgG5Quovq8-2LBH_CASWI2HbKnSVIs0ROBW_rybQgvAuYQLh2yv_pg1jNJXBV5sPa_xk7HQ283-OtKVcGxAxfILKcbTLGOS8LynnFyzyBCUTcFjSnWV5xTinPtmxJ4Ht9u93kjDFaliwrqoI-lgk4G_rTr-DyA6l_Zo8)

## Comments

Version:  010.3f.3.0.1

Date:     20250214

## Footnotes
[^1]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^2]: Wireshark configuration to decrypt TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^3]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518
