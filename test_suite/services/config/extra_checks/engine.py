import inspect
from typing import Any
from .registry import get_check


class ExtraChecksEngine:

    @staticmethod
    def check(
        check_name: str,
        field_name: str,
        field_value: Any,
        data_dict: dict | None = None,
        parent_data_dict: dict | None = None,
    ) -> tuple[bool, str]:
        _ec = get_check(check_name)

        kwargs = {}

        signature = inspect.signature(_ec)
        parameters = signature.parameters

        for name, param in parameters.items():

            if name == "field_name":
                kwargs[name] = field_name

            elif name == "field_value":
                kwargs[name] = field_value

            elif name == "data_dict":
                kwargs[name] = data_dict

            elif name == "parent_data_dict":
                kwargs[name] = parent_data_dict

            elif param.default is inspect.Parameter.empty:
                raise RuntimeError(
                    f"Check '{_ec.__name__}' requires unknown parameter '{name}'"
                )

        return _ec(**kwargs)
