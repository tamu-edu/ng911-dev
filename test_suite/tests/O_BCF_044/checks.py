"""
File to place the test themselves here, in format that would allow use the with PyTest
"""


def test_udp_exchange_started(
        o_bcf_sbc_upd_audio_first_message,
        o_bcf_sbc_upd_video_first_message,
        osp_o_bcf_upd_audio_first_message,
        osp_o_bcf_upd_video_first_message
):
    """
    Test to validate Udp exchange started.
    """
    try:
        assert o_bcf_sbc_upd_audio_first_message or o_bcf_sbc_upd_video_first_message, \
            "FAILED to find any UDP media packet from O_BCF to SBC"
        assert osp_o_bcf_upd_audio_first_message or osp_o_bcf_upd_video_first_message, \
            "FAILED to find any UDP media packet from SBC to O_BCF"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_media_ports(
        o_bcf_audio_port,
        o_bcf_video_port,
        sbc_audio_port,
        sbc_video_port
):
    """
    Test media ports configuration.
    """
    try:
        assert o_bcf_audio_port or o_bcf_video_port, \
            "FAILED to find O_BCF media ports configuration"
        assert sbc_audio_port or sbc_video_port, \
            "FAILED to find SBC media ports configuration"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_o_bcf_sbc_ports_configuration(
        o_bcf_sbc_upd_audio_first_message,
        o_bcf_sbc_upd_video_first_message,
        o_bcf_audio_port,
        o_bcf_video_port,
        sbc_audio_port,
        sbc_video_port,
):
    """
    Test O_BCF -> SBC ports configuration.
    """
    if o_bcf_sbc_upd_audio_first_message:
        try:
            audio_scr_port = str(o_bcf_sbc_upd_audio_first_message.udp.srcport)
        except AttributeError:
            audio_scr_port = None
        try:
            audio_dst_port = str(o_bcf_sbc_upd_audio_first_message.udp.dstport)
        except AttributeError:
            audio_dst_port = None
    else:
        audio_scr_port = None
        audio_dst_port = None

    if o_bcf_sbc_upd_video_first_message:
        try:
            video_scr_port = str(o_bcf_sbc_upd_video_first_message.udp.srcport)
        except AttributeError:
            video_scr_port = None
        try:
            video_dst_port = str(o_bcf_sbc_upd_video_first_message.udp.dstport)
        except AttributeError:
            video_dst_port = None
    else:
        video_scr_port = None
        video_dst_port = None

    try:
        if audio_scr_port:
            assert audio_scr_port == o_bcf_audio_port, "FAILED - O_BCF -> SBC audio source ports wrong configuration"
        if audio_dst_port:
            assert audio_dst_port == sbc_audio_port, "FAILED - O_BCF -> SBC audio destination ports wrong configuration"

        if video_scr_port:
            assert video_scr_port == o_bcf_video_port, "FAILED - O_BCF -> SBC video source ports wrong configuration"
        if video_dst_port:
            assert video_dst_port == sbc_video_port, "FAILED - O_BCF -> SBC video destination ports wrong configuration"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_sbc_o_bcf_ports_configuration(
        osp_o_bcf_upd_audio_first_message,
        osp_o_bcf_upd_video_first_message,
        o_bcf_audio_port,
        o_bcf_video_port,
        sbc_audio_port,
        sbc_video_port,
):
    """
    Test SBC -> O_BCF ports configuration.
    """
    if osp_o_bcf_upd_audio_first_message:
        try:
            audio_scr_port = str(osp_o_bcf_upd_audio_first_message.udp.srcport)
        except AttributeError:
            audio_scr_port = None
        try:
            audio_dst_port = str(osp_o_bcf_upd_audio_first_message.udp.dstport)
        except AttributeError:
            audio_dst_port = None
    else:
        audio_scr_port = None
        audio_dst_port = None

    if osp_o_bcf_upd_video_first_message:
        try:
            video_scr_port = str(osp_o_bcf_upd_video_first_message.udp.srcport)
        except AttributeError:
            video_scr_port = None
        try:
            video_dst_port = str(osp_o_bcf_upd_video_first_message.udp.dstport)
        except AttributeError:
            video_dst_port = None
    else:
        video_scr_port = None
        video_dst_port = None

    try:
        if audio_scr_port:
            assert audio_scr_port == sbc_audio_port, "FAILED - SBC -> O_BCF audio source ports wrong configuration"
        if audio_dst_port:
            assert audio_dst_port == o_bcf_audio_port, \
                "FAILED - SBC -> O_BCF audio destination ports wrong configuration"

        if video_scr_port:
            assert video_scr_port == sbc_video_port, "FAILED - SBC -> O_BCF video source ports wrong configuration"
        if video_dst_port:
            assert video_dst_port == o_bcf_video_port, \
                "FAILED - SBC -> O_BCF video destination ports wrong configuration"
        return "PASSED"
    except AssertionError as e:
        return str(e)
