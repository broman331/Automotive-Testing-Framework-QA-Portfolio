import xml.etree.ElementTree as ET
import json
import sys
import os

def parse_requirements(json_path):
    with open(json_path, 'r') as f:
        return json.load(f)

def parse_junit_xml(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    test_results = {}
    
    # Iterate through all testcases
    for testcase in root.iter('testcase'):
        test_name = testcase.get('name')
        
        # Determine status
        status = "PASSED"
        if testcase.find('failure') is not None:
            status = "FAILED"
        elif testcase.find('skipped') is not None:
            status = "SKIPPED"
        elif testcase.find('error') is not None:
            status = "ERROR"
            
        # Extract the requirement ID from properties
        req_id = None
        properties = testcase.find('properties')
        if properties is not None:
            for prop in properties.iter('property'):
                if prop.get('name') == 'req':
                    req_id = prop.get('value')
                    break
        
        if req_id:
            test_results[req_id] = {
                'test_name': test_name,
                'status': status
            }
            
    return test_results

def generate_markdown_matrix(requirements, test_results, output_path):
    uncovered_reqs = []
    
    with open(output_path, 'w') as f:
        f.write("# ASPICE Traceability Matrix\n\n")
        f.write("| Requirement ID | Title | Test Case Name | Status |\n")
        f.write("|---|---|---|---|\n")
        
        for req_id, details in requirements.items():
            title = details.get('title', 'Unknown')
            if req_id in test_results:
                test_name = test_results[req_id]['test_name']
                status = test_results[req_id]['status']
                # Add color emojis for quick visual grepping
                if status == "PASSED": status_fmt = f"✅ {status}"
                else: status_fmt = f"❌ {status}"
                
                f.write(f"| {req_id} | {title} | `{test_name}` | {status_fmt} |\n")
            else:
                f.write(f"| {req_id} | {title} | **MISSING** | ⚠️ UNCOVERED |\n")
                uncovered_reqs.append(req_id)
                
    return uncovered_reqs

def main():
    print("--- ASPICE Traceability Generator ---")
    req_file = 'requirements.json'
    xml_file = 'report.xml'
    out_file = 'traceability_matrix.md'
    
    if not os.path.exists(xml_file):
        print(f"Error: Could not find JUnit XML log '{xml_file}'. Please run pytest first.")
        sys.exit(1)
        
    reqs = parse_requirements(req_file)
    results = parse_junit_xml(xml_file)
    
    uncovered = generate_markdown_matrix(reqs, results, out_file)
    
    print(f"Generated traceability matrix at {out_file}")
    print(f"Total Requirements: {len(reqs)}")
    print(f"Total Requirements Tested: {len(results)}")
    
    if uncovered:
        print("\n[!] ASPICE COMPLIANCE ERROR: The following requirements have no linked test cases:")
        for r in uncovered:
            print(f"  - {r}")
        print("\nTraceability check failed. Failing the build pipeline.")
        sys.exit(1)
        
    print("\n100% Requirement Test Coverage Achieved! ASPICE compliance check passed.")
    sys.exit(0)

if __name__ == '__main__':
    main()
