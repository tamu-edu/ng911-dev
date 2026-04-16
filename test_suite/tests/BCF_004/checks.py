from test_suite.services.aux_services.json_services import is_valid_fqdn


def validate_bcf_and_source_id(stimulus_messages, bcf_output_messages, source_id_list):
    try:
        # assert stimulus_messages, "STOP EXECUTION -> No stimullus messages found"  # TODO DISABLED NOT IMPLEMENTED

        assert (
            bcf_output_messages
        ), "INCONCLUSIVE -> SIP INVITE messages from BCF to ESRP not found"
        assert (
            source_id_list
        ), "FAILED -> Call-Info header fields with  'purpose=emergency-source' not found"
        assert len(source_id_list) == len(
            set(source_id_list)
        ), "FAILED -> added source-ID values are not unique"
        for source_id in source_id_list:
            source_id = source_id.split(";")[0]
            id_part = source_id.split("@")[0] if "@" in source_id else ""
            fqdn_part = source_id.split("@")[1] if "@" in source_id else ""
            assert (
                id_part and id_part.isalnum()
            ), f"FAILED -> ID part of source-ID {source_id} is incorrect"
            assert is_valid_fqdn(
                fqdn_part
            ), f"FAILED -> FQDN part of source-ID {source_id} is incorrect"
        return "PASSED"
    except AssertionError as e:
        return str(e)
