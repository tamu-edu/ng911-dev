from dataclasses import dataclass, field
from typing import Any

from test_suite.services.config.types.lab_config import LabConfig
from test_suite.services.pcap_service import (
    PcapCaptureService,
    FilterConfig,
    PacketTypeFilter,
)

Packet = Any


@dataclass
class InterfaceMessages:
    """
    Container for packets associated with a logical interface.
    """

    requests: list[Packet] = field(default_factory=list)
    responses: list[Packet] = field(default_factory=list)


class MessageCollectorService:
    """
    Collects and caches logical request/response traffic for interface pairs.

    The service resolves interface names from LabConfig and generates
    corresponding FilterConfig objects for both request and response
    directions.

    Request traffic is collected using:

        src_ip=<interface_ip>
        dst_ip=<reverse_interface_ip>

    Response traffic is collected using:

        src_ip=<reverse_interface_ip>
        dst_ip=<interface_ip>
        response_mode=True

    Results are lazily loaded and cached per interface.

    Example:

        collector.get_requests("IF_OSP_BCF")
        collector.get_responses("IF_OSP_BCF")
        collector.get_all("IF_OSP_BCF")
    """

    def __init__(
        self,
        interfaces: list[str],
        pcap_service: PcapCaptureService,
        lab_config: LabConfig,
        packet_type: PacketTypeFilter = None,
    ) -> None:
        """
        Initialize MessageCollectorService.

        Args:
            interfaces:
                List of logical interface names to support.

            pcap_service:
                PcapCaptureService instance used for packet retrieval.

            lab_config:
                LabConfig instance used for interface resolution.

            packet_type:
                Optional packet type filter.

                Examples:

                    PacketTypeEnum.SIP

                    PacketTypeEnum.HTTP

                    [
                        PacketTypeEnum.SIP,
                        PacketTypeEnum.HTTP,
                    ]

                If provided, only matching packet types will be collected.

        Raises:
            ValueError:
                If any interface or its reverse pair cannot be found
                in the LabConfig.
        """
        self.interfaces = interfaces
        self.pcap = pcap_service
        self.lab_config = lab_config
        self.packet_type = packet_type

        self._interfaces_data: dict[str, dict] = lab_config.get_interfaces_data()

        self._cache: dict[str, InterfaceMessages] = {}

        self._validate_interfaces()

    def _validate_interfaces(self) -> None:
        """
        Validate configured interfaces.

        Ensures that:

        - every configured interface exists in LabConfig
        - every configured interface has a reverse interface

        Examples:

            IF_OSP_BCF  -> IF_BCF_OSP
            IF_BCF_ESRP -> IF_ESRP_BCF

        Raises:
            ValueError:
                If an interface or reverse interface is missing.
        """
        for interface_name in self.interfaces:
            if interface_name not in self._interfaces_data:
                raise ValueError(f"Interface '{interface_name}' not found in LabConfig")

            reverse_if = self._get_reverse_interface(interface_name)

            if reverse_if not in self._interfaces_data:
                raise ValueError(
                    f"Reverse interface '{reverse_if}' not found in LabConfig"
                )

    @staticmethod
    def _get_reverse_interface(interface_name: str) -> str:
        """
        Return the reverse logical interface.

        Examples:

            IF_OSP_BCF
                -> IF_BCF_OSP

            IF_ESRP_CHFE
                -> IF_CHFE_ESRP

        Args:
            interface_name:
                Interface name in IF_SRC_DST format.

        Returns:
            Reverse interface name.
        """
        _, src, dst = interface_name.split("_")

        return f"IF_{dst}_{src}"

    def get_packet_type_filter(self) -> PacketTypeFilter:
        """
        Return configured packet type filter.
        """
        return self.packet_type

    def _collect_interface(
        self,
        interface_name: str,
    ) -> InterfaceMessages:
        """
        Collect request and response traffic for a logical interface.

        Request packets are collected using standard filtering.

        Response packets are collected using response_mode=True.

        Results are cached after the first retrieval.

        Args:
            interface_name:
                Logical interface name.

        Returns:
            InterfaceMessages containing requests and responses.
        """
        if interface_name in self._cache:
            return self._cache[interface_name]

        reverse_if = self._get_reverse_interface(interface_name)

        src_ip = self._interfaces_data[interface_name]["ip"]
        dst_ip = self._interfaces_data[reverse_if]["ip"]

        request_filter = FilterConfig(
            src_ip=src_ip,
            dst_ip=dst_ip,
            packet_type=self.packet_type,
        )

        response_filter = FilterConfig(
            src_ip=dst_ip,
            dst_ip=src_ip,
            packet_type=self.packet_type,
            response_mode=True,
        )

        try:
            requests: list[Packet] = (
                self.pcap.get_messages_by_config(request_filter) or []
            )
        except IndexError:
            requests = []

        try:
            responses: list[Packet] = (
                self.pcap.get_messages_by_config(response_filter) or []
            )
        except IndexError:
            responses = []

        data = InterfaceMessages(
            requests=requests,
            responses=responses,
        )

        self._cache[interface_name] = data

        return data

    def get_requests(
        self,
        interface_name: str,
    ) -> list[Packet]:
        """
        Return request packets for a logical interface.

        Request packets represent traffic flowing in the logical
        direction of the interface.

        Example:

            IF_OSP_BCF

            OSP -> BCF

        Args:
            interface_name:
                Logical interface name.

        Returns:
            List of request packets.
        """
        return self._collect_interface(interface_name).requests

    def get_responses(
        self,
        interface_name: str,
    ) -> list[Packet]:
        """
        Return response packets for a logical interface.

        Response packets are resolved using reverse conduit matching
        and response_mode filtering.

        Example:

            IF_OSP_BCF

            BCF -> OSP

        Args:
            interface_name:
                Logical interface name.

        Returns:
            List of response packets.
        """
        return self._collect_interface(interface_name).responses

    def get_all(
        self,
        interface_name: str,
    ) -> list[Packet]:
        """
        Return all packets for a logical interface.

        Request and response packets are merged and sorted by
        capture timestamp.

        This method is useful for:

        - transcript generation
        - sequence diagrams
        - protocol flow validation

        Args:
            interface_name:
                Logical interface name.

        Returns:
            Chronologically ordered packet list.
        """
        data = self._collect_interface(interface_name)

        return sorted(
            data.requests + data.responses,
            key=lambda packet: float(packet.frame_info.time_epoch),
        )

    def get_data(
        self,
        interface_name: str,
    ) -> InterfaceMessages:
        """
        Return complete cached data for a logical interface.

        Provides direct access to both request and response
        collections.

        Args:
            interface_name:
                Logical interface name.

        Returns:
            InterfaceMessages object.
        """
        return self._collect_interface(interface_name)

    def preload(self) -> None:
        """
        Preload packet data for all configured interfaces.

        Forces packet collection immediately instead of waiting
        for the first request.

        Useful when many checks will access the same interfaces
        repeatedly.
        """
        for interface_name in self.interfaces:
            self._collect_interface(interface_name)

    def clear_cache(self) -> None:
        """
        Clear all cached packet collections.

        Subsequent calls will trigger packet retrieval again.
        """
        self._cache.clear()
