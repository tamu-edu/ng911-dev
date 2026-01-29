def test_compare_stimulus_and_output_messages(stimulus, output):
    """
    Test to validate the stimulus and output messages.
    """
    try:
        assert stimulus or output, "FAILED -> No bcf_output nor stimulus found"
        assert stimulus, "FAILED -> No stimulus found"
        assert output, "FAILED -> No bcf_output found"
        assert stimulus.sip.call_id == output.sip.call_id, \
            "FAILED - Stimulus and Output messages have different call_id"
        return "PASSED"
    except AssertionError as e:
        return str(e)
