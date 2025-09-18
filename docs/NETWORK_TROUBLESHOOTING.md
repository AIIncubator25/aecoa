# AECOA Network Troubleshooting Guide

## GovTech API Connection Issues

If you encounter the error: `GovTech API connection failed: HTTPSConnectionPool... Failed to establish a new connection`, this indicates network connectivity issues with the GovTech AI API endpoint.

### Quick Solutions

1. **Switch AI Provider (Recommended)**
   - Go to **Settings** → **AI Provider** → Select **"OpenAI"** or **"Ollama"**
   - Both alternatives have been tested and work with your current network setup

2. **Use OpenAI (Cloud-based)**
   - Requires OpenAI API key from https://platform.openai.com/api-keys
   - Works with most network configurations
   - Fast and reliable

3. **Use Ollama (Local/Offline)**
   - No internet required after initial setup
   - Install from https://ollama.ai
   - Run: `ollama run llama3.2` to get started
   - Perfect for sensitive documents or offline use

### Network Diagnostics

The connection failure to `llmaas.govtext.gov.sg` could be due to:
- Corporate firewall restrictions
- DNS resolution issues
- Regional access limitations
- Temporary service unavailability

### For IT Administrators

If your organization needs access to GovTech API:
- Whitelist domain: `llmaas.govtext.gov.sg`
- Allow HTTPS traffic on port 443
- Ensure DNS resolution for the domain

### Alternative Setup

**Recommended configuration for reliable operation:**
1. Primary: OpenAI (with API key)
2. Fallback: Ollama (local installation)

Both alternatives provide the same YAML conversion functionality without network dependencies on GovTech infrastructure.