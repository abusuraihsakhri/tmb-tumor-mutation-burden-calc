# Tumor Mutational Burden (TMB) Calculator

> **TMB Calculation for Immunotherapy Eligibility**
> Reference: Marabelle A et al. Lancet Oncol. 2020;21(1):71-82 (KEYNOTE-158)

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg)

## Overview

Real implementation of Tumor Mutational Burden (TMB) calculation for immunotherapy eligibility:

- **TMB calculation**: Total mutations / coding region size (mut/Mb)
- **FDA-approved threshold**: TMB ≥10 mut/Mb for pembrolizumab (June 2020)
- **Panel size adjustment**: Correction factor for small gene panels
- **Immunotherapy response assessment**: Evidence-based likelihood scoring
- **Panel support**: FoundationOne CDx, MSK-IMPACT, Tempus xT, Guardant360, TSO-500

## Quick Start

```bash
# Calculate TMB
python tmb_calc.py calc --mutations 380 --region-mb 38.0

# Panel-adjusted TMB
python tmb_calc.py panel --mutations 15 --panel foundationone_cdx

# Immunotherapy assessment
python tmb_calc.py immune --tmb 12.0 --cancer-type NSCLC

# Get panel info
python tmb_calc.py panel-info --name msk_impact

# Batch processing
python tmb_calc.py batch -i cases.csv -o results.csv
```

## TMB Thresholds

| TMB (mut/Mb) | Category | Clinical Significance |
|---------------|----------|----------------------|
| <5 | Low | Lower likelihood of checkpoint inhibitor response |
| 5-10 | Intermediate | Variable response; consider other biomarkers |
| ≥10 | **High** | **FDA-approved threshold for pembrolizumab** |
| ≥16 | Very High | Strong predictor of checkpoint inhibitor response |

## FDA Approval (June 2020)

Pembrolizumab approved for:
- **TMB-High solid tumors** (≥10 mut/Mb)
- **Any cancer type** (tumor-agnostic)
- Measured by FDA-approved companion diagnostic (FoundationOne CDx)

## Common Gene Panels

| Panel | Coding Region | Notes |
|-------|---------------|-------|
| FoundationOne CDx | 1.14 Mb | FDA-approved companion Dx for TMB |
| MSK-IMPACT | 1.22 Mb | Validated for TMB assessment |
| Tempus xT | 1.50 Mb | Comprehensive genomic profiling |
| TSO-500 | 1.70 Mb | Illumina comprehensive panel |
| Guardant360 | 0.73 Mb | Liquid biopsy (ctDNA) |
| Whole Exome | 38.0 Mb | Gold standard reference |

## Python API

```python
from tmb_calc import calculate_tmb, immunotherapy_response_assessment

# Calculate TMB
result = calculate_tmb(total_mutations=380, coding_region_size_mb=38.0)
print(result["tmb"])  # 10.0
print(result["fda_eligible"])  # True

# Immunotherapy assessment
result = immunotherapy_response_assessment(tmb=12.0, cancer_type="NSCLC")
print(result["therapy_recommendation"])  # Pembrolizumab approved...
```

## Running Tests

```bash
python -m pytest test_tmb_calc.py -v
```

## License

MIT License. See [LICENSE](LICENSE) for details.
