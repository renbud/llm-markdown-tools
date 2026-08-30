from io import BytesIO

from PIL import Image

from llm_markdown_tools import MarkdownClientConfig, MarkdownExtractor


def test_config_dataclass():
    cfg = MarkdownClientConfig(
        base_url="http://localhost:1234/v1",
        api_key="demo-key",
        model="demo-model",
    )

    assert cfg.base_url == "http://localhost:1234/v1"
    assert cfg.api_key == "demo-key"
    assert cfg.model == "demo-model"
    assert cfg.client_kwargs["base_url"] == "http://localhost:1234/v1"


def test_html_noise_cleaning():
    extractor = MarkdownExtractor(MarkdownClientConfig(base_url="http://localhost:1234/v1"))

    html = "<div><script>alert('x')</script><h1>Hello</h1><p>World</p></div>"
    cleaned = extractor._clean_html_noise(html)

    assert "script" not in cleaned.lower()
    assert "Hello" in cleaned
    assert "World" in cleaned


def test_invalid_html_raises_value_error():
    extractor = MarkdownExtractor(MarkdownClientConfig(base_url="http://localhost:1234/v1"))

    try:
        extractor.from_html("")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_tensor_error_detection():
    extractor = MarkdownExtractor(MarkdownClientConfig(base_url="http://localhost:1234/v1"))

    assert extractor._is_tensor_allocation_error("bad allocation") is True
    assert extractor._is_tensor_allocation_error("predict request failed") is True
    assert extractor._is_tensor_allocation_error("timeout while waiting for model") is False


def test_downscale_image_for_llm_returns_jpeg_bytes():
    extractor = MarkdownExtractor(MarkdownClientConfig(base_url="http://localhost:1234/v1"))

    buffer = BytesIO()
    Image.new("RGB", (2000, 2000), "white").save(buffer, format="PNG")
    resized_bytes, mime_type = extractor._downscale_image_for_llm(buffer.getvalue())

    assert mime_type == "image/jpeg"
    assert len(resized_bytes) > 0


def test_from_html_with_fallback_uses_simple_conversion(monkeypatch):
    extractor = MarkdownExtractor(MarkdownClientConfig(base_url="http://localhost:1234/v1"))

    def fake_from_html(_):
        raise RuntimeError("LLM failed")

    monkeypatch.setattr(extractor, "from_html", fake_from_html)
    result = extractor.from_html_with_fallback("<h1>Test</h1>", "unit test fallback")

    assert "Test" in result


def test_from_image_retries_after_tensor_error(monkeypatch):
    extractor = MarkdownExtractor(MarkdownClientConfig(base_url="http://localhost:1234/v1"))
    calls = []

    def fake_call_llm(messages):
        calls.append(messages)
        if len(calls) == 1:
            raise ValueError("bad allocation")
        return "Recovered markdown"

    monkeypatch.setattr(extractor, "_call_llm", fake_call_llm)
    monkeypatch.setattr(
        extractor,
        "_downscale_image_for_llm",
        lambda image_bytes, max_dimension=512: (b"fake-jpeg-data", "image/jpeg"),
    )

    result = extractor.from_image("Zm9v", mime_type="image/png")

    assert result == "Recovered markdown"
    assert len(calls) == 2


def test_from_document_path_raises_when_missing(tmp_path):
    extractor = MarkdownExtractor(MarkdownClientConfig(base_url="http://localhost:1234/v1"))
    missing = tmp_path / "missing.pdf"

    try:
        extractor.from_document_path(missing)
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass
