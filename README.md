# bess-field-evidence

Minimal, reproducible field-data reconstructions for grid-scale Battery Energy Storage System (BESS) telemetry and commissioning verification.

Each case study in this repository follows strict epistemic rules:
- **No dataset redistribution when an official archive exists:** source files are fetched directly from their canonical DOI/archive URL and verified against cryptographic hashes (`MD5` and `SHA-256`).
- **Transparent post-hoc analysis:** every computation is presented as a reproducible check of published data, never as a pre-registered test.
- **No invented contractual verdicts:** descriptive statistics are never presented as contractual round-trip efficiency (RTE) compliance or Factory/Site Acceptance Test (FAT/SAT) pass/fail judgments unless contractual test rules are explicitly known and satisfied.

## Cases

### 1. [`enw-pnnl-epri/`](./enw-pnnl-epri/) — One BESS dataset, five plausible energy ratios
- **Source:** PNNL / EPRI Grid-Scale BESS Operational Datasets (`ENW`, DOI [`10.5281/zenodo.22947521`](https://doi.org/10.5281/zenodo.22947521), `CC-BY-4.0`)
- **Result:** Changing only the metering boundary (`PDC`, `PAC`, `PGCP`) or interval-selection rule (`full`, `QualityFlag` exclusion, authors' `Use` segments) yields five distinct exported-to-imported ratios from **`74.5%`** to **`88.9%`** on the exact same 1-minute dataset.
- **Quick run:**
  ```bash
  pip install -r requirements.txt
  python enw-pnnl-epri/reproduce.py
  ```

## License
- Code in this repository is licensed under the [MIT License](./LICENSE).
- Third-party datasets retain their original licenses and attribution (e.g., `CC-BY-4.0` for the PNNL/EPRI Zenodo release).
