from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", include_in_schema=False)
def health_check():
    return {"status": "ok"}
