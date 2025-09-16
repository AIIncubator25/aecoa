# AECOA Deployment Guide - Local AI Setup

## For End Users: Quick Setup

### Prerequisites
- Windows 10/11, macOS, or Linux
- 8GB+ RAM (16GB+ recommended)
- 10-20GB free disk space
- Internet connection (for initial setup only)

### 1. Download AECOA
```bash
git clone https://github.com/AIIncubator25/aecoa.git
cd aecoa
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Ollama (Local AI Runtime)

**Windows:**
1. Download from https://ollama.ai/download
2. Run `OllamaSetup.exe`
3. Ollama starts automatically

**macOS:**
```bash
brew install ollama
# or download from https://ollama.ai/download
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### 4. Download AI Model
```bash
# Recommended model (~2GB)
ollama pull llama3.2

# For powerful machines (~4.7GB)
ollama pull llama3.1
```

### 5. Start AECOA
```bash
streamlit run app.py
```

### 6. Verify Setup
1. Open http://localhost:8501
2. Go to "🎯 AI Management" tab
3. Click "⚙️ AI Settings"
4. Click "🔍 Test AI Connection"
5. Should show "✅ AI connection successful!"

## For Developers: Deployment Options

### Option 1: Individual User Deployment (Recommended for MVP)
Each user runs their own AECOA instance with local Ollama.

**Pros:**
- Complete data privacy
- No cloud costs
- Works offline
- Full user control

**Cons:**
- Each user needs setup
- Resource requirements on user machine

### Option 2: Shared Server Deployment (Future)
Central AECOA server with shared Ollama instance.

**Pros:**
- Easier user setup
- Centralized model management
- Resource sharing

**Cons:**
- Data privacy concerns
- Server maintenance required
- Network dependency

### Option 3: Hybrid Deployment (Future)
Users can choose local or cloud AI backend.

## Architecture Overview

```
User's Computer:
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Web       │    │   AECOA     │    │   Ollama    │  │
│  │   Browser   │◄───│   Streamlit │◄───│   + Llama   │  │
│  │             │    │   App       │    │   Models    │  │
│  └─────────────┘    └─────────────┘    └─────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                Local Storage                        │  │
│  │  - Compliance data                                  │  │
│  │  - AI models                                        │  │
│  │  - Conversation history                             │  │
│  │  - Prompt templates                                 │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Configuration Management

### AI Models
- **llama3.2**: Default, ~2GB, good for laptops
- **llama3.1**: Better quality, ~4.7GB, needs 16GB+ RAM
- **llama2**: Legacy support, ~3.8GB

### Storage Requirements
- **AI Models**: 2-5GB per model
- **Application**: ~50MB
- **User Data**: Varies (documents, drawings, reports)

### Network Requirements
- **Initial Setup**: Download AI models (one-time)
- **Operation**: Fully offline capable
- **Updates**: Periodic model/app updates

## Security & Privacy

### Local Deployment Benefits
✅ **Data Privacy**: All data stays on user's computer
✅ **No Cloud Dependency**: Works completely offline
✅ **Compliance**: Meets strict data security requirements
✅ **Control**: Users control all AI processing

### Best Practices
- Keep Ollama updated
- Regular backups of templates and configurations
- Firewall protection for Ollama service
- Monitor disk space usage

## Troubleshooting

### Common Issues

**"ollama: command not found"**
- Windows: Restart terminal, check Ollama service
- macOS/Linux: Add to PATH or restart terminal

**"Model not found"**
```bash
ollama pull llama3.2
ollama list
```

**"Connection refused"**
```bash
ollama serve
# or restart Ollama service
```

**Out of memory**
- Close other applications
- Use smaller model (llama3.2)
- Increase virtual memory

**Slow responses**
- Use SSD storage
- Close unnecessary apps
- Reduce max_tokens in settings

### Performance Optimization

**For Speed:**
- Use llama3.2 model
- Lower temperature (0.1-0.3)
- Reduce max_tokens (1000-2000)
- Close other applications

**For Quality:**
- Use llama3.1 model (if sufficient RAM)
- Higher temperature (0.5-0.7)
- Increase max_tokens (3000-4000)
- Monitor conversation history

## Support

### User Support
1. Check setup guide: `LOCAL_LLAMA_SETUP.md`
2. Test AI connection in app
3. Review troubleshooting section
4. Check system resources

### Developer Support
- Application logs in Streamlit interface
- Ollama logs: `ollama logs`
- Configuration files in application directory
- Conversation history in AI Management tab

## Future Enhancements

### Planned Features
- **Multi-model support**: Switch between models per task
- **Cloud backup**: Optional cloud sync for templates
- **Team sharing**: Share prompt templates across team
- **Performance monitoring**: Detailed AI performance metrics
- **Model management**: GUI for downloading/managing models

### Scalability
- **Resource monitoring**: Track CPU/RAM usage
- **Model optimization**: Quantized models for lower-end hardware
- **Batch processing**: Process multiple projects
- **API integration**: External system integration

This deployment model ensures that AECOA can be used in compliance-sensitive environments while maintaining ease of use and powerful AI capabilities.
