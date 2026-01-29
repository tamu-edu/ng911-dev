import copy
from typing import Dict
from logger.logger_service import LoggingMeta
from services.test_services.pre_post_amble_methods.pre_post_amble_methods_loader import load_callable


class PrePostAmbleService(metaclass=LoggingMeta):
    """
    TestOracle service is a class to conduct tests using provided configs
    """
    method_name: str
    required_for: list
    kwargs: Dict[str, any]

    def __init__(self, method_name: str, kwargs: Dict[str, any], required_for: list = None):
        self.method_name = method_name
        self.kwargs = copy.deepcopy(kwargs)
        self.required_for = required_for

    def run_method(self, configs: dict):
        fn = load_callable(self.method_name)
        return fn(**{"configs": configs}, **self.kwargs)
