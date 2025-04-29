# NG911 Test Suite

## Overview
The **NG911 Test Suite** is a custom testing framework designed to conduct automated tests on NG911 systems according to the **NENA 911** standard. It provides structured testing for various scenarios, ensuring compliance and reliability.

## Features
- Automated testing for NG911 systems
- Configurable test scenarios
- Support for PCAP-based and live-capture testing
- SIP and HTTP(S) message transmission and reception
- Comprehensive reporting (PDF, DOCX, XML, JSON, CSV)
- Centralized logging with flexible verbosity levels

## Installation
### Prerequisites
Ensure you have the following installed:
- Python 3.8+
- Required dependencies (see `requirements.txt`)

### Steps
1. Clone the repository:
   ```sh
   git clone https://github.com/tamu-edu/ng911-exp
   cd test_suite
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
   or
    ```sh
   pip3 install -r requirements.txt
   ```
3. Run tests or start services as needed.

## Usage
### Running Tests
To validate a configuration file:
```sh
python3 -m main validate test_files/configs/base_config.yaml --output_file_path output.txt
```
To execute a test using a configuration file:
```sh
python3 -m main run test_files/configs/base_config.yaml
```
To run an individual test case:
```sh
python3 -m main run_test BCF_001
```

## Configuration
The framework requires configuration files to define test scenarios. The main configuration file should specify test and lab configurations.

Example structure:
```yaml
lab_config:
  entities:
    - name: "O-BCF-1"
      type: "BCF"
      fqdn: ""
      certificate_file: "test_files/test_certs/esrp-1.test.example.com.crt"
      interfaces:
        - name: "IF_O-BCF-1_OSP"
          fqdn: "obcf1.test.example.com"
          ip: "192.168.200.200"
          port_mapping:
            - protocol: "TLSv1.3"
              port: 5061
```

## Main Services
### **ConfigService**
The `ConfigService` is responsible for loading, parsing, and validating configuration files for test execution. It ensures that test and lab configurations are properly structured and error-free before running tests.

### **TestOracle**
The `TestOracle` service orchestrates test execution. It takes a `TestConfig` and `LabConfig` as input, prepares test scenarios, runs them, and collects verdicts. It also generates final reports summarizing test results.

### **Test Conduction Service**
The `TestScenarioConductionService` is responsible for executing individual test scenarios within a test suite. It manages interactions with test modules and collects intermediate results.

### **SIP Receiver and Sender Services**
- `SipSenderService`: Sends SIP messages using UDP or TCP.
- `SipReceiverService`: Listens for incoming SIP messages and processes them accordingly.

### **HTTP(S) Receiver and Sender Services**
- `HttpRequestService`: Sends HTTP(S) requests (GET, POST, PUT, DELETE) with optional SSL support.
- `HttpReceiverService`: Hosts an HTTP(S) server that can handle GET, POST, PUT, and DELETE requests, making it useful for testing NG911 interactions.

### **PCAP Capture Service**
The `PcapCaptureService` allows packet capture from a network interface or PCAP file, enabling in-depth analysis of test case execution.

### **Logging Service**
The `LoggerService` provides centralized logging for all components, redirecting print statements and warnings into structured log files. It supports different verbosity levels and output options.

### **Report Service**
The `ReportService` generates test execution reports in various formats, including PDF, DOCX, XML (JUnitXML), JSON, and CSV.

## Logging
The framework uses a structured logging system. Logs are written to a specified output file and displayed in the console with adjustable verbosity levels. 

Example log entry:
```
INFO - SIP Receiver started on 0.0.0.0:5060
DEBUG - Running test: BCF_001
ERROR - Test failed due to timeout
```

## Reporting
The test framework generates reports in multiple formats:
- **PDF & DOCX**: Detailed reports with structured test results
- **XML (JUnitXML)**: Machine-readable format for test integration
- **JSON & CSV**: Structured data export for analysis

Example command to generate a report:
```sh
python3 -m main run test_files/configs/base_config.yaml
```