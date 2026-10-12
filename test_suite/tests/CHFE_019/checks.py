def validate_service_urn_prefix(
    service_urn: str | None,
    allowed_prefixes: tuple[str, ...],
) -> str:
    """
    Validates that the Refer-To serviceurn parameter starts with one of
    the allowed service URN prefixes.
    """

    if not service_urn:
        return "FAILED -> Refer-To serviceurn parameter is not present"

    value = service_urn.strip().strip('"')

    if not value.startswith(allowed_prefixes):
        return (
            "FAILED -> Refer-To serviceurn parameter has invalid value: "
            f"'{service_urn}'"
        )

    return "PASSED"
