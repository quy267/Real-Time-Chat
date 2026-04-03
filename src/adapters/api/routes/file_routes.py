"""File upload API routes — multipart file upload returning a URL."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from src.adapters.api.middleware.jwt_auth_middleware import get_current_user_id
from src.adapters.api.schemas.file_schemas import FileUploadResponse
from src.domain.exceptions import ValidationError

router = APIRouter(prefix="/api/files", tags=["files"])

_MAX_READ_BYTES = 11 * 1024 * 1024  # read up to 11 MB to detect over-limit files


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
):
    from src.adapters.api.dependencies import get_upload_file_use_case

    content = await file.read(_MAX_READ_BYTES)
    content_type = file.content_type or "application/octet-stream"
    filename = file.filename or "upload"

    uc = get_upload_file_use_case()
    try:
        url = await uc.execute(
            filename=filename,
            content=content,
            content_type=content_type,
            user_id=user_id,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)

    return FileUploadResponse(
        url=url,
        filename=filename,
        content_type=content_type,
        size_bytes=len(content),
    )
