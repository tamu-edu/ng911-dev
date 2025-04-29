from enum import Enum


class ScenarioMode(str, Enum):
    """
    Enum for Scenario modes.
    """
    PCAP = "pcap"
    CAPTURE = "online"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class EntityMode(str, Enum):
    """
    Enum for Scenario modes.
    """
    REAL = "REAL_DEVICE"
    STUB = "STUB_SERVER"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class FilterMessageType(str, Enum):
    """
    Enum for Scenario modes.
    """
    STIMULUS = "stimulus"
    OUTPUT = "output"
    OTHER = "other"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class TestId(str, Enum):
    """
    WARNING - DEPRECATED
    Enum for Tests ids.
    """
    BCF_001 = "BCF_001"
    BRIDGE_001 = "BRIDGE_001"
    CHE_002 = "CHE_002"
    CHE_003 = "CHE_003"
    ECRF_LVF_001 = "ECRF_LVF_001"
    ECRF_LVF_002 = "ECRF_LVF_002"
    ECRF_LVF_003 = "ECRF_LVF_003"
    ESRP_001 = "ESRP_001"
    ESRP_002 = "ESRP_002"
    ESRP_003 = "ESRP_003"
    LIS_001 = "LIS_001"
    LIS_002 = "LIS_002"
    LOG_001 = "LOG_001"
    LOG_002 = "LOG_002"
    LOG_003 = "LOG_003"
    LOG_004 = "LOG_004"
    LOG_005 = "LOG_005"
    LOG_007 = "LOG_007"
    O_BCF_044 = "O_BCF_044"
    PS_001 = "PS_001"
    PS_002 = "PS_002"
    PS_003 = "PS_003"
    PS_004 = "PS_004"
    PS_005 = "PS_005"
    PS_006 = "PS_006"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class EntityFunction(str, Enum):
    """
    Enum for Entity function.

    TODO
    - check if the list is full
    """
    BCF = "BCF"
    BRIDGE = "BRIDGE"
    CHE = "CHE"
    ESRP = "ESRP"
    LIS = "LIS"
    LOG = "LOG"
    OSP = "OSP"
    PS = "PS"
    ECRF_LVF = "ECRF-LVF"
    ADR = "ADR"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))
