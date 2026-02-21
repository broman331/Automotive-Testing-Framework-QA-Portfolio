import os
import json
import xml.etree.ElementTree as ET
import glob

class VectorCastParser:
    def __init__(self):
        self.metrics = {
            "execution": {
                "passed": 0,
                "failed": 0,
                "total": 0
            },
            "coverage": {
                "statement_achieved_sum": 0.0,
                "statement_total_sum": 0.0,
                "branch_achieved_sum": 0.0,
                "branch_total_sum": 0.0,
                "mcdc_achieved_sum": 0.0,
                "mcdc_total_sum": 0.0
            },
            "errors": []
        }

    def parse_file(self, file_path: str):
        """Attempts to parse a single VectorCAST XML file and accumulate metrics."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extract execution metrics
            execution_node = root.find("execution_report")
            if execution_node is not None:
                for test_suite in execution_node.findall("test_suite"):
                    test_cases = test_suite.find("test_cases")
                    if test_cases is not None:
                        self.metrics["execution"]["passed"] += int(test_cases.get("passed", 0))
                        self.metrics["execution"]["failed"] += int(test_cases.get("failed", 0))
                        self.metrics["execution"]["total"] += int(test_cases.get("total", 0))

            # Extract coverage metrics
            coverage_node = root.find("coverage_report")
            if coverage_node is not None:
                for module in coverage_node.findall("module"):
                    stmt = module.find("statement_coverage")
                    if stmt is not None:
                        self.metrics["coverage"]["statement_achieved_sum"] += float(stmt.get("achieved", 0.0))
                        self.metrics["coverage"]["statement_total_sum"] += float(stmt.get("total", 0.0))
                        
                    branch = module.find("branch_coverage")
                    if branch is not None:
                        self.metrics["coverage"]["branch_achieved_sum"] += float(branch.get("achieved", 0.0))
                        self.metrics["coverage"]["branch_total_sum"] += float(branch.get("total", 0.0))

                    mcdc = module.find("mcdc_coverage")
                    if mcdc is not None:
                        self.metrics["coverage"]["mcdc_achieved_sum"] += float(mcdc.get("achieved", 0.0))
                        self.metrics["coverage"]["mcdc_total_sum"] += float(mcdc.get("total", 0.0))

        except ET.ParseError as e:
            self.metrics["errors"].append(f"Malformed XML in {os.path.basename(file_path)}: {str(e)}")
        except Exception as e:
            self.metrics["errors"].append(f"Unexpected error in {os.path.basename(file_path)}: {str(e)}")

    def parse_directory(self, directory_path: str):
        """Scans a directory for all XML files and aggregates them."""
        search_pattern = os.path.join(directory_path, "*.xml")
        xml_files = glob.glob(search_pattern)
        
        for file in xml_files:
            self.parse_file(file)

    def compute_deltas(self, current_report: dict, baseline_path: str) -> dict:
        """Compares current execution metrics against a historical baseline."""
        try:
            with open(baseline_path, 'r') as f:
                baseline = json.load(f)
                
            deltas = {
                "execution": {
                    "passed_delta": current_report["execution"]["passed"] - baseline["execution"]["passed"],
                    "failed_delta": current_report["execution"]["failed"] - baseline["execution"]["failed"],
                    "pass_rate_delta": round(current_report["execution"]["pass_rate_percentage"] - baseline["execution"]["pass_rate_percentage"], 2)
                },
                "coverage": {
                    "statement_delta": round(current_report["coverage"]["statement_coverage_percentage"] - baseline["coverage"]["statement_coverage_percentage"], 2),
                    "branch_delta": round(current_report["coverage"]["branch_coverage_percentage"] - baseline["coverage"]["branch_coverage_percentage"], 2),
                    "mcdc_delta": round(current_report["coverage"]["mcdc_coverage_percentage"] - baseline["coverage"]["mcdc_coverage_percentage"], 2)
                }
            }
            return deltas
        except FileNotFoundError:
            return None # No baseline to compare against
        except Exception as e:
            self.metrics["errors"].append(f"Delta computation error: {str(e)}")
            return None

    def generate_json_report(self, output_path: str = None, baseline_path: str = None) -> dict:
        """Calculates final averages and returns a clean JSON structure."""
        report = {
            "execution": {
                "passed": self.metrics["execution"]["passed"],
                "failed": self.metrics["execution"]["failed"],
                "total": self.metrics["execution"]["total"],
                "pass_rate_percentage": 0.0
            },
            "coverage": {
                "statement_coverage_percentage": 0.0,
                "branch_coverage_percentage": 0.0,
                "mcdc_coverage_percentage": 0.0
            },
            "errors": self.metrics["errors"]
        }

        # Calculate Pass Rate Average
        if report["execution"]["total"] > 0:
            rate = (report["execution"]["passed"] / report["execution"]["total"]) * 100
            report["execution"]["pass_rate_percentage"] = round(rate, 2)

        # Calculate Coverage Averages
        cov = self.metrics["coverage"]
        if cov["statement_total_sum"] > 0:
            report["coverage"]["statement_coverage_percentage"] = round(
                (cov["statement_achieved_sum"] / cov["statement_total_sum"]) * 100, 2
            )
        if cov["branch_total_sum"] > 0:
            report["coverage"]["branch_coverage_percentage"] = round(
                (cov["branch_achieved_sum"] / cov["branch_total_sum"]) * 100, 2
            )
        if cov["mcdc_total_sum"] > 0:
            report["coverage"]["mcdc_coverage_percentage"] = round(
                (cov["mcdc_achieved_sum"] / cov["mcdc_total_sum"]) * 100, 2
            )

        if baseline_path:
            report["deltas"] = self.compute_deltas(report, baseline_path)

        if output_path:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=4)
                
        return report

    def generate_html_report(self, report_json: dict, output_path: str = "index.html"):
        """Generates a developer-friendly HTML dashboard from the aggregated JSON math."""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>VectorCAST CI/CD Dashboard</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 40px; background-color: #f4f4f9; color: #333; }}
                h1 {{ color: #2c3e50; }}
                .container {{ display: flex; gap: 20px; }}
                .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); flex: 1; }}
                .metric {{ font-size: 24px; font-weight: bold; margin-top: 10px; }}
                .delta.pos {{ color: #27ae60; font-size: 14px; margin-left: 10px; }}
                .delta.neg {{ color: #c0392b; font-size: 14px; margin-left: 10px; }}
                .error {{ color: #c0392b; padding: 10px; border-left: 4px solid #c0392b; background: #fdf5f5; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <h1>VectorCAST Coverage & Execution Dashboard</h1>
            
            <div class="container">
                <div class="card">
                    <h3>Execution Overview</h3>
                    <div class="metric">Passed: {report_json['execution']['passed']}</div>
                    <div class="metric">Failed: {report_json['execution']['failed']}</div>
                    <div class="metric">Pass Rate: {report_json['execution']['pass_rate_percentage']}%</div>
                </div>
                
                <div class="card">
                    <h3>Structural Coverage</h3>
                    <div class="metric">Statement: {report_json['coverage']['statement_coverage_percentage']}%</div>
                    <div class="metric">Branch: {report_json['coverage']['branch_coverage_percentage']}%</div>
                    <div class="metric">MC/DC: {report_json['coverage']['mcdc_coverage_percentage']}%</div>
                </div>
            </div>
        """
        
        if report_json.get("deltas"):
            deltas = report_json["deltas"]
            # Formatting helpers
            sc_c = "pos" if deltas["coverage"]["statement_delta"] >= 0 else "neg"
            br_c = "pos" if deltas["coverage"]["branch_delta"] >= 0 else "neg"
            
            html_content += f"""
            <h2 style="margin-top: 40px;">Historical Pipeline Drift (vs Baseline)</h2>
            <div class="container">
                <div class="card">
                    <h3>Execution Deltas</h3>
                    <p>New Passed Tests: <span class="delta {sc_c}">{deltas['execution']['passed_delta']:+}</span></p>
                    <p>New Failing Tests: <span class="delta {br_c}">{deltas['execution']['failed_delta']:+}</span></p>
                </div>
                <div class="card">
                    <h3>Coverage Deltas</h3>
                    <p>Statement Range: <span class="delta {sc_c}">{deltas['coverage']['statement_delta']:+}%</span></p>
                    <p>Branch Math: <span class="delta {br_c}">{deltas['coverage']['branch_delta']:+}%</span></p>
                </div>
            </div>
            """
            
        if report_json["errors"]:
            html_content += """<h2 style="margin-top: 40px;">Parser Faults</h2>"""
            for err in report_json["errors"]:
                html_content += f"""<div class="error">{err}</div>"""
                
        html_content += """
        </body>
        </html>
        """
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        return True

if __name__ == "__main__":
    parser = VectorCastParser()
    parser.parse_directory("sample_data")
    report = parser.generate_json_report(baseline_path="sample_data/baseline.json")
    parser.generate_html_report(report, "index.html")
    print(json.dumps(report, indent=4))
    print("Exported dashboard to index.html")
