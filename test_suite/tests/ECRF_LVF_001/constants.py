from enums import Enum


class ListServicesScenarioFiles(str, Enum):
    urn_service_sos = "test_files/HTTP_messages/HTTP_LoST/listServices_urn-service-sos"
    urn_emergency_service_sos = "test_files/HTTP_messages/HTTP_LoST/listServices_urn-emergency-service-sos"


class ListServicesByLocationScenarioFiles(str, Enum):
    urn_service_sos = "test_files/HTTP_messages/HTTP_LoST/listServicesByLocation_urn-service-sos"
    urn_emergency_service_sos = "test_files/HTTP_messages/HTTP_LoST/listServicesByLocation_urn-emergency-service-sos"


BCF_IP = "192.168.64.7"
ESRP_IP = "192.168.64.7"
ECRF_LVF_IP = "192.168.64.6"
