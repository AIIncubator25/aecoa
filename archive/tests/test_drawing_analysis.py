"""
Test script to analyze drawings with AI directly
"""
import os
import sys
import pandas as pd
from pathlib import Path

# Add the current directory to Python path
sys.path.append('.')

from agents.analyzers.agent2_drawing_analyzer import DrawingAnalysisAgent

def test_drawing_analysis():
    """Test AI drawing analysis with current setup"""
    
    # Initialize agent
    agent = DrawingAnalysisAgent()
    agent.set_intelligent_mode()  # Use intelligent AI mode
    
    # Test with files in uploads directory first
    uploads_dir = Path("uploads")
    jpg_files = list(uploads_dir.glob("*.jpg"))
    dxf_files = list(uploads_dir.glob("*.dxf"))
    
    print(f"Found JPG files: {[f.name for f in jpg_files]}")
    print(f"Found DXF files: {[f.name for f in dxf_files]}")
    
    if not jpg_files:
        print("No JPG files found in uploads directory")
        return
    
    # Create test parameters
    test_params = pd.DataFrame({
        'parameter': [
            'hs_area_clear_ge_1500_mm_m2',
            'hs_enclosed_volume_m3', 
            'hs_ceiling_slab_thickness_mm',
            'vent_sleeve_wall_clearance_mm'
        ],
        'description': [
            'HS area with clear height ≥ 1500mm',
            'Total enclosed volume of HS',
            'Thickness of the HS ceiling slab',
            'Clearance from HS wall to nearest structural element'
        ],
        'value': ['', '', '', ''],
        'unit': ['m²', 'm³', 'mm', 'mm']
    })
    
    # Test DXF extraction
    if dxf_files:
        print("\n=== Testing DXF Text Extraction ===")
        for dxf_file in dxf_files[:1]:  # Test first DXF
            dxf_text = agent.extract_dxf_text(str(dxf_file))
            print(f"DXF {dxf_file.name}: {len(dxf_text) if dxf_text else 0} characters")
            if dxf_text and len(dxf_text) > 50:
                print(f"Preview: {dxf_text[:200]}...")
            else:
                print(f"Content: {dxf_text}")
    
    # Test with a simple custom prompt
    print("\n=== Testing AI Analysis ===")
    
    # Use environment variable or dummy key for testing
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("No OPENAI_API_KEY found in environment")
        print("Set your API key with: set OPENAI_API_KEY=your_key_here")
        return
    
    try:
        image_paths = [str(f) for f in jpg_files[:1]]  # Test with first image
        dxf_paths = [str(f) for f in dxf_files[:1]] if dxf_files else []
        
        success, result = agent._analyze_with_ai(test_params, image_paths, dxf_paths, api_key)
        
        print(f"Analysis success: {success}")
        if success:
            print("Analysis result keys:", list(result.keys()) if isinstance(result, dict) else "Not a dict")
            if 'compliance_summary' in result:
                summary = result['compliance_summary']
                print(f"Total parameters: {summary.get('total', 0)}")
                print(f"Compliant: {summary.get('compliant', 0)}")
                print(f"Non-compliant: {summary.get('non_compliant', 0)}")
                print(f"Not found: {summary.get('not_found', 0)}")
        else:
            print(f"Analysis failed: {result}")
            
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_drawing_analysis()