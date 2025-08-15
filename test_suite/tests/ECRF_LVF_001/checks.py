def validate_ecrf_lvf_certs_acceptance(variation_type, has_app_data, has_alert_message):

    if variation_type == 'generate_random_certificate':
        if not has_alert_message:
            return "FAILED-> Required 'alert_message' information is missing."
        if has_app_data:
            return "FAILED-> 'app_data' shouldn't be present."

    else:
        if not has_app_data:
            return "FAILED-> Required 'app_data' information is missing."
        if has_alert_message:
            return "FAILED-> 'alert_message' shouldn't be present."

    return "PASSED"
