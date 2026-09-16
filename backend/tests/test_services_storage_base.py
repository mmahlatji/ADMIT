import pytest

from app.services.storage import base
from app.services.storage.exceptions import (
    FileEmptyException,
    FileNotAllowedException,
    FileTooLargeException,
)


class FakeFile:
    def __init__(self, content):
        self._content = content
        self.filename = "upload.bin"
        self.content_type = "application/octet-stream"

    async def read(self):
        return self._content


def test_detect_extension_pdf():
    assert base.detect_extension(b"%PDF-1.4\n...") == ".pdf"


def test_detect_extension_xlsx():
    assert base.detect_extension(b"PK\x03\x04.....[Content_Types].xml.....") == ".xlsx"


def test_detect_extension_plain_zip_is_not_xlsx():
    # a ZIP without an OOXML content-types entry must not masquerade as xlsx
    assert base.detect_extension(b"PK\x03\x04\x00\x00\x00\x00\x00\x00\xff\xfe") is None


def test_detect_extension_csv_text():
    assert base.detect_extension(b"a,b,c\n1,2,3\n") == ".csv"


def test_detect_extension_binary_unknown():
    assert base.detect_extension(b"\x89PNG\r\n\x1a\n\x00") is None


@pytest.mark.asyncio
async def test_read_and_validate_empty_raises():
    with pytest.raises(FileEmptyException):
        await base.read_and_validate(FakeFile(b""), frozenset({".pdf"}))


@pytest.mark.asyncio
async def test_read_and_validate_too_large_raises():
    content = b"x" * (base.MAX_FILE_SIZE + 1)
    with pytest.raises(FileTooLargeException):
        await base.read_and_validate(FakeFile(content), frozenset({".pdf"}))


@pytest.mark.asyncio
async def test_read_and_validate_disallowed_type_raises():
    # text is detected as .csv, which a pdf-only allowlist rejects
    with pytest.raises(FileNotAllowedException):
        await base.read_and_validate(FakeFile(b"hello world"), frozenset({".pdf"}))


@pytest.mark.asyncio
async def test_read_and_validate_returns_content_and_extension():
    content = b"%PDF-1.4\n..."
    result = await base.read_and_validate(FakeFile(content), frozenset({".pdf"}))
    assert result == (content, ".pdf")
