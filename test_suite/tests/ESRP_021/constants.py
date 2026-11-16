TIMESTAMP_THRESHOLD = 3.0  # 3 sec

VARIATIONS = {
    "SUBSCRIBE_refresh": 1,
    "SUBSCRIBE_termination": 2,
    "SUBSCRIBE_with_unsupported_event": 3,
}


# variation number -> expected count of SubscribeLogEvent records
EXPECTED_COUNTS = {
    1: 2,
    2: 2,
    3: 1,
}

# variation number -> expected 'purpose' values, in order
EXPECTED_PURPOSES = {
    1: ["initial", "refresh"],
    2: ["initial", "terminate"],
    3: ["initial"],
}

# variation number -> expected 'response' values, in order
EXPECTED_RESPONSES = {
    1: ["200", "200"],
    2: ["200", "200"],
    3: ["489"],
}

# Variations with a paired initial + refresh/terminate transaction sharing
# the same 'subscriptionId'.
VARIATIONS_WITH_SUBSCRIPTION_ID_PAIR = {1, 2}
