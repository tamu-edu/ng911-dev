from __future__ import annotations


class SRTPError(RuntimeError):
    """
    Raised when libSRTP reports an error.
    """


_SRTP_STATUS_NAMES = {
    0: "ok",
    1: "fail",
    2: "bad_param",
    3: "alloc_fail",
    4: "dealloc_fail",
    5: "init_fail",
    6: "terminus",
    7: "auth_fail",
    8: "cipher_fail",
    9: "replay_fail",
    10: "replay_old",
    11: "algo_fail",
    12: "no_such_op",
    13: "no_ctx",
    14: "cant_check",
    15: "key_expired",
    16: "socket_err",
    17: "signal_err",
    18: "nonce_bad",
    19: "read_fail",
    20: "write_fail",
    21: "parse_err",
    22: "encode_err",
    23: "semaphore_err",
    24: "pfkey_err",
    25: "bad_mki",
    26: "pkt_idx_old",
    27: "pkt_idx_adv",
}


def get_srtp_status_name(
    status: int,
) -> str:
    return _SRTP_STATUS_NAMES.get(
        int(status),
        "unknown",
    )


def require_srtp_success(
    status: int,
    operation: str,
) -> None:
    """
    Raise SRTPError unless libSRTP returned srtp_err_status_ok.
    """
    if status == 0:
        return

    raise SRTPError(
        f"{operation} failed with libSRTP status "
        f"{status} ({get_srtp_status_name(status)})"
    )
