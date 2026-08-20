from test_suite.services.config.types.forward_conduit_config import (
    Conduit,
    ForwardConduit,
)
from test_suite.services.config.types.lab_config import LabConfig


class ForwardConduitService:
    """
    Generates ForwardConduit configuration from LabConfig.
    """

    PROXY_SUFFIX = "_PRS"

    def __init__(self, lab_config: LabConfig):
        self._lab_config = lab_config

    def build(self) -> ForwardConduit:
        conduits = []

        for entity in self._lab_config.entities or []:

            if entity.function in ("PROXY", "FORWARD"):
                continue

            for interface in entity.interfaces or []:

                to_if = self._reverse_interface_name(interface.name)

                if self._lab_config.get_if_by_name(to_if) is None:
                    continue

                proxy_if = f"{to_if}{self.PROXY_SUFFIX}"

                conduits.append(
                    Conduit(
                        name=self._build_conduit_name(interface.name),
                        from_if=interface.name,
                        to_if=to_if,
                        proxy_if=proxy_if,
                    )
                )

        return ForwardConduit(
            forward_conduits=conduits,
        )

    @staticmethod
    def _reverse_interface_name(name: str) -> str:
        parts = name.split("_")

        if len(parts) < 3:
            raise ValueError(f"Invalid interface name: {name}")

        return "_".join(
            [
                "IF",
                parts[2],
                parts[1],
                *parts[3:],
            ]
        )

    @staticmethod
    def _build_conduit_name(name: str) -> str:
        parts = name.split("_")

        if len(parts) < 3:
            raise ValueError(f"Invalid interface name: {name}")

        return f"{parts[1]}_to_{parts[2]}"

    def check(self, forward_conduit: ForwardConduit) -> list:
        """
        Validates that every conduit references existing interfaces
        in the current LabConfig.
        Raises ValueError on the first inconsistency.
        """
        errors = []
        for conduit in forward_conduit.forward_conduits:

            if self._lab_config.get_if_by_name(conduit.from_if) is None:
                errors.append(
                    f"Conduit '{conduit.name}': "
                    f"from_if '{conduit.from_if}' does not exist."
                )

            if self._lab_config.get_if_by_name(conduit.to_if) is None:
                errors.append(
                    f"Conduit '{conduit.name}': "
                    f"to_if '{conduit.to_if}' does not exist."
                )

            if self._lab_config.get_if_by_name(conduit.proxy_if) is None:
                errors.append(
                    f"Conduit '{conduit.name}': "
                    f"proxy_if '{conduit.proxy_if}' does not exist."
                )
        return errors
