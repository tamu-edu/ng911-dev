# Test Description: TD_XXXX_###
## Overview
### Summary
Short one or two sentence description.

### Description
More detailed description 
* The test system sends ...
* The Implementation Under Test will ...
* The test system receives ...

### References
* Requirements : RQ_XXXX_###, ...
* Test Purpose : TP_XXXX_###, ...
* Test Case    : TC_XXXX_###, ...

## Configuration
### Implementation Under Test Interface Connections
<!-- Identify each of the FEs that are part of the configuration and how they are connected -->
* FE2 Name (e.x., ESRP)
  * IF_FE2_FE1 (e.x., IF_ESRP_OBCF) - connected to Test System IF_BCF_ESRP
  * IF_FE2_FE3 (e.x., IF_ESRP_TBCF) - connected to FE3
* FE3 Name (e.x., TBCF)
  * IF_FE3_FE2 (e.x., IF_TBCF_ESRP) - connected to FE2
  * IF_FE3_FE4 (e.x., IF_TBCF_CHE) - connected to CHE

### Test System Interfaces
<!-- Identify each of the test system interfaces and whether it will be in active or monitor mode -->
* FE1 Name (e.x. OBCF)
  * IF_BCF_ESRP - Active
* FE2 Name
  * IF_FE2_FE1 (e.x., IF_ESRP_OBCF) - Passive
  * IF_FE2_FE2 (e.x., IF_ESRP_TBCF) - Passive
* FE3 Name
  * IF_FE3_FE2 (e.g., IF_TBCF_ESRP) - Passive
  * IF_FE3_FE4 (e.x., IF_TBCF_CHE)  - Passive
* FE4 Name (e.x., CHE)
  * IF_CHE_TBCF - Active
 
### Connectivity Diagram
Include a diagram of the configuration

## Pre-Test Conditions
### Test System FE1
<!-- Where FE# is the FE abbreviation (LIS, BCF, ESRP, ECRF, ...) -->
* Condition 1
* Condition 2
### FE2
* Condition 1
* Condition 2
### FE3
* Condition 1
* Condition 2
### Test System FE4
* Condition 1
* Condition 2

## Test Sequence
### Test Preamble
* Step 1
* Step 2

### Test Body
* Step 1
  * Step 1.1
  * Step 1.2
  * Verdict
* Step 2

### Test Postamble
* Step 1
* Step 2

## Post-Test Conditions
### Test System FE1
* Condition 1
* Condition 2
### FE2
* Condition 1
* Condition 2
### FE3
* Condition 1
* Condition 2
### Test System FE4
* Condition 1
* Condition 2

## Sequence Diagram

## Comments

## Footnotes
[^1]First footnote
[^2]Second footnote
