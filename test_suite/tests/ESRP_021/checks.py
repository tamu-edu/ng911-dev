from services.aux_services.json_services import is_valid_fqdn


def precondition_check(stimulus_messages, subscribe_log_events) -> str:
    try:
        assert (
            stimulus_messages
        ), "NOT RUN -> No SIP SUBSCRIBE CHFE to ESRP stimulus message found."
        assert (
            subscribe_log_events
        ), "FAILED -> No ESRP to LOGGER POST 'SubscribeLogEvent' message found. Please check 'certificate_key' configuration value if signed JWS."
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_fqdn_field(fqdn_string) -> str:
    try:
        assert is_valid_fqdn(
            fqdn_string
        ), f"FAILED -> '{fqdn_string}' is not a valid FQDN"
        return "PASSED"
    except AssertionError as e:
        return str(e)
