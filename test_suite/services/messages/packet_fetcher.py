from functools import partialmethod

from enums import PacketTypeEnum, SIPMethodEnum, HTTPMethodEnum
from services.pcap_service import PcapCaptureService, FilterConfig


class PacketFetcher:
    """
    Wrapper around pcap_service for retrieving packets from a pcap file.
    Route names follow "role1_role2" (e.g. "bcf_esrp") — add_route() also
    registers the reverse direction automatically.

    get_first_<packet_type>_<method> shortcuts below return just the
    message by default; pass return_timestamp=True for (message, timestamp).

    call_id and branch are optional post-filters applied on top of
    FilterConfig results (matched against the SIP Call-ID header and the
    Via branch parameter) — they are not pushed down into FilterConfig.
    """

    def __init__(self, pcap_service: PcapCaptureService):

        self.pcap_service = pcap_service
        self._routes: dict[str, tuple[str, str]] = {}

    def add_route(self, name: str, src_ip: str, dst_ip: str):
        """Registers a named traffic direction and its reverse."""

        self._routes[name] = (src_ip, dst_ip)
        role1, role2 = name.split("_", 1)
        self._routes[f"{role2}_{role1}"] = (dst_ip, src_ip)

    def _resolve(self, route: str) -> tuple[str, str]:
        try:
            return self._routes[route]
        except KeyError:
            raise ValueError(
                f"Unknown route '{route}'. Registered: {list(self._routes)}"
            ) from None

    @staticmethod
    def _filter_by_sip_identifiers(messages, call_id=None, branch=None):
        """Post-filters a list of messages by SIP Call-ID and/or Via branch."""
        if call_id is None and branch is None:
            return messages

        filtered = []
        for message in messages:
            sip = getattr(message, "sip", None)
            if sip is None:
                continue
            if call_id is not None and getattr(sip, "call_id", None) != call_id:
                continue
            if branch is not None and getattr(sip, "via_branch", None) != branch:
                continue
            filtered.append(message)

        return filtered

    def get_messages(
        self,
        route,
        packet_type=None,
        message_method=None,
        after_timestamp=None,
        call_id=None,
        branch=None,
        **kw,
    ):
        """
        Returns all messages matching the given route and filter criteria.

        :param route: name registered via add_route(), e.g. "bcf_esrp"
        :param packet_type: PacketTypeEnum value to filter by
        :param message_method: list of SIP/HTTP methods to filter by
        :param after_timestamp: only messages after this timestamp
        :param call_id: if given, only messages whose SIP Call-ID header
            matches this value are kept (post-filter, not pushed to FilterConfig)
        :param branch: if given, only messages whose Via branch parameter
            matches this value are kept (post-filter)
        :param kw: any other FilterConfig field (dst_port, src_port,
            http_status_code, header_part, body_part, etc.)
        :return: list of messages (empty if nothing matched)
        """
        src_ip, dst_ip = self._resolve(route)
        filter_config = FilterConfig(
            src_ip=src_ip,
            dst_ip=dst_ip,
            packet_type=packet_type,
            message_method=message_method,
            after_timestamp=after_timestamp,
            **kw,
        )
        try:
            messages = self.pcap_service.get_messages_by_config(filter_config) or []
        except IndexError:
            messages = []

        if call_id is None and branch is None:
            return messages

        return self._filter_by_sip_identifiers(messages, call_id=call_id, branch=branch)

    def get_first(
        self,
        route,
        packet_type=None,
        message_method=None,
        after_timestamp=None,
        return_timestamp=False,
        call_id=None,
        branch=None,
        **kw,
    ):
        """
        Returns the first matching message. (message, timestamp) if
        return_timestamp=True. See get_messages() for call_id/branch.
        """
        messages = self.get_messages(
            route,
            packet_type,
            message_method,
            after_timestamp,
            call_id=call_id,
            branch=branch,
            **kw,
        )
        message = messages[0] if messages else None
        if not return_timestamp:
            return message
        return message, getattr(message, "sniff_timestamp", 0)

    # --- shortcuts

    get_first_sip = partialmethod(get_first, packet_type=PacketTypeEnum.SIP)
    get_sip_messages = partialmethod(get_messages, packet_type=PacketTypeEnum.SIP)

    get_first_sip_invite = partialmethod(
        get_first, packet_type=PacketTypeEnum.SIP, message_method=[SIPMethodEnum.INVITE]
    )
    get_sip_invites = partialmethod(
        get_messages,
        packet_type=PacketTypeEnum.SIP,
        message_method=[SIPMethodEnum.INVITE],
    )

    get_first_sip_ack = partialmethod(
        get_first, packet_type=PacketTypeEnum.SIP, message_method=[SIPMethodEnum.ACK]
    )
    get_sip_acks = partialmethod(
        get_messages, packet_type=PacketTypeEnum.SIP, message_method=[SIPMethodEnum.ACK]
    )

    get_first_sip_bye = partialmethod(
        get_first, packet_type=PacketTypeEnum.SIP, message_method=[SIPMethodEnum.BYE]
    )
    get_sip_byes = partialmethod(
        get_messages, packet_type=PacketTypeEnum.SIP, message_method=[SIPMethodEnum.BYE]
    )

    get_first_sip_cancel = partialmethod(
        get_first, packet_type=PacketTypeEnum.SIP, message_method=[SIPMethodEnum.CANCEL]
    )
    get_sip_cancels = partialmethod(
        get_messages,
        packet_type=PacketTypeEnum.SIP,
        message_method=[SIPMethodEnum.CANCEL],
    )

    get_first_sip_register = partialmethod(
        get_first,
        packet_type=PacketTypeEnum.SIP,
        message_method=[SIPMethodEnum.REGISTER],
    )
    get_sip_registers = partialmethod(
        get_messages,
        packet_type=PacketTypeEnum.SIP,
        message_method=[SIPMethodEnum.REGISTER],
    )

    get_first_sip_options = partialmethod(
        get_first,
        packet_type=PacketTypeEnum.SIP,
        message_method=[SIPMethodEnum.OPTIONS],
    )
    get_sip_options_messages = partialmethod(
        get_messages,
        packet_type=PacketTypeEnum.SIP,
        message_method=[SIPMethodEnum.OPTIONS],
    )

    get_first_sip_info = partialmethod(
        get_first, packet_type=PacketTypeEnum.SIP, message_method=[SIPMethodEnum.INFO]
    )
    get_sip_infos = partialmethod(
        get_messages,
        packet_type=PacketTypeEnum.SIP,
        message_method=[SIPMethodEnum.INFO],
    )

    get_first_sip_prack = partialmethod(
        get_first, packet_type=PacketTypeEnum.SIP, message_method=[SIPMethodEnum.PRACK]
    )
    get_sip_pracks = partialmethod(
        get_messages,
        packet_type=PacketTypeEnum.SIP,
        message_method=[SIPMethodEnum.PRACK],
    )

    get_first_sip_subscribe = partialmethod(
        get_first,
        packet_type=PacketTypeEnum.SIP,
        message_method=[SIPMethodEnum.SUBSCRIBE],
    )
    get_sip_subscribes = partialmethod(
        get_messages,
        packet_type=PacketTypeEnum.SIP,
        message_method=[SIPMethodEnum.SUBSCRIBE],
    )

    get_first_sip_notify = partialmethod(
        get_first, packet_type=PacketTypeEnum.SIP, message_method=[SIPMethodEnum.NOTIFY]
    )
    get_sip_notifies = partialmethod(
        get_messages,
        packet_type=PacketTypeEnum.SIP,
        message_method=[SIPMethodEnum.NOTIFY],
    )

    get_first_sip_publish = partialmethod(
        get_first,
        packet_type=PacketTypeEnum.SIP,
        message_method=[SIPMethodEnum.PUBLISH],
    )
    get_sip_publishes = partialmethod(
        get_messages,
        packet_type=PacketTypeEnum.SIP,
        message_method=[SIPMethodEnum.PUBLISH],
    )

    get_first_sip_refer = partialmethod(
        get_first, packet_type=PacketTypeEnum.SIP, message_method=[SIPMethodEnum.REFER]
    )
    get_sip_refers = partialmethod(
        get_messages,
        packet_type=PacketTypeEnum.SIP,
        message_method=[SIPMethodEnum.REFER],
    )

    get_first_sip_message = partialmethod(
        get_first,
        packet_type=PacketTypeEnum.SIP,
        message_method=[SIPMethodEnum.MESSAGE],
    )
    get_sip_message_messages = partialmethod(
        get_messages,
        packet_type=PacketTypeEnum.SIP,
        message_method=[SIPMethodEnum.MESSAGE],
    )

    get_first_sip_update = partialmethod(
        get_first, packet_type=PacketTypeEnum.SIP, message_method=[SIPMethodEnum.UPDATE]
    )
    get_sip_updates = partialmethod(
        get_messages,
        packet_type=PacketTypeEnum.SIP,
        message_method=[SIPMethodEnum.UPDATE],
    )

    get_first_sip_ok = partialmethod(
        get_first, packet_type=PacketTypeEnum.SIP, message_method=[SIPMethodEnum.OK]
    )
    get_sip_oks = partialmethod(
        get_messages, packet_type=PacketTypeEnum.SIP, message_method=[SIPMethodEnum.OK]
    )

    get_first_http = partialmethod(get_first, packet_type=PacketTypeEnum.HTTP)
    get_http_messages = partialmethod(get_messages, packet_type=PacketTypeEnum.HTTP)

    get_first_http_post = partialmethod(
        get_first, packet_type=PacketTypeEnum.HTTP, message_method=[HTTPMethodEnum.POST]
    )
    get_http_posts = partialmethod(
        get_messages,
        packet_type=PacketTypeEnum.HTTP,
        message_method=[HTTPMethodEnum.POST],
    )

    get_first_http_get = partialmethod(
        get_first, packet_type=PacketTypeEnum.HTTP, message_method=[HTTPMethodEnum.GET]
    )
    get_http_gets = partialmethod(
        get_messages,
        packet_type=PacketTypeEnum.HTTP,
        message_method=[HTTPMethodEnum.GET],
    )

    get_first_https = partialmethod(get_first, packet_type=PacketTypeEnum.HTTPS)
    get_https_messages = partialmethod(get_messages, packet_type=PacketTypeEnum.HTTPS)

    get_first_tcp = partialmethod(get_first, packet_type=PacketTypeEnum.TCP)
    get_tcp_messages = partialmethod(get_messages, packet_type=PacketTypeEnum.TCP)

    get_first_udp = partialmethod(get_first, packet_type=PacketTypeEnum.UDP)
    get_udp_messages = partialmethod(get_messages, packet_type=PacketTypeEnum.UDP)

    get_first_rtp = partialmethod(get_first, packet_type=PacketTypeEnum.RTP)
    get_rtp_messages = partialmethod(get_messages, packet_type=PacketTypeEnum.RTP)

    get_first_dns = partialmethod(get_first, packet_type=PacketTypeEnum.DNS)
    get_dns_messages = partialmethod(get_messages, packet_type=PacketTypeEnum.DNS)

    get_first_icmp = partialmethod(get_first, packet_type=PacketTypeEnum.ICMP)
    get_icmp_messages = partialmethod(get_messages, packet_type=PacketTypeEnum.ICMP)

    get_first_arp = partialmethod(get_first, packet_type=PacketTypeEnum.ARP)
    get_arp_messages = partialmethod(get_messages, packet_type=PacketTypeEnum.ARP)
