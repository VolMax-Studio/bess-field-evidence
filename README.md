# bess-field-evidence

Minimal, reproducible field-data reconstructions for grid-scale Battery Energy Storage System (BESS) telemetry and commissioning verification.

Each case study in this repository follows strict epistemic rules:
- **No dataset redistribution when an official archive exists:** source files are fetched directly from their canonical DOI/archive URL and verified against cryptographic hashes (`MD5` and `SHA-256`).
- **Transparent post-hoc analysis:** every computation is presented as a reproducible check of published data, never as a pre-registered test.
- **No invented contractual verdicts:** descriptive statistics are never presented as contractual round-trip efficiency (RTE) compliance or Factory/Site Acceptance Test (FAT/SAT) pass/fail judgments unless contractual test rules are explicitly known and satisfied.

## Cases

### 1. [`enw-pnnl-epri/`](./enw-pnnl-epri/) — One BESS dataset, five plausible energy ratios
- **Source:** PNNL / EPRI Grid-Scale BESS Operational Datasets (`ENW`, DOI [`10.5281/zenodo.22947521`](https://doi.org/10.5281/zenodo.22947521), `CC-BY-4.0`)
- **Result:** Across the 1-minute `ENW` dataset, five standard boundary/selection choices span **`74.5%`** to **`88.9%`**. Isolating the common `70,105`-minute valid-DC window separates the pure metering boundary effect (**`75.607% -> 88.865%`**, **`+13.259 pp`** unrounded from `PGCP` to `PDC`) from extending `PGCP` to the full `85,858`-minute series (**`75.607% -> 74.486%`**, **`-1.120 pp`** unrounded from `15,753` disconnected-DC standby minutes).
- **Quick run:**
  ```bash
  pip install -r requirements.txt
  python enw-pnnl-epri/reproduce.py
  ```

## License
- Code in this repository is licensed under the [MIT License](./LICENSE).
- Third-party datasets retain their original licenses and attribution (e.g., `CC-BY-4.0` for the PNNL/EPRI Zenodo release).
