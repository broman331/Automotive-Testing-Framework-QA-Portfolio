import os
import pytest
from parser import VectorCastParser

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "../sample_data")

def test_1001_parse_execution_results():
    """TC-1001: Assert the parser cleanly extracts passed and failed counts"""
    parser = VectorCastParser()
    parser.parse_file(os.path.join(SAMPLE_DIR, "exec_results.xml"))
    
    report = parser.generate_json_report()
    
    assert report["execution"]["passed"] == 63 # 45 + 18
    assert report["execution"]["failed"] == 2
    assert report["execution"]["total"] == 65
    assert report["execution"]["pass_rate_percentage"] == round((63/65)*100, 2)
    assert len(report["errors"]) == 0

def test_1002_parse_coverage_metrics():
    """TC-1002: Assert the parser correctly extracts structural coverage."""
    parser = VectorCastParser()
    parser.parse_file(os.path.join(SAMPLE_DIR, "coverage_results.xml"))
    
    report = parser.generate_json_report()
    
    # statement total: 200 (100+100), achieved 195.5 (95.5 + 100) -> 97.75%
    assert report["coverage"]["statement_coverage_percentage"] == 97.75
    # branch total 200, achieved 186.2 -> 93.1%
    assert report["coverage"]["branch_coverage_percentage"] == 93.1
    # mcdc total 200, achieved 177.1 -> 88.55%
    assert report["coverage"]["mcdc_coverage_percentage"] == 88.55
    assert len(report["errors"]) == 0

def test_1003_multi_file_aggregation():
    """TC-1003: Assert multiple XML files natively aggregate into a single dictionary."""
    parser = VectorCastParser()
    
    # Notice we use parse_file twice manually to avoid hitting the corrupted.xml just yet.
    # In reality `parse_directory` will grab all 3.
    parser.parse_file(os.path.join(SAMPLE_DIR, "exec_results.xml"))
    parser.parse_file(os.path.join(SAMPLE_DIR, "coverage_results.xml"))
    
    report = parser.generate_json_report()
    
    # Assert execution metrics exist
    assert report["execution"]["total"] == 65
    # Assert coverage metrics exist simultaneously
    assert report["coverage"]["branch_coverage_percentage"] == 93.1

def test_1004_malformed_xml_resilience():
    """TC-1004: Assert that an unclosed XML tag does not crash the pipeline, but throws a tracked error."""
    parser = VectorCastParser()
    
    # `parse_directory` grabs exec, coverage, AND corrupted.xml
    parser.parse_directory(SAMPLE_DIR)
    report = parser.generate_json_report()
    
    # We should still have our metrics from the good files!
    assert report["execution"]["total"] == 65
    assert report["coverage"]["statement_coverage_percentage"] == 97.75
    
    # AND we should have gracefully caught 1 error
    assert len(report["errors"]) == 1
    assert "corrupted.xml" in report["errors"][0]
