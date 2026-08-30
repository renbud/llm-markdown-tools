"""
Use openai to extract markdown from a file or image.
The configured model should be a general purpose image capable model.
"""

from __future__ import annotations

import base64
import logging
import mimetypes
import re
from io import BytesIO
from pathlib import Path

from openai import OpenAI
from PIL import Image
import html2text

from .config import MarkdownClientConfig

logger = logging.getLogger(__name__)


class MarkdownExtractor:
    """OpenAI-compatible helper for HTML and document-to-Markdown workflows."""

    def __init__(self, config: MarkdownClientConfig):
        """Initialize the extractor with explicit runtime configuration."""
        self.config = config
        self.client = OpenAI(
            base_url=self.config.base_url,
            api_key=self.config.api_key,
        )

    def _call_llm(self, messages: list[dict]):
        """
        Common helper to call LLM with messages and extract markdown response.

        Args:
            messages: List of message dictionaries for the chat completion

        Returns:
            Markdown-formatted string

        Raises:
            ValueError: If the API call fails or response is invalid
        """
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            timeout=self.config.timeout,
        )

        content = response.choices[0].message.content

        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict) and "text" in block:
                    parts.append(block["text"])
            content = "\n".join(parts)

        if not isinstance(content, str):
            content = str(content)

        return content

    def _is_tensor_allocation_error(self, message: str) -> bool:
        """
        Check if the error is related to image tensor allocation issues.

        Args:
            error_message: The error message from the API

        Returns:
            True if this appears to be a tensor allocation error
        """
        lower = message.lower()
        return any(
            keyword in lower
            for keyword in [
                "bad allocation",
                "tensor",
                "predict request failed",
                "channel error",
                "engine protocol predict",
            ]
        )

    def _downscale_image_for_llm(self, image_bytes: bytes, max_dimension: int = 512):
        """
        Downscale an image to reduce tensor size for LLM processing.

        This handles cases where the original image is too large for the hardware,
        causing errors like "bad allocation" or "predict request failed".

        Args:
            image_bytes: Raw image bytes
            max_dimension: Maximum dimension in pixels (default 512)

        Returns:
            Tuple of (downscaled image bytes, mime type)
        """
        try:
            img = Image.open(BytesIO(image_bytes))
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
            output = BytesIO()
            img.save(output, format="JPEG", quality=70, optimize=True)
            return output.getvalue(), "image/jpeg"
        except Exception as exc:
            logger.warning("Could not downscale image: %s. Returning original.", exc)
            return image_bytes, "image/png"

    def from_html(self, html_text: str) -> str:
        """
        Converts HTML text to clean markdown using LLM.

        Args:
            html_text: Raw HTML content to convert

        Returns:
            Clean, well-formatted markdown string

        Raises:
            ValueError: If the API call fails or response is invalid
        """
        if not html_text or not isinstance(html_text, str):
            raise ValueError("HTML text must be a non-empty string")

        cleaned_html = self._clean_html_noise(html_text)
        prompt = self.config.default_prompt + "\n\n" + cleaned_html
        messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]

        try:
            return self._call_llm(messages)
        except Exception as exc:
            raise ValueError(f"Failed to convert HTML to markdown: {exc}") from exc

    def from_html_simple(self, html_text: str) -> str:
        """
        Converts HTML text to clean markdown using html2text.

        Args:
            html_text: Raw HTML content to convert

        Returns:
            Plain text string. Most formatting and tables lost.
            Simple markdown used in some cases
        """
        try:
            return html2text.html2text(html_text)
        except Exception:
            return html_text

    def from_html_with_fallback(self, html_text: str, context_msg: str) -> str:
        """
        Convert HTML to markdown using LLM, with a fallback to simple conversion if LLM fails.

        Args:
            html_text: Raw HTML content to convert
            context_msg: Contextual message for logging in case of failure

        Returns:
            Plain text string. Most formatting and tables lost.
        """
        try:
            return self.from_html(html_text) if html_text.strip() else ""
        except Exception:
            logger.warning("LLM conversion failed for HTML content, using fallback. %s", context_msg)
            return self.from_html_simple(html_text)

    def from_text(self, text: str) -> str:
        """
        Extracts markdown from text using LLM (useful for OCR results or raw text extraction).

        Args:
            text: Plain text input

        Returns:
            Markdown-formatted string

        Raises:
            ValueError: If the API call fails or response is invalid
        """
        if not text:
            raise ValueError("Text must be a non-empty string")
        messages = [
            {"role": "user", "content": [
                {"type": "text", "text": self.config.default_prompt},
                {"type": "text", "text": text},
            ]}
        ]
        return self._call_llm(messages)

    def from_image(self, image_base64: str, mime_type: str | None = None) -> str:
        """
        Extracts markdown from a base64-encoded image using LLM.

        Args:
            image_base64: Base64-encoded image data (without data URI prefix)
            mime_type: MIME type for the image data

        Returns:
            Extracted markdown content as string

        Raises:
            ValueError: If the API call fails or response is invalid
        """
        if not mime_type:
            mime_type = "image/png"

        messages = [
            {"role": "user", "content": [
                {"type": "text", "text": self.config.default_prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_base64}"}},
            ]}
        ]

        try:
            return self._call_llm(messages)
        except ValueError as exc:
            error_msg = str(exc).lower()
            if self._is_tensor_allocation_error(error_msg):
                try:
                    img_bytes = base64.b64decode(image_base64)
                    downsampled_img_bytes, new_mime_type = self._downscale_image_for_llm(img_bytes)
                    messages[0]["content"][1]["image_url"]["url"] = (
                        f"data:{new_mime_type};base64,{base64.b64encode(downsampled_img_bytes).decode()}"
                    )
                    return self._call_llm(messages)
                except Exception as retry_error:
                    raise ValueError(
                        f"Failed to extract content from image after downsampling. "
                        f"Original error: {exc}. Downscaling error: {retry_error}"
                    ) from retry_error
            raise

    def from_image_path(self, image_path: str | Path) -> str:
        """
        Extracts markdown from an image file using LLM.

        Args:
            image_path: Path to the image file

        Returns:
            Extracted markdown content as string

        Raises:
            ValueError: If the API call fails or response is invalid
            FileNotFoundError: If the image file doesn't exist
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        with path.open("rb") as fh:
            image_bytes = fh.read()

        b64 = base64.b64encode(image_bytes).decode()
        mime_type = mimetypes.guess_type(str(path))[0] or "image/png"

        messages = [
            {"role": "user", "content": [
                {"type": "text", "text": self.config.default_prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
            ]}
        ]

        try:
            return self._call_llm(messages)
        except ValueError as exc:
            if self._is_tensor_allocation_error(str(exc).lower()):
                downsampled_img_bytes, new_mime_type = self._downscale_image_for_llm(image_bytes)
                messages[0]["content"][1]["image_url"]["url"] = (
                    f"data:{new_mime_type};base64,{base64.b64encode(downsampled_img_bytes).decode()}"
                )
                return self._call_llm(messages)
            raise

    def from_document_path(self, document_path: str | Path) -> str:
        """
        Extracts markdown from a document file using LLM.

        Args:
            document_path: Path to the document file

        Returns:
            Markdown-formatted string

        Raises:
            FileNotFoundError: If the document file doesn't exist
            ValueError: If the API call fails or response is invalid
        """
        path = Path(document_path)
        if not path.exists():
            raise FileNotFoundError(f"Document file not found: {document_path}")

        mime_type, _ = mimetypes.guess_type(str(path)) or ("application/octet-stream", "")
        with path.open("rb") as fh:
            data = fh.read()

        b64 = base64.b64encode(data).decode("utf-8")
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": self.config.default_prompt},
                {"type": "document", "document": {"data": b64, "mime": mime_type}},
            ],
        }]

        return self._call_llm(messages)

    @staticmethod
    def _clean_html_noise(html_text: str) -> str:
        """
        Pre-processes HTML to remove common noise before LLM processing.

        Args:
            html_text: Raw HTML content

        Returns:
            Cleaned HTML with common noise removed
        """
        html = re.sub(r"<script\b[^>]*>.*?</script>", "", html_text, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<style\b[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<iframe\b[^>]*>.*?</iframe>", "", html, flags=re.DOTALL | re.IGNORECASE)

        nav_patterns = [
            r'<a\b[^>]*href=["\'][^"\']*/(sign|login|logout|account|profile)["\'][^>]*>',
            r'<a\b[^>]*href=["\'][^"\']*facebook["\'][^>]*>',
            r'<a\b[^>]*href=["\'][^"\']*twitter["\'][^>]*>',
        ]
        for pattern in nav_patterns:
            html = re.sub(pattern, "", html, flags=re.IGNORECASE)

        ad_patterns = [
            r'class=["\']?(?:ad|advertisement|promo|promo-banner)["\']?',
            r'id=["\']?(?:ad|advertisement|promo|sidebar)["\']?',
        ]
        for pattern in ad_patterns:
            html = re.sub(pattern, "", html, flags=re.IGNORECASE)

        html = re.sub(r"<[^>]+>\s*</[^>]+>", "", html)
        return html.strip()
