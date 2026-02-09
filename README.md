<img src="./logo.png" alt="Paperless-Hooks Logo" width="200"/>

# Paperless-Hooks

A Python library for creating event-driven integrations with [Paperless-NGX](https://github.com/paperless-ngx/paperless-ngx) webhooks.

Ever wanted to extend Paperless-ngx workflows with custom actions? 

With Paperless-Hooks, you can easily create Python functions that respond to document events.
Extract data via llm, regex, trigger notifications, or integrate with other services—all without modifying Paperless-ngx itself.

## How it works

Paperless-Hooks listens for webhook events from Paperless-ngx. When a document event occurs (like a new document being added), Paperless-ngx sends a POST request to your Paperless-Hooks server. 
Paperless-Hooks then processes the event and executes any registered hooks based on the document's metadata, tags, or other criteria.

### Supported Backends

Paperless-Hooks requires a backend to receive webhook events. These are the supported backends:
- **Flask**
- **FastAPI**
- **Django**


## Quick Start (FastAPI)

```bash
# Using pip
pip install git+https://github.com/al-eax/paperless-hooks.git
pip install fastapi uvicorn 
```

```python
import os
import uvicorn
from fastapi import FastAPI
from http_backend.fastapi import FastApiBackend
from paperless_hooks import PaperlessHooks, DocumentAddedEvent

PAPERLESS_URL = "http://localhost:8000"  # URL of your Paperless-NGX instance
PAPERLESS_API_KEY =  "your-paperless-api-key"  # API key from Paperless-NGX settings
WEBHOOK_BASE_URL = "http://localhost:8080"  # URL of your Paperless-Hooks server (must be accessible by Paperless-NGX)

# 1. Create your FastAPI app and backend
app = FastAPI(title="My Paperless Hooks")
backend = FastApiBackend(app)

# 2. Configure Paperless-Hooks
hooks = PaperlessHooks(
    paperless_url=PAPERLESS_URL,
    paperless_api_key=PAPERLESS_API_KEY,
    webhook_base_url=WEBHOOK_BASE_URL,
    backend=backend,
)

# 3. Register event handlers
@hooks.document_added(filters={"filter_filename": "*.pdf"})
def on_document_added(event: DocumentAddedEvent):
    doc = event.get_document()
    print("New document: %s (ID: %s)" % (doc.title, doc.id))
    doc.title += " (Processed by Paperless-Hooks)"
    event.api.update_document(doc)

# 4. Initialize workflows and start the server
if __name__ == "__main__":
    hooks.init()
    uvicorn.run(app, host="0.0.0.0", port=8080)
```


## License

This project is open source and available under the MIT License.
