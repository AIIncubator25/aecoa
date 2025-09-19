#!/usr/bin/env python3
"""
Demo: Adding New Compliance Types to Agent 2
Shows how to extend the system for new compliance domains.
"""

import pandas as pd
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.analyzers.agent2_drawing_analyzer import DrawingAnalysisAgent

def demo_add_energy_efficiency_compliance():
    """Demo adding a new energy efficiency compliance type."""
    print("🔧 DEMO: Adding Energy Efficiency Compliance Type")
    print("=" * 50)
    
    # Create an agent instance
    agent = DrawingAnalysisAgent()
    
    # Add a new compliance template dynamically
    energy_template = {
        'name': 'Energy Efficiency Analysis',
        'key_columns': [
            'No', 'Clause', 'Parameter', 'Required_Value', 'Found_Value', 
            'Unit', 'U_Value', 'R_Value', 'Thermal_Performance', 
            'Compliance_Status', 'Reference_Drawing', 'Notes'
        ],
        'domain_patterns': {
            'U_Value': ['u value', 'u-value', 'thermal transmittance', 'heat transfer coefficient'],
            'R_Value': ['r value', 'r-value', 'thermal resistance', 'insulation value'],
            'Thermal_Performance': ['thermal performance', 'energy performance', 'thermal efficiency'],
            'Glazing_Ratio': ['glazing ratio', 'window wall ratio', 'window area ratio'],
            'Shading_Coefficient': ['shading coefficient', 'solar heat gain', 'shgc']
        }
    }
    
    # Add the template to the agent
    agent.compliance_templates['energy_efficiency'] = energy_template
    
    print("✅ Added energy efficiency template")
    print(f"📋 Available domains: {list(agent.compliance_templates.keys())}")
    
    # Test with sample energy efficiency data
    energy_data = {
        'item no': [1, 2, 3],
        'building code': ['J1.5', 'J2.3', 'J3.1'],
        'criteria': ['Wall U-Value', 'Window R-Value', 'Thermal Bridge'],
        'u-value': [0.25, 'N/A', 'N/A'],
        'thermal resistance': ['N/A', 3.5, 'N/A'],
        'thermal performance': ['N/A', 'N/A', 'Good'],
        'assessment': ['Compliant', 'Compliant', 'Not Found'],
        'drawing source': ['Wall-Detail', 'Window-Schedule', 'Thermal-Plan'],
        'analysis notes': ['Meets standard', 'High performance glazing', 'Need more info']
    }
    
    df = pd.DataFrame(energy_data)
    print(f"\n📊 Original data columns: {list(df.columns)}")
    
    # Set the domain and test column mapping
    agent.set_compliance_domain('energy_efficiency')
    standardized_df = agent._standardize_columns_intelligently(df)
    
    print(f"✅ Standardized columns: {list(standardized_df.columns)}")
    
    # Check if domain-specific patterns worked
    domain_success = (
        'U_Value' in standardized_df.columns and
        'R_Value' in standardized_df.columns and
        'Thermal_Performance' in standardized_df.columns
    )
    
    if domain_success:
        print("🎉 Energy efficiency domain patterns working!")
        print(f"📋 Sample standardized data:")
        print(standardized_df.head(3).to_string(index=False))
    else:
        print("⚠️ Energy efficiency patterns need refinement")
    
    return domain_success

def demo_add_mep_compliance():
    """Demo adding MEP (Mechanical, Electrical, Plumbing) compliance."""
    print("\n🔧 DEMO: Adding MEP Compliance Type")
    print("=" * 50)
    
    agent = DrawingAnalysisAgent()
    
    # Add MEP template
    mep_template = {
        'name': 'MEP Systems Analysis',
        'key_columns': [
            'No', 'Clause', 'Parameter', 'Required_Value', 'Found_Value',
            'Unit', 'Flow_Rate', 'Pressure', 'Load_Capacity', 'Efficiency',
            'Compliance_Status', 'Reference_Drawing', 'Notes'
        ],
        'domain_patterns': {
            'Flow_Rate': ['flow rate', 'air flow', 'water flow', 'ventilation rate'],
            'Pressure': ['pressure', 'static pressure', 'water pressure', 'air pressure'],
            'Load_Capacity': ['electrical load', 'cooling load', 'heating load', 'power capacity'],
            'Efficiency': ['efficiency', 'cop', 'energy efficiency ratio', 'performance'],
            'Pipe_Size': ['pipe size', 'duct size', 'conduit size', 'diameter'],
            'Temperature': ['temperature', 'supply temp', 'return temp', 'ambient temp']
        }
    }
    
    agent.compliance_templates['mep_systems'] = mep_template
    print("✅ Added MEP systems template")
    
    # Test with MEP data
    mep_data = {
        'system no': [1, 2, 3, 4],
        'mep code': ['M1.1', 'E2.3', 'P1.5', 'H3.2'],
        'specification': ['HVAC Flow Rate', 'Electrical Load', 'Water Pressure', 'Heating Efficiency'],
        'air flow': [500, 'N/A', 'N/A', 'N/A'],
        'power capacity': ['N/A', 100, 'N/A', 'N/A'],
        'water pressure': ['N/A', 'N/A', 350, 'N/A'],
        'cop': ['N/A', 'N/A', 'N/A', 4.2],
        'check result': ['Compliant', 'Compliant', 'Non-Compliant', 'Compliant'],
        'plan ref': ['HVAC-01', 'Electrical-02', 'Plumbing-01', 'Heating-Detail'],
        'engineering notes': ['Adequate CFM', 'Within capacity', 'Low pressure', 'High efficiency']
    }
    
    df = pd.DataFrame(mep_data)
    print(f"\n📊 Original MEP columns: {list(df.columns)}")
    
    agent.set_compliance_domain('mep_systems')
    standardized_df = agent._standardize_columns_intelligently(df)
    
    print(f"✅ Standardized columns: {list(standardized_df.columns)}")
    
    # Check MEP-specific patterns
    mep_success = (
        'Flow_Rate' in standardized_df.columns and
        'Load_Capacity' in standardized_df.columns and
        'Pressure' in standardized_df.columns
    )
    
    if mep_success:
        print("🎉 MEP systems domain patterns working!")
        print(f"📋 Sample MEP data:")
        print(standardized_df.head(3).to_string(index=False))
    else:
        print("⚠️ MEP patterns need refinement")
    
    return mep_success

def main():
    """Run the demo showing how to extend the system."""
    print("🚀 AGENT 2 EXTENSIBILITY DEMO")
    print("Showing how to add new compliance types to the agnostic system")
    print("=" * 70)
    
    results = []
    results.append(demo_add_energy_efficiency_compliance())
    results.append(demo_add_mep_compliance())
    
    # Summary
    print("\n" + "=" * 70)
    print("🎯 EXTENSIBILITY DEMO RESULTS:")
    print(f"✅ Energy Efficiency: {'SUCCESS' if results[0] else 'NEEDS WORK'}")
    print(f"✅ MEP Systems: {'SUCCESS' if results[1] else 'NEEDS WORK'}")
    
    if all(results):
        print("\n🎉 DEMO COMPLETE: System successfully extended with new compliance types!")
        print("\n💡 KEY TAKEAWAYS:")
        print("   • No hardcoded mappings - AI adapts to new domains")
        print("   • Template-based approach allows easy extension")
        print("   • Domain-specific patterns improve accuracy")
        print("   • Universal patterns ensure compatibility")
        print("\n🔧 TO ADD NEW COMPLIANCE TYPE:")
        print("   1. Define template with key_columns and domain_patterns")
        print("   2. Add to agent.compliance_templates dictionary")
        print("   3. Use agent.set_compliance_domain('your_domain')")
        print("   4. System automatically handles column mapping")
    else:
        print("\n⚠️ Some extensions need refinement, but core system is working!")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)