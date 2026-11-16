# Test Description: TD_BRIDGE_009

## Overview
### Summary
Verification of JWS Protected Header algorithm and certificate chain in LogEvents sent by BRIDGE

### Description
Test covers that BRIDGE, when sending LogEvents to the Logging Service, forms a JWS Protected Header that:
* contains exactly one "alg" field set to "EdDSA" (signed) or "none" (unsigned)
* for signed LogEvents — includes the signing entity's X.509 certificate with all intermediate certificates up to the 
  trusted root, either by value (x5c) or by reference (x5u + x5t#256)

### References
* Requirements : RQ_BRG_144, RQ_BRG_146
* Test Case    : TC_BRIDGE_009

### Requirements
IXIT config file for IUT

### HTTP transport types
Test can be performed with 2 different SIP and HTTP transport types. Steps describing actions for specific one are marked as following:
- (TLS) - used by default inside ESInet on production environment
- (TCP) - used if default TLS is not possible

## Configuration
### Implementation Under Test Interface Connections
<!-- Identify each of the FEs that are part of the configuration and how they are connected -->
* Test System CHFE
  * IF_CHFE_BRIDGE - connected to IF_BRIDGE_CHFE
* BRIDGE
  * IF_BRIDGE_CHFE - connected to IF_CHFE_BRIDGE
  * IF_BRIDGE_LOG - connected to IF_LOG_BRIDGE
  * IF_BRIDGE_PS - connected to IF_PS_BRIDGE
* Test System Logging Service
  * IF_LOG_BRIDGE - connected to IF_BRIDGE_LOG
* Test System Policy Store
  * IF_PS_BRIDGE - connected to IF_BRIDGE_PS

### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* Test System CHFE
  * IF_CHFE_BRIDGE - Active
* BRIDGE
  * IF_BRIDGE_CHFE - Active
  * IF_BRIDGE_LOG - Active
  * IF_BRIDGE_PS - Active
* Test System Logging Service
  * IF_LOG_BRIDGE - Active
* Test System Policy Store
  * IF_PS_BRIDGE - Active

### Connectivity Diagram
<!--
https://mermaid.live/edit#pako:eNqNkl1vgjAUhv9KcxLjDRoUVCDLLubXTFxmZFdLE9NBxUZoTSmbjvDfVxG_l2VcNO3bt-95Wk4OgQgpeFCr5Ywz5aG8rlY0oXUP1UMi13UDYYiFWGPwMAQxSVMWYCiKWg3zZSy-ghWRCk3nmCP9TUaL_vNouHiaTwbj4UOj8aiVw6LcOLkqbfo6rkx6Vom3nplfWWb-leMwptlHJMlmhd5oqpC_SxVN0LnUPdRBpzzE_I-EqYgixiPkU_nJAnoVdouqs448N4mXrutL3RGeH-Q3eeb_D3smYhbskK-EvGa-eTudAwZEkoXgKZlRAxIqE7JfQl5eBMo20H9dTyUNs21j3w6NQMRCYsC80Oc3hL8LkYC3JHGqM6TIotVplW1CouiAEY154dGlqeyLjCvwWmbbAJIp4e94cCShIdP4L4e-LNuzrAReDlt9pNt0em3Xdp2OpQfT7Bmw07JlNq2u7bStntlxWm2nMOC7ZDObju26Zs9pdexO13JN-4g2LAtVZMUPpnfnpg
-->

![image](../_assets/BRIDGE/TD_BRIDGE_009_Connectivity_Diagram.png)


## Pre-Test Conditions

### Test System CHFE/Test System Logging Service/Test System Policy Store
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device is active
* ng911 repository cloned to local storage
* (TLS) Generated own PCA-signed certificate and private key files (test_system.crt, test_system.key)
* (TLS) Certificate and key used by CHFE copied to local storage
* (TLS) PCA certificate copied to local storage

### BRIDGE
* Interfaces are connected to network
* Interfaces have IP addresses assigned by DHCP
* Device configured to use Test System Logging Service as a Logging Service
* Device is active
* Device is in normal operating state
* IUT is initialized using IXIT config file

## Test Sequence
### Test Preamble

#### Test System CHFE
* Install SIPp by following steps from documentation[^1]
* Copy following XML scenario file to local storage:

  `SIP_INVITE_with_CANCEL.xml`
  `SIP_SUBSCRIBE_ServiceState.xml`

* Install Wireshark[^2]
* (TLS v1.2) Configure Wireshark to decode SIP over TLS, use tests system and IUT certificate keys [^3]
* (TLS v1.3) Configure logging of session keys and configure Wireshark to decode SIP over TLS [^4]
* Using Wireshark on 'Test System' start packet tracing on IF_CHFE_BRIDGE interface - run following filter:
   * (TLS)
     > ip.addr == IF_CHFE_BRIDGE_IP_ADDRESS and tls
   * (TCP)
     > ip.addr == IF_CHFE_BRIDGE_IP_ADDRESS and sip

#### Test System Logging Service
* Install Wireshark[^2]
* Install OpenSSL v1.1.1 or higher[^5].
* (TLS v1.2) Configure Wireshark to decode HTTP over TLS, use tests system and BRIDGE certificate keys [^3]
* (TLS v1.3) Configure logging of session keys and configure Wireshark to decode HTTP over TLS [^4]
* Using Wireshark on 'Test System' start packet tracing on IF_LOG_BRIDGE interface - run following filter:
   * (TLS)
     > ip.addr == IF_LOG_BRIDGE_IP_ADDRESS and tls
   * (TCP)
     > ip.addr == IF_LOG_BRIDGE_IP_ADDRESS and http
* The Logging Service must be configured to accept and process HTTP POST requests. To verify this manually, you can simulate a listening HTTP endpoint on port 8080 using command in the terminal:
    * Step 1 - Prepare logEventId and JSON body
      ```
      ID="urn:emergency:uid:logid:$(date +%s%N):logger.state.pa.us"
      BODY="{\"logEventId\":\"$ID\"}"
      ```
    * Step 2 - Run server:
      * (TLS)
      ```
      python3 http_entry.py --ip IF_LOG_BRIDGE --port 4443 --role RECEIVER --path /LogEvents --method POST --body "$BODY" --content_type application/json --response_code 201 --server_cert /tmp/cert.crt --server_key /tmp/cert.key
      ```
      * (TCP)
      ```
      python3 http_entry.py --ip IF_LOG_BRIDGE --port 8080 --role RECEIVER --path /LogEvents --method POST --body "$BODY" --content_type application/json --response_code 201
      ```
    * Step 3 - In another terminal, send a POST request to verify it is working:
      * (TLS)
      ```
      curl -k -X POST https://localhost:4443/LogEvents -d '{"log":"test"}'
      ```   
      * (TCP)
      ```
      curl -X POST http://localhost:8080/LogEvents -d '{"log":"test"}'
      ```   

#### Test System Policy Store
* Install Wireshark[^2]
* Copy following XML file to local storage:
  ```
     XACML_ServiceState.xml
  ```
* Edit the `XACML_ServiceState.xml` scenario file, find and change following string values:
  * `ALLOWED_FQDN` -> change to FQDN of the Test System CHFE
  * `IUT_FQDN` -> change to FQDN of the BRIDGE
* (TLS v1.2) Configure Wireshark to decode HTTP over TLS, use tests system and BRIDGE certificate keys [^3]
* (TLS v1.3) Configure logging of session keys and configure Wireshark to decode HTTP over TLS [^4]
* Using Wireshark on 'Test System' start packet tracing on IF_PS_BRIDGE interface - run following filter:
   * (TLS)
     > ip.addr == IF_PS_BRIDGE_IP_ADDRESS and tls
   * (TCP)
     > ip.addr == IF_PS_BRIDGE_IP_ADDRESS and http
* Prepare certificate files to be used for JWS generation:
  * Variation 2 (unsupported algorithm for JWS):
    ```
    openssl genrsa -out test_system.key 2048
    ```
    ```
    openssl req -new -key test_system.key -out test_system.csr -sha256 -subj "/C=US/ST=Texas/L=College Station/O=TAMU/CN=ps.ng911.dev.lab"
    ```
    ```
    openssl req -new -in test_system.csr -CA PCA.crt -CAkey PCA.key -CAcreateserial -out test_system.crt -days 1 -sha256
    ```
  * Variation 3 (correct):
    ```
    openssl genpkey -algorithm Ed448 -out test_system.key
    ```
    ```
    openssl req -new -key test_system.key -out test_system.csr -subj "/C=US/ST=Texas/L=College Station/O=TAMU/CN=ps.ng911.dev.lab"
    ```
    ```
    openssl req -new -in test_system.csr -CA PCA.crt -CAkey PCA.key -CAcreateserial -out test_system.crt -days 1
    ```
* The Policy Store must be configured to accept and process HTTP GET requests.
  * generate JWS object and save to file jws.json, example:
  ```
  python3 -m main generate_jws XACML_ServiceState.xml --cert test_system.crt --key test_system.key --output_file jws.json
  ```
  * simulate a listening HTTP endpoint on port 8080 using command in the terminal:
  * (TLS):
    * `python3 http_entry.py --ip IF_PS_BRIDGE --port 4443 --role RECEIVER --path /Policies?policyType=ServiceState --method GET --body jws.json --server_cert test_system.crt --server_key test_system.key`
  * (TCP):
    * `python3 http_entry.py --ip IF_PS_BRIDGE --port 8080 --role RECEIVER --path /Policies?policyType=ServiceState --method GET --body jws.json`

    
### Test Body

#### Variations
1. JWS with LogEvents sent by the BRIDGE
2. Rejecting policy JWS signed by a certificate using unsupported algorithm
3. Applying XACML policies from correct JWS

#### Stimulus

##### Variation 1
Run SIPp scenario by using following command on Test System CHFE, example:
  * (TLS transport)
    ``` 
    sudo sipp -t l1 -i IF_CHFE_BRIDGE_IPv4 -p 5061 -bind_local -tls_cert test_system.crt -tls_key test_system.key -sf 
    SIP_INVITE_with_CANCEL.xml IF_BRIDGE_CHFE_IPv4:5061
    ```
  * (TCP transport)
    ```
    sudo sipp -t t1 -i IF_CHFE_BRIDGE_IPv4 -p 5060 -bind_local -sf SIP_INVITE_with_CANCEL.xml IF_BRIDGE_CHFE_IPv4:5060
    ```

##### Variations 2-3
1. Restart BRIDGE to trigger fetching policies from the Test System Policy Store
2. From 'Test System CHFE' start subscription to emergency-ServiceState event - run following SIPp scenario file, example command:
  * (TLS transport)
    ``` 
    sudo sipp -t l1 -timeout 7s -i IF_CHFE_BRIDGE_IPv4 -p 5061 -bind_local -tls_cert test_system.crt -tls_key test_system.key -sf 
    SIP_SUBSCRIBE_ServiceState.xml IF_BRIDGE_CHFE_IPv4:5061
    ```
  * (TCP transport)
    ```
    sudo sipp -t t1 -timeout 7s -i IF_CHFE_BRIDGE_IPv4 -p 5060 -bind_local -sf SIP_SUBSCRIBE_ServiceState.xml IF_BRIDGE_CHFE_IPv4:5060
    ```

#### Response

##### Variation 1

Using traced packets on Wireshark check:
* If BRIDGE sends HTTP POST to Test System Logging Service with JWS body. Then decode JWS fields from Base64url and verify the following:
  * The "payload" field decoded from Base64url contains a valid LogEvent JSON object (e.g. CallSignalingMessageLogEvent). This confirms the JWS wraps actual LogEvent content.
  * Decode the "protected" field from Base64url into a raw string;
  * Verify that the raw decoded string contains the exact substring "alg" only once (to prevent duplicate key injection like {"alg": "none", "alg": "EdDSA"} );
  * Parse the raw string into a JSON object and verify the value of the "alg" field is either:
    * "none";
    * "EdDSA";
    * no other values are permitted for the "alg" field.

  * If "protected" contains "alg": "none":
    * check that "signature" is an empty string
  
  * If "protected" contains "alg": "EdDSA":
    * check if "signature" contains non-empty string value
    * using PCA-signed key file used by BRIDGE verify if JWS object is properly signed, use decode_jws method, example command:
      
    ```
           python3 -m main decode_jws JWS_FILE_PATH --key BRIDGE.key --password pass123
    ```

    * verify if method did not return any decoding errors
    * verify if key file used by BRIDGE for JWS signing is Edwards-curve Digital Signature Algorithm with Curve448, run example command:
    ```
       openssl pkey -in BRIDGE.key -text -noout
    ```
      Command must return "ED448", example:
    ```
    ED448 Private-Key:
    priv:
        cb:18:b3:9a:3a:09:ba:87:ad:86:79:0c:84:08:79:
        2a:16:31:76:19:a1:0f:92:1e:11:e5:7f:2c:7a:01:
        66:7e:f8:2a:04:47:8a:da:25:c2:c8:99:3a:52:20:
        37:54:a5:ea:d9:1d:a0:70:29:d8:3b:20
    pub:
        07:cc:7b:cc:d0:ff:e6:1c:79:fc:65:df:18:fc:f2:
        89:15:db:68:6a:08:2c:b6:7d:20:45:e8:81:64:b6:
        4c:8f:62:f1:63:df:f5:b3:38:ea:14:d4:28:0a:2b:
        88:62:7d:32:ed:c3:ab:8d:fc:a3:e0:80
    ```
    * The Protected Header shall contain one of the following keys:
      * `x5c` - with value being an array with X.509 certificate and all intermediate certificates up to one signed 
        by the trusted root. Example:
      ```
        {
            "alg": "EdDSA",
            "x5c": ["BASE64_CERT", "BASE64_INTERMEDIATE_CERT"]
        }
      ```
      * `x5u` with string value containing a valid URL pointing to a certificate chain.
        `x5u` field MUST be used with `x5t#256` field - the SHA-256 thumbprint of the certificate, to allow detection of when the certificate chain needs to be retrieved. Example:
          ```
          {
          "alg": "EdDSA",
          "x5u": "https://certs.example.agency.gov/bridge-signing.crt",
          "x5t#256": "BASE64URL_SHA256_THUMBPRINT"
          }
          ```
        * Verify the `x5u` URL is resolvable and download the certificate chain (respons 200):
            ```
            curl -o cert_chain.pem <x5u_URL_value>
            ```
        * Verify the downloaded chain is complete up to the PCA root — inspect certificates in the chain
        * Extract the leaf certificate (first in chain) and compute its SHA-256 thumbprint:
           ```
          openssl x509 -in cert_chain.pem -outform DER | openssl dgst -sha256 -binary | base64 | tr '+/' '-_' | tr -d '='
          ```
          Output MUST match the value in "x5t#256" field of the Protected Header

##### Variation 2

Using traced packets on Wireshark check:
* If BRIDGE did not apply provided XACML policy - SIP SUBSCRIBE request from Test System CHFE is rejected with 4xx error

##### Variation 3

Using traced packets on Wireshark check:
* If BRIDGE applied provided XACML policy - SIP SUBSCRIBE request from Test System CHFE is accepted and BRIDGE sends SIP NOTIFY with Event: emergency-ServiceState back to the Test System CHFE

VERDICT:
* PASSED - if all checks passed
* FAILED - any other cases

### Test Postamble
#### Test System CHFE
* stop SIPp (if still running)
* stop Wireshark (if still running)
* archive all logs generated
* disconnect interfaces from IUT
* (TLS) remove certificates

#### Test System Logging Service/Test System Policy Store
* stop Wireshark (if still running)
* archive all logs generated
* disconnect interfaces from IUT
* (TLS) remove certificates

#### BRIDGE
* restore default configuration
* disconnect interfaces from Test Systems
* reconnect interfaces back to default

## Post-Test Conditions
### Test System CHFE/Test System Logging Service/Test System Policy Store
* Test tools stopped
* interfaces disconnected from IUT

### BRIDGE
* device connected back to default
* device in normal operating state

## Sequence Diagram
<!--
https://mermaid.live/edit#pako:eNrVVV1v2koQ_SujlaK0ikltnBSw1FTEIalv84EwaXuv_LJdL86qZtd3dx2FIv57xzYUlLhpnirVL_jjzJkzM4edJWEq5SQgnU4nkUzJmciCRALMhdZKD5lV2gQwo7nhiaxBe3tLIYUNYLlv7_ic7wewn1L9bd-BhORKfUtIkBCWU2MES8hqtbeXyEQa_n_JJeNngmaazqsczVVQbQUTBZUWwg_nI6AGptxYiBfG8nn9rh19OonOLmp8c9eOury5eEx5qbJMyAxiru8F4-1x4_hx2Fjlgi0gxp7sxFwry0Hdc10rdTAugE9UC2qFkuD9GtiIDiDUnFpuIMTuc131qEJv4yp05-RkA4-jMUTXn6LpCF7thJzTalYLuJ1EDsRn49dbgiaygxwVVQC-24UrFJJidfNCaRSbL2oyiyRgRBHsiInSA2FmipXmKeXJyQG2N4AP0-kYxjfxFN5gb0f3XFqDhDTPY5FJ_MFuX3FjaMY333fIkKJi2hRYk3VdDzZQiEvGMHpW5qizGh5PK0v9rrHDmcV3XRcMZ8Ao1pIbQM-Crrxo7JMWH-z2OBxeh6PLtpKbLlaYruvCzcct5qWu6LYBN8knKA19CNHtFKwCqwUWrKFo3Dfjlt1hO1uEVTnq5l2McBC1WwU375vA6aLg79aGjy0abkswjnfste5-VRccwD-fY_gyDK8u4dUkHqI1MsnT18-pj_AU0Zqjj9aChQGpLNCiyEU1t2dsHd-exuEkOkVn14MPAM8XnaELF51d6W1G3A7l6OHhpXPw_8I5jNKzn5PAesIhKqOM0685f3Yw4ZOx_LmRPP6ftECub6bR-b8vz9KitclCHJJpkZLA6pI7BHnmtHokyyo4IfXSwh2Ft5qn5UOnWl4dpnKlE5LIFcbj-f-fUnMS1HvPIVqV2d3Pp7JIUcp6j20xXKZch6qUlgSed-QQWloVLyTbKOGpwBP6qtm39dqtM5FgSR5I4LuHfr_XO_IG3ttj1z8e-A5ZIJPfPxy4Xtf13V7X7R8PVg75XmvzDt2-1-v3PHfg9443skZ1krWq1Q-hXlpf
-->

![image](../_assets/BRIDGE/TD_BRIDGE_009_Sequence_Diagram.png)

## Comments

Version:  010.3d.5.0.0

Date:     20261013

## Footnotes

[^1]: SIPp - tool for SIP packet simulations. Official documentation: https://sipp.sourceforge.net/doc/reference.html#Getting+SIPp
[^2]: Wireshark - tool for packet tracing and anaylisis. Official website: https://www.wireshark.org/download.html
[^3]: Wireshark configuration to decrypt TLS packets: https://www.zoiper.com/en/support/home/article/162/How%20to%20decode%20SIP%20over%20TLS%20with%20Wireshark%20and%20Decrypting%20SDES%20Protected%20SRTP%20Stream
[^4]: TLS v1.3 session keys logging + Wireshark configuration to decrypt traffic: https://my.f5.com/manage/s/article/K50557518
[^5]: OpenSSL v1.1.1 or higher - toolkit required for TLS operations and certificate/key handling. Official website and downloads: https://www.openssl.org/source/ . Installation documentation: https://github.com/openssl/openssl/blob/master/INSTALL.md