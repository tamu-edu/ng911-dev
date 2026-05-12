import threading

_RTP_SENDERS = set()
_lock = threading.Lock()


def register_rtp_sender(sender):
    with _lock:
        _RTP_SENDERS.add(sender)


def unregister_rtp_sender(sender):
    with _lock:
        _RTP_SENDERS.discard(sender)


def stop_all_rtp_senders():
    print("[cleanup] Stopping all RTP senders")
    with _lock:
        for sender in list(_RTP_SENDERS):
            try:
                sender.stop()
            except Exception as e:
                print(f"[cleanup] Failed stopping RTP sender: {e}")
        _RTP_SENDERS.clear()
