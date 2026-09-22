from __future__ import annotations

from dataclasses import MISSING, dataclass, field, fields
from typing import get_type_hints

# =============================================================================
# Base
# =============================================================================


@dataclass(kw_only=True, init=False)
class LogEvent:
    """Base NENA Logging Service LogEvent (NENA-STA-010, loggingservice.yaml).

    Common fields carried by every LogEvent subtype. Concrete subtypes inherit
    from this class and add their own type-specific fields.

    Mandatory fields:
        logEventType: LogEvent subtype name.
            Example: ``"CallStateChangeLogEvent"``
        timestamp: RFC 3339 date-time when the event was generated.
            Example: ``"2020-03-10T11:00:01-05:00"``
        elementId: FQDN of the functional element that produced the event.
            Example: ``"esrp1.state.pa.us"``
        agencyId: FQDN of the agency the element belongs to.
            Example: ``"psap.allegheny.pa.us"``

    Optional fields:
        clientAssignedIdentifier: Client-generated identifier for correlation.
            Example: ``"client-abc-42"``
        agencyAgentId: Agent identifier within the agency.
            Example: ``"agent42@psap.allegheny.pa.us"``
        agencyPositionId: Position identifier within the agency.
            Example: ``"position7@psap.allegheny.pa.us"``
        callId: NENA CallID URN.
            Example: ``"urn:emergency:uid:callid:a1b2c3@psap.allegheny.pa.us"``
        incidentId: NENA IncidentID URN.
            Example: ``"urn:emergency:uid:incidentid:x9y8@psap.allegheny.pa.us"``
        callIdSip: SIP Call-ID header value.
            Example: ``"3848276298220188511@atlanta.example.com"``
        ipAddressPort: ``ip:port`` of the peer involved in the event.
            Example: ``"192.0.2.10:5060"``
        extension: Free-form vendor extension object.
            Example: ``{"vendorX": {"foo": "bar"}}``
    """

    logEventType: str  # TODO check if missing
    timestamp: str
    elementId: str
    agencyId: str

    clientAssignedIdentifier: str | None = None
    agencyAgentId: str | None = None
    agencyPositionId: str | None = None
    callId: str | None = None
    incidentId: str | None = None
    callIdSip: str | None = None
    ipAddressPort: str | None = None
    extension: dict | None = None

    def __init__(self, data: dict | None = None):
        data = data or {}
        for f in fields(self):
            setattr(self, f.name, data.get(f.name, None))

    @classmethod
    def mandatory_fields(cls) -> dict[str, type]:
        """Return ``{field_name: resolved_type}`` for fields without a default."""
        type_hints = get_type_hints(cls)
        return {
            f.name: type_hints[f.name]
            for f in fields(cls)
            if f.default is MISSING and f.default_factory is MISSING
        }

    @classmethod
    def optional_fields(cls) -> dict[str, type]:
        """Return ``{field_name: resolved_type}`` for fields with a default."""
        type_hints = get_type_hints(cls)
        return {
            f.name: type_hints[f.name]
            for f in fields(cls)
            if f.default is not MISSING or f.default_factory is not MISSING
        }


# =============================================================================
# Call context intermediate
# =============================================================================


@dataclass(kw_only=True, init=False)
class CallLogEvent(LogEvent):
    """Intermediate LogEvent adding call-context fields.

    Corresponds to the ``CallLogEvent`` schema mixed in via ``allOf`` in
    loggingservice.yaml. Not a discriminator value itself — used as the base
    for CallStart/CallEnd/RecCallStart/RecCallEnd/SessionStart/SessionEnd.

    Additional mandatory fields:
        direction: ``"incoming"`` or ``"outgoing"``.

    Additional optional fields:
        standardPrimaryCallType: Value from NENA LogEvent CallTypes registry.
            Example: ``"emergency"``
        standardSecondaryCallType: Value from NENA LogEvent CallTypes registry.
            Example: ``"medical"``
        localCallType: Local classification of the call.
            Example: ``"non-emergency-abandoned"``
        localUse: Free-form vendor-local object.
            Example: ``{"routingReason": "overflow"}``
        to: Destination URI/address of the call.
            Example: ``"sip:911@psap.allegheny.pa.us"``
        from_: Originating URI/address of the call.
            Example: ``"sip:+15551234567@originating.example.com"``
            Note: exposed as ``from_`` in Python because ``from`` is reserved.
    """

    direction: str
    standardPrimaryCallType: str | None = None
    standardSecondaryCallType: str | None = None
    localCallType: str | None = None
    localUse: dict | None = None
    to: str | None = None
    from_: str | None = None


# =============================================================================
# Call lifecycle
# =============================================================================


@dataclass(kw_only=True, init=False)
class CallProcessLogEvent(LogEvent):
    """Marks a call-processing step on a functional element. No extra fields.

    Example ``logEventType`` value: ``"CallProcessLogEvent"``.
    """


@dataclass(kw_only=True, init=False)
class CallStartLogEvent(CallLogEvent):
    """Marks the start of a call. Inherits all CallLogEvent fields.

    Example ``logEventType`` value: ``"CallStartLogEvent"``.
    """


@dataclass(kw_only=True, init=False)
class CallEndLogEvent(CallLogEvent):
    """Marks the end of a call. Inherits all CallLogEvent fields.

    Example ``logEventType`` value: ``"CallEndLogEvent"``.
    """


@dataclass(kw_only=True, init=False)
class RecCallStartLogEvent(CallLogEvent):
    """Recorder-side start of a call. Inherits all CallLogEvent fields.

    Example ``logEventType`` value: ``"RecCallStartLogEvent"``.
    """


@dataclass(kw_only=True, init=False)
class RecCallEndLogEvent(CallLogEvent):
    """Recorder-side end of a call. Inherits all CallLogEvent fields.

    Example ``logEventType`` value: ``"RecCallEndLogEvent"``.
    """


@dataclass(kw_only=True, init=False)
class CallTransferLogEvent(LogEvent):
    """Records a call transfer to a new target.

    Additional mandatory fields:
        target: URI of the transfer target.
            Example: ``"sip:secondary@psap.allegheny.pa.us"``

    Additional optional fields:
        targetCallIdSip: SIP Call-ID of the resulting leg to the target.
            Example: ``"transfer-a1b2@psap.allegheny.pa.us"``
    """

    target: str
    targetCallIdSip: str | None = None


# =============================================================================
# Routing / policy
# =============================================================================


@dataclass(kw_only=True, init=False)
class RouteLogEvent(LogEvent):
    """Records a routing decision made by an ESRP or similar element.

    Additional mandatory fields:
        recipientUri: URI the call/message was routed to.
            Example: ``"sip:queue1@psap.allegheny.pa.us"``
        ruleId: Identifier of the policy rule that fired.
            Example: ``"rule-042"``
        policyOwner: Owner/authority of the policy.
            Example: ``"psap.allegheny.pa.us"``
        policyType: Value from the policyType registry.
            Example: ``"NormalNextHop"``

    Additional optional fields:
        policyQueueName: Queue URI referenced by the policy.
            Example: ``"sip:queue1@psap.allegheny.pa.us"``
        policyId: Identifier of the policy document.
            Example: ``"policy-2025-01"``
        cause: Free-form cause/explanation.
            Example: ``"peak-hour overflow"``
    """

    recipientUri: str
    ruleId: str
    policyOwner: str
    policyType: str
    policyQueueName: str | None = None
    policyId: str | None = None
    cause: str | None = None


@dataclass(kw_only=True, init=False)
class RouteRuleMsgLogEvent(LogEvent):
    """Records an informational message emitted by the route-rule engine.

    Additional mandatory fields:
        ruleId: Identifier of the rule that produced the message.
            Example: ``"rule-042"``
        priority: Integer priority of the message.
            Example: ``5``
        message: Human-readable message text.
            Example: ``"queue full, overflow triggered"``
        policyOwner: Owner/authority of the policy.
            Example: ``"psap.allegheny.pa.us"``
        policyType: Value from the policyType registry.
            Example: ``"NormalNextHop"``

    Additional optional fields:
        policyQueueName: Queue URI referenced by the policy.
        policyId: Identifier of the policy document.
    """

    ruleId: str
    priority: int
    message: str
    policyOwner: str
    policyType: str
    policyQueueName: str | None = None
    policyId: str | None = None


@dataclass(kw_only=True, init=False)
class PolicyChangeLogEvent(LogEvent):
    """Records a policy CREATE/UPDATE/DELETE by an editor.

    Additional mandatory fields:
        policyType: Value from the policyType registry.
            Example: ``"NormalNextHop"``
        owner: Policy owner.
            Example: ``"psap.allegheny.pa.us"``
        changeType: One of ``"CREATE"``, ``"UPDATE"``, ``"DELETE"``.
        policyContent: Full serialized policy content.
        policyStoreId: Identifier of the policy store.
            Example: ``"ps-01"``
        policyEditor: Identifier of the editor who made the change.
            Example: ``"editor42@psap.allegheny.pa.us"``

    Additional optional fields:
        policyQueueName: Queue URI referenced by the policy.
        policyId: Identifier of the policy document.
    """

    policyType: str
    owner: str
    changeType: str
    policyContent: str
    policyStoreId: str
    policyEditor: str
    policyQueueName: str | None = None
    policyId: str | None = None


# =============================================================================
# Media
# =============================================================================


@dataclass(kw_only=True, init=False)
class MediaStartLogEvent(LogEvent):
    """Records the start of a media stream.

    Additional mandatory fields:
        sdp: SDP body describing the stream.
        mediaLabel: List of media labels (mid values).
            Example: ``["audio", "video"]``
        direction: ``"incoming"`` or ``"outgoing"``.

    Note: the YAML's ``required`` list contains the typo ``mediaLabal``; the
    Python model uses the corrected name ``mediaLabel`` per intent.
    """

    sdp: str
    mediaLabel: list[str]
    direction: str


@dataclass(kw_only=True, init=False)
class MediaEndLogEvent(LogEvent):
    """Records the end of a media stream.

    Additional mandatory fields:
        mediaLabel: List of media labels (mid values).

    Additional optional fields:
        mediaQualityStats: Serialized RTCP/media quality metrics.
    """

    mediaLabel: list[str]
    mediaQualityStats: str | None = None


@dataclass(kw_only=True, init=False)
class RecMediaStartLogEvent(LogEvent):
    """Recorder-side start of a media stream.

    Additional mandatory fields:
        sdp: SDP body describing the stream.
        mediaLabel: List of media labels (mid values).

    Additional optional fields:
        direction: ``"incoming"`` or ``"outgoing"``.
        mediaTranscodeFrom: Original codec/format before transcoding.
            Example: ``"AMR-WB"``
    """

    sdp: str
    mediaLabel: list[str]
    direction: str | None = None
    mediaTranscodeFrom: str | None = None


@dataclass(kw_only=True, init=False)
class RecMediaEndLogEvent(LogEvent):
    """Recorder-side end of a media stream.

    Additional mandatory fields:
        mediaLabel: List of media labels (mid values).

    Additional optional fields:
        mediaQualityStats: Serialized RTCP/media quality metrics.
        mediaTranscodeFrom: Original codec/format before transcoding.
    """

    mediaLabel: list[str]
    mediaQualityStats: str | None = None
    mediaTranscodeFrom: str | None = None


@dataclass(kw_only=True, init=False)
class RecordingFailedLogEvent(LogEvent):
    """Records a recording failure with reason.

    Additional mandatory fields:
        sdp: SDP body of the failed session.
        reasonCode: Value from the NENA ReasonCode registry.
            Example: ``"storage-full"``
        reasonText: Human-readable explanation.
            Example: ``"disk quota exceeded on primary recorder"``
    """

    sdp: str
    reasonCode: str
    reasonText: str


# =============================================================================
# Messaging / signaling
# =============================================================================


@dataclass(kw_only=True, init=False)
class MessageLogEvent(LogEvent):
    """Records a text message exchanged in a call/session.

    Additional mandatory fields:
        text: Message body.
            Example: ``"Sending medical to 123 Main St"``
        direction: ``"incoming"`` or ``"outgoing"``.
    """

    text: str
    direction: str


@dataclass(kw_only=True, init=False)
class CallSignalingMessageLogEvent(LogEvent):
    """Records a SIP (or other) signaling message associated with a call.

    Additional mandatory fields:
        text: Full raw signaling message.
        direction: ``"incoming"`` or ``"outgoing"``.

    Additional optional fields:
        protocol: Protocol name.
            Example: ``"SIP"``
    """

    text: str
    direction: str
    protocol: str | None = None


@dataclass(kw_only=True, init=False)
class SipRecMetadataLogEvent(LogEvent):
    """Records SIPREC metadata associated with a recorded session.

    Additional mandatory fields:
        text: SIPREC metadata XML/JSON body.
    """

    text: str


@dataclass(kw_only=True, init=False)
class NonRtpMediaMessageLogEvent(LogEvent):
    """Records a non-RTP media message (e.g. MSRP, T.140 out-of-band).

    Additional mandatory fields:
        text: Message body.
        direction: ``"incoming"`` or ``"outgoing"``.

    Additional optional fields:
        protocol: Protocol name.
            Example: ``"MSRP"``
    """

    text: str
    direction: str
    protocol: str | None = None


@dataclass(kw_only=True, init=False)
class MalformedMessageLogEvent(LogEvent):
    """Records receipt of a malformed message from a peer.

    Additional mandatory fields:
        text: Raw malformed message.
        ipAddress: Source IP address of the sender.
            Example: ``"198.51.100.7"``

    Additional optional fields:
        explanationText: Explanation of why the message was rejected.
    """

    text: str
    ipAddress: str
    explanationText: str | None = None


# =============================================================================
# Incident lifecycle
# =============================================================================


@dataclass(kw_only=True, init=False)
class AdditionalAgencyLogEvent(LogEvent):
    """Records an additional agency joining a call or incident.

    Reuses the base ``agencyId`` field (already mandatory) — no new fields.
    Example ``logEventType`` value: ``"AdditionalAgencyLogEvent"``.
    """


@dataclass(kw_only=True, init=False)
class IncidentMergeLogEvent(LogEvent):
    """Records the merge of one incident into another.

    Additional mandatory fields:
        incidentId: Surviving incident identifier (overrides base optional).
        mergeIncidentId: Identifier of the incident that was merged in.
    """

    incidentId: str = field()
    mergeIncidentId: str


@dataclass(kw_only=True, init=False)
class IncidentUnMergeLogEvent(LogEvent):
    """Records the un-merge (reversal) of a prior merge.

    Additional mandatory fields:
        incidentId: Current incident identifier (overrides base optional).
        unmergedFromIncidentId: Identifier of the incident that was un-merged.
    """

    incidentId: str = field()
    unmergedFromIncidentId: str


@dataclass(kw_only=True, init=False)
class IncidentLinkLogEvent(LogEvent):
    """Records a link between two incidents (parent/child/unspecified).

    Additional mandatory fields:
        incidentId: Anchor incident identifier (overrides base optional).
        linkedIncidentId: Identifier of the linked incident.
        relationship: One of ``"parent"``, ``"child"``, ``"unspecified"``.
    """

    incidentId: str = field()
    linkedIncidentId: str
    relationship: str


@dataclass(kw_only=True, init=False)
class IncidentUnLinkLogEvent(LogEvent):
    """Records removal of a prior incident link.

    Additional mandatory fields:
        incidentId: Anchor incident identifier (overrides base optional).
        unlinkedFromIncidentId: Identifier of the previously linked incident.
    """

    incidentId: str = field()
    unlinkedFromIncidentId: str


@dataclass(kw_only=True, init=False)
class IncidentClearLogEvent(LogEvent):
    """Marks an incident as cleared. No extra fields.

    Example ``logEventType`` value: ``"IncidentClearLogEvent"``.
    """


@dataclass(kw_only=True, init=False)
class IncidentReopenLogEvent(LogEvent):
    """Marks a previously cleared incident as reopened. No extra fields.

    Example ``logEventType`` value: ``"IncidentReopenLogEvent"``.
    """


@dataclass(kw_only=True, init=False)
class IncidentSplitLogEvent(LogEvent):
    """Records a split of one incident into two.

    Additional mandatory fields:
        incidentId: Incident identifier of the resulting record
            (overrides base optional).
        type: ``"old"`` (original incident) or ``"new"`` (split-off incident).
    """

    incidentId: str = field()
    type: str


@dataclass(kw_only=True, init=False)
class DiscrepancyReportLogEvent(LogEvent):
    """Records a discrepancy report exchange.

    Additional mandatory fields:
        contents: Discrepancy report body.
        direction: ``"incoming"`` or ``"outgoing"``.
        type: Discrepancy report type.
            Example: ``"data-quality"``
    """

    contents: str
    direction: str
    type: str


# =============================================================================
# Location / ALI
# =============================================================================


@dataclass(kw_only=True, init=False)
class AliLocationQueryLogEvent(LogEvent):
    """Records an ALI (legacy location) query.

    Additional mandatory fields:
        text: Raw query message.
        direction: ``"incoming"`` or ``"outgoing"``.
        queryId: Correlation identifier for the query.
    """

    text: str
    direction: str
    queryId: str


@dataclass(kw_only=True, init=False)
class AliLocationResponseLogEvent(LogEvent):
    """Records an ALI (legacy location) response.

    Additional mandatory fields:
        text: Raw response message.
        direction: ``"incoming"`` or ``"outgoing"``.
        responseId: Correlation identifier for the response.

    Additional optional fields:
        responseStatus: Value from the Status Codes registry.
            Example: ``"200"``
    """

    text: str
    direction: str
    responseId: str
    responseStatus: str | None = None


@dataclass(kw_only=True, init=False)
class LocationQueryLogEvent(LogEvent):
    """Records a HELD/LIS location query.

    Additional mandatory fields:
        uri: Query target URI.
            Example: ``"https://lis.example.com/location"``
        text: Raw query body.
        direction: ``"incoming"`` or ``"outgoing"``.
        queryId: Correlation identifier for the query.
    """

    uri: str
    text: str
    direction: str
    queryId: str


@dataclass(kw_only=True, init=False)
class LocationResponseLogEvent(LogEvent):
    """Records a HELD/LIS location response.

    Additional mandatory fields:
        text: Raw response body.
        direction: ``"incoming"`` or ``"outgoing"``.
        responseId: Correlation identifier for the response.

    Additional optional fields:
        responseStatus: Value from the Status Codes registry.
    """

    text: str
    direction: str
    responseId: str
    responseStatus: str | None = None


# =============================================================================
# LoST
# =============================================================================


@dataclass(kw_only=True, init=False)
class LostQueryLogEvent(LogEvent):
    """Records a LoST (Location-to-Service Translation) query.

    Additional mandatory fields:
        queryAdapter: Adapter/interface used to send the query.
        direction: ``"incoming"`` or ``"outgoing"``.
        queryId: Correlation identifier for the query.

    Additional optional fields:
        malformedQuery: Raw body of the query if it was malformed.
    """

    queryAdapter: str
    direction: str
    queryId: str
    malformedQuery: str | None = None


@dataclass(kw_only=True, init=False)
class LostResponseLogEvent(LogEvent):
    """Records a LoST response.

    Additional mandatory fields:
        responseAdapter: Adapter/interface used to receive the response.
        direction: ``"incoming"`` or ``"outgoing"``.
        responseId: Correlation identifier for the response.

    Additional optional fields:
        responseStatus: Response status code/string.
        malformedResponse: Raw body of the response if it was malformed.
    """

    responseAdapter: str
    direction: str
    responseId: str
    responseStatus: str | None = None
    malformedResponse: str | None = None


# =============================================================================
# Additional data
# =============================================================================


@dataclass(kw_only=True, init=False)
class AdditionalDataAddedLogEvent(LogEvent):
    """Records that an Additional Data block was attached to a call/incident.

    Not present in the ``LogEventType`` enum in loggingservice.yaml but defined
    under ``components/schemas``; included here for schema completeness.

    Additional mandatory fields:
        block: Serialized Additional Data block.
    """

    block: str


@dataclass(kw_only=True, init=False)
class AdditionalDataQueryLogEvent(LogEvent):
    """Records an Additional Data dereference query.

    Additional mandatory fields:
        uri: URI being dereferenced.
        text: Raw query body.
        direction: ``"incoming"`` or ``"outgoing"``.
        queryId: Correlation identifier for the query.
    """

    uri: str
    text: str
    direction: str
    queryId: str


@dataclass(kw_only=True, init=False)
class AdditionalDataResponseLogEvent(LogEvent):
    """Records an Additional Data dereference response.

    Additional mandatory fields:
        text: Raw response body.
        direction: ``"incoming"`` or ``"outgoing"``.
        responseId: Correlation identifier for the response.

    Additional optional fields:
        responseStatus: Value from the Status Codes registry.
    """

    text: str
    direction: str
    responseId: str
    responseStatus: str | None = None


# =============================================================================
# State change (call / session / element / service / agent / queue)
# =============================================================================


@dataclass(kw_only=True, init=False)
class CallStateChangeLogEvent(LogEvent):
    """LogEvent recording a SIP call state transition on a functional element.

    Additional mandatory fields:
        state: Call state per the NENA CallStates registry.
            Example: ``"Ringing"``, ``"Answered"``, ``"Hangup"``
        direction: ``"incoming"`` or ``"outgoing"``.

    Additional optional fields:
        legCallId: SIP Call-ID of the specific call leg the state refers to.
            Example: ``"leg-77aa@atlanta.example.com"``
        targetId: URI of the transfer/redirection target, when applicable.
            Example: ``"sip:agent99@psap.allegheny.pa.us"``
        changeReason: Free-form human-readable reason for the transition.
            Example: ``"answered by agent42"``
    """

    state: str
    direction: str
    legCallId: str | None = None
    targetId: str | None = None
    changeReason: str | None = None


@dataclass(kw_only=True, init=False)
class SessionStateChangeLogEvent(LogEvent):
    """LogEvent recording a session state transition.

    Additional mandatory fields:
        state: Session state per the NENA CallStates registry.
        direction: ``"incoming"`` or ``"outgoing"``.
        legCallId: SIP Call-ID of the specific call leg.

    Additional optional fields:
        targetId: URI of a transfer target, when applicable.
        changeReason: Free-form reason for the transition.
    """

    state: str
    direction: str
    legCallId: str
    targetId: str | None = None
    changeReason: str | None = None


@dataclass(kw_only=True, init=False)
class ElementStateChangeLogEvent(LogEvent):
    """Records a state change of a functional element.

    Additional mandatory fields:
        notificationContents: Serialized state-change notification body.
        direction: ``"incoming"`` or ``"outgoing"``.

    Additional optional fields:
        StateChangeNotificationContents: Alternate notification body
            (name preserved as-is from the YAML).
        affectedElementId: FQDN of the affected element if different from
            the emitting one.
    """

    notificationContents: str
    direction: str
    StateChangeNotificationContents: str | None = None
    affectedElementId: str | None = None


@dataclass(kw_only=True, init=False)
class ServiceStateChangeLogEvent(LogEvent):
    """Records a state change of a service.

    Additional mandatory fields:
        newState: New service state.
            Example: ``"Normal"``, ``"Down"``
        affectedServiceIdentifier: Identifier of the affected service.
            Example: ``"esrp@psap.allegheny.pa.us"``
        direction: ``"incoming"`` or ``"outgoing"``.

    Additional optional fields:
        newSecurityPosture: New security posture value.
            Example: ``"Elevated"``
    """

    newState: str
    affectedServiceIdentifier: str
    direction: str
    newSecurityPosture: str | None = None


@dataclass(kw_only=True, init=False)
class AgentStateChangeLogEvent(LogEvent):
    """Records an agent state change.

    Additional mandatory fields:
        primaryAgentState: ``"Available"`` or ``"NotAvailable"``.

    Additional optional fields:
        secondaryAgentState: Value from the Secondary Agent State registry.
            Example: ``"OnBreak"``
        deviceId: Identifier of the agent's device.
    """

    primaryAgentState: str
    secondaryAgentState: str | None = None
    deviceId: str | None = None


@dataclass(kw_only=True, init=False)
class QueueStateChangeLogEvent(LogEvent):
    """Records a queue state change.

    Additional mandatory fields:
        notificationContents: Serialized notification body.
        queueId: Identifier of the affected queue.
            Example: ``"sip:queue1@psap.allegheny.pa.us"``
        direction: ``"incoming"`` or ``"outgoing"``.
    """

    notificationContents: str
    queueId: str
    direction: str


# =============================================================================
# Gateway / legacy telephony
# =============================================================================


@dataclass(kw_only=True, init=False)
class GatewayCallLogEvent(LogEvent):
    """Records gateway-side context for a call (all fields optional).

    Additional optional fields:
        portTrunkGroup: Gateway port or trunk group identifier.
            Example: ``"TG-42"``
        pAni: Pseudo-ANI number.
            Example: ``"5551234567"``
        digits: Digits collected.
        direction: ``"incoming"`` or ``"outgoing"``.
        signallingProtocol: Legacy signaling protocol.
            Example: ``"ISUP"``, ``"MF"``
        legacyCallId: Legacy call identifier.
        esn: Emergency Service Number.
            Example: ``"12345"``
    """

    portTrunkGroup: str | None = None
    pAni: str | None = None
    digits: str | None = None
    direction: str | None = None
    signallingProtocol: str | None = None
    legacyCallId: str | None = None
    esn: str | None = None


@dataclass(kw_only=True, init=False)
class HookflashLogEvent(LogEvent):
    """Records a legacy hookflash on a line.

    Additional optional fields:
        lineId: Identifier of the line the hookflash occurred on.
    """

    lineId: str | None = None


@dataclass(kw_only=True, init=False)
class LegacyDigitsLogEvent(LogEvent):
    """Records legacy DTMF/MF digit events.

    Additional mandatory fields:
        digits: Collected digits.
            Example: ``"911"``
        sentReceived: ``"sent"`` or ``"received"``.
        type: ``"DTMF"`` or ``"MF"``.
    """

    digits: str
    sentReceived: str
    type: str


# =============================================================================
# Keep-alive / versions
# =============================================================================


@dataclass(kw_only=True, init=False)
class KeepAliveFailureLogEvent(LogEvent):
    """Records a keep-alive failure.

    Additional mandatory fields:
        responseStatus: Value from the Status Codes registry.
            Example: ``"408"``
    """

    responseStatus: str


@dataclass(kw_only=True, init=False)
class VersionsLogEvent(LogEvent):
    """Records the outcome of a Versions query.

    Additional mandatory fields:
        source: Source of the versions query.
            Example: ``"esrp1.state.pa.us"``
        response: Serialized versions response.
    """

    source: str
    response: str


# =============================================================================
# Subscribe
# =============================================================================


@dataclass(kw_only=True, init=False)
class SubscribeLogEvent(LogEvent):
    """Records a SIP SUBSCRIBE exchange.

    Additional mandatory fields:
        package: Value from the SIP Event Package registry.
            Example: ``"presence"``
        peer: Peer URI.
        parameter: List of ``{"type": ..., "value": ...}`` parameter objects.
            Example: ``[{"type": "expires", "value": "3600"}]``
        expiration: Subscription expiration in seconds.
            Example: ``3600``
        response: Serialized response.
        purpose: ``"initial"``, ``"refresh"``, or ``"terminate"``.
        direction: ``"incoming"`` or ``"outgoing"``.
        subscriptionId: Identifier of the subscription.
    """

    package: str
    peer: str
    parameter: list[dict]
    expiration: int
    response: str
    purpose: str
    direction: str
    subscriptionId: str


# =============================================================================
# Announcements
# =============================================================================


@dataclass(kw_only=True, init=False)
class AnnouncementStartLogEvent(LogEvent):
    """Records the start of an in-call announcement.

    Additional mandatory fields:
        announcementType: Type of announcement.
            Example: ``"queue-hold"``

    Additional optional fields:
        announcementTag: Tag/identifier of the specific announcement.
            Example: ``"tag-42"``
    """

    announcementType: str
    announcementTag: str | None = None


@dataclass(kw_only=True, init=False)
class AnnouncementEndLogEvent(LogEvent):
    """Records the end of an in-call announcement.

    Additional mandatory fields:
        announcementType: Type of announcement.

    Additional optional fields:
        announcementTag: Tag/identifier of the specific announcement.
    """

    announcementType: str
    announcementTag: str | None = None


# =============================================================================
# Sessions
# =============================================================================


@dataclass(kw_only=True, init=False)
class SessionStartLogEvent(CallLogEvent):
    """Marks the start of a session. Inherits all CallLogEvent fields.

    Example ``logEventType`` value: ``"SessionStartLogEvent"``.
    """


@dataclass(kw_only=True, init=False)
class SessionEndLogEvent(CallLogEvent):
    """Marks the end of a session. Inherits all CallLogEvent fields.

    Example ``logEventType`` value: ``"SessionEndLogEvent"``.
    """


# =============================================================================
# EIDO
# =============================================================================


@dataclass(kw_only=True, init=False)
class EidoLogEvent(LogEvent):
    """Records an EIDO (Emergency Incident Data Object) message.

    Additional mandatory fields:
        direction: ``"incoming"`` or ``"outgoing"``.

    Additional optional fields:
        peerId: Peer URI.
        body: EIDO document body.
        reference: Reference URI when the EIDO is transmitted by reference.
        subscriptionId: Associated subscription identifier.
    """

    direction: str
    peerId: str | None = None
    body: str | None = None
    reference: str | None = None
    subscriptionId: str | None = None


@dataclass(kw_only=True, init=False)
class EidoDereferenceFactoryQueryLogEvent(LogEvent):
    """Records an EIDO dereference-factory query.

    Additional mandatory fields:
        queryId: Correlation identifier for the query.
        direction: ``"incoming"`` or ``"outgoing"``.
        peerId: Peer URI.
    """

    queryId: str
    direction: str
    peerId: str


@dataclass(kw_only=True, init=False)
class EidoDereferenceFactoryQueryResponseLogEvent(LogEvent):
    """Records an EIDO dereference-factory response.

    Additional mandatory fields:
        queryId: Correlation identifier for the query.
        direction: ``"incoming"`` or ``"outgoing"``.
        peerId: Peer URI.

    Additional optional fields:
        generatedURI: Dereference URI generated by the factory.
        responseError: Error string if the dereference failed.
        responseText: Response body.
    """

    queryId: str
    direction: str
    peerId: str
    generatedURI: str | None = None
    responseError: str | None = None
    responseText: str | None = None


@dataclass(kw_only=True, init=False)
class EidoDeniedLogEvent(LogEvent):
    """Records that access to an EIDO dereference was denied.

    Additional mandatory fields:
        direction: ``"incoming"`` or ``"outgoing"``.
        peerId: Peer URI.
        eidoDereference: Requested dereference URI.
        reasonCode: Value from the ReasonCode registry.
        reasonText: Human-readable reason.
    """

    direction: str
    peerId: str
    eidoDereference: str
    reasonCode: str
    reasonText: str


@dataclass(kw_only=True, init=False)
class EidoTransmissionErrorLogEvent(LogEvent):
    """Records a failed EIDO transmission attempt.

    Additional mandatory fields:
        peerId: Peer URI.
        transactionId: Transaction identifier.
        direction: ``"incoming"`` or ``"outgoing"``.
        retries: Number of retries attempted.
        reasonCode: Value from the ReasonCode registry.
        reasonText: Human-readable reason.
    """

    peerId: str
    transactionId: str
    direction: str
    retries: int
    reasonCode: str
    reasonText: str


# =============================================================================
# Subscriptions
# =============================================================================


@dataclass(kw_only=True, init=False)
class SubscriptionRequestedLogEvent(LogEvent):
    """Records a subscription request.

    Additional mandatory fields:
        peerId: Peer URI.
        direction: ``"incoming"`` or ``"outgoing"``.
        queryId: Correlation identifier for the request.

    Additional optional fields:
        protocol: Subscription protocol.
        expires: Requested expiration in seconds.
        subscriptionId: Assigned subscription identifier.
        qualFilter: Qualification filter.
        unitId: Unit identifier.
    """

    peerId: str
    direction: str
    queryId: str
    protocol: str | None = None
    expires: int | None = None
    subscriptionId: str | None = None
    qualFilter: str | None = None
    unitId: str | None = None


@dataclass(kw_only=True, init=False)
class SubscriptionRequestedResponseLogEvent(LogEvent):
    """Records the response to a subscription request.

    Additional mandatory fields:
        queryId: Correlation identifier from the original request.
        direction: ``"incoming"`` or ``"outgoing"``.

    Additional optional fields:
        subscriptionId: Assigned subscription identifier.
        expires: Granted expiration in seconds.
        errorCode: Error code when the subscription was rejected.
        errorText: Error text when the subscription was rejected.
    """

    queryId: str
    direction: str
    subscriptionId: str | None = None
    expires: int | None = None
    errorCode: str | None = None
    errorText: str | None = None


@dataclass(kw_only=True, init=False)
class SubscriptionTerminatedLogEvent(LogEvent):
    """Records termination of a subscription.

    Additional mandatory fields:
        peerId: Peer URI.
        subscriptionId: Identifier of the terminated subscription.
        direction: ``"incoming"`` or ``"outgoing"``.
        requestId: Correlation identifier for the terminate request.
        reason: Termination reason.
    """

    peerId: str
    subscriptionId: str
    direction: str
    requestId: str
    reason: str


@dataclass(kw_only=True, init=False)
class SubscriptionTerminatedResponseLogEvent(LogEvent):
    """Records the response to a subscription-termination request.

    Additional mandatory fields:
        peerId: Peer URI.
        direction: ``"incoming"`` or ``"outgoing"``.
        queryId: Correlation identifier for the response.
        subscriptionId: Identifier of the subscription.
        statusCode: Response status code.
        statusText: Response status text.
    """

    peerId: str
    direction: str
    queryId: str
    subscriptionId: str
    statusCode: str
    statusText: str


# =============================================================================
# WebSocket
# =============================================================================


@dataclass(kw_only=True, init=False)
class WebSocketEstablishedLogEvent(LogEvent):
    """Records establishment of a WebSocket connection.

    Additional mandatory fields:
        peerId: Peer URI.
        direction: ``"incoming"`` or ``"outgoing"``.
        status: HTTP-style status of the handshake.
            (YAML's ``required`` uses ``statusCode`` which does not match the
            defined property ``status``; the Python model follows the
            property.)
        statusDescription: Human-readable description of the status.
        webSocketId: Local WebSocket identifier.
    """

    peerId: str
    direction: str
    status: str
    statusDescription: str
    webSocketId: str


@dataclass(kw_only=True, init=False)
class WebSocketTerminatedLogEvent(LogEvent):
    """Records termination of a WebSocket connection.

    Additional mandatory fields:
        peerId: Peer URI.
        direction: ``"incoming"`` or ``"outgoing"``.
        closeCode: WebSocket close code (uint16).
            Example: ``1000``
        closeText: WebSocket close reason text.
        webSocketId: Local WebSocket identifier.
    """

    peerId: str
    direction: str
    closeCode: int
    closeText: str
    webSocketId: str


# =============================================================================
# Requests / resources
# =============================================================================


@dataclass(kw_only=True, init=False)
class RequestForServiceLogEvent(LogEvent):
    """Records a request-for-service message.

    Additional mandatory fields:
        peerId: Peer URI.
        direction: ``"incoming"`` or ``"outgoing"``.
        requestId: Correlation identifier for the request.
            (The YAML lists ``requesttId`` in ``required`` — treated as a
            typo; the property name ``requestId`` is used.)
    """

    peerId: str
    direction: str
    requestId: str


@dataclass(kw_only=True, init=False)
class RequestAwarenessLogEvent(LogEvent):
    """Records a request-awareness message.

    Additional mandatory fields:
        peerId: Peer URI.
        direction: ``"incoming"`` or ``"outgoing"``.
        requestId: Correlation identifier for the request.
    """

    peerId: str
    direction: str
    requestId: str


@dataclass(kw_only=True, init=False)
class CancelRequestLogEvent(LogEvent):
    """Records a cancel-request message.

    Additional mandatory fields:
        peerId: Peer URI.
        direction: ``"incoming"`` or ``"outgoing"``.
        requestId: Correlation identifier for the cancelled request.
    """

    peerId: str
    direction: str
    requestId: str


@dataclass(kw_only=True, init=False)
class ResponseToRequestLogEvent(LogEvent):
    """Records a response to a prior request.

    Additional mandatory fields:
        peerId: Peer URI.
        direction: ``"incoming"`` or ``"outgoing"``.
        responseCode: Response code.
        responseText: Response text.
    """

    peerId: str
    direction: str
    responseCode: str
    responseText: str


@dataclass(kw_only=True, init=False)
class ResourceMesssageLogEvent(LogEvent):  # noqa: N801 — YAML class name has a typo
    """Records a resource message exchange.

    Class name preserves the triple-``s`` typo (``Messsage``) from the
    ``LogEventType`` enum in loggingservice.yaml so string-matching against
    the wire ``logEventType`` value is exact.

    Additional mandatory fields:
        peerId: Peer URI.
        direction: ``"incoming"`` or ``"outgoing"``.
        resourceMessage: Resource message object.
    """

    peerId: str
    direction: str
    resourceMessage: dict


@dataclass(kw_only=True, init=False)
class ResourceDiscoveryLogEvent(LogEvent):
    """Records a resource discovery exchange.

    Additional mandatory fields:
        peerId: Peer URI.
        direction: ``"incoming"`` or ``"outgoing"``.
        emergencyResourceComponent: Emergency resource component object.
    """

    peerId: str
    direction: str
    emergencyResourceComponent: dict
