"""cache.py on its own, in a temp folder."""
import dataclasses

import pytest

from api.core import cache, config


@pytest.fixture(autouse=True)
def tmp_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "settings", dataclasses.replace(config.settings, cache_dir=str(tmp_path)))
    return tmp_path


def test_image_key_is_sha256_of_the_exact_bytes():
    assert cache.image_key(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert cache.image_key(b"abc") != cache.image_key(b"abd")


def test_put_then_get(tmp_cache):
    key = cache.image_key(b"photo")
    assert cache.get(key) is None
    cache.put(key, {"id": "chk_0007", "verdict": "USUAL"})
    assert cache.get(key) == {"id": "chk_0007", "verdict": "USUAL"}
    assert [p.name for p in tmp_cache.iterdir()] == [f"{key}.json"]      # no .part left behind


def test_broken_file_is_a_miss(tmp_cache):
    key = cache.image_key(b"photo")
    (tmp_cache / f"{key}.json").write_text("{not json", encoding="utf-8")
    assert cache.get(key) is None


def test_bad_key_is_refused():
    assert cache.get("../../.env") is None
    with pytest.raises(ValueError):
        cache.put("../../.env", {})


def test_all_results(tmp_cache):
    cache.put(cache.image_key(b"a"), {"id": "chk_0001"})
    cache.put(cache.image_key(b"b"), {"id": "chk_0009"})
    (tmp_cache / "junk.json").write_text("{", encoding="utf-8")
    assert sorted(r["id"] for r in cache.all_results()) == ["chk_0001", "chk_0009"]
