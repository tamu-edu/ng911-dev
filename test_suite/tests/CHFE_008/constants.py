SERVICE_STATE_VALUES = [
    "Normal",
    "Unstaffed",
    "ScheduledMaintenanceDown",
    "ScheduledMaintenanceAvailable",
    "MajorIncidentInProgress",
    "Partial",
    "Overloaded",
    "GoingDown",
    "Down",
    "Unreachable",
]

SERVICE_NAMES = [
    "ADR",
    "Bridge",
    "ECRF",
    "ESRP",
    "GCS",
    "IMR",
    "Logging",
    "LVF",
    "MCS",
    "MDS",
    "PolicyStore",
    "PSAP",
]

POSTURE_VALUES = ["Green", "Yellow", "Orange", "Red"]

EVENT = "emergency-ServiceState"
PASSED = "PASSED"
