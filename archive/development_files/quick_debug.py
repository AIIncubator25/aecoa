#!/usr/bin/env python3
"""
Quick test to see what AI response looks like
"""
import os

# Check if there's a saved AI response or debug info
debug_file = "debug_agent2_prompts.txt"

if os.path.exists(debug_file):
    with open(debug_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 CHECKING AI PROMPT AND RESPONSE")
    print("="*50)
    
    # Check if there's a recent AI response - look for any CSV or JSON in recent files
    print("📋 DXF TEXT CONTENT SUMMARY:")
    if "DATA OF HOUSEHOLD SHELTER" in content:
        print("✅ Found HS data table reference")
    if "12.33" in content and "4.42" in content:
        print("✅ Found key area/volume values (12.33, 4.42)")  
    if "300 mm" in content:
        print("✅ Found 300mm thickness reference")
    if "AREA=4.42 SQ.M." in content:
        print("✅ Found specific area measurement")
    
    print("\n🤖 EXPECTED AI BEHAVIOR:")
    print("With this data, AI should return CSV with:")
    print("- HS Area: 4.42")
    print("- HS Volume: 12.33") 
    print("- HS Slab Thickness: 300")
    print("- Compliance Status: Compliant/Not Found")
    
    print("\n❓ LIKELY ISSUE:")
    print("AI might be returning the data but the parsing is failing")
    print("Need to check the _parse_ai_response_intelligent method")
    
else:
    print("No debug file found - run analysis first")