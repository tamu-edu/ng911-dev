from functools import partialmethod

from enums import PacketTypeEnum, SIPMethodEnum, HTTPMethodEnum
from services.messages.sip.sip_message import SipMessage
from services.pcap_service import PcapCaptureService, FilterConfig


class PacketFetcher:
    """
    Wrapper around pcap_service for retrieving packets from a pcap file.
    Route names follow "role1_role2" (e.g. "bcf_esrp") — add_route() also
    registers the reverse direction automatically.

    get_first_<packet_type>_<method> shortcuts below return just the
    message by default; pass return_timestamp=True for (message, timestamp).

    call_id, branch, and event are optional SIP post-filters; url_contains
    is an optional HTTP post-filter. All are applied on top of
    FilterConfig results — they are not pushed down into FilterConfig.
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
    def _filter_by_sip_identifiers(
        messages,
        call_id=None,
        branch=None,
        event=None,
        status_code=None,
        cseq_method=None,
    ):
        """
        Post-filters a list of messages by SIP Call-ID, Via branch,
        Event header, response status code and/or CSeq method.
        """
        if all(
            value is None
            for value in (call_id, branch, event, status_code, cseq_method)
        ):
            return messages

        expected_cseq_method = (
            str(getattr(cseq_method, "value", cseq_method)).upper()
            if cseq_method is not None
            else None
        )

        filtered = []
        for message in messages:
            sip = getattr(message, "sip", None)
            if sip is None:
                continue
            if call_id is not None and getattr(sip, "call_id", None) != call_id:
                continue
            if branch is not None and getattr(sip, "via_branch", None) != branch:
                continue
            if status_code is not None and str(getattr(sip, "status_code", "")) != str(
                status_code
            ):
                continue
            if expected_cseq_method is not None and (
                str(getattr(sip, "cseq_method", "")).upper() != expected_cseq_method
            ):
                continue
            if event is not None:
                sip_message = SipMessage.from_packet(message)
                if not sip_message or sip_message.event != event:
                    continue
            filtered.append(message)

        return filtered

    @staticmethod
    def _filter_by_http_identifiers(messages, url_contains=None):
        """Post-filters a list of messages by a substring in the HTTP request target URL."""
        if url_contains is None:
            return messages

        filtered = []
        for message in messages:
            http = getattr(message, "http", None)
            if http is None:
                continue
            request_target = getattr(http, "request_uri", None) or getattr(
                http, "request_full_uri", None
            )
            if request_target is None:
                continue
            if url_contains not in request_target:
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
        event=None,
        status_code=None,
        cseq_method=None,
        url_contains=None,
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
        :param event: if given, only messages whose SIP Event header value
            (via SipMessage.from_packet(packet).event) matches this value
            are kept (post-filter, e.g. for SUBSCRIBE/NOTIFY correlation)
        :param status_code: if given, only SIP responses with this status
            code (e.g. 200, 486) are kept (post-filter); requests are dropped
        :param cseq_method: if given, only SIP messages whose CSeq method
            matches this value
        :param url_contains: if given, only HTTP messages whose request
            target URL contains this substring are kept (post-filter)
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

        if packet_type == PacketTypeEnum.HTTP:
            return self._filter_by_http_identifiers(messages, url_contains=url_contains)

        return self._filter_by_sip_identifiers(
            messages,
            call_id=call_id,
            branch=branch,
            event=event,
            status_code=status_code,
            cseq_method=cseq_method,
        )

    def get_first(
        self,
        route,
        packet_type=None,
        message_method=None,
        after_timestamp=None,
        return_timestamp=False,
        call_id=None,
        branch=None,
        event=None,
        status_code=None,
        cseq_method=None,
        url_contains=None,
        **kw,
    ):
        """
        Returns the first matching message. (message, timestamp) if
        return_timestamp=True. See get_messages() for
        call_id/branch/event/status_code/cseq_method/url_contains.
        """
        messages = self.get_messages(
            route,
            packet_type,
            message_method,
            after_timestamp,
            call_id=call_id,
            branch=branch,
            event=event,
            status_code=status_code,
            cseq_method=cseq_method,
            url_contains=url_contains,
            **kw,
        )
        message = messages[0] if messages else None
        if not return_timestamp:
            return message
        return message, getattr(message, "sniff_timestamp", 0)

    def get_http_response_for(
        self,
        route,
        request,
        return_timestamp=False,
        time_fallback=False,
    ):
        """
        Returns the HTTP response to the given request.

        Matching layers:
        1. shark link: request 'http.response_in' frame number
        2. same TCP stream: first response in the request's 'tcp.stream'
        3. time order, first response after the request (time_fallback=True)

        :param route: route name of the response direction, e.g. "ecrf_chfe"
        :param request: HTTP request packet
        :param return_timestamp: return (message, timestamp)
        :param time_fallback: take the first http packet as response
        """
        response = None
        if request is not None:
            candidates = [
                message
                for message in self.get_http_messages(
                    route, after_timestamp=getattr(request, "sniff_timestamp", None)
                )
                # response should contain status code
                if getattr(getattr(message, "http", None), "response_code", None)
                is not None
            ]

            # 1. shark request/response link
            response_in = getattr(getattr(request, "http", None), "response_in", None)
            if response_in is not None:
                response = next(
                    (
                        m
                        for m in candidates
                        if str(getattr(m, "number", "")) == str(response_in)
                    ),
                    None,
                )

            # 2. TCP connection request order
            if response is None:
                stream = getattr(getattr(request, "tcp", None), "stream", None)
                if stream is not None:
                    response = next(
                        (
                            m
                            for m in candidates
                            if getattr(getattr(m, "tcp", None), "stream", None)
                            == stream
                        ),
                        None,
                    )

            # 3. Time order
            if response is None and time_fallback and candidates:
                response = candidates[0]

        if not return_timestamp:
            return response
        return response, getattr(response, "sniff_timestamp", 0)

    # --- shortcuts

    # SIP

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

    # HTTP

    get_first_http = partialmethod(get_first, packet_type=PacketTypeEnum.HTTP)
    get_http_messages = partialmethod(get_messages, packet_type=PacketTypeEnum.HTTP)

    get_first_http_get = partialmethod(
        get_first, packet_type=PacketTypeEnum.HTTP, message_method=[HTTPMethodEnum.GET]
    )
    get_http_gets = partialmethod(
        get_messages,
        packet_type=PacketTypeEnum.HTTP,
        message_method=[HTTPMethodEnum.GET],
    )

    get_first_http_head = partialmethod(
        get_first, packet_type=PacketTypeEnum.HTTP, message_method=[HTTPMethodEnum.HEAD]
    )
    get_http_heads = partialmethod(
        get_messages,
        packet_type=PacketTypeEnum.HTTP,
        message_method=[HTTPMethodEnum.HEAD],
    )

    get_first_http_post = partialmethod(
        get_first, packet_type=PacketTypeEnum.HTTP, message_method=[HTTPMethodEnum.POST]
    )
    get_http_posts = partialmethod(
        get_messages,
        packet_type=PacketTypeEnum.HTTP,
        message_method=[HTTPMethodEnum.POST],
    )

    get_first_http_put = partialmethod(
        get_first, packet_type=PacketTypeEnum.HTTP, message_method=[HTTPMethodEnum.PUT]
    )
    get_http_puts = partialmethod(
        get_messages,
        packet_type=PacketTypeEnum.HTTP,
        message_method=[HTTPMethodEnum.PUT],
    )

    get_first_http_delete = partialmethod(
        get_first,
        packet_type=PacketTypeEnum.HTTP,
        message_method=[HTTPMethodEnum.DELETE],
    )
    get_http_deletes = partialmethod(
        get_messages,
        packet_type=PacketTypeEnum.HTTP,
        message_method=[HTTPMethodEnum.DELETE],
    )

    get_first_http_patch = partialmethod(
        get_first,
        packet_type=PacketTypeEnum.HTTP,
        message_method=[HTTPMethodEnum.PATCH],
    )
    get_http_patches = partialmethod(
        get_messages,
        packet_type=PacketTypeEnum.HTTP,
        message_method=[HTTPMethodEnum.PATCH],
    )

    get_first_http_options = partialmethod(
        get_first,
        packet_type=PacketTypeEnum.HTTP,
        message_method=[HTTPMethodEnum.OPTIONS],
    )
    get_http_options_messages = partialmethod(
        get_messages,
        packet_type=PacketTypeEnum.HTTP,
        message_method=[HTTPMethodEnum.OPTIONS],
    )

    get_first_http_connect = partialmethod(
        get_first,
        packet_type=PacketTypeEnum.HTTP,
        message_method=[HTTPMethodEnum.CONNECT],
    )
    get_http_connects = partialmethod(
        get_messages,
        packet_type=PacketTypeEnum.HTTP,
        message_method=[HTTPMethodEnum.CONNECT],
    )

    get_first_http_trace = partialmethod(
        get_first,
        packet_type=PacketTypeEnum.HTTP,
        message_method=[HTTPMethodEnum.TRACE],
    )
    get_http_traces = partialmethod(
        get_messages,
        packet_type=PacketTypeEnum.HTTP,
        message_method=[HTTPMethodEnum.TRACE],
    )

    get_first_http_200 = partialmethod(
        get_first, packet_type=PacketTypeEnum.HTTP, http_status_code=200
    )
    get_http_200_responses = partialmethod(
        get_messages, packet_type=PacketTypeEnum.HTTP, http_status_code=200
    )

    get_first_https = partialmethod(get_first, packet_type=PacketTypeEnum.HTTPS)
    get_https_messages = partialmethod(get_messages, packet_type=PacketTypeEnum.HTTPS)

    # Other protocols

    get_first_tcp = partialmethod(get_first, packet_type=PacketTypeEnum.TCP)
    get_tcp_messages = partialmethod(get_messages, packet_type=PacketTypeEnum.TCP)

    get_first_udp = partialmethod(get_first, packet_type=PacketTypeEnum.UDP)
    get_udp_messages = partialmethod(get_messages, packet_type=PacketTypeEnum.UDP)

    get_first_rtp = partialmethod(get_first, packet_type=PacketTypeEnum.RTP)
    get_rtp_messages = partialmethod(get_messages, packet_type=PacketTypeEnum.RTP)

    get_first_msrp = partialmethod(get_first, packet_type=PacketTypeEnum.MSRP)
    get_msrp_messages = partialmethod(get_messages, packet_type=PacketTypeEnum.MSRP)

    get_first_dns = partialmethod(get_first, packet_type=PacketTypeEnum.DNS)
    get_dns_messages = partialmethod(get_messages, packet_type=PacketTypeEnum.DNS)

    get_first_icmp = partialmethod(get_first, packet_type=PacketTypeEnum.ICMP)
    get_icmp_messages = partialmethod(get_messages, packet_type=PacketTypeEnum.ICMP)

    get_first_arp = partialmethod(get_first, packet_type=PacketTypeEnum.ARP)
    get_arp_messages = partialmethod(get_messages, packet_type=PacketTypeEnum.ARP)
