#!/usr/bin/env python3
"""
Test script for the combined Agent 3 (Executive Reporter with Insights)
"""
import os
import sys
from pathlib import Path
import pandas as pd

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_combined_agent3():
    """Test the combined Agent 3 implementation."""
    print("🚀 TESTING COMBINED AGENT 3 (EXECUTIVE REPORTER + INSIGHTS)")
    print("=" * 70)
    
    # Import the combined Agent 3
    try:
        from agents.reporters.agent3_combined_reporter import CombinedExecutiveReporter
        print("✅ Successfully imported CombinedExecutiveReporter")
    except ImportError as e:
        print(f"❌ Error importing CombinedExecutiveReporter: {e}")
        return False
    
    # Load API key
    api_key = get_api_key()
    if not api_key:
        print("❌ Failed to get API key")
        return False
    print("✅ API key loaded")
    
    # Check if comparisons.csv exists
    comparison_path = "output/comparison.csv"
    if not os.path.exists(comparison_path):
        print(f"❌ Comparison file not found: {comparison_path}")
        return False
    print(f"✅ Found comparison file: {comparison_path}")
    
    # Initialize the combined reporter
    reporter = CombinedExecutiveReporter()
    print("✅ Initialized CombinedExecutiveReporter")
    
    # Process the compliance report
    print("\n🔍 Processing compliance report...")
    result = reporter.process_compliance_report(comparison_path, api_key)
    
    # Check if executive report was generated
    if result.get('report_success', False):
        print("✅ Executive report generated successfully")
        report_path = "output/executive_report.txt"
        if os.path.exists(report_path):
            print(f"✅ Executive report saved to {report_path}")
            # Get file size
            size_kb = os.path.getsize(report_path) / 1024
            print(f"   Report size: {size_kb:.1f} KB")
            
            # Get word count
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
                word_count = len(content.split())
                print(f"   Word count: {word_count}")
    else:
        print(f"❌ Executive report generation failed: {result.get('error', 'Unknown error')}")
    
    # Check if insights were generated
    if result.get('insights_success', False):
        print("\n✅ Insights generated successfully")
        insights_path = "output/insights.csv"
        if os.path.exists(insights_path):
            print(f"✅ Insights saved to {insights_path}")
            
            # Read and display insights
            try:
                insights_df = pd.read_csv(insights_path)
                print(f"   Insights count: {len(insights_df)}")
                print("\n📊 INSIGHTS PREVIEW:")
                print(insights_df.head().to_string())
            except Exception as e:
                print(f"❌ Error reading insights file: {e}")
    else:
        print(f"\n❌ Insights generation failed: {result.get('error', 'Unknown error')}")
    
    print("\n=" * 70)
    success = result.get('report_success', False) and result.get('insights_success', False)
    if success:
        print("🎉 COMBINED AGENT 3 TEST: SUCCESS")
        print("   ✅ Both executive report and insights generated successfully")
    else:
        print("❌ COMBINED AGENT 3 TEST: FAILURE")
        print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
    
    return success

def get_api_key():
    """Get OpenAI API key from environment variables or secrets.toml."""
    # First try environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    
    # If not found, try to read from .streamlit/secrets.toml
    if not api_key:
        try:
            secrets_path = Path(".streamlit/secrets.toml")
            if secrets_path.exists():
                with open(secrets_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                lines = content.split('\n')
                in_openai_section = False
                for line in lines:
                    line = line.strip()
                    if line == '[openai]':
                        in_openai_section = True
                        continue
                    if in_openai_section and line.startswith('api_key'):
                        api_key = line.split('=')[1].strip().strip('"')
                        break
                    if line.startswith('[') and line != '[openai]':
                        in_openai_section = False
        except Exception as e:
            print(f"Error reading secrets file: {e}")
    
    return api_key

if __name__ == "__main__":
    success = test_combined_agent3()
    sys.exit(0 if success else 1)