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
            if req_id not in test_results:
                test_results[req_id] = []
                
            test_results[req_id].append({
                'test_name': test_name,
                'status': status
            })
            
    return test_results

def generate_markdown_matrix(requirements, test_results, output_path):
    uncovered_reqs = []
    orphaned_tests = []
    
    with open(output_path, 'w') as f:
        f.write("# ASPICE Traceability Matrix\n\n")
        f.write("| Requirement ID | Title | Executed Test Cases | Aggregated Status |\n")
        f.write("|---|---|---|---|\n")
        
        for req_id, details in requirements.items():
            title = details.get('title', 'Unknown')
            if req_id in test_results:
                # Aggregate results: If ANY child test failed, the requirement fails
                tests = test_results[req_id]
                test_names = "<br>".join([f"`{t['test_name']}`" for t in tests])
                
                # Check if any test in the list failed
                any_failure = any(t['status'] != "PASSED" for t in tests)
                agg_status = "FAILED" if any_failure else "PASSED"
                
                # Add color emojis for quick visual grepping
                if agg_status == "PASSED": status_fmt = f"✅ {agg_status}"
                else: status_fmt = f"❌ {agg_status}"
                
                f.write(f"| {req_id} | {title} | {test_names} | {status_fmt} |\n")
            else:
                f.write(f"| {req_id} | {title} | **MISSING** | ⚠️ UNCOVERED |\n")
                uncovered_reqs.append(req_id)
                
        # Detect orphaned tests (tests mapped to reqs not in the JSON)
        for req_id in test_results.keys():
            if req_id not in requirements:
                tests_str = ", ".join([t['test_name'] for t in test_results[req_id]])
                orphaned_tests.append(f"Req: {req_id} -> Tests: [{tests_str}]")
                
    return uncovered_reqs, orphaned_tests

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
    
    uncovered, orphaned = generate_markdown_matrix(reqs, results, out_file)
    
    print(f"Generated traceability matrix at {out_file}")
    print(f"Total Formal Requirements: {len(reqs)}")
    
    # Calculate coverage
    tested_reqs_count = len([r for r in reqs.keys() if r in results])
    print(f"Total Requirements Tested: {tested_reqs_count}")
    
    has_error = False
    
    if uncovered:
        has_error = True
        print("\n[!] ASPICE COMPLIANCE ERROR: The following requirements have no linked test cases:")
        for r in uncovered:
            print(f"  - {r}")
            
    if orphaned:
        has_error = True
        print("\n[!] ORPHANED TEST ERROR: The following tests are linked to invalid requirement IDs:")
        for r in orphaned:
            print(f"  - {r}")
            
    if has_error:
        print("\nTraceability check failed. Failing the build pipeline.")
        sys.exit(1)
        
    print("\n100% Requirement Test Coverage Achieved and no orphaned tests! ASPICE compliance check passed.")
    sys.exit(0)

if __name__ == '__main__':
    main()
