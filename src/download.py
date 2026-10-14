"""Download raw data. Usage:

    python -m src.download --stage 1            # question sources (each < 1 GB)
    python -m src.download --stage 2 --yes-large  # corpora (two files > 1 GB need explicit consent)

Every downloaded file's size and sha256 are recorded in data/raw/MANIFEST.json.
"""
from __future__ import annotations

import argparse
import json
import logging
import shutil
import tarfile
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests
from tqdm import tqdm

from src.config import load_config
from src.io_utils import setup_logging, sha256_file, write_json

log = logging.getLogger("download")

LARGE = 1_000_000_000  # bytes; anything above needs --yes-large
MIN_FREE_STAGE2 = 60_000_000_000  # stop before corpus downloads + indexing if less disk is free


@dataclass(frozen=True)
class Source:
    name: str
    stage: int
    filename: str
    size: int                    # expected bytes (from HEAD request, 2026-10-14)
    url: str | None = None
    gdrive_id: str | None = None
    extract: bool = False
    license: str = ""


SOURCES = [
    # --- stage 1: questions ---------------------------------------------------
    Source("ircot_processed", 1, "processed_data.zip", 550_756_969,
           gdrive_id="1t2BjJtsejSIUZI54PKObMFG6_wMMG3bC", extract=True,
           license="per dataset (HotpotQA CC BY-SA 4.0, 2Wiki Apache-2.0, MuSiQue CC BY 4.0)"),
    Source("nq_dev", 1, "biencoder-nq-dev.json.gz", 256_239_282,
           url="https://dl.fbaipublicfiles.com/dpr/data/retriever/biencoder-nq-dev.json.gz",
           license="NQ: CC BY-SA 3.0"),
    Source("trivia_dev", 1, "biencoder-trivia-dev.json.gz", 207_271_749,
           url="https://dl.fbaipublicfiles.com/dpr/data/retriever/biencoder-trivia-dev.json.gz",
           license="TriviaQA: Apache-2.0"),
    Source("popqa", 1, "popqa_test.tsv", 5_205_200,
           url="https://huggingface.co/datasets/akariasai/PopQA/resolve/"
               "098765c79ea10a2cb19c828324e33281b8336ec0/test.tsv",
           license="MIT (github.com/AkariAsai/adaptive-retrieval); no license on HF card"),
    # --- stage 2: large corpora ------------------------------------------------
    Source("dpr_wiki", 2, "psgs_w100.tsv.gz", 4_694_541_059,
           url="https://dl.fbaipublicfiles.com/dpr/wikipedia_split/psgs_w100.tsv.gz",
           license="Wikipedia text: CC BY-SA 3.0"),
    Source("hotpotqa_wiki", 2, "enwiki-20171001-pages-meta-current-withlinks-abstracts.tar.bz2",
           1_553_565_403,
           url="https://nlp.stanford.edu/projects/hotpotqa/"
               "enwiki-20171001-pages-meta-current-withlinks-abstracts.tar.bz2",
           extract=True, license="CC BY-SA 4.0"),
    Source("2wiki_raw", 1, "data_ids.zip", 259_216_602,
           url="https://www.dropbox.com/s/7ep3h8unu2njfxv/data_ids.zip?dl=1", extract=True,
           license="Apache-2.0"),
    Source("musique_raw", 1, "musique_data_v1.0.zip", 272_049_578,
           gdrive_id="1tGdADlNjWFaHLeZZGShh2IRcpO6Lv24h", extract=True, license="CC BY 4.0"),
]


def _http_download(url: str, dest: Path, expected: int, max_attempts: int = 20) -> None:
    """Resumable download: on a dropped connection, continue from the .part file via HTTP Range."""
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, max_attempts + 1):
        have = tmp.stat().st_size if tmp.exists() else 0
        if have == expected:
            break
        headers = {"Range": f"bytes={have}-"} if have else {}
        try:
            with requests.get(url, stream=True, timeout=60, headers=headers) as r:
                r.raise_for_status()
                if have and r.status_code != 206:
                    log.warning("server ignored Range; restarting %s from 0", dest.name)
                    have = 0
                mode = "ab" if have else "wb"
                with open(tmp, mode) as f, tqdm(total=expected, initial=have, unit="B",
                                                unit_scale=True, desc=dest.name) as bar:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
                        bar.update(len(chunk))
        except (requests.ConnectionError, requests.Timeout,
                requests.exceptions.ChunkedEncodingError) as e:
            wait = min(60, 2 ** attempt)
            log.warning("%s: attempt %d failed at %d bytes (%s); retrying in %ds",
                        dest.name, attempt, tmp.stat().st_size if tmp.exists() else 0, e, wait)
            time.sleep(wait)
    else:
        raise RuntimeError(f"{dest.name}: gave up after {max_attempts} attempts")
    tmp.replace(dest)


def _gdrive_download(file_id: str, dest: Path) -> None:
    import gdown

    tmp = dest.with_suffix(dest.suffix + ".part")
    out = gdown.download(id=file_id, output=str(tmp), quiet=False)
    if out is None:
        raise RuntimeError(f"gdown failed for {file_id}; download manually to {dest}")
    tmp.replace(dest)


def _safe_extract(archive: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as z:
            root = out_dir.resolve()
            for m in z.infolist():
                target = (out_dir / m.filename).resolve()
                if not str(target).startswith(str(root)):
                    raise RuntimeError(f"unsafe path in zip: {m.filename}")
                if "__MACOSX" in m.filename or m.filename.endswith(".DS_Store"):
                    continue
                z.extract(m, out_dir)
    else:
        with tarfile.open(archive) as t:
            t.extractall(out_dir, filter="data")


def run(stage: int, yes_large: bool) -> None:
    cfg = load_config()
    raw = cfg.path("raw")
    raw.mkdir(parents=True, exist_ok=True)
    manifest_path = raw / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    todo = [s for s in SOURCES if s.stage == stage]
    print(f"Stage {stage} sources:")
    for s in todo:
        print(f"  {s.name:16s} {s.size / 1e9:6.2f} GB  {s.filename}")
    print(f"  total: {sum(s.size for s in todo) / 1e9:.2f} GB")

    free = shutil.disk_usage(raw).free
    print(f"  free disk: {free / 1e9:.0f} GB")
    if stage == 2 and free < MIN_FREE_STAGE2:
        raise SystemExit(f"only {free / 1e9:.0f} GB free; stage 2 needs >= {MIN_FREE_STAGE2 / 1e9:.0f} GB")

    big = [s for s in todo if s.size > LARGE]
    if big and not yes_large:
        raise SystemExit(f"{[s.name for s in big]} are > 1 GB. Re-run with --yes-large after approval.")

    for s in todo:
        dest_dir = raw / s.name
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / s.filename
        if dest.exists() and dest.stat().st_size == s.size and s.name in manifest:
            log.info("%s already present, skipping", s.name)
            continue
        log.info("downloading %s", s.name)
        if s.gdrive_id:
            _gdrive_download(s.gdrive_id, dest)
        else:
            _http_download(s.url, dest, s.size)
        size = dest.stat().st_size
        if size != s.size:
            log.warning("%s: size %d differs from expected %d", s.name, size, s.size)
        if s.extract:
            log.info("extracting %s", dest.name)
            _safe_extract(dest, dest_dir / "extracted")
        manifest[s.name] = {
            "file": str(dest.relative_to(raw)),
            "source": s.url or f"gdrive:{s.gdrive_id}",
            "bytes": size,
            "sha256": sha256_file(dest),
            "license": s.license,
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
        }
        write_json(manifest_path, manifest)
    print(f"done; manifest at {manifest_path}")


def main() -> None:
    setup_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, choices=[1, 2], required=True)
    ap.add_argument("--yes-large", action="store_true", help="consent to downloads > 1 GB")
    args = ap.parse_args()
    run(args.stage, args.yes_large)


if __name__ == "__main__":
    main()
