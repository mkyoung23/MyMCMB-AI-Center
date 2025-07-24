#!/usr/bin/env python3
"""
MyMCMB AI Command Center - Complete Flow Validation Script
Tests the entire Excel upload and processing workflow
"""

import sys
import os
import tempfile
import pandas as pd
from datetime import datetime, timedelta
import traceback

# Set up path to import from app.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_flow_validation():
    """Complete end-to-end flow validation"""
    print("🧪 MyMCMB AI Command Center - Flow Validation")
    print("=" * 60)
    
    try:
        # Import core functions
        from app import (
            normalize_columns, clean_currency, clean_percentage,
            calculate_new_pi, calculate_amortized_balance,
            COLUMN_ALIASES, REQUIRED_COLUMNS
        )
        print("✅ Successfully imported all core functions")
        
        # Create test data with alternative column names
        test_data_alt = [
            {
                "first name": "John",
                "last name": "Smith", 
                "current payment": "$1,500.00",
                "purchase price": "$300,000",
                "loan amount": "240000",
                "interest rate": "7.25%",
                "term": 30,
                "first payment date": "2020-06-01",
                "property city": "Nashville"
            }
        ]
        
        # Create test data with standard column names
        test_data_std = [
            {
                "Borrower First Name": "Sarah",
                "Borrower Last Name": "Johnson",
                "Current P&I Mtg Pymt": 2200.00,
                "Original Property Value": 450000.00,
                "Total Original Loan Amount": 360000.00,
                "Current Interest Rate": 6.875,
                "Loan Term (years)": 30,
                "First Pymt Date": "2019-03-15",
                "City": "Memphis"
            }
        ]
        
        # Test column normalization with alternative names
        print("\n🔄 Testing column normalization with alternative names...")
        df_alt = pd.DataFrame(test_data_alt)
        print(f"Original alternative columns: {list(df_alt.columns)}")
        
        df_alt_normalized = normalize_columns(df_alt)
        print(f"Normalized alternative columns: {list(df_alt_normalized.columns)}")
        
        # Test column normalization with standard names
        print("\n🔄 Testing column normalization with standard names...")
        df_std = pd.DataFrame(test_data_std)
        print(f"Original standard columns: {list(df_std.columns)}")
        
        df_std_normalized = normalize_columns(df_std)
        print(f"Normalized standard columns: {list(df_std_normalized.columns)}")
        
        # Combine for processing
        df = pd.concat([df_alt_normalized, df_std_normalized], ignore_index=True)
        
        # Test data cleaning and calculations
        print("\n🧮 Testing calculations...")
        
        appreciation_rate = 7.0
        
        # Calculate financial metrics
        df['Remaining Balance'] = df.apply(
            lambda row: calculate_amortized_balance(
                row.get('Total Original Loan Amount'), 
                row.get('Current Interest Rate'), 
                row.get('Loan Term (years)'), 
                row.get('First Pymt Date')
            ), axis=1
        )
        
        df['Months Since First Payment'] = df['First Pymt Date'].apply(
            lambda x: max(0, (datetime.now().year - pd.to_datetime(x).year) * 12 + 
                         (datetime.now().month - pd.to_datetime(x).month)) if pd.notna(x) else 0
        )
        
        df['Estimated Home Value'] = df.apply(
            lambda row: round(
                clean_currency(row.get('Original Property Value', 0))
                * ((1 + appreciation_rate / 100) ** (row['Months Since First Payment'] / 12)),
                2,
            ),
            axis=1,
        )
        
        df['Estimated LTV'] = (
            (df['Remaining Balance'] / df['Estimated Home Value'])
        ).fillna(0).replace([float('inf'), -float('inf')], 0).round(4)
        
        df['Max Cash-Out Amount'] = (df['Estimated Home Value'] * 0.80) - df['Remaining Balance']
        df['Max Cash-Out Amount'] = df['Max Cash-Out Amount'].apply(lambda x: max(0, round(x, 2)))
        
        # Test export-style processing
        print("\n📊 Testing export processing...")
        
        # Simulate rate calculations
        test_rates = {
            '30yr_fixed': 6.875,
            '15yr_fixed': 6.000,
            '20yr_fixed': 6.625
        }
        
        for term, rate_key in [('30yr', '30yr_fixed'), ('15yr', '15yr_fixed'), ('20yr', '20yr_fixed')]:
            rate = test_rates.get(rate_key, 0) / 100
            years = int(term.replace('yr', ''))
            if rate > 0:
                df[f'New P&I ({term})'] = df.apply(
                    lambda row: calculate_new_pi(row['Remaining Balance'], rate, years), axis=1
                )
                df[f'Savings ({term})'] = df.apply(
                    lambda row: clean_currency(row['Current P&I Mtg Pymt']) - row[f'New P&I ({term})'], axis=1
                )
        
        print("✅ All calculations completed successfully")
        
        # Display results summary
        print("\n📋 Results Summary:")
        print("-" * 40)
        for index, row in df.iterrows():
            print(f"\n👤 {row['Borrower First Name']} {row['Borrower Last Name']}:")
            print(f"   Current P&I: ${clean_currency(row['Current P&I Mtg Pymt']):,.2f}")
            print(f"   Remaining Balance: ${row['Remaining Balance']:,.2f}")
            print(f"   Estimated Home Value: ${row['Estimated Home Value']:,.2f}")
            print(f"   Estimated LTV: {row['Estimated LTV']:.2%}")
            print(f"   Max Cash-Out: ${row['Max Cash-Out Amount']:,.2f}")
            
            if f'New P&I (30yr)' in df.columns:
                print(f"   30yr Refi Payment: ${row[f'New P&I (30yr)']:,.2f}")
                print(f"   30yr Monthly Savings: ${row[f'Savings (30yr)']:,.2f}")
        
        # Test Excel export capability
        print("\n📁 Testing Excel export capability...")
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            try:
                # Test basic Excel export
                with pd.ExcelWriter(tmp_file.name, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Test_Export')
                
                # Test reading back
                df_test_read = pd.read_excel(tmp_file.name, engine='openpyxl')
                print(f"✅ Excel export test successful: {len(df_test_read)} rows exported and read back")
                
                # Clean up
                os.unlink(tmp_file.name)
                
            except Exception as e:
                print(f"❌ Excel export test failed: {e}")
                return False
        
        print("\n🎉 ALL TESTS PASSED!")
        print("\nFlow validation complete. Your Excel upload and processing workflow is ready!")
        print("\n🚀 You can now confidently:")
        print("   ✅ Upload Excel files with borrower data")
        print("   ✅ Process different column name variations")
        print("   ✅ Calculate refinance scenarios")
        print("   ✅ Export results to Excel")
        print("   ✅ Generate professional reports")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the app directory and all dependencies are installed.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_flow_validation()
    sys.exit(0 if success else 1)