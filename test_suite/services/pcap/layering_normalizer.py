import logging
import os

from scapy.layers.inet import IP, TCP
from scapy.utils import rdpcap, wrpcap

logger = logging.getLogger("MethodLoggerService")


class LayeringNormalizer:
    """
    Detects TCP-pipelined layered frames in a pcap file
    """

    @staticmethod
    def _extract_content_length(headers: str) -> int:
        import re

        match = re.search(r"Content-Length\s*:\s*(\d+)", headers, re.IGNORECASE)
        return int(match.group(1)) if match else 0

    @classmethod
    def _find_layering_boundaries(cls, payload: bytes) -> list[tuple[int, int]] | None:
        """
        Returns a list of (start, end) byte offsets into payload, one per
        sub-message, or None if payload is not layered.
        """
        offsets = []
        pos = 0
        while pos < len(payload):
            header_end = payload.find(b"\r\n\r\n", pos)
            if header_end == -1:
                break
            headers = payload[pos:header_end].decode(errors="ignore")
            content_length = cls._extract_content_length(headers)
            msg_end = header_end + 4 + content_length
            if msg_end > len(payload):
                break
            offsets.append((pos, msg_end))
            pos = msg_end

        if len(offsets) >= 2 and offsets[-1][1] == len(payload):
            return offsets
        return None

    @staticmethod
    def _split_layered_frame(
        original_frame, msg_bytes: bytes, sub_index: int, seq_offset: int
    ):
        new_frame = original_frame.copy()
        new_frame[TCP].remove_payload()
        new_frame = new_frame / msg_bytes

        new_frame[TCP].seq = (original_frame[TCP].seq + seq_offset) % 0x100000000

        del new_frame[IP].len
        del new_frame[IP].chksum
        del new_frame[TCP].chksum

        new_frame.time = float(original_frame.time) + sub_index * 1e-6
        return new_frame

    @classmethod
    def normalize(cls, pcap_file: str) -> str:
        """
        Runs the detect+split pass over pcap_file
        """
        try:
            raw_frames = list(rdpcap(pcap_file))
        except Exception as e:
            logger.warning(
                f"[LayeringNormalizer] Could not read {pcap_file} with scapy: "
                f"{e}. Skipping normalization."
            )
            return pcap_file

        normalized: list = []
        any_layered = False

        for i, frame in enumerate(raw_frames):
            frame_number = i + 1

            if not frame.haslayer(TCP):
                normalized.append(frame)
                continue

            try:
                payload = bytes(frame[TCP].payload)
                boundaries = cls._find_layering_boundaries(payload)
            except Exception as e:
                logger.warning(
                    f"[LayeringNormalizer] Detection failed for frame "
                    f"{frame_number} in {pcap_file}: {e}. Keeping frame as-is."
                )
                normalized.append(frame)
                continue

            if not boundaries:
                normalized.append(frame)
                continue

            try:
                sub_frames = [
                    cls._split_layered_frame(
                        frame, payload[start:end], sub_index, seq_offset=start
                    )
                    for sub_index, (start, end) in enumerate(boundaries)
                ]
            except Exception as e:
                logger.warning(
                    f"[LayeringNormalizer] Split failed for frame "
                    f"{frame_number} in {pcap_file}: {e}. Keeping original frame."
                )
                normalized.append(frame)
                continue

            print(
                f"🔀 [LayeringNormalizer] Frame {frame_number} in {pcap_file} "
                f"was layered -> normalized into {len(sub_frames)} frames."
            )
            normalized.extend(sub_frames)
            any_layered = True

        if not any_layered:
            return pcap_file

        directory = os.path.dirname(pcap_file)
        normalized_name = f"normalized_{os.path.basename(pcap_file)}"
        normalized_path = os.path.join(directory, normalized_name)

        wrpcap(normalized_path, normalized)
        print(
            f"✅ [LayeringNormalizer] Wrote {normalized_path}: "
            f"{len(raw_frames)} -> {len(normalized)} frames "
        )
        return normalized_path
