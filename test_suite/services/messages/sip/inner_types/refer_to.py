from __future__ import annotations

from services.messages.sip.inner_types.uri import Uri


class ReferTo(Uri):
    """
    RFC 3261 Refer-To header - the transfer target, e.g.:
        Refer-To: <sip:CHFE-2@172.16.0.101:5060>;serviceurn="urn:service:sos"
    `uri` holds the target URI, `params` holds all header params (with
    `service_urn` as a convenience accessor for the "serviceurn" one).
    """

    _NAME = "Refer-To"

    @property
    def service_urn(self) -> str | None:
        return self.params.get("serviceurn")
