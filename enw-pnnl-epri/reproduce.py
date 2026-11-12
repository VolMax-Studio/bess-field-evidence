"""Independent, read-only reproduction of the five ENW exported/imported energy ratios.

Downloads ENW.feather from the official Zenodo record listed in source_manifest.json
(unless already cached locally with matching checksums), verifies MD5 and SHA-256
hashes, and computes the five descriptive exported-to-imported energy ratios across
measurement boundaries and interval selection rules.

Epistemic scope:
- Transparent post-hoc analysis of a public field dataset (not a pre-registered test).
- Descriptive energy ratios only — NOT verified contractual round-trip efficiency (RTE)
  values and NOT Site Acceptance Test (SAT) pass/fail verdicts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
MANIFEST_PATH = HERE / "source_manifest.json"
DEFAULT_DATA_DIR = HERE / "data"


def compute_hashes(file_path: Path) -> tuple[str, str]:
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            md5.update(chunk)
            sha256.update(chunk)
    return md5.hexdigest(), sha256.hexdigest()


def verify_file(file_path: Path, expected_md5: str, expected_sha256: str) -> None:
    actual_md5, actual_sha256 = compute_hashes(file_path)
    if actual_md5 != expected_md5:
        raise RuntimeError(
            f"MD5 mismatch for {file_path.name}: expected {expected_md5}, got {actual_md5}"
        )
    if actual_sha256 != expected_sha256:
        raise RuntimeError(
            f"SHA-256 mismatch for {file_path.name}: expected {expected_sha256}, got {actual_sha256}"
        )


def download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "VolMax-Studio-bess-field-evidence/1.0"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp, tmp_path.open("wb") as out:
        while True:
            chunk = resp.read(1024 * 256)
            if not chunk:
                break
            out.write(chunk)
    tmp_path.replace(dest)


def ensure_enw_feather(manifest: dict, data_dir: Path, force_download: bool = False) -> Path:
    entry = next(f for f in manifest["files"] if f["filename"] == "ENW.feather")
    target = data_dir / entry["filename"]

    if target.exists() and not force_download:
        try:
            verify_file(target, entry["md5"], entry["sha256"])
            return target
        except RuntimeError:
            pass

    print(f"Downloading {entry['filename']} from {entry['download_url']} ...")
    download_file(entry["download_url"], target)
    verify_file(target, entry["md5"], entry["sha256"])
    return target


def energy_ratio(power_series: pd.Series) -> dict[str, float | int]:
    """Compute exported/imported ratio over uniform 1-minute (1/60 h) samples.

    Positive Power denotes export/discharge; negative Power denotes import/charge.
    Power values in ENW.feather are normalized to C-rate, so integrating over
    HoursElapsed yields normalized energy units rather than kWh/MWh.
    """
    valid = power_series.dropna()
    dt_hours = 1.0 / 60.0
    exported = float(valid[valid > 0].sum() * dt_hours)
    imported = float((-valid[valid < 0]).sum() * dt_hours)
    ratio_pct = 100.0 * exported / imported
    return {
        "intervals": int(len(valid)),
        "exported_norm": exported,
        "imported_norm": imported,
        "ratio_pct": ratio_pct,
    }


def run_reproduction(data_dir: Path, force_download: bool = False, as_json: bool = False) -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    feather_path = ensure_enw_feather(manifest, data_dir=data_dir, force_download=force_download)

    df = pd.read_feather(feather_path)

    # Round HoursElapsed only to align floating-point 1-minute grid across meters cleanly
    df = df.copy()
    df["HoursElapsed_key"] = df["HoursElapsed"].round(8)

    # Verify uniform 60.0 s time step per meter (0 gaps)
    for meter, grp in df.groupby("Meter"):
        times_s = np.sort(grp["HoursElapsed"].to_numpy()) * 3600.0
        diffs = np.diff(times_s)
        if not np.allclose(diffs, 60.0, atol=1e-3):
            raise RuntimeError(f"Non-uniform time grid detected for meter {meter}")

    piv_p = df.pivot(index="HoursElapsed_key", columns="Meter", values="Power")
    piv_qf = df.pivot(index="HoursElapsed_key", columns="Meter", values="QualityFlag")
    piv_use = df.pivot(index="HoursElapsed_key", columns="Meter", values="Use")
    piv_cyc = df.pivot(index="HoursElapsed_key", columns="Meter", values="CycleIndex")

    any_qf = piv_qf.any(axis=1)
    use_mask = piv_use["PGCP"].astype(bool)

    soc_non_null = df["SOC"].dropna()
    soc_start_pct = float(soc_non_null.iloc[0] * 100.0)
    soc_end_pct = float(soc_non_null.iloc[-1] * 100.0)

    total_segments = int(piv_cyc["PGCP"].nunique())
    use_segments = int(piv_cyc.loc[use_mask, "PGCP"].nunique())

    rows = [
        ("Battery DC (PDC) - valid DC intervals only", energy_ratio(piv_p["PDC"])),
        ("Inverter AC (PAC) - full observation period", energy_ratio(piv_p["PAC"])),
        ("Grid connection (PGCP) - full observation period", energy_ratio(piv_p["PGCP"])),
        ("Grid connection (PGCP) - excl. quality-flagged rows", energy_ratio(piv_p.loc[~any_qf, "PGCP"])),
        ("Grid connection (PGCP) - authors' \"Use\" segments", energy_ratio(piv_p.loc[use_mask, "PGCP"])),
    ]

    if as_json:
        payload = {
            "source_doi": manifest["doi"],
            "file_verified": feather_path.name,
            "total_timestamps_per_meter": int(len(piv_p)),
            "soc_start_pct": round(soc_start_pct, 2),
            "soc_end_pct": round(soc_end_pct, 2),
            "total_segments": total_segments,
            "use_segments": use_segments,
            "disclaimer": (
                "Descriptive exported/imported ratios only (post-hoc public-data analysis). "
                "NOT verified contractual RTE values and NOT SAT pass/fail verdicts."
            ),
            "ratios": [
                {
                    "label": label,
                    "intervals_min": res["intervals"],
                    "exported_norm": round(res["exported_norm"], 6),
                    "imported_norm": round(res["imported_norm"], 6),
                    "ratio_pct_1dp": round(res["ratio_pct"], 1),
                    "ratio_pct_exact": round(res["ratio_pct"], 6),
                }
                for label, res in rows
            ],
        }
        print(json.dumps(payload, indent=2))
        return 0

    entry = next(f for f in manifest["files"] if f["filename"] == "ENW.feather")
    print("=" * 78)
    print("PNNL / EPRI ENW - Independent Exported-to-Imported Energy Ratio Reproduction")
    print("=" * 78)
    print(f"Source DOI       : {manifest['doi']} ({manifest['license']})")
    print(f"Verified file    : {feather_path} ")
    print(f"  MD5            : {entry['md5']} [OK]")
    print(f"  SHA-256        : {entry['sha256']} [OK]")
    print(f"Grid resolution  : {len(piv_p):,} timestamps/meter at exact 60.0 s (0 gaps)")
    print(f"System SoC span  : {soc_start_pct:.1f}% start -> {soc_end_pct:.1f}% end")
    print(f"Authors' Use rule: {use_segments} of {total_segments} CycleIndex segments selected")
    print("-" * 78)
    print(f"{'Measurement / Selection Rule':52s} {'Intervals':>10s} {'Ratio':>8s}")
    print("-" * 78)
    for label, res in rows:
        print(f"{label:52s} {res['intervals']:8,d} min {res['ratio_pct']:6.1f}%")
    print("-" * 78)
    print("IMPORTANT EPISTEMIC BOUNDARY:")
    print("  1. These values are DESCRIPTIVE exported-to-imported energy ratios,")
    print("     NOT verified contractual round-trip efficiency (RTE) values and")
    print("     NOT Site Acceptance Test (SAT) pass/fail verdicts.")
    print("  2. System SoC changes from 15.8% to 92.0% over the series, and power")
    print("     values are C-rate normalized (elapsed hours, not physical kWh).")
    print("  3. This is a transparent post-hoc analysis of published data, not a")
    print("     pre-registered commissioning test.")
    print("=" * 78)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download (with hash verification) and reproduce the 5 ENW energy ratios."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Directory to cache downloaded ENW.feather (default: ./data).",
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Re-download ENW.feather from Zenodo even if cached locally.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON summary.",
    )
    args = parser.parse_args()
    return run_reproduction(
        data_dir=args.data_dir,
        force_download=args.force_download,
        as_json=args.json,
    )


if __name__ == "__main__":
    sys.exit(main())
