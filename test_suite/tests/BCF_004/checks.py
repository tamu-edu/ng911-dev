def validate_bcf_and_source_id(stimulus_messages, bcf_output_messages, source_id_list, bad_actors_text_data):
    try:
        # assert stimulus_messages, "STOP EXECUTION -> No stimullus messages found"  # TODO DISABLED NOT IMPLEMENTED

        assert bcf_output_messages, "INCONCLUSIVE -> SIP INVITE messages from BCF to ESRP not found"

        assert bad_actors_text_data not in source_id_list, \
            "INCONCLUSIVE -> stimulus HTTP POST message contains already known source-ID"

        return "PASSED"
    except AssertionError as e:
        return str(e)

