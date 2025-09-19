#!/usr/bin/env python3
"""
Test complete data flow: JPG → AI analysis → CSV parsing
"""
import sys
import os
import json
from pathlib import Path

# Add the project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.analyzers.agent2_drawing_analyzer import DrawingAnalysisAgent

def test_complete_jpg_analysis():
    """Test complete JPG analysis with enhanced HS prompts."""
    print("🔧 TESTING COMPLETE JPG ANALYSIS")
    print("="*50)
    
    # File paths
    jpg_file = "uploads/HS-53SA-05-no-hatch.jpg"
    json_file = "output/parameters/2.10_HS_parameters.json"
    
    # Check files exist
    if not os.path.exists(jpg_file):
        print(f"❌ JPG file not found: {jpg_file}")
        return False
    
    if not os.path.exists(json_file):
        print(f"❌ JSON file not found: {json_file}")
        return False
    
    print(f"✅ JPG file found: {jpg_file}")
    print(f"✅ JSON file found: {json_file}")
    
    # Initialize analyzer
    analyzer = DrawingAnalysisAgent()
    
    # Set HS domain (should auto-load enhanced prompts)
    print("\n🎯 Setting HS compliance domain...")
    success = analyzer.set_compliance_domain('hs_household_shelter')
    
    if not success:
        print("❌ Failed to set HS domain")
        return False
    
    # Check prompt lengths to confirm enhanced prompts loaded
    system_length = len(analyzer.prompt.get('system', ''))
    user_length = len(analyzer.prompt.get('user', ''))
    print(f"📏 System prompt: {system_length} characters (expected ~6886)")
    print(f"📏 User prompt: {user_length} characters (expected ~18698)")
    
    # Load parameters from JSON
    print("\n📋 Loading parameters from JSON...")
    params_df = analyzer.data_processor.load_parameters_from_json(json_file)
    if params_df is not None and not params_df.empty:
        param_count = len(params_df)
        print(f"✅ Loaded {param_count} parameters from JSON")
    else:
        print("❌ Failed to load parameters from JSON")
        return False
    
    # Analyze the JPG
    print(f"\n🖼️ Analyzing JPG: {jpg_file}")
    print("   This may take a moment...")
    
    # Get API key from environment
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        return False
    
    try:
        success, result = analyzer.analyze_drawings([jpg_file], json_file, api_key)
        
        if success and result:
            print("✅ Analysis completed successfully!")
            
            # Check result structure
            if 'csv_content' in result:
                csv_lines = result['csv_content'].split('\n')
                data_lines = [line for line in csv_lines 
                            if line.strip() and not line.strip().startswith('Parameter')]
                
                print(f"📊 CSV result has {len(data_lines)} data rows")
                
                if len(data_lines) > 0:
                    print("🎉 SUCCESS: Parameters found in analysis!")
                    print("\n📝 Sample results:")
                    for i, line in enumerate(data_lines[:5]):  # Show first 5
                        if line.strip():
                            print(f"   {i+1}. {line[:100]}...")  # First 100 chars
                    
                    if len(data_lines) > 5:
                        print(f"   ... and {len(data_lines) - 5} more rows")
                    
                    return True
                else:
                    print("⚠️ No parameter data found in CSV result")
                    print("📄 Raw CSV content preview:")
                    print(result['csv_content'][:500] + "...")
                    return False
            else:
                print("❌ No CSV content in result")
                print(f"📋 Result keys: {list(result.keys())}")
                return False
        else:
            if not success:
                print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
            else:
                print("❌ Analysis failed - no result returned")
            return False
            
    except Exception as e:
        print(f"❌ Analysis failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_complete_jpg_analysis()