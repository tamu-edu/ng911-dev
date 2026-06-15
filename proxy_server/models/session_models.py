from pydantic import BaseModel, Field
from proxy_server.state.enums import State


class SessionEndpoint(BaseModel):
    ip: str
    port: int
    protocol: str


class TLSCertConfig(BaseModel):
    cert: str
    key: str
    ca: str | None = None


class TLSConfig(BaseModel):
    enabled: bool = False
    mode: str | None = None
    server_side: TLSCertConfig | None = None
    client_side: TLSCertConfig | None = None


class TransportConfig(BaseModel):
    protocol: str
    tls: TLSConfig | None = None


class ConduitConfig(BaseModel):
    name: str
    from_: SessionEndpoint = Field(alias="from")
    to: SessionEndpoint
    proxy: SessionEndpoint
    transport: TransportConfig

    model_config = {
        "populate_by_name": True,
    }


class NetworkConfig(BaseModel):
    host: str
    user: str
    ssh_key: str


class StartSessionConfig(BaseModel):
    network: NetworkConfig
    conduits: list[ConduitConfig]


class StartSessionRequest(BaseModel):
    session_id: str
    config: StartSessionConfig


class SessionRequest(BaseModel):
    session_id: str


class SessionStatusResponse(BaseModel):
    status: State
    artifacts: dict[str, str] | None = None
