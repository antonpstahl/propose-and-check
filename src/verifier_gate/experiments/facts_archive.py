"""The Facts archive: what a fresh clone needs to reproduce every number of the paper offline.

The fitted models' Facts and bootstrap draws (cache/facts/, about 480 MB, not tracked: refitting them from the fixed seeds
takes about six hours) and the TaiwanCredit file the plasmode tier is built on (data/raw/taiwan_credit.zip as
published by UCI, dataset 350, CC BY 4.0, DOI 10.24432/C55S3H), packed into one archive. It is attached to the
repository's release `facts-v1`. With it, `experiments/reproduce.py` re-derives every number in about seven minutes,
without network access; without it, the same command refits every model and downloads the data.

cache/facts_manifest.csv, committed, lists every file of the archive with its size and SHA-256. `--unpack` checks
every file against it before anything is written, and `--check` compares the Facts on disk with it, e.g. Facts
refitted on another machine (the JSON files hold every number the experiments read; the .npz files are zip
containers, so their bytes can differ where their arrays do not). The archive itself is deterministic: packing the
same files again gives the same bytes.

Run:
  uv run python -m verifier_gate.experiments.facts_archive --pack              # dist/facts-v1.tar.gz and the manifest
  uv run python -m verifier_gate.experiments.facts_archive --unpack <archive>  # check every file, then extract
  uv run python -m verifier_gate.experiments.facts_archive --check             # the files on disk against the manifest
"""

import argparse
import csv
import gzip
import hashlib
import io
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).parents[3]
FACTS = ROOT / "cache" / "facts"
MANIFEST = ROOT / "cache" / "facts_manifest.csv"
VERSION = "facts-v1"
DEFAULT = ROOT / "dist" / f"{VERSION}.tar.gz"
RAW_DATA = ("data/raw/taiwan_credit.zip",)
ATTRIBUTION = "data/raw/taiwan_credit_ATTRIBUTION.txt"
ATTRIBUTION_TEXT = """\
taiwan_credit.zip is the "Default of Credit Card Clients" dataset as published by the UCI Machine Learning
Repository (dataset 350): Yeh, I-Cheng (2009), https://doi.org/10.24432/C55S3H. It is licensed under the Creative
Commons Attribution 4.0 International license (CC BY 4.0, https://creativecommons.org/licenses/by/4.0/) and is
included here unchanged. The plasmode tier keeps its feature rows and replaces its label with a planted one.
"""
CHUNK = 1 << 20


def _sha256(stream) -> str:
    digest = hashlib.sha256()
    for block in iter(lambda: stream.read(CHUNK), b""):
        digest.update(block)
    return digest.hexdigest()


def _file_sha256(path: Path) -> str:
    with path.open("rb") as f:
        return _sha256(f)


def members() -> list[str]:
    """The archive's files, relative to the repository, in a fixed order (the logs of the fitting runs are left out)."""
    facts = sorted(p.relative_to(ROOT).as_posix() for p in FACTS.glob("*/*") if p.is_file())
    return facts + list(RAW_DATA)


def read_manifest() -> dict[str, dict]:
    with MANIFEST.open() as f:
        return {row["path"]: row for row in csv.DictReader(f)}


def pack(target: Path) -> Path:
    names = members()
    missing = [n for n in names if not (ROOT / n).exists()]
    if missing or not names:
        raise SystemExit(f"nothing to pack or files missing: {missing[:5]}")
    (ROOT / ATTRIBUTION).write_text(ATTRIBUTION_TEXT)  # on disk too, so that the files on disk equal the archive's
    rows = []
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz, \
            tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tar:  # fmt: skip
        for name in names + [ATTRIBUTION]:
            data = ATTRIBUTION_TEXT.encode() if name == ATTRIBUTION else None
            size = len(data) if data is not None else (ROOT / name).stat().st_size
            info = tarfile.TarInfo(name)
            info.size, info.mtime, info.mode = size, 0, 0o644
            with (io.BytesIO(data) if data is not None else (ROOT / name).open("rb")) as source:
                digest = _sha256(source)
                source.seek(0)
                tar.addfile(info, source)
            rows.append({"path": name, "bytes": size, "sha256": digest})
    with MANIFEST.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"{target}: {len(rows)} files, {sum(r['bytes'] for r in rows) / 1e6:.0f} MB unpacked, "
          f"{target.stat().st_size / 1e6:.0f} MB packed, SHA-256 {_file_sha256(target)}")  # fmt: skip
    print(f"manifest: {MANIFEST.relative_to(ROOT)}")
    return target


def _safe(name: str) -> bool:
    path = Path(name)
    return not path.is_absolute() and ".." not in path.parts and name.startswith(("cache/facts/", "data/raw/"))


def _extract_xls() -> None:
    """The plasmode tier reads the .xls inside the UCI zip (data/plasmode.py, `fetch`): extract it, no download."""
    from verifier_gate.data import plasmode

    archive, xls = ROOT / RAW_DATA[0], ROOT / "data" / "raw" / plasmode.XLS.name
    if not archive.exists() or _file_sha256(archive) != plasmode.ZIP_SHA256:
        return
    if not xls.exists() or _file_sha256(xls) != plasmode.XLS_SHA256:
        with zipfile.ZipFile(archive) as z:
            xls.write_bytes(z.read(plasmode.XLS_MEMBER))
    if _file_sha256(xls) != plasmode.XLS_SHA256:
        raise SystemExit("the TaiwanCredit file extracted from the archive does not match its recorded hash")


def unpack(archive: Path, force: bool = False) -> None:
    expected = read_manifest()
    with tarfile.open(archive, "r:gz") as tar:
        found = {}
        for m in tar:  # first pass: every file checked before anything is written
            if not (m.isfile() and _safe(m.name)) or m.name not in expected:
                raise SystemExit(f"unexpected member in the archive: {m.name}")
            found[m.name] = _sha256(tar.extractfile(m))
    missing = sorted(set(expected) - set(found))
    wrong = sorted(n for n, digest in found.items() if digest != expected[n]["sha256"])
    if missing or wrong:
        raise SystemExit(f"the archive does not match {MANIFEST.relative_to(ROOT)}: missing {missing[:5]}, differing {wrong[:5]}")
    clash = [n for n in found if (ROOT / n).exists() and _file_sha256(ROOT / n) != found[n]]
    if clash and not force:
        raise SystemExit(f"{len(clash)} file(s) on disk differ from the archive, e.g. {clash[0]}; rerun with --force to replace them")
    written = 0
    with tarfile.open(archive, "r:gz") as tar:
        for m in tar:
            target = ROOT / m.name
            if target.exists() and m.name not in clash:
                continue  # already the archived file
            target.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(m) as source, target.open("wb") as out:
                for block in iter(lambda: source.read(CHUNK), b""):
                    out.write(block)
            written += 1
    _extract_xls()
    print(f"{len(found)} files checked against the manifest, {written} written; "
          "now `uv run python -m verifier_gate.experiments.reproduce` runs offline")  # fmt: skip


def check() -> bool:
    expected = read_manifest()
    missing, differ = [], []
    for name, row in expected.items():
        path = ROOT / name
        if not path.exists():
            missing.append(name)
        elif _file_sha256(path) != row["sha256"]:
            differ.append(name)
    print(f"{len(expected) - len(missing) - len(differ)} of {len(expected)} files equal the archive's; "
          f"{len(missing)} missing; {len(differ)} differ")  # fmt: skip
    for name in differ:
        print(f"  differs: {name}" + ("" if name.endswith(".json") else " (a container; compare the arrays)"))
    return not missing and not differ


def main() -> None:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--pack", nargs="?", const=DEFAULT, type=Path, metavar="TARGET", help=f"write the archive (default {DEFAULT.relative_to(ROOT)})")
    action.add_argument("--unpack", type=Path, metavar="ARCHIVE", help="check every file against the manifest, then extract")
    action.add_argument("--check", action="store_true", help="compare the files on disk with the manifest")
    parser.add_argument("--force", action="store_true", help="with --unpack: replace files on disk that differ")
    args = parser.parse_args()
    if args.pack:
        pack(args.pack)
    elif args.unpack:
        unpack(args.unpack, args.force)
    elif not check():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
