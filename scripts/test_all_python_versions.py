#!/usr/bin/env python3
"""
Test script to verify compatibility across all Python versions (3.8-3.12)
using uv for virtual environment management.
"""

import subprocess
import sys
import time
import os

def run_command(cmd, description, python_version=None):
    """Run a command and return success status"""
    print(f"\n{'='*80}")
    print(f"🐍 Testing Python {python_version}")
    print(f"📝 {description}")
    print(f"💻 Command: {' '.join(cmd)}")
    print(f"{'='*80}")
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=False)
    end_time = time.time()
    
    duration = end_time - start_time
    status = "✅ PASSED" if result.returncode == 0 else "❌ FAILED"
    print(f"\n{status} - Python {python_version} completed in {duration:.2f}s")
    
    return result.returncode == 0

def run_python_version_tests(version):
    """Test a specific Python version"""
    print(f"\n🚀 Testing Python {version}")
    
    # Create virtual environment
    venv_name = f".venv-{version}"
    create_venv_cmd = ["uv", "venv", venv_name, "--python", f"python{version}"]
    
    if not run_command(create_venv_cmd, f"Creating virtual environment for Python {version}", version):
        return False
    
    # Install dependencies using uv
    install_cmd = ["uv", "pip", "install", "-e", ".[test]", "--python", f"{venv_name}/bin/python"]
    
    if not run_command(install_cmd, f"Installing dependencies for Python {version}", version):
        return False
    
    # Run unit tests (fast) using the venv python
    python_cmd = f"{venv_name}/bin/python"
    unit_test_cmd = [python_cmd, "-m", "pytest", "-v", "-n", "auto", 
                    "tests/libp2p_stubs/", "tests/test_p2pclient.py", 
                    "tests/test_datastructures.py", "tests/test_serialization.py", 
                    "tests/test_utils.py"]
    
    if not run_command(unit_test_cmd, f"Running unit tests for Python {version}", version):
        return False
    
    print(f"✅ Python {version} - All unit tests passed!")
    return True

def main():
    """Test all Python versions"""
    print("🧪 Testing py-libp2p-daemon-bindings across Python versions")
    print("📋 Testing: Python 3.8, 3.9, 3.10, 3.11, 3.12")
    
    versions = ["3.8", "3.9", "3.10", "3.11", "3.12"]
    results = {}
    
    for version in versions:
        try:
            success = run_python_version_tests(version)
            results[version] = success
        except Exception as e:
            print(f"❌ Error testing Python {version}: {e}")
            results[version] = False
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 TEST RESULTS SUMMARY")
    print(f"{'='*80}")
    
    passed = 0
    total = len(versions)
    
    for version in versions:
        status = "✅ PASSED" if results[version] else "❌ FAILED"
        print(f"Python {version}: {status}")
        if results[version]:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} Python versions passed")
    
    if passed == total:
        print("🎉 All Python versions are compatible!")
        return True
    else:
        print("⚠️  Some Python versions failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
