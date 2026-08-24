"""Template CRUD endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.v1.dependencies import get_template_repo
from src.domain.entities import NotificationTemplate
from src.domain.schemas import PaginatedResponse, TemplateCreateRequest, TemplateResponse, TemplateUpdateRequest
from src.repositories.template_repository import SQLAlchemyTemplateRepository

router = APIRouter()


@router.post(
    "/templates",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["templates"],
)
def create_template(
    payload: TemplateCreateRequest,
    repo: SQLAlchemyTemplateRepository = Depends(get_template_repo),
) -> TemplateResponse:
    if repo.get_by_name(payload.name):
        raise HTTPException(status_code=409, detail="Template name already exists")
    entity = NotificationTemplate(
        name=payload.name,
        subject=payload.subject,
        body=payload.body,
        variables=payload.variables,
    )
    saved = repo.save(entity)
    return TemplateResponse.model_validate(saved)


@router.get("/templates/{template_id}", response_model=TemplateResponse, tags=["templates"])
def get_template(
    template_id: UUID,
    repo: SQLAlchemyTemplateRepository = Depends(get_template_repo),
) -> TemplateResponse:
    template = repo.get(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return TemplateResponse.model_validate(template)


@router.get("/templates", response_model=PaginatedResponse[TemplateResponse], tags=["templates"])
def list_templates(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: str | None = None,
    repo: SQLAlchemyTemplateRepository = Depends(get_template_repo),
) -> PaginatedResponse[TemplateResponse]:
    items, total = repo.list_all(limit=limit, offset=offset, search=search)
    return PaginatedResponse(
        items=[TemplateResponse.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.put("/templates/{template_id}", response_model=TemplateResponse, tags=["templates"])
def update_template(
    template_id: UUID,
    payload: TemplateUpdateRequest,
    repo: SQLAlchemyTemplateRepository = Depends(get_template_repo),
) -> TemplateResponse:
    template = repo.get(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    if payload.subject is not None:
        template.subject = payload.subject
    if payload.body is not None:
        template.body = payload.body
    if payload.variables is not None:
        template.variables = payload.variables
    saved = repo.update(template)
    return TemplateResponse.model_validate(saved)
