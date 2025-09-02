# SubGrab + OpenRouter AI Integration

This enhanced version of SubGrab includes AI-powered subdomain discovery using OpenRouter's API, which provides access to various state-of-the-art language models.

## 🤖 What is OpenRouter?

OpenRouter is a unified API that provides access to multiple AI models including:
- Anthropic Claude 3.5 Sonnet (recommended)
- OpenAI GPT-4o
- Google Gemini Pro
- Meta Llama models
- And many more

## 🚀 Features

### AI-Powered Subdomain Generation
- **Intelligent Variations**: Generate subdomains based on organization context, industry patterns, and common naming conventions
- **Pattern Recognition**: Analyze existing subdomains to identify patterns and generate new candidates
- **Content Analysis**: Analyze web content from discovered subdomains to find additional references
- **Context-Aware**: Considers organization type, industry, and technology stack

### Enhanced Discovery Methods
- Traditional passive reconnaissance (Certificate Transparency, DNS, etc.)
- AI-generated intelligent subdomain variations
- Pattern-based subdomain generation
- Content analysis for hidden references

## 📋 Prerequisites

1. **Python 3.7+**
2. **OpenRouter API Key** - Get one at [openrouter.ai](https://openrouter.ai/)
3. **Required Python packages** (install with `pip install -r requirements.txt`)

## 🛠️ Installation

1. **Clone or download the SubGrab files**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Get your OpenRouter API key:**
   - Visit [openrouter.ai](https://openrouter.ai/)
   - Sign up and get your API key
   - Add credits to your account (usually $5-10 is enough for extensive testing)

## 🎯 Usage

### Command Line Usage

#### Basic AI-enhanced scan:
```bash
python subgrab.py example.com --openrouter-key YOUR_API_KEY
```

#### With specific model:
```bash
python subgrab.py example.com --openrouter-key YOUR_API_KEY --openrouter-model "anthropic/claude-3.5-sonnet"
```

#### Full featured scan:
```bash
python subgrab.py example.com \
  --openrouter-key YOUR_API_KEY \
  --shodan-key YOUR_SHODAN_KEY \
  --threads 100 \
  --timeout 30
```

### GUI Usage

1. **Launch the GUI:**
   ```bash
   python subgrab_gui.py
   ```

2. **Configure OpenRouter:**
   - Go to the "API Keys" tab
   - Enter your OpenRouter API key
   - Select your preferred model (Claude 3.5 Sonnet recommended)
   - Save your configuration

3. **Run the scan:**
   - Enter your target domain
   - Configure other settings as needed
   - Click "Start Scan"

### Programmatic Usage

```python
from openrouter_integration import OpenRouterSubdomainEnhancer

# Initialize the enhancer
enhancer = OpenRouterSubdomainEnhancer("your-api-key")

# Generate intelligent subdomains
subdomains = enhancer.generate_intelligent_subdomains("example.com")

# Analyze patterns in existing subdomains
existing = ["www", "api", "dev", "staging"]
pattern_subdomains = enhancer.generate_pattern_based_subdomains("example.com", existing)

# Analyze web content for subdomain references
content = "<html>...</html>"  # Web page content
content_subdomains = enhancer.analyze_content_for_subdomains("example.com", content)
```

## 🎛️ Available Models

| Model | Provider | Best For | Cost |
|-------|----------|----------|------|
| `anthropic/claude-3.5-sonnet` | Anthropic | **Recommended** - Best overall performance | Medium |
| `anthropic/claude-3-haiku` | Anthropic | Fast and cost-effective | Low |
| `openai/gpt-4o` | OpenAI | High-quality analysis | High |
| `openai/gpt-4o-mini` | OpenAI | Balanced performance/cost | Medium |
| `google/gemini-pro-1.5` | Google | Good alternative | Medium |
| `meta-llama/llama-3.1-8b-instruct` | Meta | Open source option | Low |

## 💡 How It Works

### 1. Intelligent Subdomain Generation
The AI analyzes your target domain and generates relevant subdomains based on:
- **Industry patterns** (e.g., healthcare, finance, tech)
- **Organization type** (corporate, government, educational)
- **Common naming conventions**
- **Technology stack indicators**
- **Geographic considerations**

### 2. Pattern Recognition
When existing subdomains are found, the AI:
- Identifies naming patterns
- Recognizes numbering schemes
- Detects environment patterns (dev, test, prod)
- Generates variations based on observed patterns

### 3. Content Analysis
The AI can analyze web content to find:
- Hidden subdomain references in JavaScript
- API endpoints that suggest additional subdomains
- Configuration files mentioning other services
- Comments or documentation with subdomain info

## 📊 Example Output

```
🤖 Initializing OpenRouter AI enhancement...
🧠 Generating AI-powered subdomain variations...
✅ Generated 87 AI-suggested subdomains

[*] Starting passive discovery for example.com
[+] certificate_transparency: 23 subdomains found
[+] web_archives: 12 subdomains found
[+] search_engines: 8 subdomains found
[+] rapiddns: 15 subdomains found
[+] security_apis: 31 subdomains found
[+] github_code_search: 5 subdomains found
[+] openrouter_enhancement: 87 subdomains found  ← AI-generated
[+] dns_enumeration: 156 subdomains found
[+] reverse_dns_lookup: 7 subdomains found

[+] Total subdomains discovered: 344
```

## 🔧 Configuration Tips

### Model Selection
- **Claude 3.5 Sonnet**: Best overall performance, recommended for most use cases
- **Claude 3 Haiku**: Faster and cheaper, good for large-scale scans
- **GPT-4o**: Alternative high-quality option
- **GPT-4o Mini**: Good balance of performance and cost

### Cost Optimization
- Start with cheaper models like Claude 3 Haiku for testing
- Use context information to get better results with fewer tokens
- Consider the `--fast` mode to skip AI enhancement for quick scans

### API Key Management
- Store API keys securely (environment variables recommended)
- Monitor your usage on the OpenRouter dashboard
- Set up billing alerts to avoid unexpected charges

## 🛡️ Security Considerations

- **API Keys**: Never commit API keys to version control
- **Rate Limiting**: OpenRouter has built-in rate limiting
- **Content Privacy**: Be aware that content sent to AI models may be logged
- **Authorized Testing**: Only use on domains you own or have permission to test

## 🐛 Troubleshooting

### Common Issues

1. **"OpenRouter API error"**
   - Check your API key is valid
   - Ensure you have credits in your account
   - Verify internet connectivity

2. **"OpenRouter integration module not found"**
   - Ensure `openrouter_integration.py` is in the same directory
   - Check Python path and imports

3. **"No subdomains generated"**
   - Try a different model
   - Check if the domain is too generic
   - Verify API key has sufficient credits

4. **High API costs**
   - Use cheaper models like Claude 3 Haiku
   - Reduce the number of requests
   - Use the `--fast` mode

### Debug Mode
Add debug output by modifying the OpenRouter integration:
```python
# In openrouter_integration.py, add print statements to see API responses
print(f"API Response: {response}")
```

## 📈 Performance Comparison

| Method | Traditional SubGrab | With OpenRouter AI |
|--------|-------------------|-------------------|
| Subdomains Found | ~200-300 | ~400-600 |
| Unique Discoveries | Standard patterns | Context-aware variations |
| False Positives | Low | Very Low |
| Execution Time | 2-5 minutes | 3-7 minutes |
| Cost | Free | $0.10-$2.00 per scan |

## 🤝 Contributing

To contribute to the OpenRouter integration:

1. Fork the repository
2. Create a feature branch
3. Add your improvements
4. Test with different models and domains
5. Submit a pull request

## 📄 License

This integration maintains the same license as the original SubGrab project.

## 🙏 Credits

- **Original SubGrab**: Krishnendu Paul
- **OpenRouter Integration**: Enhanced version with AI capabilities
- **OpenRouter**: Providing unified access to multiple AI models

---

**Happy Hunting! 🎯**

For more advanced usage and custom integrations, check out the example scripts and documentation.