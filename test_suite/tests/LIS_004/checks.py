import re


def extract_parameter_value(input_str: str, parameter: str) -> float | None:
    """
    Extracts the value of a given parameter from a multi-line string.
    param:input_str (str): The input multi-line string.
    param: prameter (str): The parameter name to search for.
    return: str | None: The extracted value if found, otherwise None.
    """
    pattern = re.compile(rf'{re.escape(parameter)}\s*=\s*([-+]?\d*\.?\d+)')

    for line in input_str.splitlines():
        match = pattern.search(line)
        if match:
            return float(match.group(1))

    return None


def is_expected_rate(timestamps, threshold=2,  max_rate=False):
    """
    Checks if the rate between neighboring timestamps meets the required threshold.

    :param: timestamps (list): List of timestamps as strings.
    :param: threshold (float): Number of messages per second (default: 2).
    return: bool: True if all intervals meet the threshold, False otherwise.
    """
    # Convert string timestamps to float
    times = [float(ts) for ts in timestamps]
    max_interval = round(1 / threshold, 2)

    for i in range(1, len(times)):
        time_diff = round(times[i] - times[i - 1], 2)
        if max_rate:
            if time_diff * 1.1 < max_interval:  # Additional +10% threshold added
                return False
        else:
            if time_diff > max_interval * 1.1:  # Additional +10% threshold added
                return False

    return True


def validate_lis_response_time_between_messages(subscribe_msgs, responses, variation_name, param_value):
    """
    Verifies time between LIS responses. It should match specific thresholds that differs for each variation
    """
    timestamps = []

    if not responses or not subscribe_msgs:
        return "FAILED -> No SIP SUBSCRIBE/NOTIFY messages found."

    if not variation_name:
        return "FAILED -> Cannot find SIPp file."

    # TODO: potential "INCONCLUSIVE" test result scenario
    if not param_value:
        return "FAILED -> Parameter for selected variation cannot be found."

    for message in responses:
        timestamps.append(message.sniff_timestamp)

    if variation_name == 'max-rate':
        if not is_expected_rate(timestamps, threshold=param_value, max_rate=True):
            return "FAILED -> The interval between message responses fails to satisfy the defined threshold criteria."
    if not is_expected_rate(timestamps, threshold=param_value):
        return "FAILED -> The interval between message responses fails to satisfy the defined threshold criteria."

    return "PASSED"
