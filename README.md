# 🏗️ AECOA - AI-Enhanced Compliance & Optimization Assistant

> **Automated compliance checking using AI agents for YAML requirements and technical drawings**

## 🎯 Overview

AECOA is a sophisticated multi-agent AI system designed for architectural and engineering compliance analysis. It processes YAML requirement specifications and technical drawings to generate comprehensive compliance reports.

## 🏗️ System Architecture

```
🏗️ AECOA (Main Directory)
├── 📁 Main Application Files
│   ├── app.py                    # 🎮 Main Streamlit application & UI controller
│   ├── start.py                  # 🚀 Cross-platform startup script with validation
│   ├── start.bat                 # 🖱️ Windows one-click launcher
│   └── requirements.txt          # 📦 Python dependencies
│
├── 🤖 agents/                    # AI Agent System (Modular Architecture)
│   ├── 🔧 core/                 # Core System Components
│   │   ├── api_key_manager.py   # 🔑 Centralized API key management (BYOK + Admin)
│   │   └── __init__.py          # Module initialization
│   │
│   ├── 🔐 auth/                 # Authentication System
│   │   ├── auth.py              # 👤 User authentication & session management
│   │   └── __init__.py          # Module initialization
│   │
│   ├── 🎨 ui/                   # User Interface Components
│   │   ├── ui_components.py     # 🖼️ Reusable UI elements (BYOK interface, etc.)
│   │   └── __init__.py          # Module initialization
│   │
│   ├── 📥 extractors/           # Data Extraction Agents
│   │   ├── agent1_yaml_extractor.py        # 📄 YAML → Parameters extraction
│   │   ├── agent1_parameter_definition.py  # 📋 Parameter definition logic
│   │   └── agent1_parameter_definition_clean.py # 🧹 Clean parameter processing
│   │
│   ├── 🔍 analyzers/            # Analysis Agents
│   │   └── agent2_drawing_analyzer.py      # 🖼️ Technical drawing analysis
│   │
│   ├── 📊 reporters/            # Report Generation Agents
│   │   ├── agent3_executive_reporter.py    # 👔 Executive summary generation
│   │   ├── agent3_compliance_comparison.py # ⚖️ Compliance comparison logic
│   │   └── agent4_insights_report.py       # 💡 Detailed insights & recommendations
│   │
│   ├── 🛠️ utils/               # Utility Functions
│   │   ├── postprocess.py       # 🔄 Data processing & formatting
│   │   └── __init__.py          # Module initialization
│   │
│   ├── orchestrator.py          # 🎯 Main workflow coordination engine
│   ├── model_manager.py         # 🧠 AI model management & selection
│   ├── providers.py             # 🌐 Multi-provider AI integration
│   └── yaml_loader.py           # 📁 YAML file processing utilities
│
├── 📋 Configuration & Setup
│   ├── .streamlit/
│   │   ├── secrets.toml         # 🔒 API keys (local, git-ignored)
│   │   └── secrets.example.toml # 📝 API key template
│   ├── BYOK_SETUP.md           # 🔑 Bring Your Own Key setup guide
│   ├── DEPLOYMENT_GUIDE.md     # 🚀 Deployment instructions
│   └── LOCAL_LLAMA_SETUP.md    # 🦙 Local Ollama setup guide
│
├── 📁 Data & Uploads
│   └── uploads/                 # 📂 User-uploaded files (git-ignored for security)
│       └── .gitkeep            # Maintains directory structure
│
└── 📚 Documentation
    ├── README.md               # 📖 This comprehensive guide
    ├── GOVTECH_API_GUIDE.md    # 🏛️ Government API integration guide
    └── DEPLOYMENT_SUMMARY.md   # ⚡ Quick deployment reference
```

## 🔄 Workflow Process

```
📁 Upload YAML Requirements
           ↓
🤖 Agent 1: Parameter Extraction
           ↓
📊 Generate parameters.csv
           ↓
📸 Upload Technical Drawings
           ↓
🤖 Agent 2: Drawing Analysis
           ↓
⚖️ Compliance Comparison
           ↓
🤖 Agent 3: Executive Report
           ↓
📋 Final Compliance Report

    🎯 Orchestrator manages entire workflow
```

## 🚀 Quick Start

### Method 1: One-Click Launch (Windows)
```bash
# Just double-click:
start.bat
```

### Method 2: Cross-Platform Launch
```bash
python start.py
```

### Method 3: Traditional Launch
```bash
conda activate py3106
streamlit run app.py
```

## 🔑 Multi-Provider AI Support

### Supported Providers:
- **🤖 OpenAI** - `gpt-4o`, `gpt-4o-mini` (Recommended for most users)
- **🏛️ GovTech** - Enterprise/Government deployment
- **🦙 Ollama** - Local deployment (Free, Private)

### API Key Management:
- **👤 BYOK (Bring Your Own Key)** - For public deployment
- **🔐 Admin Keys** - Pre-configured local keys
- **🌐 Environment Variables** - System-level configuration

## 🛠️ Key Components Explained

### 🎮 Main Application (`app.py`)
- **Purpose**: Primary Streamlit interface and workflow coordination
- **Functions**: 
  - User authentication
  - Provider selection and configuration
  - Step-by-step workflow management
  - Results display and export

### 🎯 Orchestrator (`agents/orchestrator.py`)
- **Purpose**: Central coordination engine for complex workflows
- **Functions**:
  - Agent lifecycle management
  - Data flow coordination
  - Error recovery and fallback
  - Progress tracking and logging

### 🔑 API Key Manager (`agents/core/api_key_manager.py`)
- **Purpose**: Centralized API key management system
- **Functions**:
  - BYOK (Bring Your Own Key) support
  - Multi-provider key routing
  - Secure session storage
  - API validation and testing

### 🎨 UI Components (`agents/ui/ui_components.py`)
- **Purpose**: Reusable interface elements
- **Functions**:
  - BYOK interface components
  - Provider status displays
  - Configuration panels
  - API testing interfaces

### 🤖 AI Agents

#### 📥 Extractor Agents (`agents/extractors/`)
- **agent1_yaml_extractor.py**: Converts YAML requirements → structured parameters
- **Features**: Multi-provider support, robust error handling, format validation

#### 🔍 Analyzer Agents (`agents/analyzers/`)
- **agent2_drawing_analyzer.py**: Technical drawing analysis and compliance checking
- **Features**: Image processing, component detection, measurement validation

#### 📊 Reporter Agents (`agents/reporters/`)
- **agent3_executive_reporter.py**: Executive summary generation
- **agent4_insights_report.py**: Detailed analysis and recommendations
- **Features**: Professional reporting, compliance status, actionable insights

## 🔧 Development & Maintenance

### File Size Management
- **Before**: Large monolithic files (1000+ lines)
- **After**: Modular components (100-300 lines each)
- **Benefits**: Easier testing, parallel development, better maintainability

### Adding New Features
1. **New Agent**: Add to appropriate `/agents/{category}/` folder
2. **New UI Component**: Add to `/agents/ui/ui_components.py`
3. **New Provider**: Update `/agents/providers.py` and `/agents/core/api_key_manager.py`
4. **New Utility**: Add to `/agents/utils/`

### Testing Strategy
```bash
# Test individual components
python -m pytest agents/core/test_api_key_manager.py
python -m pytest agents/extractors/test_yaml_extractor.py

# Test full workflow
python -m pytest tests/integration/test_full_workflow.py
```

## 🚀 Deployment Options

### 1. 🌐 Public Cloud (Streamlit Cloud)
- **URL**: `compliancechecks.streamlit.app`
- **Features**: BYOK support, public access, automatic scaling
- **Setup**: Link GitHub repo, configure secrets

### 2. 🏢 Enterprise Deployment
- **Features**: Pre-configured API keys, SSO integration, custom branding
- **Setup**: Follow `DEPLOYMENT_GUIDE.md`

### 3. 🔒 Local Deployment
- **Features**: Full privacy, custom models (Ollama), no internet required
- **Setup**: Follow `LOCAL_LLAMA_SETUP.md`

## 📊 File Statistics

| Component | Purpose | Lines | Status |
|-----------|---------|-------|---------|
| `app.py` | Main application | ~500 | ✅ Optimized |
| `orchestrator.py` | Workflow coordination | ~900 | ✅ Modular |
| `api_key_manager.py` | API management | ~150 | ✅ New |
| `ui_components.py` | Interface elements | ~200 | ✅ New |
| `auth.py` | Authentication | ~500 | ✅ Moved |
| Agent files | AI processing | 200-400 each | ✅ Organized |

## 🔒 Security Features

- **🔑 BYOK Support**: Users provide their own API keys
- **🚫 No Key Storage**: Keys stored in session only, never committed
- **📁 Upload Security**: Sensitive files kept local, ignored by Git
- **🔐 Authentication**: Multi-level access control
- **🛡️ Input Validation**: Comprehensive input sanitization

## 📞 Support & Documentation

- **📖 Setup Guides**: `BYOK_SETUP.md`, `DEPLOYMENT_GUIDE.md`
- **🔧 Troubleshooting**: Check individual component logs
- **💡 Features**: Comprehensive inline help and tooltips
- **🐛 Issues**: Report in GitHub repository

---

**💡 Pro Tip**: Start with `start.bat` (Windows) or `python start.py` (any platform) for the best experience!

**🎯 Mission**: Making architectural compliance analysis accessible, efficient, and intelligent through AI automation.