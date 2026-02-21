#!/bin/bash
set -e

echo "========================================="
echo "=== 1. Building for gcov Coverage     ==="
echo "========================================="
make clean
make coverage

echo ""
echo "========================================="
echo "=== 2. Running Pytest Suite           ==="
echo "========================================="
pytest --html=/app/reports/report.html --self-contained-html

echo ""
echo "========================================="
echo "=== 3. Building for Valgrind          ==="
echo "========================================="
make valgrind_build

echo ""
echo "========================================="
echo "=== 4. Running Valgrind Memory Check  ==="
echo "========================================="
valgrind --leak-check=full --show-leak-kinds=all --error-exitcode=1 ./valgrind_test

echo ""
echo "========================================="
echo "=== 5. Generating Coverage Report     ==="
echo "========================================="
gcov aeb_logic.cpp
echo "--- Coverage Summary ---"
cat aeb_logic.cpp.gcov | grep -v " -:" | head -n 30

echo ""
echo "✅ All AST / Memory Safety pipelines passed successfully!"
