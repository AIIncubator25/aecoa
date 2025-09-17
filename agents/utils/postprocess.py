from __future__ import annotations
from typing import Dict, Any, List, Optional
import pandas as pd
from pathlib import Path
import yaml

# Standard compliance schema for AEC household shelter requirements
STANDARD_CSV_SCHEMA = {
    "columns_pretty": [
        "No", "Clause", "Parameter", "Min. Rectilinear HS Countable Area", 
        "Min. Irregular HS Countable Area", "Unit", "Min. Volume (m3)",
        "identified value", "source", "compliance"
    ],
    "columns": [
        "no", "clause", "parameter", "min_rectilinear_hs_countable_area",
        "min_irregular_hs_countable_area", "unit", "min_volume_m3",
        "identified_value", "source", "compliance"
    ],
    "rows": [
        {"no": 1, "clause": "2.10 (a) & (b)", "parameter": "HS Floor Area for GFA Under 40", "min_rectilinear_hs_countable_area": 1.44, "min_irregular_hs_countable_area": "1.08 (3*0.36)", "unit": "m2", "min_volume_m3": 3.6},
        {"no": 2, "clause": "2.10 (a) & (b)", "parameter": "HS Floor Area for 40 < GFA < 45", "min_rectilinear_hs_countable_area": 1.6, "min_irregular_hs_countable_area": "1.08 (3*0.36)", "unit": "m2", "min_volume_m3": 3.6},
        {"no": 3, "clause": "2.10 (a) & (b)", "parameter": "HS Floor Area for 45 < GFA < 75", "min_rectilinear_hs_countable_area": 2.2, "min_irregular_hs_countable_area": "1.44 (4*0.36)", "unit": "m2", "min_volume_m3": 5.4},
        {"no": 4, "clause": "2.10 (a) & (b)", "parameter": "HS Floor Area for 75 < GFA < 140", "min_rectilinear_hs_countable_area": 2.8, "min_irregular_hs_countable_area": "1.8 (5*0.36)", "unit": "m2", "min_volume_m3": 7.2},
        {"no": 5, "clause": "2.10 (a) & (b)", "parameter": "HS Floor Area for GFA above 140", "min_rectilinear_hs_countable_area": 3.4, "min_irregular_hs_countable_area": "2.16 (6*0.36)", "unit": "m2", "min_volume_m3": 9.0},
        {"no": 6, "clause": "2.10 (a)", "parameter": "Height Clearance Requirement", "min_rectilinear_hs_countable_area": 1500, "min_irregular_hs_countable_area": 1500, "unit": "mm", "min_volume_m3": "na"},
        {"no": 7, "clause": "2.10 (c)", "parameter": "HS ceiling slab", "min_rectilinear_hs_countable_area": 300, "min_irregular_hs_countable_area": 300, "unit": "mm", "min_volume_m3": "na"},
        {"no": 8, "clause": "2.10 (c)", "parameter": "waist of the staircase", "min_rectilinear_hs_countable_area": 300, "min_irregular_hs_countable_area": 300, "unit": "mm", "min_volume_m3": "na"},
        {"no": 9, "clause": "2.10 (d)", "parameter": "unobstructed distance from the HS wall with ventilation sleeve opening", "min_rectilinear_hs_countable_area": 700, "min_irregular_hs_countable_area": 700, "unit": "mm", "min_volume_m3": "na"}
    ]
}

def build_result_bundle(yaml_text: Optional[str], extracted: Dict[str, Any]) -> Dict[str, Any]:
    """Build complete result bundle with compliance analysis"""
    
    # Use YAML schema if provided, otherwise use standard schema
    schema = STANDARD_CSV_SCHEMA
    if yaml_text:
        try:
            yaml_obj = yaml.safe_load(yaml_text)
            if isinstance(yaml_obj, dict) and 'csv_schema' in yaml_obj:
                schema = yaml_obj['csv_schema']
        except Exception:
            pass
    
    # Extract analysis results from AI response
    analysis_results = []
    if isinstance(extracted, dict) and 'analysis_results' in extracted:
        analysis_results = extracted['analysis_results']
    
    # Build the compliance DataFrame
    df_rows = []
    base_rows = schema.get('rows', STANDARD_CSV_SCHEMA['rows'])
    
    for base_row in base_rows:
        # Start with the base row data
        row = base_row.copy()
        
        # Find matching analysis result by row number
        analysis_match = None
        for result in analysis_results:
            if result.get('no') == base_row.get('no'):
                analysis_match = result
                break
        
        # Populate the last 3 columns
        if analysis_match:
            row['identified_value'] = analysis_match.get('identified_value', 'not found')
            row['source'] = analysis_match.get('source', 'not analyzed')
            row['compliance'] = analysis_match.get('compliance', '− Not checked')
        else:
            row['identified_value'] = 'not found'
            row['source'] = 'not analyzed'
            row['compliance'] = '− Not checked'
        
        df_rows.append(row)
    
    # Create DataFrame with pretty column names
    columns = schema.get('columns_pretty', STANDARD_CSV_SCHEMA['columns_pretty'])
    df = pd.DataFrame(df_rows)
    
    # Fix mixed data types to prevent PyArrow serialization errors
    # Convert all columns to string first to handle mixed types
    for col in df.columns:
        df[col] = df[col].astype(str)
    
    # Replace pandas NaN representations with empty strings
    df = df.replace(['nan', 'None', 'NaN'], '', regex=False)
    
    # Reorder columns to match the expected order
    if len(columns) == len(df.columns):
        df.columns = columns
    
    # Save CSV
    try:
        df.to_csv("comparisons.csv", index=False)
    except Exception:
        pass
    
    # Tables passthrough from extracted data
    tables = []
    try:
        if isinstance(extracted, dict):
            if isinstance(extracted.get('tables'), list):
                for t in extracted['tables']:
                    if isinstance(t, dict):
                        hdrs = t.get('headers')
                        if isinstance(hdrs, list):
                            t['headers'] = [str(h) for h in hdrs]
                        tables.append(t)
    except Exception:
        pass
    
    return {
        "extracted": extracted, 
        "comparisons": df, 
        "tables": tables,
        "schema_used": "yaml" if yaml_text else "standard",
        "analysis_summary": extracted.get('summary', 'No summary provided') if isinstance(extracted, dict) else "Analysis completed"
    }
