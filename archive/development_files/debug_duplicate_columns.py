#!/usr/bin/env python3
"""
Debug script to identify duplicate column issues in Agent 2 analysis.
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.analyzers.agent2_drawing_analyzer import DrawingAnalysisAgent

def test_column_mapping():
    """Test the column mapping for duplicates."""
    print("🔍 DEBUGGING DUPLICATE COLUMN ISSUE")
    print("="*50)
    
    # Initialize analyzer
    analyzer = DrawingAnalysisAgent()
    
    # Test HS domain
    analyzer.set_compliance_domain('hs_household_shelter')
    
    # Check templates
    print("📋 COMPLIANCE TEMPLATE COLUMNS:")
    template = analyzer.compliance_templates['hs_household_shelter']
    columns = template['key_columns']
    
    for i, col in enumerate(columns):
        print(f"   {i+1:2}. {col}")
    
    # Check for duplicates
    duplicates = []
    unique_columns = set()
    for col in columns:
        if col in unique_columns:
            duplicates.append(col)
        unique_columns.add(col)
    
    if duplicates:
        print(f"\n❌ DUPLICATES FOUND: {duplicates}")
    else:
        print("\n✅ NO DUPLICATES IN TEMPLATE")
    
    print("\n" + "="*50)
    print("🔧 COLUMN MAPPING LOGIC:")
    
    # Test column mapping
    test_columns = ['Unit', 'unit', 'Unit_Area', 'Parameter', 'parameter']
    standardized = analyzer._standardize_columns_intelligently(test_columns)
    
    print("Original → Standardized:")
    for orig, std in zip(test_columns, standardized):
        print(f"   {orig} → {std}")
    
    # Check for duplicates in standardized
    std_duplicates = []
    std_unique = set()
    for col in standardized:
        if col in std_unique:
            std_duplicates.append(col)
        std_unique.add(col)
    
    if std_duplicates:
        print(f"\n❌ DUPLICATES IN STANDARDIZED: {std_duplicates}")
    else:
        print("\n✅ NO DUPLICATES IN STANDARDIZED")

if __name__ == "__main__":
    test_column_mapping()