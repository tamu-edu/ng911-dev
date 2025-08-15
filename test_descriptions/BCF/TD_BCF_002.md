# Test Description: TD_BCF_002
## Overview
### Summary
Discrepancy Reporting support

### Description
This tests checks if BCF supports Discrepancy Report function

### HTTP transport types
Test can be performed with 2 different HTTP transport types. Steps describing actions for specific one are marked as following:
- (TLS transport) - used by default inside ESInet on production environment
- (TCP transport) - used in lab for testing purposes only if default TLS is not possible

### References
* Requirements : RQ_BCF_009
* Test Case    : TC_BCF_002

### Requirements
IXIT config file for BCF

## Configuration
### Implementation Under Test Interface Connections
<!-- Identify each of the FEs that are part of the configuration and how they are connected -->
* O-BCF
  * IF_O-BCF_ESRP - connected to Test System IF_ESRP_O-BCF
* Test System ESRP
  * IF_ESRP_O-BCF - connected to IF_O-BCF_ESRP

### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* O-BCF
  * IF_O-BCF_ESRP - Active
* Test System ESRP
  * IF_ESRP_O-BCF - Active

 
### Connectivity Diagram
<!--
[![](https://mermaid.ink/img/pako:eNplkdFPgzAQxv8Vcs9AENoCjfHB6ZIlGs3waSFZKnRAXFtSShQJ_7sdODXznu6-fL_7LrkRClVyoHA4qveiZto4D9tcOrY26_2Td7ta7--z7fO1591slnZRF0_Xv1aatbXzR_vHLjKX5QXzwjvjZENnuHB-fd_4ZZLFwYVKNyVQo3vuguBasNMI48mSg6m54DlQ25ZMv-WQy8kyLZM7pcQZ06qvaqAHduzs1LclM_yuYfYk8aNqm8b1SvXSAI3ieQfQET6AEuLHEY4SEoQRTjAJXRiAJshPcURIkOKrMEIxmlz4nEMDPwlQbGWE0yRBBCEXWG9UNsjifBIvG6P04_KI-R_TF9BteQM?type=png)](https://mermaid.live/edit#pako:eNplkdFPgzAQxv8Vcs9AENoCjfHB6ZIlGs3waSFZKnRAXFtSShQJ_7sdODXznu6-fL_7LrkRClVyoHA4qveiZto4D9tcOrY26_2Td7ta7--z7fO1591slnZRF0_Xv1aatbXzR_vHLjKX5QXzwjvjZENnuHB-fd_4ZZLFwYVKNyVQo3vuguBasNMI48mSg6m54DlQ25ZMv-WQy8kyLZM7pcQZ06qvaqAHduzs1LclM_yuYfYk8aNqm8b1SvXSAI3ieQfQET6AEuLHEY4SEoQRTjAJXRiAJshPcURIkOKrMEIxmlz4nEMDPwlQbGWE0yRBBCEXWG9UNsjifBIvG6P04_KI-R_TF9BteQM)
-->

![image](https://github.com/user-attachments/assets/d82e9c3a-4689-4761-bb40-f8d985effae6)



## Pre-Test Conditions

### O-BCF
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Default configuration is loaded
* Device is initialized with steps from IXIT config file
* Device is active
* Device is in normal operating state
* No active calls

### Test System ESRP
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* No active calls


## Test Sequence
### Test Preamble

#### Test System ESRP
* Install cURL [^1]
* Install Wireshark[^2]
* Copy to local storage Discrepancy Report JSON body:
  > discrepancy_report_example_v010.3f.3.0.1.json
* (TLS transport) Copy to local storage TLS certificate and private key files used to decrypt HTTP packets within ESInet:
  > cacert.pem
  > cakey.pem
* (TLS transport) Copy to local storage PCA certificate for mTLS:
  > PCA.crt
* (TLS transport) Configure Wireshark to decode HTTP over TLS packets[^3]
* Using Wireshark on 'Test System ESRP' start packet tracing on IF_ESRP_O-BCF interface - run following filter:
   * (TLS transport)
     > ip.addr == IF_ESRP_O-BCF_IP_ADDRESS and tls
   * (TCP transport)
     > ip.addr == IF_ESRP_O-BCF_IP_ADDRESS and http


### Test Body

#### Stimulus
Send HTTP POST with Discrepancy Report to O-BCF:
* (TCP transport)
  ```
  curl -X POST https://IF_ESRP_O-BCF_IP_ADDRESS:PORT/Reports -H "Content-Type: application/json" -d @discrepancy_report_example_v010.3f.3.0.1.json
  ```
* (TLS transport)
  ```
  curl --cert cacert.pem --key cakey.pem --cacert PCA.crt --tlsv1.2 -X POST https://IF_ESRP_O-BCF_IP_ADDRESS:PORT/Reports -H "Content-Type: application/json" -d @discrepancy_report_example_v010.3f.3.0.1.json
  ```

#### Response
Verify if O-BCF responds with HTTP 201 Report Successfully Created containing JSON body with:
- respondingAgencyName with FQDN value
- respondingContactJcard with jCard format value
- (optional) respondingAgentId with string value
- (optional) responseEstimatedReturnTime with timestamp (example: `2015-08-21T12:58:03.01-05:00`) as a value
- (optional) responseComments with string value

VERDICT:
* PASSED - if all checks passed for variation

### Test Postamble
#### O-BCF
* disconnect IF_O-BCF_ESRP
* reconnect interfaces back to default

#### Test System ESRP
* stop Wireshark (if still running)
* archive traced packets in Wireshark
* remove certificate files
* disconnect interfaces from O-BCF
* (TLS transport) remove certificates

## Post-Test Conditions
### O-BCF
* device connected back to default
* device in normal operating state

### Test System ESRP
* Test tools stopped
* interfaces disconnected from O-BCF

## Sequence Diagram
<!--
[![](https://mermaid.ink/img/pako:eNpdkU1PwzAMQP9K5Cvt1CzrVw6TYANxQZvWnlAuUet1BZKMNJUYVf87acc4cHPs95w4HqAyNQKHMAyFrow-tg0XmhDVWmvsfeWM7Tg5yo8OhZ6hDj971BVuW9lYqSaYkBI7R4pL51CRx-KwD9frXfiweeLkuSz3ZL8rSnJHtgfy1hl9Vea65_6rv8oyot6YcAigsW0N3NkeA1BolZyOMEyNBLgTKhTAfVhL-y5A6NE7Z6lfjVE3zZq-OQGfJwmgP9fS3Ub4y1rUNdqN6bUDvsyTuQnwAb6Ap9GC0jhKMkYpZRnzxQvwPF7EySpLWRozyuI0HwP4nm-NFknswYSxLKVRmq3yAGTvTHHR1e1NWLf-f1-uG5gXMf4AFNl62w?type=png)](https://mermaid.live/edit#pako:eNpdkU1PwzAMQP9K5Cvt1CzrVw6TYANxQZvWnlAuUet1BZKMNJUYVf87acc4cHPs95w4HqAyNQKHMAyFrow-tg0XmhDVWmvsfeWM7Tg5yo8OhZ6hDj971BVuW9lYqSaYkBI7R4pL51CRx-KwD9frXfiweeLkuSz3ZL8rSnJHtgfy1hl9Vea65_6rv8oyot6YcAigsW0N3NkeA1BolZyOMEyNBLgTKhTAfVhL-y5A6NE7Z6lfjVE3zZq-OQGfJwmgP9fS3Ub4y1rUNdqN6bUDvsyTuQnwAb6Ap9GC0jhKMkYpZRnzxQvwPF7EySpLWRozyuI0HwP4nm-NFknswYSxLKVRmq3yAGTvTHHR1e1NWLf-f1-uG5gXMf4AFNl62w)
-->

![image](https://github.com/user-attachments/assets/a2d6f3ef-ec83-4b63-abc9-7bda5375a471)


## Comments

Version:  010.3d.3.2.7

Date:     20250728


## Footnotes
[^1]: cURL - tool for transfering data with URL syntax https://curl.se/
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt SIP over TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
