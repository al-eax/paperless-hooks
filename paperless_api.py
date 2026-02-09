import logging
import json
from datetime import date, datetime
from enum import IntEnum
from typing import Any, Dict, List, Optional, Generator
import requests
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class BasicUser(BaseModel):
    id: int
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class Note(BaseModel):
    id: int
    note: str
    created:str 
    user: BasicUser


class CustomFieldInstance(BaseModel):
    value: Optional[Any] = None
    field: int


class CustomField(BaseModel):
    id: int
    name: str
    data_type: str
    extra_data: Optional[Any] = None
    document_count: int


class TriggerType(IntEnum):
    CONSUMPTION_STARTED = 1  # Before document is consumed
    DOCUMENT_ADDED = 2  # After document is added
    DOCUMENT_UPDATED = 3  # When document is updated
    SCHEDULED = 4  # Scheduled trigger


class MatchingAlgorithm(IntEnum):
    NONE = 0
    CONTAINS = 1
    REGEX = 2
    EXACT = 3
    FUZZY = 4
    ICONTAINS = 5
    AUTO = 6


class ActionType(IntEnum):
    ASSIGNMENT = 1
    REMOVAL = 2
    WEBHOOK = 3
    WEBHOOK_WITH_CONFIG = 4


class AssignCorrespondentFrom(IntEnum):
    DO_NOT_ASSIGN = 1
    USE_MAIL_ADDRESS = 2
    USE_NAME = 3
    USE_SELECTED = 4


class AssignTitleFrom(IntEnum):
    USE_SUBJECT = 1
    USE_FILENAME = 2
    DO_NOT_ASSIGN = 3


class WorkflowTrigger(BaseModel):
    """Paperless workflow trigger"""

    id: Optional[int] = None
    type: TriggerType | int
    sources: List[int] = Field(default_factory=list)
    filter_filename: Optional[str] = None
    filter_path: Optional[str] = None
    filter_mailrule: Optional[int] = None
    matching_algorithm: MatchingAlgorithm | int = MatchingAlgorithm.NONE
    match: Optional[str] = None
    is_insensitive: bool = True
    filter_has_tags: List[int] = Field(default_factory=list)
    filter_has_all_tags: List[int] = Field(default_factory=list)
    filter_has_not_tags: List[int] = Field(default_factory=list)
    filter_custom_field_query: Optional[Any] = None
    filter_has_not_correspondents: List[int] = Field(default_factory=list)
    filter_has_not_document_types: List[int] = Field(default_factory=list)
    filter_has_not_storage_paths: List[int] = Field(default_factory=list)
    filter_has_correspondent: Optional[int] = None
    filter_has_document_type: Optional[int] = None
    filter_has_storage_path: Optional[int] = None


class WebhookConfig(BaseModel):
    id: Optional[int] = None
    url: str
    use_params: bool = False
    as_json: bool = True
    params: Dict[str, Any] = Field(default_factory=dict)
    body: str = ""
    headers: Optional[Dict[str, str]] = None
    include_document: bool = True


class PlaceholderTemplates(BaseModel):

    # General placeholders
    correspondent: str = "{{correspondent}}"
    document_type: str = "{{document_type}}"
    owner_username: str = "{{owner_username}}"
    added: str = "{{added}}"
    added_year: str = "{{added_year}}"
    added_year_short: str = "{{added_year_short}}"
    added_month: str = "{{added_month}}"
    added_month_name: str = "{{added_month_name}}"
    added_month_name_short: str = "{{added_month_name_short}}"
    added_day: str = "{{added_day}}"
    added_time: str = "{{added_time}}"
    original_filename: str = "{{original_filename}}"
    filename: str = "{{filename}}"
    doc_title: str = "{{doc_title}}"

    # Added/updated-only placeholders
    created: str = "{{created}}"
    created_year: str = "{{created_year}}"
    created_year_short: str = "{{created_year_short}}"
    created_month: str = "{{created_month}}"
    created_month_name: str = "{{created_month_name}}"
    created_month_name_short: str = "{{created_month_name_short}}"
    created_day: str = "{{created_day}}"
    created_time: str = "{{created_time}}"
    doc_url: str = "{{doc_url}}"


class WorkflowAction(BaseModel):
    id: Optional[int] = None
    type: ActionType | int
    assign_title: Optional[str] = None
    assign_tags: List[int] = Field(default_factory=list)
    assign_document_type: Optional[int] = None
    assign_correspondent: Optional[int] = None
    assign_storage_path: Optional[int] = None
    assign_owner: Optional[int] = None
    assign_view_users: List[int] = Field(default_factory=list)
    assign_view_groups: List[int] = Field(default_factory=list)
    assign_change_users: List[int] = Field(default_factory=list)
    assign_change_groups: List[int] = Field(default_factory=list)
    assign_custom_fields: List[int] = Field(default_factory=list)
    webhook: Optional[WebhookConfig] = None


class Workflow(BaseModel):
    id: Optional[int] = None
    name: str
    order: int = 0
    enabled: bool = True
    triggers: List[WorkflowTrigger]
    actions: List[WorkflowAction]


class Document(BaseModel):
    id: int
    correspondent: Optional[int] = None
    document_type: Optional[int] = None
    storage_path: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None
    tags: List[int] = Field(default_factory=list)
    created: Optional[str] = None
    modified: str
    added:str 
    deleted_at: Optional[str] = None
    archive_serial_number: Optional[int] = None
    original_file_name: Optional[str] = None
    archived_file_name: Optional[str] = None
    owner: Optional[int] = None
    permissions: Dict[str, Any] = Field(default_factory=dict)
    user_can_change: Optional[bool] = None
    is_shared_by_requester: Optional[bool] = None
    notes: List[Note] = Field(default_factory=list)
    custom_fields: List[CustomFieldInstance] = Field(default_factory=list)
    page_count: Optional[int] = None
    mime_type: Optional[str] = None


class Correspondent(BaseModel):
    id: Optional[int] = None
    slug: Optional[str] = None
    name: str
    match: str = ""
    matching_algorithm: MatchingAlgorithm | int = MatchingAlgorithm.NONE
    is_insensitive: bool = True
    document_count: Optional[int] = None
    last_correspondence: Optional[datetime] = None
    owner: Optional[int] = None
    permissions: Dict[str, Any] = Field(default_factory=dict)
    set_permissions: Optional[Dict[str, Any]] = None
    user_can_change: Optional[bool] = None


class DocumentType(BaseModel):
    id: Optional[int] = None
    slug: Optional[str] = None
    name: str
    match: str = ""
    matching_algorithm: MatchingAlgorithm | int = MatchingAlgorithm.NONE
    is_insensitive: bool = True
    document_count: Optional[int] = None
    owner: Optional[int] = None
    permissions: Dict[str, Any] = Field(default_factory=dict)
    set_permissions: Optional[Dict[str, Any]] = None
    user_can_change: Optional[bool] = None


class Tag(BaseModel):
    id: Optional[int] = None
    slug: Optional[str] = None
    name: str
    color: Optional[str] = None
    text_color: Optional[str] = None
    match: str = ""
    matching_algorithm: MatchingAlgorithm | int = MatchingAlgorithm.NONE
    is_insensitive: bool = True
    is_inbox_tag: bool = False
    document_count: Optional[int] = None
    owner: Optional[int] = None
    user_can_change: Optional[bool] = None
    parent: Optional[int] = None
    children: List[int] = Field(default_factory=list)


class PaginatedDocumentList(BaseModel):
    count: int
    next: Optional[str]
    previous: Optional[str]
    results: List[Document]
    all: Optional[List[int]] = None


class PaginatedCustomFieldList(BaseModel):
    count: int
    next: Optional[str]
    previous: Optional[str]
    results: List[CustomField]
    all: Optional[List[int]] = None


class PaperlessAPIError(Exception):
    pass


class PaperlessAPI:
    def __init__(self, base_url: str, api_token: str, timeout: int = 10) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        if not api_token:
            raise PaperlessAPIError("paperless api_token is required")
        self.session.headers.update({"Authorization": f"Token {api_token}"})

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def _get_json(self, path: str, params: dict | None = None) -> dict:
        return self._request("get", path, params=params or {}).json()

    def _get_content(self, path: str) -> bytes:
        return self._request("get", path).content

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Send an HTTP request and raise a PaperlessAPIError on failure.

        Returns the raw requests.Response on success.
        """
        url = self._url(path)
        logger.debug(
            "%s %s kwargs=%s",
            method.upper(),
            url,
            {k: v for k, v in kwargs.items() if k != "json"},
        )
        try:
            resp = self.session.request(method, url, timeout=self.timeout, **kwargs)
            resp.raise_for_status()
        except requests.RequestException as exc:
            # Log response body for debugging
            if hasattr(exc, "response") and exc.response is not None:
                try:
                    error_body = exc.response.text
                    logger.error("API error response body: %s", error_body)
                except:
                    pass
            logger.exception("Paperless API request failed: %s %s", method.upper(), url)
            raise PaperlessAPIError(str(exc)) from exc
        return resp

    def _documents(self, page: int = 1) -> dict:
        """Return a single page dict from /api/documents/ (paginated)."""
        return self._get_json("/api/documents/", params={"page": page})

    def documents_custom_field_query_iter(
        self, custom_field_query: object
    ) -> Generator[Document, None, None]:

        page = 1
        while True:
            params = {
                "page": page,
                "custom_field_query": json.dumps(custom_field_query),
            }
            payload = self._get_json("/api/documents/", params=params)
            for doc in payload.get("results", []):
                yield Document.model_validate(doc)
            if not payload.get("next"):
                break
            page += 1

    def update_document(self, document : Document) -> Document:
        """Update a document by ID with the provided Document model data."""
        updated_doc = self._request(
            "put",
            f"/api/documents/{document.id}/",
            json=document.model_dump(),
        ).json()
        return Document.model_validate(updated_doc)

    def documents_iter(self) -> Generator[Document, None, None]:
        """Yield documents across all pages as `Document` models."""
        page = 1
        while True:
            payload = self._documents(page=page)
            for doc in payload.get("results", []):
                yield Document.model_validate(doc)
            if not payload.get("next"):
                break
            page += 1

    def document(self, doc_id: int) -> Document:
        """Return document metadata from /api/documents/{id}/ as a Document."""
        return Document.model_validate(self._get_json(f"/api/documents/{doc_id}/"))

    def document_notes(self, doc_id: int) -> List[Note]:
        """Return list of notes for a document as `Note` models."""
        return [
            Note.model_validate(n)
            for n in self._get_json(f"/api/documents/{doc_id}/notes/")
        ]

    def download_document(self, doc_id: int) -> bytes:
        """Return bytes for a document from /api/documents/{id}/download"""
        res = self._get_content(f"/api/documents/{doc_id}/download/")
        return res

    def add_note_to_document(self, doc_id: int, note: str) -> Note:
        """Add a note to a document (POST /api/documents/{id}/notes/).

        Returns the created note dict.
        """
        notes = self._request(
            "post", f"/api/documents/{doc_id}/notes/", json={"note": note}
        ).json()
        if not notes:
            return None
        return Note.model_validate(notes[-1])

    def delete_note(self, doc_id: int, note_id: int) -> bool:
        """Delete a note from a document"""
        self._request(
            "delete", f"/api/documents/{doc_id}/notes/", params={"id": note_id}
        )
        return True

    def custom_fields(self, page: int = 1) -> dict:
        """Return a single page of custom fields from /api/custom-fields/"""
        return self._get_json("/api/custom_fields/", params={"page": page})

    def custom_fields_iter(self) -> Generator[dict, None, None]:
        """Yield all custom field objects across pages."""
        page = 1
        while True:
            payload = self.custom_fields(page=page)
            for cf in payload.get(
                "results", payload if isinstance(payload, list) else []
            ):
                yield CustomField.model_validate(cf)
            if not payload.get("next"):
                break
            page += 1

    def get_custom_field_by_name(self, name: str) -> Optional[CustomField]:
        """Find a custom field by name (returns first match) or None."""
        for cf in self.custom_fields_iter():
            if cf.name == name:
                return cf
        return None

    def create_custom_field(self, name: str, data_type: str = "url") -> CustomField:
        """Create a new global custom field (/api/custom_fields/)."""
        return CustomField.model_validate(
            self._request(
                "post",
                "/api/custom_fields/",
                json={"name": name, "data_type": data_type},
            ).json()
        )

    def delete_custom_field(self, custom_field_id: int) -> bool:
        """Delete a custom field by id (/api/custom_fields/{id}/).

        Returns True on success (200/204). Raises PaperlessAPIError on failure.
        """
        self._request("delete", f"/api/custom_fields/{custom_field_id}/")
        return True

    def add_custom_field_to_document(
        self, doc: Document, custom_field_id: int, value: str
    ) -> Document:
        """Add or update a custom field instance on a document."""

        doc_cf_instances = doc.custom_fields or []

        updated = False
        for inst in doc_cf_instances:
            if inst.field == custom_field_id:
                inst.value = value
                updated = True
                break

        if not updated:
            doc_cf_instances.append(
                CustomFieldInstance(field=custom_field_id, value=value)
            )

        updated_doc = self._request(
            "patch",
            f"/api/documents/{doc.id}/",
            json={"custom_fields": [cf.model_dump() for cf in doc_cf_instances]},
        ).json()
        return Document.model_validate(updated_doc)

    def delete_custom_field_from_document(
        self, doc: Document, custom_field_id: int
    ) -> Document:
        """Delete a custom field instance from a document."""

        doc_cf_instances = doc.custom_fields

        filtered = [
            inst.model_dump()
            for inst in doc_cf_instances
            if not (inst.field == custom_field_id)
        ]

        if len(filtered) == len(doc_cf_instances):
            # No change needed
            return doc

        updated_doc = self._request(
            "patch",
            f"/api/documents/{doc.id}/",
            json={"custom_fields": filtered},
        ).json()
        return Document.model_validate(updated_doc)

    # --- Correspondent methods ---
    def correspondents(self, page: int = 1) -> dict:
        """Return a single page of correspondents from /api/correspondents/."""
        return self._get_json("/api/correspondents/", params={"page": page})

    def correspondents_iter(self) -> Generator[Correspondent, None, None]:
        """Yield all correspondents across pages."""
        page = 1
        while True:
            payload = self.correspondents(page=page)
            for c in payload.get("results", []):
                yield Correspondent.model_validate(c)
            if not payload.get("next"):
                break
            page += 1

    def get_correspondent(self, correspondent_id: int) -> Correspondent:
        """Get a correspondent by ID."""
        return Correspondent.model_validate(
            self._get_json(f"/api/correspondents/{correspondent_id}/")
        )

    def create_correspondent(self, correspondent: Correspondent) -> Correspondent:
        """Create a new correspondent."""
        return Correspondent.model_validate(
            self._request(
                "post",
                "/api/correspondents/",
                json=correspondent.model_dump(exclude_none=True),
            ).json()
        )

    def update_correspondent(
        self, correspondent_id: int, correspondent: Correspondent
    ) -> Correspondent:
        """Full update (PUT) of a correspondent."""
        return Correspondent.model_validate(
            self._request(
                "put",
                f"/api/correspondents/{correspondent_id}/",
                json=correspondent.model_dump(exclude_none=True),
            ).json()
        )

    def delete_correspondent(self, correspondent_id: int) -> bool:
        """Delete a correspondent by ID."""
        self._request("delete", f"/api/correspondents/{correspondent_id}/")
        return True

    # --- Document type methods ---
    def document_types(self, page: int = 1) -> dict:
        """Return a single page of document types from /api/document_types/."""
        return self._get_json("/api/document_types/", params={"page": page})

    def document_types_iter(self) -> Generator[DocumentType, None, None]:
        """Yield all document types across pages."""
        page = 1
        while True:
            payload = self.document_types(page=page)
            for dt in payload.get("results", []):
                yield DocumentType.model_validate(dt)
            if not payload.get("next"):
                break
            page += 1

    def get_document_type(self, document_type_id: int) -> DocumentType:
        """Get a document type by ID."""
        return DocumentType.model_validate(
            self._get_json(f"/api/document_types/{document_type_id}/")
        )

    def get_document_type_by_name(self, name: str) -> Optional[DocumentType]:
        """Find a document type by name (first match) or None."""
        for dt in self.document_types_iter():
            if dt.name == name:
                return dt
        return None

    def create_document_type(self, document_type: DocumentType) -> DocumentType:
        """Create a new document type."""
        return DocumentType.model_validate(
            self._request(
                "post",
                "/api/document_types/",
                json=document_type.model_dump(exclude_none=True),
            ).json()
        )

    def update_document_type(
        self, document_type_id: int, document_type: DocumentType
    ) -> DocumentType:
        """Full update (PUT) of a document type."""
        return DocumentType.model_validate(
            self._request(
                "put",
                f"/api/document_types/{document_type_id}/",
                json=document_type.model_dump(exclude_none=True),
            ).json()
        )

    def delete_document_type(self, document_type_id: int) -> bool:
        """Delete a document type by ID."""
        self._request("delete", f"/api/document_types/{document_type_id}/")
        return True

    # --- Tag methods ---
    def tags(self, page: int = 1) -> dict:
        """Return a single page of tags from /api/tags/."""
        return self._get_json("/api/tags/", params={"page": page})

    def tags_iter(self) -> Generator[Tag, None, None]:
        """Yield all tags across pages."""
        page = 1
        while True:
            payload = self.tags(page=page)
            for t in payload.get("results", []):
                yield Tag.model_validate(t)
            if not payload.get("next"):
                break
            page += 1

    def get_tag(self, tag_id: int) -> Tag:
        """Get a tag by ID."""
        return Tag.model_validate(self._get_json(f"/api/tags/{tag_id}/"))

    def get_tag_by_name(self, name: str) -> Optional[Tag]:
        """Find a tag by name (first match) or None."""
        for t in self.tags_iter():
            if t.name == name:
                return t
        return None

    def create_tag(self, tag: Tag) -> Tag:
        """Create a new tag."""
        return Tag.model_validate(
            self._request(
                "post",
                "/api/tags/",
                json=tag.model_dump(exclude_none=True),
            ).json()
        )

    def update_tag(self, tag_id: int, tag: Tag) -> Tag:
        """Full update (PUT) of a tag."""
        return Tag.model_validate(
            self._request(
                "put",
                f"/api/tags/{tag_id}/",
                json=tag.model_dump(exclude_none=True),
            ).json()
        )

    def delete_tag(self, tag_id: int) -> bool:
        """Delete a tag by ID."""
        self._request("delete", f"/api/tags/{tag_id}/")
        return True

    # --- Workflow management methods ---
    def workflows(self, page: int = 1) -> dict:
        """Return a single page of workflows from /api/workflows/"""
        return self._get_json("/api/workflows/", params={"page": page})

    def workflows_iter(self) -> Generator[Workflow, None, None]:
        """Yield all workflows across pages."""
        page = 1
        while True:
            payload = self.workflows(page=page)
            for wf in payload.get("results", []):
                yield Workflow.model_validate(wf)
            if not payload.get("next"):
                break
            page += 1

    def get_workflow(self, workflow_id: int) -> Workflow:
        """Get a specific workflow by ID."""
        return Workflow.model_validate(self._get_json(f"/api/workflows/{workflow_id}/"))

    def create_workflow(self, workflow: Workflow) -> Workflow:
        """Create a new workflow."""
        workflow_dict = workflow.model_dump(exclude_none=True, exclude={"id"})

        logger.debug("Creating workflow with data: %s", workflow_dict)
        response = self._request(
            "post",
            "/api/workflows/",
            json=workflow_dict,
        ).json()
        return Workflow.model_validate(response)

    def update_workflow(self, workflow_id: int, workflow: Workflow) -> Workflow:
        """Update an existing workflow."""
        response = self._request(
            "put",
            f"/api/workflows/{workflow_id}/",
            json=workflow.model_dump(exclude_none=True),
        ).json()
        return Workflow.model_validate(response)

    def delete_workflow(self, workflow_id: int) -> bool:
        """Delete a workflow by ID."""
        self._request("delete", f"/api/workflows/{workflow_id}/")
        return True
