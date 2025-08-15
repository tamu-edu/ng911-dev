from checks.http.checks import is_type


def validate_version_int_values(response):
    """
    Validation of 'major' and 'minor' values that should be integers.
    """
    if not response:
        return "FAILED -> No json data found in response "
    if (result := is_type(response['versions'], 'versions', (list, dict))) != 'PASSED':
        return result
    if not response['versions']:
        return "FAILED -> 'versions' array is empty"
    for version in response['versions']:
        if ((result := is_type(version.get('major', None), 'major', int)) != 'PASSED'
                and not isinstance(version.get('major', None), int)):
            return result
        if ((result := is_type(version.get('minor', None), 'minor', int)) != 'PASSED'
                and not isinstance(version.get('major', None), int)):
            return result
        return "PASSED"


def validate_version_service_info(response):
    """
    Validation of 'serviceInfo' value.
    """
    if not response:
        return "FAILED -> No json data found in response "

    if (result := is_type(response['versions'],
                          'versions',
                          (list, dict))) != 'PASSED':
        return result
    if not response['versions']:
        return "FAILED -> 'versions' array is empty"
    for version in response['versions']:
        service_info = version.get('serviceInfo', None)
        if (result := is_type(service_info,
                              'serviceInfo',
                              (list, dict))) != 'PASSED':
            return result

        if (result := is_type(service_info.get('requiredAlgorithms', None),
                              'requiredAlgorithms',
                              (list, dict))) != 'PASSED':
            return result

        if not service_info['requiredAlgorithms']:
            return "FAILED -> 'requiredAlgorithms' array is empty"
        for algorithm in service_info['requiredAlgorithms']:
            if (result := is_type(algorithm,
                                  'algorithm',
                                  str)) != 'PASSED':
                return result
    return "PASSED"


def validate_version_vendor(response):
    if not response:
        return "FAILED -> No json data found in response "

    for version in response['versions']:
        if (version['vendor']
                and (result := is_type(version['vendor'], 'vendor', str)) != 'PASSED'):
            return result
