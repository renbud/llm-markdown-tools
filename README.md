# llm-markdown-tools

Small, reusable Python utilities for turning HTML, documents, and images into clean Markdown using an OpenAI-compatible API.

## Why this package exists

This package provides conversion to markdown from image, html and text.
The user must provide an OpenAI compatible server.

- HTML to Markdown conversion
- image OCR / extraction into Markdown
- text and document conversion into Markdown
- retry and fallback handling for model failures


## Installation

```bash
pip install llm-markdown-tools
```

## Quick start

```python
from llm_markdown_tools import MarkdownClientConfig, MarkdownExtractor

cfg = MarkdownClientConfig(
    base_url="http://localhost:1234/v1",
    api_key="not-needed",
    model="qwen/qwen3.5-9b",
)

extractor = MarkdownExtractor(cfg)
markdown = extractor.from_html("<h1>Hello</h1><p>World</p>")
print(markdown)
```

## Configuration

Prefer passing a `MarkdownClientConfig` object directly instead of loading local project files.

```python
cfg = MarkdownClientConfig(
    base_url="https://api.openai.com/v1",
    api_key="YOUR_API_KEY",
    model="gpt-4o-mini",
    timeout=60.0,
)
```

## Example YAML

```yaml
llm:
  endpoint: http://localhost:1234/v1
  api_key: not-needed
  model: qwen/qwen3.5-9b
  timeout: 60
```

This package does not use a config file; use a template file or environment variables in your own application.

## Public API

```python
from llm_markdown_tools import MarkdownClientConfig, MarkdownExtractor
```

The extractor exposes methods such as:

- `from_html(html_text: str) -> str`
- `from_text(text: str) -> str`
- `from_image(image_base64: str, mime_type: str | None = None) -> str`
- `from_image_path(path: str | Path) -> str`
- `from_document_path(path: str | Path) -> str`

### `from_html(...)`

```python
from llm_markdown_tools import MarkdownClientConfig, MarkdownExtractor

cfg = MarkdownClientConfig(
    base_url="http://localhost:1234/v1",
    api_key="not-needed",
    model="qwen/qwen3.5-9b",
)

extractor = MarkdownExtractor(cfg)
html = "<html><body><h1>Quarterly Report</h1><p>Revenue grew 18%.</p></body></html>"
markdown = extractor.from_html(html)
print(markdown)
```

### `from_text(...)`

```python
from llm_markdown_tools import MarkdownClientConfig, MarkdownExtractor

cfg = MarkdownClientConfig(
    base_url="http://localhost:1234/v1",
    api_key="not-needed",
    model="qwen/qwen3.5-9b",
)

extractor = MarkdownExtractor(cfg)
text = "Invoice 1234\nCustomer: Acme Corp\nTotal: $1,250.00"
markdown = extractor.from_text(text)
print(markdown)
```

### `from_image(...)`

```python
import base64
from llm_markdown_tools import MarkdownClientConfig, MarkdownExtractor

cfg = MarkdownClientConfig(
    base_url="http://localhost:1234/v1",
    api_key="not-needed",
    model="qwen/qwen3.5-9b",
)

extractor = MarkdownExtractor(cfg)
with open("receipt.png", "rb") as fh:
    image_bytes = fh.read()

image_b64 = base64.b64encode(image_bytes).decode("utf-8")
markdown = extractor.from_image(image_b64, mime_type="image/png")
print(markdown)
```

### `from_image_path(...)`

```python
from pathlib import Path
from llm_markdown_tools import MarkdownClientConfig, MarkdownExtractor

cfg = MarkdownClientConfig(
    base_url="http://localhost:1234/v1",
    api_key="not-needed",
    model="qwen/qwen3.5-9b",
)

extractor = MarkdownExtractor(cfg)
markdown = extractor.from_image_path(Path("images/scan-01.png"))
print(markdown)
```

### `from_document_path(...)`

```python
from pathlib import Path
from llm_markdown_tools import MarkdownClientConfig, MarkdownExtractor

cfg = MarkdownClientConfig(
    base_url="http://localhost:1234/v1",
    api_key="not-needed",
    model="qwen/qwen3.5-9b",
)

extractor = MarkdownExtractor(cfg)
markdown = extractor.from_document_path(Path("sample.pdf"))
print(markdown)
```

### `from_html_simple(...)`

```python
from llm_markdown_tools import MarkdownClientConfig, MarkdownExtractor

cfg = MarkdownClientConfig(
    base_url="http://localhost:1234/v1",
    api_key="not-needed",
    model="qwen/qwen3.5-9b",
)

extractor = MarkdownExtractor(cfg)
html = "<h2>Notes</h2><p>Simple conversion fallback.</p>"
markdown = extractor.from_html_simple(html)
print(markdown)
```

### `from_html_with_fallback(...)`

```python
from llm_markdown_tools import MarkdownClientConfig, MarkdownExtractor

cfg = MarkdownClientConfig(
    base_url="http://localhost:1234/v1",
    api_key="not-needed",
    model="qwen/qwen3.5-9b",
)

extractor = MarkdownExtractor(cfg)
html = "<div><h1>Fallback Example</h1><p>Try the LLM first, then fall back.</p></div>"
markdown = extractor.from_html_with_fallback(html, "email body conversion")
print(markdown)
```

## License

MIT
