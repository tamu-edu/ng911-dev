class BaseResult:
    _REQUIRED = ("verdict", "error", "warnings")

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        missing = [f for f in cls._REQUIRED if f not in cls.__annotations__]
        if missing:
            raise TypeError(f"{cls.__name__} must define: {', '.join(missing)}")
