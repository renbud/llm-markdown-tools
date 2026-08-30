import os

import pytest

from llm_markdown_tools import MarkdownClientConfig, MarkdownExtractor


pytestmark = pytest.mark.integration


BASE_URL = os.getenv("LLM_MARKDOWN_TOOLS_BASE_URL", "http://localhost:1234/v1")
API_KEY = os.getenv("LLM_MARKDOWN_TOOLS_API_KEY", "not-needed")
MODEL = os.getenv("LLM_MARKDOWN_TOOLS_MODEL", "qwen/qwen3.5-9b")
RUN_INTEGRATION = os.getenv("LLM_MARKDOWN_TOOLS_RUN_INTEGRATION", "0").lower() in {"1", "true", "yes", "on"}


@pytest.mark.skipif(not RUN_INTEGRATION, reason="Set LLM_MARKDOWN_TOOLS_RUN_INTEGRATION=1 to enable integration tests")
def test_live_html_conversion():
    cfg = MarkdownClientConfig(
        base_url=BASE_URL,
        api_key=API_KEY,
        model=MODEL,
        timeout=90.0,
    )
    extractor = MarkdownExtractor(cfg)

    html = "<html><body><h1>Integration Test</h1><p>This should convert to markdown.</p></body></html>"
    result = extractor.from_html(html)

    assert isinstance(result, str)
    assert "Integration Test" in result or "This should convert to markdown" in result


@pytest.mark.skipif(not RUN_INTEGRATION, reason="Set LLM_MARKDOWN_TOOLS_RUN_INTEGRATION=1 to enable integration tests")
def test_live_text_conversion():
    cfg = MarkdownClientConfig(
        base_url=BASE_URL,
        api_key=API_KEY,
        model=MODEL,
        timeout=90.0,
    )
    extractor = MarkdownExtractor(cfg)

    text = "Customer: Acme Corp\nInvoice: 1234\nTotal: $250.00"
    result = extractor.from_text(text)

    assert isinstance(result, str)
    assert len(result) > 0
