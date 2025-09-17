# 🔑 BYOK Setup Guide - Bring Your Own API Keys

This guide helps you configure AECOA with your own API keys for secure, personalized AI access.

## 🚨 Security First

**NEVER share or commit API keys to version control!** Each user should have their own private configuration.

## 📋 Quick Setup Steps

### 1. Copy the Template
```bash
# In your project directory
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
```

### 2. Edit Your Configuration
Open `.streamlit/secrets.toml` and configure your settings:

#### 👤 **Authentication Setup**
```toml
[auth]
admin = "your_secure_admin_password"
user = "your_secure_user_password"
```

#### 🔑 **Choose Your AI Provider**

**Option A: OpenAI (Recommended for most users)**
1. Visit https://platform.openai.com/
2. Create account and get API key
3. Update your `secrets.toml`:
```toml
[openai]
api_key = "sk-your_actual_api_key_here"
model = "gpt-4o-mini"  # Cost-effective choice

[ai_provider]
primary = "openai"
```

**Option B: GovTech AI (Government/Enterprise)**
1. Register with GovTech AI services
2. Get your API credentials
3. Update your `secrets.toml`:
```toml
[govtech]
api_key = "your_govtech_key_here"
base_url = "https://llmaas.govtext.gov.sg/gateway"

[ai_provider]
primary = "govtech"
```

**Option C: Local Ollama (Free & Private)**
1. Install Ollama: https://ollama.ai/
2. Download model: `ollama pull llama3.2`
3. Update your `secrets.toml`:
```toml
[ollama]
host = "http://localhost:11434"
model = "llama3.2:latest"

[ai_provider]
primary = "ollama"
```

### 3. Test Your Setup
1. Start the application: `streamlit run app.py`
2. Go to "🎯 AI Management" → "⚙️ AI Settings"
3. Click "🔍 Test AI Connection"
4. Should show "✅ AI connection successful!"

## 👥 Multi-User Scenarios

### For Development Teams
Each developer maintains their own `secrets.toml`:
- Clone the repository
- Copy `secrets.example.toml` to `secrets.toml`
- Configure with personal API keys
- Never commit `secrets.toml`

### For Organizations
**Centralized Approach:**
- IT provides API keys to authorized users
- Each user configures their own `secrets.toml`
- Use consistent provider settings across team

**Distributed Approach:**
- Each user gets their own API keys
- Different users can use different providers
- Flexible based on role/department needs

## 💰 Cost Management

### OpenAI Cost Tips
- Start with `gpt-4o-mini` (most cost-effective)
- Monitor usage at https://platform.openai.com/usage
- Set usage limits in your OpenAI account

### GovTech Enterprise
- Contact GovTech for enterprise pricing
- Usually includes usage quotas
- Better for government/compliance use cases

### Local Ollama
- Completely free after initial setup
- Requires good hardware (8GB+ RAM)
- Perfect for privacy-sensitive work

## 🔧 Advanced Configuration

### Multiple Providers Setup
```toml
[ai_provider]
primary = "openai"     # Your main provider
fallback = "ollama"    # Backup if primary fails
```

### Custom Model Settings
```toml
[ai_provider]
temperature = 0.1      # Lower = more consistent
max_tokens = 4000      # Adjust based on needs
```

## ❓ Troubleshooting

### "API Key Not Found" Error
1. Check `secrets.toml` exists in `.streamlit/` folder
2. Verify API key format (OpenAI starts with `sk-`)
3. Ensure no extra spaces in key
4. Restart Streamlit application

### "Connection Failed" Error
1. Check internet connection (for cloud providers)
2. Verify API key is active and has credits
3. Test with different model name
4. Check provider base_url is correct

### Permission Errors
1. Verify file permissions on `secrets.toml`
2. Check if antivirus is blocking file access
3. Run as administrator if needed

## 🛡️ Security Best Practices

1. **Never commit secrets.toml to git**
2. **Use strong authentication passwords**
3. **Regularly rotate API keys**
4. **Monitor API usage for anomalies**
5. **Use least-privilege access**
6. **Enable 2FA on provider accounts**

## 📞 Support

If you need help:
1. Check this guide first
2. Verify your `secrets.toml` format matches the example
3. Test with a simple provider (like Ollama) first
4. Contact your organization's IT team
5. Create an issue in the project repository

---

**Remember: Your API keys = Your responsibility. Keep them secure!** 🔒