"""Regression tests for TMB cutoffs, CSV validation, API and audit integrity."""
import pytest
from fastapi.testclient import TestClient
from tmb_calc import calculate_tmb, adjust_for_panel_size, immunotherapy_response_assessment, process_batch
from agents.base import AuditTrail
from agents.api import app

def test_unrounded_cutoff_not_display_rounding():
    result = calculate_tmb(10, 1.00009)
    assert result["tmb"] == 10.0
    assert result["tmb_unrounded"] < 10
    assert result["tmb_category"] == "Intermediate"
    assert not result["fda_eligible"]
    assert not result["clinical_eligibility_determined"]

@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), 0, -1, True])
def test_invalid_territory(value):
    with pytest.raises(ValueError):
        calculate_tmb(10, value)

@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1])
def test_invalid_response_input(value):
    with pytest.raises(ValueError):
        immunotherapy_response_assessment(value)

def test_panel_adjustment_default_is_identity():
    assert adjust_for_panel_size(10, 1.14)["adjusted_tmb"] == 10
    assert adjust_for_panel_size(10, 1.14, experimental_correction=True)["adjusted_tmb"] > 10

def test_csv_validation(tmp_path):
    src = tmp_path / "input.csv"
    dst = tmp_path / "output.csv"
    src.write_text("bad,headers\n10,1\n")
    with pytest.raises(ValueError, match="requires"):
        process_batch(str(src), str(dst))
    src.write_text("total_mutations,coding_region_size_mb\n10,nan\n")
    with pytest.raises(ValueError, match="finite"):
        process_batch(str(src), str(dst))
    with pytest.raises(ValueError, match="paths must differ"):
        process_batch(str(src), str(src))

def test_csv_formula_injection_escaped(tmp_path):
    src = tmp_path / "input.csv"
    dst = tmp_path / "output.csv"
    src.write_text('total_mutations,coding_region_size_mb,comment\n10,1,"=1+1"\n')
    assert process_batch(str(src), str(dst)) == 1
    assert "'=1+1" in dst.read_text()

def test_hmac_detects_modified_entry():
    audit = AuditTrail(secret_key="test-audit-key-is-long-and-random-enough")
    audit.log("tester", "test", "EVALUATE", {"id":"example"})
    assert audit.verify_integrity()
    result_copy = audit.get_trail()
    result_copy[0]["actor"] = "modified"
    assert audit.verify_integrity()
    audit.logs[0]["actor"] = "modified"
    assert not audit.verify_integrity()

def test_api_serves_calculator_and_protects_audit_logs(monkeypatch):
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    assert "Tumor mutational burden calculator" in client.get("/").text
    assert "function calc" in client.get("/app.js").text
    monkeypatch.delenv("AUDIT_API_TOKEN", raising=False)
    assert client.get("/api/audit/logs").status_code == 503
    monkeypatch.setenv("AUDIT_API_TOKEN", "test-only-token")
    assert client.get("/api/audit/logs").status_code == 403
    assert client.get("/api/audit/logs", headers={"X-Audit-Token":"test-only-token"}).status_code == 200
    assert client.post("/api/audit", json={"task_id":"T1","target_identifier":"MRN-998877","primary_metric":3}).status_code == 422
