# Preconditions
NOT_RUN_BCF = "NOT RUN -> No SIP SUBSCRIBE (emergency-QueueState.winfo) from Test System BCF to ESRP found"
NOT_RUN_SUBSCRIBE = "NOT RUN -> No SIP SUBSCRIBE (emergency-QueueState) from Test System {role} to ESRP found"
NOT_RUN_TERMINATE = "NOT RUN -> No terminating SIP SUBSCRIBE (Expires: 0) from Test System {role} to ESRP found"

# Test Systems
BCF = "BCF"
CHFE = "CHFE"
ESRP_2 = "ESRP-2"

# Route name prefix used for the Test System <-> ESRP direction (see PacketFetcher.add_route)
ROUTE_KEYS = {BCF: "bcf", CHFE: "chfe", ESRP_2: "esrp-2"}

# Interfaces used for pcap filtering (see get_filter_parameters)
INTERFACE_NAMES = ("if_bcf_esrp", "if_chfe_esrp", "if_esrp-2_esrp")

# SIP Event packages / content types
QUEUE_STATE_EVENT = "emergency-QueueState"
WINFO_EVENT = "emergency-QueueState.winfo"
WINFO_CONTENT_TYPE = "application/watcherinfo+xml"
QUEUE_STATE_CONTENT_TYPE = "application/EmergencyCallData.QueueState+json"

# Subscription-State header values
STATE_ACTIVE = "active"
STATE_TERMINATED = "terminated"

# watcherinfo (RFC 3858) attributes
WINFO_STATE_FULL = "full"
WINFO_STATE_PARTIAL = "partial"
WATCHER_STATUS_ACTIVE = "active"
WATCHER_STATUS_TERMINATED = "terminated"
