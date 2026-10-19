"""The Facts archive (experiments/facts_archive.py): packed deterministically, unpacked only after every file matches
the manifest, so a changed file is refused before anything is written."""

import pytest

from verifier_gate.experiments import facts_archive as fa


def use(monkeypatch, root):
    monkeypatch.setattr(fa, "ROOT", root)
    monkeypatch.setattr(fa, "FACTS", root / "cache" / "facts")
    monkeypatch.setattr(fa, "MANIFEST", root / "cache" / "facts_manifest.csv")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    (root / "cache" / "facts" / "syn-x").mkdir(parents=True)
    (root / "cache" / "facts" / "syn-x" / "EBM.json").write_text('{"share": 0.25}')
    (root / "cache" / "facts" / "build.log").write_text("logs are not packed")
    (root / "data" / "raw").mkdir(parents=True)
    (root / "data" / "raw" / "taiwan_credit.zip").write_bytes(b"the UCI file")
    use(monkeypatch, root)
    return root


def clone(tmp_path, manifest: bytes):
    root = tmp_path / "clone"
    (root / "cache").mkdir(parents=True)
    (root / "cache" / "facts_manifest.csv").write_bytes(manifest)
    return root


def test_packing_twice_gives_the_same_bytes_and_unpacking_restores_every_file(repo, tmp_path, monkeypatch):
    first, second = fa.pack(tmp_path / "a.tar.gz"), fa.pack(tmp_path / "b.tar.gz")
    assert first.read_bytes() == second.read_bytes()
    assert set(fa.read_manifest()) == {"cache/facts/syn-x/EBM.json", "data/raw/taiwan_credit.zip", fa.ATTRIBUTION}
    target = clone(tmp_path, fa.MANIFEST.read_bytes())
    use(monkeypatch, target)
    assert not fa.check()
    fa.unpack(first)
    assert (target / "cache" / "facts" / "syn-x" / "EBM.json").read_text() == '{"share": 0.25}'
    assert fa.check()


def test_an_archive_that_differs_from_the_manifest_is_refused_before_anything_is_written(repo, tmp_path, monkeypatch):
    fa.pack(tmp_path / "a.tar.gz")
    manifest = fa.MANIFEST.read_bytes()
    (repo / "cache" / "facts" / "syn-x" / "EBM.json").write_text('{"share": 0.35}')
    changed = fa.pack(tmp_path / "b.tar.gz")
    target = clone(tmp_path, manifest)
    use(monkeypatch, target)
    with pytest.raises(SystemExit, match="does not match"):
        fa.unpack(changed)
    assert not (target / "cache" / "facts").exists()
