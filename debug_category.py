#!/usr/bin/env python3
"""
Comprehensive debugging script for the 'category' error
"""

import sys
import traceback
import pandas as pd
from agents.parsers.agent0_clause_parser import ClauseParser

def debug_category_error():
    print("🔍 Debugging the persistent 'category' error...")
    print("=" * 60)
    
    parser = ClauseParser()
    test_files = ['uploads/test_clause.csv', 'uploads/sample_2.10_HS.csv', 'uploads/2.10_HS.csv']
    
    for file_path in test_files:
        print(f"\n📄 Testing: {file_path}")
        print("-" * 40)
        
        try:
            # Test 1: Raw file reading
            print("1. Testing raw file reading...")
            with open(file_path, 'rb') as f:
                raw_content = f.read()
            print(f"   ✅ File size: {len(raw_content)} bytes")
            
            # Test 2: Basic pandas CSV reading
            print("2. Testing pandas CSV reading...")
            try:
                df = pd.read_csv(file_path)
                print(f"   ✅ DataFrame shape: {df.shape}")
                print(f"   ✅ Columns: {list(df.columns)}")
                print(f"   ✅ Data types: {df.dtypes.to_dict()}")
            except Exception as pandas_error:
                print(f"   ❌ Pandas error: {pandas_error}")
                print(f"   ❌ Error type: {type(pandas_error)}")
                
                # Try alternative pandas reading
                print("2b. Trying alternative pandas options...")
                try:
                    df = pd.read_csv(file_path, dtype=str, na_filter=False)
                    print(f"   ✅ Alternative reading success: {df.shape}")
                except Exception as alt_error:
                    print(f"   ❌ Alternative reading failed: {alt_error}")
                    continue
            
            # Test 3: Our enhanced text extraction
            print("3. Testing our enhanced text extraction...")
            try:
                result = parser._extract_text_from_file(raw_content, file_path)
                print(f"   ✅ Text extraction success: {len(result)} characters")
            except Exception as extract_error:
                print(f"   ❌ Text extraction error: {extract_error}")
                print(f"   ❌ Error type: {type(extract_error)}")
                traceback.print_exc()
            
            # Test 4: DataFrame to text conversion (if we got a DataFrame)
            if 'df' in locals():
                print("4. Testing DataFrame to text conversion...")
                try:
                    text_result = parser._dataframe_to_text(df, "TEST")
                    print(f"   ✅ DataFrame conversion success: {len(text_result)} characters")
                except Exception as df_error:
                    print(f"   ❌ DataFrame conversion error: {df_error}")
                    print(f"   ❌ Error type: {type(df_error)}")
                    traceback.print_exc()
                    
                    # Additional DataFrame debugging
                    print("4b. DataFrame detailed debugging...")
                    try:
                        print(f"   DataFrame info:")
                        print(f"   - Shape: {df.shape}")
                        print(f"   - Columns: {list(df.columns)}")
                        print(f"   - Index: {df.index}")
                        print(f"   - Memory usage: {df.memory_usage(deep=True).sum()} bytes")
                        
                        # Check for category dtype specifically
                        for col in df.columns:
                            dtype = df[col].dtype
                            print(f"   - Column '{col}': {dtype}")
                            if str(dtype) == 'category':
                                print(f"     WARNING: Found category dtype in column '{col}'")
                                print(f"     Categories: {df[col].cat.categories if hasattr(df[col], 'cat') else 'N/A'}")
                    except Exception as debug_error:
                        print(f"   ❌ DataFrame debugging error: {debug_error}")
                        traceback.print_exc()
            
        except Exception as overall_error:
            print(f"❌ OVERALL ERROR: {overall_error}")
            print(f"   Error type: {type(overall_error)}")
            traceback.print_exc()
        
        print("\n" + "=" * 60)
    
    print("\n🎯 Debug analysis complete!")

if __name__ == "__main__":
    debug_category_error()