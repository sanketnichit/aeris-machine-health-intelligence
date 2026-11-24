import io
import zipfile

import pytest

from scripts.download_cmapss import extract_fd001, NAMES


def archive(entries):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        for name, value in entries:
            z.writestr(name, value)
    return stream.getvalue()


def test_named_members_only():
    entries = [(f"CMAPSSData/{name}", name.encode()) for name in NAMES]
    entries.append(("../../unrelated.txt", b"ignored"))
    assert extract_fd001(archive(entries)) == {name: name.encode() for name in NAMES}


def test_missing_member():
    with pytest.raises(ValueError):
        extract_fd001(archive([(NAMES[0], b"data")]))


def test_duplicate_basename():
    entries = [(name, b"data") for name in NAMES]
    entries.append((f"other/{NAMES[0]}", b"duplicate"))
    with pytest.raises(ValueError):
        extract_fd001(archive(entries))
