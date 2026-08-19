import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.transaction_import import (
    ImportConfirmRequest,
    ImportConfirmResult,
    ImportPreviewRead,
)
from app.services import import_service

router = APIRouter(prefix="/imports/transactions", tags=["imports"])


@router.post("", response_model=ImportPreviewRead, status_code=status.HTTP_201_CREATED)
async def create_import(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ImportPreviewRead:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Only .csv files are supported",
        )

    file_bytes = await file.read()
    try:
        record = import_service.create_preview(db, current_user.id, file.filename, file_bytes)
    except import_service.ImportFileError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    except import_service.ImportTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return ImportPreviewRead.model_validate(record)


@router.get("/{import_id}", response_model=ImportPreviewRead)
def get_import(
    import_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ImportPreviewRead:
    try:
        record = import_service.get_import_for_user(db, current_user.id, import_id)
    except import_service.ImportNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Import not found"
        ) from exc
    return ImportPreviewRead.model_validate(record)


@router.post("/{import_id}/confirm", response_model=ImportConfirmResult)
def confirm_import(
    import_id: uuid.UUID,
    data: ImportConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ImportConfirmResult:
    try:
        return import_service.confirm_import(
            db, current_user.id, import_id, data.include_duplicates
        )
    except import_service.ImportNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Import not found"
        ) from exc
    except import_service.ImportNotPendingError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This import has already been confirmed or cancelled",
        ) from exc


@router.delete("/{import_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_import(
    import_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        import_service.cancel_import(db, current_user.id, import_id)
    except import_service.ImportNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Import not found"
        ) from exc
    except import_service.ImportNotPendingError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This import has already been confirmed or cancelled",
        ) from exc
