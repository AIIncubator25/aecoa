# GovTech LLMaaS API Integration Guide

## Overview

GovTech Singapore's Large Language Model as a Service (LLMaaS) provides government agencies and authorized partners access to state-of-the-art AI models through a secure, compliant API gateway.

## API Configuration

### Base Configuration
- **Base URL**: `https://llmaas.govtext.gov.sg/gateway`
- **Authentication**: API key using `api-key` header (not Bearer token)
- **Format**: OpenAI-compatible API format
- **Timeout**: Recommend 30+ seconds for chat completions

### Supported Models
The GovTech LLMaaS gateway provides access to:
- `gpt-4` - Most capable model for complex reasoning
- `gpt-3.5-turbo` - Fast and efficient for simpler tasks
- `gpt-4o` - Latest multimodal capabilities
- `gpt-4o-mini` - Cost-effective latest generation
- `gpt-5-main` - Next-generation model (if available)
- `gpt-5-thinking` - Advanced reasoning model (if available)

## API Usage

### Chat Completions Endpoint
```
POST https://llmaas.govtext.gov.sg/gateway/openai/deployments/{model}/chat/completions
```

### Headers
```json
{
  "api-key": "your-govtech-api-key",
  "Content-Type": "application/json"
}
```

### Request Body
```json
{
  "messages": [
    {"role": "user", "content": "Your message here"}
  ],
  "temperature": 0.0,
  "max_tokens": 1000,
  "response_format": {"type": "json_object"}  // Optional for structured output
}
```

### Response Format
Standard OpenAI API response format:
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Response content here"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

## Error Handling

### Common HTTP Status Codes
- `200` - Success
- `401` - Invalid API key
- `403` - Insufficient permissions
- `429` - Rate limit exceeded
- `500` - Server error

### Error Response Format
```json
{
  "error": {
    "message": "Error description",
    "type": "invalid_request_error",
    "code": "invalid_api_key"
  }
}
```

## Security & Compliance

### Data Protection
- All communications over HTTPS
- API keys are sensitive credentials - store securely
- Data processing follows Singapore government data protection policies

### Access Control
- API access restricted to authorized government entities
- Rate limiting applied per API key
- Usage monitoring and audit logging

## Testing Your Integration

### Manual Test
```bash
curl -X POST \
  https://llmaas.govtext.gov.sg/gateway/openai/deployments/gpt-4/chat/completions \
  -H "api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 5,
    "temperature": 0.0
  }'
```

### Using AECOA Application
1. Navigate to "🎯 AI Management" → "⚙️ AI Settings"
2. Select "GovTech" provider
3. Enter your API key
4. Click "🔍 Test AI Connection"
5. Should display "✅ GovTech API key is valid and working!"

## Best Practices

### Performance
- Use appropriate timeouts (30+ seconds)
- Implement proper retry logic for transient failures
- Cache responses where appropriate

### Cost Optimization
- Choose the right model for your use case:
  - `gpt-3.5-turbo` for simple tasks
  - `gpt-4` for complex reasoning
  - `gpt-4o-mini` for latest features at lower cost

### Error Handling
- Handle rate limits gracefully
- Provide user-friendly error messages
- Log errors for debugging

## Integration in AECOA

The AECOA application integrates with GovTech LLMaaS through:

### Authentication (`auth.py`)
- API key validation using chat completions endpoint
- Proper error handling and user feedback
- Support for both admin and BYOK (Bring Your Own Key) configurations

### Provider Interface (`agents/providers.py`)
- Automatic selection of GovTech when configured
- Fallback to other providers if GovTech unavailable
- Proper request formatting and response parsing

### Model Management (`agents/model_manager.py`)
- Dynamic detection of available GovTech models
- Model information and recommendations
- Automatic failover capabilities

## Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Check API key format and validity
   - Ensure key has not expired
   - Verify account permissions

2. **403 Forbidden**
   - Confirm API access permissions
   - Check if account is properly authorized
   - Verify model access rights

3. **429 Rate Limited**
   - Implement exponential backoff
   - Check rate limit headers in response
   - Consider upgrading API quota

4. **Timeout Errors**
   - Increase timeout values (30+ seconds)
   - Check network connectivity
   - Try with simpler requests first

### Support
For GovTech LLMaaS specific issues:
- Contact your GovTech account representative
- Refer to official GovTech documentation
- Use built-in AECOA testing tools for diagnosis

## Changelog

- **v1.0** - Initial GovTech LLMaaS integration
- **v1.1** - Added proper error handling and model detection
- **v1.2** - Enhanced API testing and validation features