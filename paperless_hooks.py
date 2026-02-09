import logging
from typing import Callable, Dict, List
from backends.base import BackendInterface
from paperless_api import (
    Document,
    PlaceholderTemplates,
    TriggerType,
    Workflow,
    WorkflowTrigger,
    WorkflowAction,
    WebhookConfig,
    PaperlessAPI,
)


logger = logging.getLogger(__name__)


class DocumentAddedEvent:

    def __init__(self, api: PaperlessAPI, payload: PlaceholderTemplates):
        self._payload = payload
        self.api = api

    def get_document_id(self) -> int:
        doc_id = int(self._payload.doc_url.split("/")[-2])
        return doc_id

    def get_document(self) -> Document:
        return self.api.document(self.get_document_id())

    def download_document(self) -> bytes:
        """Download the document content as bytes"""
        return self.api.download_document(self.get_document_id())


class DocumentUpdatedEvent(DocumentAddedEvent):
    pass


class EventHandler:
    
    def __init__(self, func: Callable, event_type: TriggerType, index = 0,filters : dict = None):
        self.func = func
        self.event_type = event_type
        self.index = index
        self.url = None
        self.workflow = None
        self.name = func.__name__
        self.filters = filters or {}

    def __call__(self, event):
        self.func(event)


class PaperlessHooks:

    def __init__(
        self,
        paperless_url: str,
        paperless_api_key: str,
        webhook_base_url: str,
        backend: BackendInterface = None,
        workflow_start_index: int = 200,
    ):

        self.paperless_url = paperless_url.rstrip("/")
        self.paperless_api_key = paperless_api_key
        self.webhook_base_url = webhook_base_url.rstrip("/")

        self.workflow_start_index = workflow_start_index
        self.backend = backend
        self.api = PaperlessAPI(self.paperless_url, self.paperless_api_key)

        self.event_handlers: Dict[TriggerType, List[EventHandler]] = {
            TriggerType.CONSUMPTION_STARTED: [],
            TriggerType.DOCUMENT_ADDED: [],
            TriggerType.DOCUMENT_UPDATED: [],
            TriggerType.SCHEDULED: [],
        }
        self._registered_workflows = []

    def add_event_handler(self, handler : EventHandler):
        self.event_handlers[handler.event_type].append(handler)

    def consumption_started(self, filters: dict):
        """
        Decorator for consumption started events.
        Filters are required for this trigger: filter_filename, filter_path,...
        """
        logger.debug("Registering consumption started handler")
        def decorator(func: Callable):
            self.add_event_handler(EventHandler(func, TriggerType.CONSUMPTION_STARTED, filters=filters))
            return func

        return decorator

    def document_added(self, filters: dict = None):
        """
        Decorator for document added events.
        """
        logger.debug("Registering document added handler")

        def decorator(func: Callable):
            handler = EventHandler(func, TriggerType.DOCUMENT_ADDED, filters=filters)
            self.add_event_handler(handler)
            return func

        return decorator

    def document_updated(self, filters: dict = None):
        """
        Decorator for document updated events.
        """
        logger.debug("Registering document updated handler")
        def decorator(func: Callable):
            handler = EventHandler(func, TriggerType.DOCUMENT_UPDATED, filters=filters)
            self.add_event_handler(handler)
            return func

        return decorator

    def scheduled(self, filters: dict = None):
        """
        Decorator for scheduled events.
        """
        logger.debug("Registering scheduled handler")
        def decorator(func: Callable):
            handler = EventHandler(func, TriggerType.SCHEDULED, filters=filters)
            self.add_event_handler(handler)
            return func

        return decorator

    def init(self):
        """
        Initialize and register workflows in Paperless-NGX.
        """
        logger.info("Initializing Paperless hooks...")
        workflows_to_create = []

        for trigger_type, handlers in self.event_handlers.items():
            if not handlers:
                continue

            for handler in handlers:
                webhook_url = f"{self.webhook_base_url}/{handler.name}"
                trigger = WorkflowTrigger(
                    type=trigger_type,
                )
                for filter_name, filter_value in handler.filters.items():
                    setattr(trigger, filter_name, filter_value)

                webhook_config = WebhookConfig(
                    url=webhook_url,
                    use_params=True,
                    as_json=True,
                    include_document=False,
                    params=PlaceholderTemplates().model_dump(),
                )

                action = WorkflowAction(
                    type=4, webhook=webhook_config  
                )
                wf_name = f"paperless-hooks-{handler.name}"
                workflow = Workflow(
                    name=wf_name,
                    order=self.workflow_start_index,
                    enabled=True,
                    triggers=[trigger],
                    actions=[action],
                )
                handler.workflow = workflow
                handler.url = f"/{handler.name}"
                workflows_to_create.append(workflow)

        if workflows_to_create:
            registered_workflows = self._register_workflows(workflows_to_create)
            self._registered_workflows.extend(registered_workflows)
            logger.info(
                "Registered %s workflows in Paperless", len(workflows_to_create)
            )
        else:
            logger.warning("No handlers registered, no workflows created")

        self._setup_routes()

    def _register_workflows(self, workflows: List[Workflow]) -> List[Workflow]:

        registered_workflows = []
        existing_workflows = [m.name for m in self.api.workflows_iter()]

        for workflow in workflows:
            if workflow.name not in existing_workflows:
                try:
                    created_workflow = self.api.create_workflow(workflow)
                    registered_workflows.append(created_workflow)
                    logger.info(
                        "Created workflow: %s (ID: %s)",
                        workflow.name,
                        created_workflow.id,
                    )
                except Exception as e:
                    logger.error("Failed to create workflow %s: %s", workflow.name, e)

        return registered_workflows

    def _setup_routes(self):
        """Register webhook routes on the HTTP backend for every handler."""
        for handlers in self.event_handlers.values():
            for handler in handlers:
                if not handler.url:
                    continue

                def _json_handler(json_data: dict, handler=handler):
                    tmpl = PlaceholderTemplates(**json_data)
                    event = None
                    if handler.event_type == TriggerType.DOCUMENT_ADDED:
                        event = DocumentAddedEvent(self.api, tmpl)
                    elif handler.event_type == TriggerType.DOCUMENT_UPDATED:
                        event = DocumentUpdatedEvent(self.api, tmpl)
                    elif handler.event_type == TriggerType.CONSUMPTION_STARTED:
                        event = tmpl
                    elif handler.event_type == TriggerType.SCHEDULED:
                        event = tmpl
                    handler(event)

                self.backend.add_json_endpoint(handler.url, _json_handler)

    def cleanup(self):
        """Remove all registered workflows from Paperless"""
        for workflow_id in self._registered_workflows:
            try:
                self.api.delete_workflow(workflow_id)
                logger.info("Deleted workflow ID: %s", workflow_id)
            except Exception as e:
                logger.error("Failed to delete workflow %s: %s", workflow_id, e)

        self._registered_workflows.clear()
