from enum import Enum

VARIATION_DESCRIPTIONS = {
    'SIP_INVITE_SDP_with_g711alaw_audio.xml': "Validate SIP 200 OK response for SIP INVITE with g711alaw audio media",
    'SIP_INVITE_SDP_with_g711ulaw_audio.xml': "Validate SIP 200 OK response for SIP INVITE with g711ulaw audio media",
    'SIP_INVITE_SDP_with_H.264_video_level_1b.xml':
        "Validate SIP 200 OK response for SIP INVITE with H.264 video media with baseline profile level 1b",
    'SIP_INVITE_SDP_with_H.264_video_level_1.1.xml':
        "Validate SIP 200 OK response for SIP INVITE with H.264 video media with baseline profile level 1.1",
    'SIP_INVITE_SDP_with_H.264_video_level_2.0.xml':
        "Validate SIP 200 OK response for SIP INVITE with H.264 video media with baseline profile level 2.0",
    'SIP_INVITE_SDP_with_H.264_video_level_3.0.xml':
        "Validate SIP 200 OK response for SIP INVITE with H.264 video media with baseline profile level 3.0"
}
