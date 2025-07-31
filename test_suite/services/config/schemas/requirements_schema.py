from .requirements_schema_PS import REQUIREMENTS_SCHEMA as PS
from .requirements_schema_BCF import REQUIREMENTS_SCHEMA as BCF
from .requirements_schema_CHE import REQUIREMENTS_SCHEMA as CHE
from .requirements_schema_LIS import REQUIREMENTS_SCHEMA as LIS
from .requirements_schema_BRIDGE import REQUIREMENTS_SCHEMA as BRIDGE
from .requirements_schema_ECRF import REQUIREMENTS_SCHEMA as ECRF
from .requirements_schema_ESRP import REQUIREMENTS_SCHEMA as ESRP
from .requirements_schema_LOG import REQUIREMENTS_SCHEMA as LOG
from .requirements_schema_LOG_OTHER import REQUIREMENTS_SCHEMA as LOG_OTHER
from .requirements_schema_ECRF_LVF import REQUIREMENTS_SCHEMA as ECRF_LVF
from .requirements_schema_LVF import REQUIREMENTS_SCHEMA as LVF


REQUIREMENTS_SCHEMA = {
    **PS, **BCF, **CHE, **LIS, **BRIDGE, **ECRF, **LOG, **ECRF_LVF, **ESRP, **LOG_OTHER, **LVF
}

