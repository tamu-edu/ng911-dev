def validate_lis_certs_acceptance(**test_data):
    method_name, has_app_data, has_alert_message = test_data.values()

    if method_name == 'generate_random_certificate':
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
