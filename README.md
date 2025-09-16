# AECOA Compliance Checks

Automated regulatory compliance checking with **locally-hosted AI agents** for building drawings and requirements.

## Overview

This Streamlit application uses multiple AI agents powered by **locally-running Llama models** to automate compliance checking of building drawings (DXF) against regulatory requirements (Excel/PDF). The app follows a structured 3-step workflow with human-in-the-loop verification.

**🔒 Privacy First**: All AI processing happens locally on your computer - no cloud dependencies, no data sharing.

## Features

- **Multi-Agent Architecture**: 7 specialized AI agents for different tasks
- **Local AI Processing**: Llama models run on your own computer for privacy
- **3-Step Workflow**: Input → Process → Output with human gates
- **Template-Based**: JSON templates for different regulatory clauses
- **Comprehensive Reporting**: Text, PDF, and structured JSON outputs
- **Traceability**: Full audit trail with entity IDs and source references
- **Customizable AI**: Manage prompts, settings, and conversation history

## Prerequisites

⚠️ **Important**: This application requires local Llama models for AI functionality.

### System Requirements
- **RAM**: Minimum 8GB, Recommended 16GB+
- **Storage**: 10-20GB free space for AI models
- **OS**: Windows 10/11, macOS, or Linux

### Required Setup
1. **Install Ollama** (local AI runtime)
2. **Download Llama models** (one-time setup)
3. **Install Python dependencies**

📋 **See [LOCAL_LLAMA_SETUP.md](LOCAL_LLAMA_SETUP.md) for detailed installation instructions**

## Quick Start

### 1. Set Up Local AI (First Time Only)

Follow the [Local Llama Setup Guide](LOCAL_LLAMA_SETUP.md) to:
- Install Ollama
- Download Llama 3.2 model (~2GB)
- Test AI connection

### 2. Install AECOA
### 2. Install AECOA

```bash
# Clone the repository
git clone https://github.com/AIIncubator25/aecoa.git
cd aecoa

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Run Application

```bash
streamlit run app.py
```

### 4. Test AI Connection

1. Open your browser to `http://localhost:8501`
2. Go to "🎯 AI Management" tab → "⚙️ AI Settings"
3. Click "🔍 Test AI Connection"
4. Should show "✅ AI connection successful!"

## Architecture: Local AI Deployment

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User's        │    │   AECOA         │    │   Local Ollama  │
│   Browser       │◄───│   Streamlit     │◄───│   + Llama       │
│                 │    │   Application   │    │   Models        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                    │
                                              ┌─────▼─────┐
                                              │ User's    │
                                              │ Computer  │
                                              │ (Private) │
                                              └───────────┘
```

**Benefits**:
- 🔒 **Complete Privacy**: Data never leaves your computer
- 💰 **No Cloud Costs**: Free AI processing after setup
- 🌐 **Offline Capable**: Works without internet after initial setup
- ⚙️ **Full Control**: Customize AI models and settings

## Workflow

### Step 1: Input
- Upload requirements files (XLS/PDF) or use Google Drive integration
- Select regulatory clause template (e.g., HS_2.10.json)
- Upload drawing files (DXF/PDF)
- Human Gate A: Review and approve processed inputs

### Step 2: Process  
- Generate structured rules from requirements
- Evaluate compliance by comparing measured vs required values
- Generate explanations with clause citations
- Human Gate B: Verify accuracy before proceeding

### Step 3: Output
- Generate summary and detailed reports
- Create PDF deliverables with evidence
- Export structured JSON for integration
- Human Gate C: Final approval and run freeze

## Agent Architecture

| Agent | Type | Model | Purpose |
|-------|------|-------|---------|
| Agent_Requirements | LLM + RAG | Llama 4 | Clause resolution, normalization |
| Agent_Instructions | LLM | Llama 4 | Template creation & management |
| Agent_DXF_Metrics | Code + VLM | ezdxf/shapely/LLaVA | DXF parsing & measurement |
| Agent_Rule_Interpreter | LLM | Llama 4 | Rules structuring |
| Agent_Evaluator | Code | Python | Compliance checking |
| Agent_Explainer | LLM | Llama 4 | Compliance explanation |
| Agent_Reporting | LLM + Code | Llama 4/ReportLab | Report generation |

## Folder Structure

```
aecoa/
├── app.py                      # Streamlit entry point
├── agents/                     # AI agent modules
│   ├── agent_requirements.py   # Requirements processing
│   ├── agent_instructions.py   # Template management
│   ├── agent_dxf_metrics.py    # DXF parsing & metrics
│   ├── agent_rule_interpreter.py # Rule structuring
│   ├── agent_evaluator.py      # Compliance evaluation
│   ├── agent_explainer.py      # Result explanation
│   └── agent_reporting.py      # Report generation
├── instructions/               # JSON templates
│   └── HS_2.10.json           # HS Clause 2.10 template
├── data/                      # Sample input data
│   ├── requirement.txt        # Sample requirements
│   └── drawing.txt           # Sample drawing data
├── runs/                      # Time-stamped output folders
│   └── {timestamp}_{jobid}/
│       ├── ingest/           # Step 1 outputs
│       ├── validate/         # Step 2 outputs
│       └── report/           # Step 3 outputs
├── requirements.txt           # Python dependencies
├── compare.txt               # Latest comparison results
└── report.txt               # Latest compliance report
```

## Example: HS Clause 2.10

The application includes a working example for **HS Clause 2.10 - Household Shelter Beneath Internal Staircase**:

### Fixed Requirements
- Clear height: ≥ 1500 mm
- Ceiling slab thickness: ≥ 300 mm  
- Floor slab thickness: ≥ 200 mm
- Ventilation clearance: ≥ 700 mm
- Door clearance: ≥ 300 mm

### GFA-Based Requirements
| GFA Range (m²) | HS Floor Area (m²) | HS Volume (m³) |
|----------------|-------------------|----------------|
| [0, 40)        | 1.44             | 3.6            |
| [40, 45)       | 1.60             | 3.6            |
| [45, 75)       | 2.20             | 5.4            |
| [75, 140)      | 2.80             | 7.2            |
| [140, ∞)       | 3.40             | 9.0            |

## Google Drive Integration

The application supports Google Drive integration for requirements, drawings, and templates:

- **Requirements**: `https://drive.google.com/drive/folders/1lYeXIHR37vSRqAx4dolRTmp5i8JBZzYO`
- **Drawings**: `https://drive.google.com/drive/folders/1YvxYYUjsbMaoFY14g7_I3Pdi8L89ZsK2`  
- **Instructions**: `https://drive.google.com/drive/folders/1Uwp7A89O1furkzPWTUIUhu7H_z3UOrhE`
- **AI Models**: `https://drive.google.com/drive/folders/1OE95GaUuOr9d7flg961FH-vp7ZwgnUxz`

## Local Llama 4 Setup

If using local Llama 4, ensure it's installed at:
```
C:\Users\young\.ollama\models\manifests\registry.ollama.ai\library\llama4
```

## Sample Data

The application includes sample data for testing:
- Requirements: Extracted from `TRHS_2.10.xlsx` and `Figure_2.10.pdf`
- Drawings: Extracted from `HS-53SA-2FP.dxf` (plan) and `HS-53SA-05.dxf` (details)

## Output Files

Each run generates:
- `requirements_index.json` - Structured requirements data
- `drawing_parsed.json` - Extracted measurements with entity IDs
- `rules_structured.json` - Structured compliance rules
- `checks_results.json` - Detailed compliance results
- `report_summary.txt` - Executive summary (≤200 words)
- `report.txt` - Detailed findings and recommendations
- `report.pdf` - Professional report with evidence
- `report_bundle.json` - Structured export for integration

## Adding New Clauses

To support new regulatory clauses:

1. Create new JSON template in `instructions/` folder
2. Define extraction prompts, rules, and schemas
3. Template automatically loaded in UI
4. No Python code changes required

## Development

The application is designed for modularity and extensibility:

- Each agent is self-contained in its own module
- JSON schemas enforce data validation
- Templates enable rule-based configuration
- Comprehensive logging and error handling

## Dependencies

Key dependencies:
- `streamlit` - Web application framework
- `ezdxf` - DXF file parsing
- `shapely` - Geometric operations
- `reportlab` - PDF generation
- `ollama` - Llama 4 model interface
- `pandas` - Data manipulation
- `jsonschema` - Schema validation

## Contributing

1. Fork the repository
2. Create feature branch
3. Implement changes with tests
4. Submit pull request

## License

MIT License - See LICENSE file for details.

## Support

For issues and questions:
- GitHub Issues: [https://github.com/AIIncubator25/aecoa/issues](https://github.com/AIIncubator25/aecoa/issues)
- Documentation: See this README and inline code comments
