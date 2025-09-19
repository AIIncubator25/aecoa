#!/usr/bin/env python3
"""
Debug script to test AI parsing and see what's actually being returned.
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.analyzers.agent2_drawing_analyzer import DrawingAnalysisAgent
import pandas as pd

def test_ai_parsing_debug():
    """Test the AI parsing to see what's going wrong."""
    print("🔍 DEBUGGING AI PARSING ISSUE")
    print("="*60)
    
    # Initialize agent
    agent = DrawingAnalysisAgent()
    agent.set_compliance_domain('hs_household_shelter')
    agent.set_intelligent_mode(True)
    
    # Check if we have the test files
    test_image = "uploads/HS-53SA-05-no-hatch.jpg"
    test_csv = "uploads/2.10_HS.csv"
    
    if not os.path.exists(test_image):
        print(f"❌ Test image not found: {test_image}")
        return False
    
    if not os.path.exists(test_csv):
        print(f"❌ Parameters file not found: {test_csv}")
        return False
    
    print(f"✅ Test files found:")
    print(f"   - Image: {test_image}")
    print(f"   - Parameters: {test_csv}")
    
    # Check API key
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ No OpenAI API key found in environment")
        return False
    
    print(f"✅ API key found (length: {len(api_key)})")
    
    # Test the analysis
    print("\n🤖 TESTING AI ANALYSIS:")
    print("-" * 40)
    
    try:
        success, result = agent.analyze_drawings([test_image], test_csv, api_key)
        
        if success:
            print("✅ Analysis successful!")
            
            if 'comparisons_df' in result:
                df = result['comparisons_df']
                print(f"📊 DataFrame shape: {df.shape}")
                print(f"📝 Columns: {list(df.columns)}")
                
                # Check compliance status distribution
                if 'Compliance_Status' in df.columns:
                    status_counts = df['Compliance_Status'].value_counts()
                    print(f"📈 Status distribution:")
                    for status, count in status_counts.items():
                        print(f"   {status}: {count}")
                
                # Show first few rows for inspection
                print(f"\n📋 First 3 rows:")
                print(df.head(3).to_string())
                
                return True
            else:
                print("❌ No DataFrame in result")
                print(f"Result keys: {list(result.keys())}")
                return False
        else:
            print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"💥 Exception during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ai_parsing_debug()
    print("\n" + "="*60)
    if success:
        print("🎉 DEBUG COMPLETE - CHECK RESULTS ABOVE")
    else:
        print("💥 DEBUG FAILED - CHECK ERRORS ABOVE")