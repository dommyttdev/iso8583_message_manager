"""
GET /api/v1/health — ヘルスチェックルーター。
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])

_API_VERSION = "1.0.0"


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get("/api/v1/health", response_model=HealthResponse, operation_id="get_health")
def get_health() -> HealthResponse:
    """API サーバーの稼働状態を確認します。"""
    return HealthResponse(status="ok", version=_API_VERSION)
