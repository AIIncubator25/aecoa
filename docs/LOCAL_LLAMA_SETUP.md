# Local Llama Setup Guide for AECOA

This guide helps users set up Llama models locally for the AECOA Compliance Checks application.

## Overview

AECOA uses local Llama models via Ollama for AI-powered compliance checking. Each user needs to install and run Llama models on their own laptop/computer for privacy and control.

## Prerequisites

- **Operating System**: Windows 10/11, macOS, or Linux
- **RAM**: Minimum 8GB, Recommended 16GB+
- **Storage**: 10-20GB free space for models
- **Internet**: For initial model download only

## Step-by-Step Installation

### 1. Install Ollama

#### Windows:
1. Download Ollama for Windows from: https://ollama.ai/download
2. Run the installer (`OllamaSetup.exe`)
3. Follow the installation wizard
4. Ollama will start automatically as a service

#### macOS:
```bash
# Using Homebrew (recommended)
brew install ollama

# Or download from https://ollama.ai/download
```

#### Linux:
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. Download Llama Models

Open Command Prompt/Terminal and run:

```bash
# Download Llama 3.2 (recommended, ~2GB)
ollama pull llama3.2

# Alternative: Llama 3.1 for better performance on powerful machines (~4.7GB)
ollama pull llama3.1

# For slower machines: Llama 2 (~3.8GB)
ollama pull llama2
```

**Note**: First download will take time depending on your internet speed.

### 3. Verify Installation

Test if Ollama is working:

```bash
# Check available models
ollama list

# Test with a simple query
ollama run llama3.2 "Hello, respond with 'Setup successful!'"
```

Expected output: The model should respond with "Setup successful!" or similar.

### 4. Configure AECOA

1. **Install AECOA dependencies**:
   ```bash
   cd path/to/aecoa
   pip install -r requirements.txt
   ```

2. **Start AECOA application**:
   ```bash
   streamlit run app.py
   ```

3. **Test AI connection** in the application:
   - Go to "🎯 AI Management" tab
   - Click "⚙️ AI Settings" 
   - Click "🔍 Test AI Connection"
   - Should show "✅ AI connection successful!"

## Model Selection Guide

| Model | Size | RAM Required | Speed | Quality | Best For |
|-------|------|--------------|-------|---------|----------|
| llama3.2 | ~2GB | 8GB+ | Fast | Good | General use, laptops |
| llama3.1 | ~4.7GB | 16GB+ | Medium | Better | Desktop computers |
| llama2 | ~3.8GB | 12GB+ | Medium | Good | Balanced performance |

## Troubleshooting

### Common Issues

#### 1. "ollama: command not found"
**Solution**: 
- Windows: Restart Command Prompt, check if Ollama service is running
- macOS/Linux: Add Ollama to PATH or restart terminal

#### 2. "Model not found"
**Solution**:
```bash
# Re-download the model
ollama pull llama3.2

# Check what models are available
ollama list
```

#### 3. "Connection refused" in AECOA
**Solution**:
```bash
# Start Ollama service manually
ollama serve

# Or restart Ollama service
# Windows: Restart "Ollama" service in Services
# macOS/Linux: sudo systemctl restart ollama
```

#### 4. Out of memory errors
**Solutions**:
- Close other applications to free RAM
- Use a smaller model (llama3.2 instead of llama3.1)
- Increase virtual memory/swap space

#### 5. Slow responses
**Solutions**:
- Use GPU acceleration if available
- Reduce max_tokens in AI settings
- Use smaller model for faster responses

### Performance Optimization

#### For Better Speed:
1. **Use SSD storage** for model files
2. **Close unnecessary applications** to free RAM
3. **Adjust temperature** in AI Settings (lower = faster)
4. **Reduce max tokens** in AI Settings

#### For Better Quality:
1. **Use larger models** (llama3.1 if you have 16GB+ RAM)
2. **Increase temperature** slightly for more creative responses
3. **Increase max tokens** for more detailed outputs

## Security & Privacy

### ✅ Advantages of Local Deployment:
- **Data Privacy**: All data stays on your computer
- **No Internet Required**: Works offline after setup
- **No API Costs**: Free to use once installed
- **Full Control**: Configure models as needed

### 🔒 Best Practices:
- Keep Ollama updated: `ollama update`
- Regularly backup your prompt templates
- Monitor disk space (models can be large)
- Use firewall to protect Ollama service

## Advanced Configuration

### Custom Model Location

By default, models are stored in:
- **Windows**: `C:\Users\{username}\.ollama\models`
- **macOS**: `~/.ollama/models`
- **Linux**: `~/.ollama/models`

To change storage location:
```bash
# Set environment variable
export OLLAMA_MODELS="/path/to/custom/location"

# Windows (PowerShell)
$env:OLLAMA_MODELS = "D:\ollama_models"
```

### Multiple Models

You can install multiple models and switch between them:

```bash
# Install multiple models
ollama pull llama3.2
ollama pull llama3.1
ollama pull codellama

# Use specific model in AECOA AI Settings
```

### Resource Limits

Configure Ollama resource usage:

```bash
# Limit to specific GPU
export CUDA_VISIBLE_DEVICES=0

# Limit CPU threads
export OMP_NUM_THREADS=4
```

## Integration with AECOA

### Model Configuration in AECOA:

1. **Go to AI Management tab** in AECOA
2. **Select AI Settings**
3. **Choose your installed model**:
   - `llama3.2` (recommended for most users)
   - `llama3.1` (for powerful machines)
   - `llama2` (for compatibility)

4. **Adjust settings**:
   - **Temperature**: 0.3 (deterministic) to 0.7 (creative)
   - **Max Tokens**: 1000-3000 (depending on detail needed)
   - **Timeout**: 30-60 seconds

### Usage Tips:

- **Start with default settings** and adjust based on results
- **Monitor conversation history** in AI Management tab
- **Use prompt templates** for consistent results
- **Test with sample data** before real compliance checks

## Support

If you encounter issues:

1. **Check AECOA logs** in the application
2. **Test Ollama directly** with command line
3. **Verify model download** with `ollama list`
4. **Check system resources** (RAM, disk space)
5. **Restart Ollama service** if needed

For technical support, include:
- Operating system version
- Ollama version (`ollama version`)
- Model used
- Error messages
- System specifications (RAM, CPU)

## Summary

With this setup, each AECOA user will have:
- ✅ **Private AI models** running locally
- ✅ **No cloud dependencies** for AI processing
- ✅ **Full data control** and privacy
- ✅ **Offline capability** after initial setup
- ✅ **Customizable AI behavior** through settings

The local Llama deployment ensures compliance data never leaves your computer while providing powerful AI-assisted regulatory checking capabilities.
