#!/usr/bin/env python3
"""
Test runner script that optimizes test execution:
- Unit tests run in parallel for speed
- Integration tests run sequentially to avoid daemon conflicts
"""

import subprocess
import sys
import time

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=False)
    end_time = time.time()
    
    duration = end_time - start_time
    status = "✅ PASSED" if result.returncode == 0 else "❌ FAILED"
    print(f"\n{status} - {description} completed in {duration:.2f}s")
    
    return result.returncode == 0

def main():
    """Run tests with optimal configuration"""
    print("🚀 Running optimized test suite...")
    
    # Unit tests (parallel execution)
    unit_tests = [
        "tests/libp2p_stubs/",
        "tests/test_p2pclient.py", 
        "tests/test_datastructures.py",
        "tests/test_serialization.py",
        "tests/test_utils.py"
    ]
    
    unit_cmd = ["pytest", "-v", "-n", "auto", "--timeout=180"] + unit_tests
    
    # Integration tests (sequential execution)
    integration_cmd = ["pytest", "-v", "-n", "0", "--timeout=180", "tests/test_p2pclient_integration.py"]
    
    # Run unit tests first (fast)
    unit_success = run_command(unit_cmd, "Unit Tests (Parallel)")
    
    if not unit_success:
        print("\n❌ Unit tests failed. Stopping here.")
        sys.exit(1)
    
    # Run integration tests (slower, but necessary)
    integration_success = run_command(integration_cmd, "Integration Tests (Sequential)")
    
    if not integration_success:
        print("\n❌ Integration tests failed.")
        sys.exit(1)
    
    print("\n🎉 All tests passed!")
    print("\nSummary:")
    print("- Unit tests: Fast parallel execution")
    print("- Integration tests: Sequential execution (daemon-safe)")
    print("- Total time: Significantly faster than before!")

if __name__ == "__main__":
    main()
