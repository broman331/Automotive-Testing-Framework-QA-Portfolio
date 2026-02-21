# subProj 10: VectorCAST Log Parser

## Description
VectorCAST is an enterprise-grade C/C++ execution environment used heavily in Automotive Functional Safety (ISO 26262 / ASPICE). While VectorCAST provides deep execution frameworks, many CI/CD architectures require extracting the raw metrics (Execution success/failure, Statement Coverage, Branch Coverage, MC/DC Coverage) from VectorCAST's proprietary `.xml` output to feed into unified test management dashboards (like Jira Xray, Zephyr, or custom React interfaces).

This toolkit serves as an automated abstraction layer. It sweeps target directories, consumes massive numbers of VectorCAST XML reports, gracefully traps malformed or unclosed XML tags without crashing the pipeline, and aggregates the data mathematically into a singular `consolidated_report.json` document.

## Architecture

1. **`sample_data/`**: A mock repository populated by standard VectorCAST execution and coverage payload exports. Includes `exec_results.xml`, `coverage_results.xml`, maliciously corrupted `corrupted.xml` strings, and a historical `baseline.json`.
2. **`parser.py`**: A python script utilizing the native `xml.etree.ElementTree` to parse nodes, compute fractional percentages, calculate drift deltas against prior baselines, and dynamically construct a graphical HTML status dashboard.
3. **`tests/test_parser.py`**: A `pytest` suite simulating CI execution and mathematical validations.

## Test Coverage
The automated Pytest execution asserts:
* **TC-1001 Parse Execution Results**: Asserts structural matching of pass/fail node aggregation.
* **TC-1002 Parse Coverage Metrics**: Asserts fractional percentage summation of structural coverage nodes.
* **TC-1003 Multi-File Aggregation**: Points the engine at the entire directory and asserts multi-file processing sums mathematically.
* **TC-1004 Malformed XML Resilience**: Points the engine at the corrupted XML file to guarantee the `ET.ParseError` is trapped cleanly, appended to an `"errors"` list in the final JSON, and that the Python process remains alive to finish processing subsequent valid files.
* **TC-1005 Historical Delta Calculation**: Validates the mathematical precision matching the current execution XMLs against the legacy `baseline.json` file to surface positive or negative pipeline drift metrics.
* **TC-1006 Automated HTML Rendering**: Generates a temporary `index.html` mapping the Python dictionary natively into the CSS wrapper.

## Docker & Automation
Tests are fully containerized using Docker and executed automatically via the `.github/workflows/ci_subproj10.yml` pipeline.

### Local Execution
To run the framework locally:
```bash
cd "subProj 10 VectorCAST Parser"
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.
pytest tests/ -v
```
