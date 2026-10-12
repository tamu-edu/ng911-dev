# Variation names as defined in test_configs/test_config_ecrf_lvf_013.yaml
VARIATION_AUTHORITATIVE_VIA = "Adding_via_tag_with_FQDN_in_findServiceResponse"
VARIATION_RECURSIVE_VIA = "Adding_via_tag_with_FQDN_in_forwarded_recursive_findService"
VARIATION_LOOP_OWN_VIA = "Loop_detection_ECRF-LVFs_own_FQDN_already_in_via_tag"
VARIATION_LOOP_NEXT_HOP_VIA = "Loop_detection_next_hops_FQDN_already_in_via_tag"

# RFC 5222 'appUniqueString' token pattern used by the <via> 'source' attribute
APP_UNIQUE_STRING_PATTERN = r"^([a-zA-Z0-9\-]+\.)+[a-zA-Z0-9]+$"

# Interfaces used as a fallback when the run config has no 'output' filtering option
ECRF_LVF_TO_TS_INTERFACE = "IF_ECRF-LVF_TS-ECRF-LVF"
TS_TO_ECRF_LVF_INTERFACE = "IF_TS-ECRF-LVF_ECRF-LVF"
