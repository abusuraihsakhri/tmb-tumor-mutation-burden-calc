#!/usr/bin/env python3
"""Tests for TMB Calculator - 20 real test cases."""
import pytest
from tmb_calc import (
    calculate_tmb, adjust_for_panel_size, immunotherapy_response_assessment,
    get_panel_info, process_batch
)


# ---------------------------------------------------------------------------
# TMB Calculation Tests
# ---------------------------------------------------------------------------

class TestTMBCalculation:

    def test_tmb_low(self):
        result = calculate_tmb(50, 38.0)
        assert result["tmb"] == 1.32
        assert result["tmb_category"] == "Low"
        assert result["fda_eligible"] is False

    def test_tmb_intermediate(self):
        result = calculate_tmb(250, 38.0)
        assert result["tmb"] == 6.58
        assert result["tmb_category"] == "Intermediate"
        assert result["fda_eligible"] is False

    def test_tmb_high_fda_threshold(self):
        result = calculate_tmb(380, 38.0)
        assert result["tmb"] == 10.0
        assert result["tmb_category"] == "High"
        assert result["fda_eligible"] is True

    def test_tmb_very_high(self):
        result = calculate_tmb(760, 38.0)
        assert result["tmb"] == 20.0
        assert result["tmb_category"] == "Very High"
        assert result["fda_eligible"] is True

    def test_tmb_zero_mutations(self):
        result = calculate_tmb(0, 38.0)
        assert result["tmb"] == 0.0
        assert result["tmb_category"] == "Low"

    def test_tmb_with_synonymous(self):
        result = calculate_tmb(100, 38.0, include_synonymous=True, synonymous_count=20)
        assert result["total_mutations"] == 100
        assert result["non_synonymous_mutations"] == 80
        assert result["synonymous_mutations"] == 20

    def test_tmb_small_panel(self):
        result = calculate_tmb(15, 1.14)
        assert result["tmb"] == 13.16
        assert result["tmb_category"] == "High"

    def test_tmb_invalid_negative_mutations(self):
        with pytest.raises(ValueError, match="must be >= 0"):
            calculate_tmb(-1, 38.0)

    def test_tmb_invalid_zero_region(self):
        with pytest.raises(ValueError, match="must be > 0"):
            calculate_tmb(100, 0.0)

    def test_tmb_synonymous_exceeds_total(self):
        with pytest.raises(ValueError, match="cannot exceed total"):
            calculate_tmb(100, 38.0, include_synonymous=True, synonymous_count=150)


# ---------------------------------------------------------------------------
# Panel Adjustment Tests
# ---------------------------------------------------------------------------

class TestPanelAdjustment:

    def test_adjustment_small_panel(self):
        result = adjust_for_panel_size(10.0, 1.14)
        assert result["raw_tmb"] == 10.0
        assert result["correction_factor"] == 1.0
        assert result["adjusted_tmb"] == 10.0
        exploratory = adjust_for_panel_size(10.0, 1.14, experimental_correction=True)
        assert exploratory["correction_factor"] > 1.0
        assert exploratory["experimental_correction"] is True

    def test_adjustment_large_panel(self):
        result = adjust_for_panel_size(10.0, 38.0)
        assert result["correction_factor"] == 1.0
        assert result["adjusted_tmb"] == 10.0

    def test_adjustment_invalid(self):
        with pytest.raises(ValueError, match="must be >= 0"):
            adjust_for_panel_size(-1.0, 1.14)


# ---------------------------------------------------------------------------
# Immunotherapy Response Tests
# ---------------------------------------------------------------------------

class TestImmunotherapyResponse:

    def test_response_tmb_high(self):
        result = immunotherapy_response_assessment(15.0)
        assert "Higher likelihood" in result["response_likelihood"]
        assert "Pembrolizumab" in result["therapy_recommendation"]

    def test_response_tmb_intermediate(self):
        result = immunotherapy_response_assessment(7.0)
        assert "Moderate" in result["response_likelihood"]

    def test_response_tmb_low(self):
        result = immunotherapy_response_assessment(2.0)
        assert "Lower likelihood" in result["response_likelihood"]

    def test_response_with_cancer_type(self):
        result = immunotherapy_response_assessment(12.0, "NSCLC")
        assert result["cancer_type"] == "NSCLC"


# ---------------------------------------------------------------------------
# Panel Info Tests
# ---------------------------------------------------------------------------

class TestPanelInfo:

    def test_foundationone(self):
        result = get_panel_info("foundationone_cdx")
        assert result["coding_region_mb"] == 1.14

    def test_msk_impact(self):
        result = get_panel_info("msk_impact")
        assert result["coding_region_mb"] == 1.22

    def test_invalid_panel(self):
        with pytest.raises(ValueError, match="Unknown panel"):
            get_panel_info("nonexistent_panel")


# ---------------------------------------------------------------------------
# Batch Processing Tests
# ---------------------------------------------------------------------------

class TestBatchProcessing:

    def test_batch_basic(self, tmp_path):
        csv_in = tmp_path / "in.csv"
        csv_out = tmp_path / "out.csv"
        csv_in.write_text(
            "total_mutations,coding_region_size_mb,cancer_type\n"
            "380,38.0,nsclc\n"
            "50,38.0,gastric\n",
            encoding="utf-8"
        )
        count = process_batch(str(csv_in), str(csv_out))
        assert count == 2
        content = csv_out.read_text(encoding="utf-8")
        assert "tmb" in content
        assert "fda_eligible" in content
