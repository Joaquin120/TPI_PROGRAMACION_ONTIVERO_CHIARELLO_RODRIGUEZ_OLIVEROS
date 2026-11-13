from pydantic import BaseModel


class HealthStatusResponse(BaseModel):
    """Schema for server liveness status."""

    status: str
    version: str = "0.1.0"
    environment: str


class ReadinessResponse(BaseModel):
    """Schema for server and database readiness status."""

    status: str
    database: str


HealthResponse = HealthStatusResponse

