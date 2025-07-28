#!/usr/bin/env python3
"""
Simple test script to verify the MyMCMB AI Center app functionality
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required imports work"""
    print("Testing imports...")
    try:
        import streamlit as st
        import pandas as pd
        import google.generativeai as genai
        import json
        from datetime import datetime
        import re
        import io
        from fpdf import FPDF
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_utility_functions():
    """Test the utility functions from app.py"""
    print("Testing utility functions...")
    
    # Import the functions from app
    from app import clean_currency, clean_percentage, calculate_new_pi, calculate_amortized_balance
    
    # Test clean_currency
    assert clean_currency("$1,500.00") == 1500.0
    assert clean_currency("1500") == 1500.0
    assert clean_currency("") == 0.0
    
    # Test clean_percentage
    assert clean_percentage("7.5%") == 0.075
    assert clean_percentage("7.5") == 0.075
    assert clean_percentage("75") == 0.75
    
    # Test calculate_new_pi
    payment = calculate_new_pi(300000, 0.07, 30)
    assert 1900 < payment < 2100  # Should be around $1996
    
    print("✅ Utility functions working correctly")
    return True

def test_data_processing():
    """Test data processing functionality"""
    print("Testing data processing...")
    
    from app import normalize_columns, COLUMN_ALIASES
    
    # Create test DataFrame with various column name formats
    test_data = {
        'First Name': ['John', 'Jane'],
        'Last Name': ['Doe', 'Smith'],
        'Current Payment': [1500.0, 1800.0],
        'Purchase Price': [300000.0, 400000.0],
        'Original Loan Amount': [240000.0, 320000.0],
        'Rate': [0.075, 0.065],
        'Term': [30, 30],
        'First Payment': ['2020-01-01', '2019-06-01'],
        'City': ['Nashville', 'Memphis']
    }
    
    df = pd.DataFrame(test_data)
    normalized_df = normalize_columns(df)
    
    # Check that normalization worked
    expected_columns = [
        'Borrower First Name', 'Borrower Last Name', 'Current P&I Mtg Pymt',
        'Original Property Value', 'Total Original Loan Amount', 'Current Interest Rate',
        'Loan Term (years)', 'First Pymt Date', 'City'
    ]
    
    for col in expected_columns:
        if col in COLUMN_ALIASES:
            found = any(alias.lower() in [c.lower() for c in test_data.keys()] 
                       for alias in COLUMN_ALIASES[col])
            if found and col not in normalized_df.columns:
                print(f"❌ Column normalization failed for {col}")
                return False
    
    print("✅ Data processing working correctly")
    return True

def test_app_compilation():
    """Test that app.py compiles without errors"""
    print("Testing app compilation...")
    
    import py_compile
    try:
        py_compile.compile('app.py', doraise=True)
        print("✅ App compiles successfully")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Compilation error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting MyMCMB AI Center Tests\n")
    
    tests = [
        test_imports,
        test_app_compilation,
        test_utility_functions,
        test_data_processing
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with error: {e}\n")
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your MyMCMB AI Center is ready to deploy.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)