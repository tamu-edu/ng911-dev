from tests import (
    BCF_001,
    O_BCF_044,
    CHE_002,
    CHE_003,
    ESRP_001,
    ESRP_003,
    LOG_001,
    LOG_002,
    LOG_003,
    LOG_004,
    LOG_005,
    LOG_007,
    PS_001,
    PS_002,
    PS_003,
    PS_004,
    PS_005,
    PS_006
)


TEST_MAPPING = {
    "BCF_001": BCF_001.run,
    "O_BCF_044": O_BCF_044.run,
    "BRIDGE_001": CHE_002.run,
    "CHE_002": CHE_002.run,
    "CHE_003": CHE_003.run,
    "ESRP_001": ESRP_001.run,
    "ESRP_003": ESRP_003.run,
    "LOG_001": LOG_001.run,
    "LOG_002": LOG_002.run,
    "LOG_003": LOG_003.run,
    "LOG_004": LOG_004.run,
    "LOG_005": LOG_005.run,
    "LOG_007": LOG_007.run,
    "PS_001": PS_001.run,
    "PS_002": PS_002.run,
    "PS_003": PS_003.run,
    "PS_004": PS_004.run,
    "PS_005": PS_005.run,
    "PS_006": PS_006.run,

    # Add more tests as needed

}
