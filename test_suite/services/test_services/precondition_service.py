import copy
from typing import Dict
from logger.logger_service import LoggingMeta
from services.test_services.preconditions_methods.precondition_methods_loader import load_callable


class PreconditionService(metaclass=LoggingMeta):
    """
    TestOracle service is a class to conduct tests using provided configs
    """
    method_name: str
    kwargs: Dict[str, any]

    def __init__(self, method_name: str, kwargs: Dict[str, any]):
        self.method_name = method_name
        self.kwargs = copy.deepcopy(kwargs)

    def run_method(self, configs: dict):
        fn = load_callable(self.method_name)
        return fn(**{"configs": configs}, **self.kwargs)