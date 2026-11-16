import copy
import re
from typing import Dict, Any, List, Optional

from logger.logger_service import LoggingMeta
from services.aux_services.aux_services import check_value_for_file_var_mode
from services.test_services.pre_post_amble_methods.pre_post_amble_methods_loader import (
    load_callable,
)
from services import prep_services


def _resolve_config_part(part: str, configs: dict):
    match_root = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)", part)
    if not match_root:
        raise ValueError("Invalid expression, no valid root variable found")
    config_part = configs.get(match_root.group(1))
    for key in re.findall(r"\['([^']+)'\]", part):
        if isinstance(config_part, dict):
            config_part = config_part.get(key)
        else:
            raise ValueError(f"Cannot go deeper at key '{key}', current is not a dict")
    return config_part


def _resolve_value(value, context: dict):
    if isinstance(value, dict):
        return {k: _resolve_value(v, context) for k, v in value.items()}
    i_value, _, v_type = check_value_for_file_var_mode(value, True)
    if v_type == "var":
        return context.get(i_value)
    if v_type == "list":
        return [_resolve_value(v, context) for v in i_value]
    return i_value


def _run_prep_steps(prep_steps: List[Dict[str, Any]], configs: dict) -> dict:
    context: Dict[str, Any] = {}
    for step in prep_steps or []:
        method_name = step.get("method_name", "")
        kwargs = {
            k: _resolve_value(v, context)
            for k, v in copy.deepcopy(step.get("kwargs", {})).items()
        }

        if method_name == "extract_from_config" and isinstance(
            kwargs.get("config_part"), str
        ):
            kwargs["config_part"] = _resolve_config_part(kwargs["config_part"], configs)

        if method_name in ("get_interface_address", "get_interface_port_number"):
            kwargs["lab_config"] = copy.deepcopy(configs.get("lab_config"))

        method = getattr(prep_services, method_name)
        result = method(**kwargs)

        save_key, _ = check_value_for_file_var_mode(step.get("save_result_as"))
        if save_key:
            context[save_key] = result
    return context


class PrePostAmbleService(metaclass=LoggingMeta):
    """
    TestOracle service is a class to conduct tests using provided configs
    """

    method_name: str
    required_for: List[Any] | None = None
    kwargs: Dict[str, Any]
    prep_steps: List[Dict[str, Any]]

    def __init__(
        self,
        method_name: str,
        kwargs: Dict[str, Any],
        required_for: List[Any] | None = None,
        prep_steps: Optional[List[Dict[str, Any]]] = None,
    ):
        self.method_name = method_name
        self.kwargs = copy.deepcopy(kwargs)
        self.required_for = required_for
        self.prep_steps = copy.deepcopy(prep_steps) if prep_steps else []

    def run_method(self, configs: dict):
        fn = load_callable(self.method_name)
        context = _run_prep_steps(self.prep_steps, configs)
        resolved_kwargs = {
            k: _resolve_value(v, context) for k, v in self.kwargs.items()
        }
        return fn(**{"configs": configs}, **resolved_kwargs)
