from enums import Enum


class FindServiceBoundariesCoverageScenarioFiles(str, Enum):
    one_fully_and_one_partially = \
        "test_files/HTTP_messages/HTTP_LoST/findService_polygon_covering_fully_one_and_partially_another_boundary"
    two_fully = "test_files/HTTP_messages/HTTP_LoST/findService_polygon_covering_fully_two_boundaries"
    none_recursive_mode = \
        "test_files/HTTP_messages/HTTP_LoST/findService_recursive_mode_polygon_not_covering_boundaries"
    none_iterative_mode = \
        "test_files/HTTP_messages/HTTP_LoST/findService_iterative_mode_polygon_not_covering_boundaries"


BCF_IP = "192.168.64.7"
ESRP_IP = "192.168.64.7"
ECRF_LVF_IP = "192.168.64.6"

ECRF_LVF_SERVICE_BOUNDARIES = [
    {
        "POLICE": {
            "SIP_URI": "sip:laurelpd@example.com"
        }
    },
    {
        "POLICE": {
            "SIP_URI": "sip:marylandcitypd@example.com"
        }
    }
]

ECRF_LVF_2_SERVICE_BOUNDARIES = [
    {
        "POLICE": {
            "SIP_URI": "sip:buffalopd@example.com"
        }
    }
]