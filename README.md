# 🏢 AECOA - AI-Enhanced Compliance and Operations Assistant

**Automated regulatory compliance checking with locally-hosted AI agents** for building drawings and requirements.

## 🎯 Overview

This Streamlit application uses multiple AI agents powered by **locally-running Llama models** to automate compliance checking of building drawings (DXF) against regulatory requirements (Excel/PDF). The app follows a structured 3-step workflow with human-in-the-loop verification.

**🔒 Privacy First**: All AI processing happens locally on your computer - no cloud dependencies, no data sharing.

## ✨ Features

- **🤖 Multi-Agent Architecture**: 7+ specialized AI agents for different compliance tasks
- **🖥️ Local AI Processing**: Llama models run on your own computer for complete privacy
- **☁️ Multi-Provider AI Support**: Local Ollama, OpenAI, and GovTech AI models
- **🔑 BYOK (Bring Your Own Key)**: Use your own API keys for cloud providers
- **📋 3-Step Workflow**: Input → Process → Output with human verification gates
- **📄 Template-Based**: JSON/YAML templates for different regulatory clauses
- **📊 Comprehensive Reporting**: Text, PDF, and structured JSON outputs
- **🔍 Full Traceability**: Complete audit trail with entity IDs and source references
- **⚙️ Customizable AI**: Manage prompts, settings, and conversation history
- **🔐 Secure Authentication**: User management and session handling
- **🔄 Flexible I/O**: Advanced file handling and data processing utilities

## 📋 Prerequisites

⚠️ **Important**: This application requires local Llama models for AI functionality.

### 💻 System Requirements
- **RAM**: Minimum 8GB, Recommended 16GB+
- **Storage**: 10-20GB free space for AI models
- **OS**: Windows 10/11, macOS, or Linux
- **Python**: 3.8+ recommended

### 🔧 Required Setup
1. **Install Ollama** (local AI runtime) - Optional for cloud-only usage
2. **Download Llama models** (one-time setup) - Optional for cloud-only usage  
3. **Install Python dependencies**
4. **Configure authentication** (optional)
5. **Set up API keys** for your chosen AI providers (BYOK)

📋 **See [LOCAL_LLAMA_SETUP.md](LOCAL_LLAMA_SETUP.md) for detailed installation instructions**

## 🚀 Quick Start

### 1️⃣ Set Up AI Providers (Choose Your Approach)

**Option A: Local AI Only (Free & Private)**
- Follow the [Local Llama Setup Guide](LOCAL_LLAMA_SETUP.md)
- Install Ollama and download Llama 3.2 model (~2GB)
- Test AI connection

**Option B: Cloud AI with BYOK**  
- Get API keys from OpenAI and/or GovTech
- Configure in `.streamlit/secrets.toml`
- No local installation required

**Option C: Hybrid Approach (Recommended)**
- Set up both local and cloud providers
- Use local for privacy-sensitive tasks
- Use cloud for enhanced performance

### 2️⃣ Install AECOA

```bash
# Clone the repository
git clone https://github.com/AIIncubator25/aecoa.git
cd aecoa

# Install Python dependencies
pip install -r requirements.txt
```

### 3️⃣ Run Application

```bash
streamlit run app.py
```

### 4️⃣ Test AI Connection

1. Open your browser to `http://localhost:8501`
2. Go to "🎯 AI Management" tab → "⚙️ AI Settings"
3. Select your preferred AI provider (Ollama/OpenAI/GovTech)
4. Click "🔍 Test AI Connection"
5. Should show "✅ AI connection successful!" for your chosen provider(s)

## 🔐 Authentication & Configuration

The application includes robust authentication and configuration management:

- **`auth.py`**: Handles user authentication and session management
- **`io_utils.py`**: Provides I/O utilities for file handling and data processing
- **`.streamlit/secrets.toml`**: Stores API keys and sensitive configuration (not tracked)
- **Key management**: Google Cloud service account credentials via `key.json`

### Streamlit Configuration

Create a `.streamlit/secrets.toml` file for your API keys and settings:

```toml
# 🔑 BYOK - Bring Your Own Keys
# Choose your preferred AI provider(s)

# OpenAI Configuration
[openai]
api_key = "sk-your_openai_api_key_here"
model = "gpt-4o"  # Latest: gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo
base_url = "https://api.openai.com/v1"

# GovTech AI Configuration
[govtech]
api_key = "your_govtech_api_key_here"
model = "govtech-llm-v1"  # Check GovTech documentation for available models
base_url = "https://api.govtech.ai/v1"  # Update with actual GovTech endpoint

# Local AI Settings (Ollama)
[ollama]
host = "http://localhost:11434"
model = "llama3.2:latest"
timeout = 60

# Default Provider Selection
[ai_provider]
primary = "ollama"  # Options: "ollama", "openai", "govtech"
fallback = "openai"  # Fallback if primary fails

# Authentication Settings
[auth]
enabled = true
method = "google"  # or "local", "oauth"

# Google Drive Integration
[gdrive]
enabled = true
credentials_file = "key.json"

# Application Settings
[app]
max_file_size_mb = 100
allowed_extensions = ["pdf", "dxf", "xlsx", "docx"]
debug_mode = false

# Model Performance Settings
[performance]
# Recommended model configurations by use case:
# For speed: gpt-4o-mini, gpt-3.5-turbo
# For accuracy: gpt-4o, gpt-4-turbo  
# For cost-efficiency: gpt-4o-mini, ollama
temperature = 0.1  # Lower for more consistent compliance analysis
max_tokens = 4000  # Adjust based on your needs
```

### 🔑 BYOK (Bring Your Own Key) Setup

The application supports multiple AI providers with your own API keys:

#### 🖥️ **Local AI (Ollama) - Free & Private**
```bash
# Install Ollama
# Download models locally - no API key needed
ollama pull llama3.2
```

#### ☁️ **OpenAI - Cloud-based**
1. Get API key from [OpenAI Platform](https://platform.openai.com/)
2. Add to `.streamlit/secrets.toml` under `[openai]` section
3. **Latest Models Available:**
   - **`gpt-4o`** - Most capable model (recommended)
   - **`gpt-4o-mini`** - Fast and cost-effective
   - **`gpt-4-turbo`** - High performance with vision
   - **`gpt-3.5-turbo`** - Budget-friendly option

#### 🏛️ **GovTech AI - Government-grade**
1. Register for GovTech AI services
2. Obtain API credentials from GovTech portal
3. Configure in `.streamlit/secrets.toml` under `[govtech]` section
4. Supports government-specific compliance models

### 🔄 Provider Selection

You can configure multiple providers and switch between them:

```python
# In the application UI:
# Settings → AI Provider → Select Primary/Fallback
```

### 🎯 Model Selection Guide

**For Maximum Accuracy (Compliance Analysis):**
- **Primary**: `gpt-4o` (OpenAI) or `llama3.2` (Local)
- **Use Case**: Critical compliance checks, legal document analysis

**For Best Performance (Speed + Quality):**
- **Primary**: `gpt-4o-mini` (OpenAI) 
- **Use Case**: General document processing, routine checks

**For Cost Optimization:**
- **Primary**: `llama3.2` (Local) with `gpt-4o-mini` (Fallback)
- **Use Case**: High-volume processing, budget-conscious deployments

**For Government/Regulatory:**
- **Primary**: GovTech models or Local Ollama
- **Use Case**: Sensitive documents, government compliance

**Provider Benefits:**
- **🖥️ Ollama**: Complete privacy, no costs, offline capable
- **☁️ OpenAI**: High performance, latest GPT-4o models, vision capabilities  
- **🏛️ GovTech**: Government compliance, regulatory-specific models

## 🏗️ Architecture: Local AI Deployment

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User's        │    │   AECOA         │    │   AI Providers  │
│   Browser       │◄───│   Streamlit     │◄───│   • Local Ollama│
│                 │    │   Application   │    │   • OpenAI API  │
└─────────────────┘    └─────────────────┘    │   • GovTech AI  │
                                              └─────────────────┘
                                                    │
                                              ┌─────▼─────┐
                                              │ BYOK      │
                                              │ (Your     │
                                              │  API Keys)│
                                              └───────────┘
```

**✨ Benefits**:
- 🔒 **Complete Privacy**: Data never leaves your computer (with Ollama)
- 💰 **Flexible Costs**: Free local processing or pay-per-use cloud APIs
- 🌐 **Multi-Provider**: Switch between local, commercial, and government AI
- ⚙️ **Full Control**: Use your own API keys and choose providers
- 🏛️ **Government Ready**: GovTech compliance for regulatory requirements

## 🔄 Workflow

### 📥 Step 1: Input
- Upload requirements files (XLS/PDF) or use Google Drive integration
- Select regulatory clause template (e.g., HS_2.10.json)
- Upload drawing files (DXF/PDF)
- Human Gate A: Review and approve processed inputs

### ⚙️ Step 2: Process  
- Generate structured rules from requirements
- Evaluate compliance by comparing measured vs required values
- Generate explanations with clause citations
- Human Gate B: Verify accuracy before proceeding

### 📤 Step 3: Output
- Generate summary and detailed reports
- Create PDF deliverables with evidence
- Export structured JSON for integration
- Human Gate C: Final approval and run freeze

## 🤖 Agent Architecture

| Agent | Type | Model | Purpose |
|-------|------|-------|---------|
| **Agent 1 - Parameter Definition** | LLM + RAG | Llama 3.2 / OpenAI / GovTech | Extract and define parameters from requirements |
| **Agent 1 - YAML Extractor** | LLM | Llama 3.2 / OpenAI / GovTech | Extract structured YAML from documents |
| **Agent 2 - Drawing Analyzer** | Code + VLM | ezdxf/shapely/LLaVA | DXF parsing & measurement analysis |
| **Agent 3 - Compliance Comparison** | LLM + Code | Llama 3.2 / OpenAI / GovTech | Compare requirements vs measurements |
| **Agent 3 - Executive Reporter** | LLM | Llama 3.2 / OpenAI / GovTech | Generate executive summaries |
| **Agent 4 - Insights Report** | LLM + Code | Llama 3.2 / OpenAI / GovTech | Advanced analytics and insights |
| **Orchestrator** | Coordinator | Python | Workflow management and agent coordination |
| **Providers** | Interface | Python | Multi-provider LLM abstractions (Local/OpenAI/GovTech) |

## 📁 Project Structure

```
aecoa/
├── 📄 README.md                    # Project documentation
├── 📋 DEPLOYMENT_GUIDE.md          # Deployment instructions
├── 📋 DEPLOYMENT_SUMMARY.md        # Deployment summary
├── 📋 LOCAL_LLAMA_SETUP.md         # Local AI setup guide
├── 🔧 requirements.txt             # Python dependencies
├── 🚫 .gitignore                  # Git ignore rules
├── 📊 app.py                      # Main Streamlit application
├── 🔐 auth.py                     # Authentication handling
├── 🔧 io_utils.py                 # I/O utility functions
├── 🔑 key.json                    # Service account credentials (not tracked)
├── 📋 compliance_analysis.log     # Application logs (not tracked)
│
├── 📂 agents/                     # AI agent modules
│   ├── 📄 __init__.py             # Package initialization
│   ├── 🔧 orchestrator.py        # Agent coordination and workflow
│   ├── 📋 providers.py           # LLM provider integrations
│   ├── 🔄 postprocess.py         # Post-processing utilities
│   ├── 📄 yaml_loader.py         # YAML configuration loader
│   │
│   ├── 🤖 agent1_parameter_definition_clean.py  # Parameter definition (clean)
│   ├── 🤖 agent1_parameter_definition.py        # Parameter definition
│   ├── 📄 agent1_yaml_extractor.py              # YAML extraction
│   ├── 🔍 agent2_drawing_analyzer.py            # Drawing analysis
│   ├── 📋 agent3_compliance_comparison.py       # Compliance checking
│   ├── 📊 agent3_executive_reporter.py          # Executive reporting
│   └── 📈 agent4_insights_report.py             # Insights and analytics
│
└── 📂 __pycache__/               # Python cache (not tracked)
    └── *.pyc files
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
