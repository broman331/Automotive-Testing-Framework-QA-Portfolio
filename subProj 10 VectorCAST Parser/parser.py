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

    def generate_json_report(self, output_path: str = None) -> dict:
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

        if output_path:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=4)
                
        return report

if __name__ == "__main__":
    parser = VectorCastParser()
    parser.parse_directory("sample_data")
    print(json.dumps(parser.generate_json_report(), indent=4))
