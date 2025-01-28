# Browser Use Server

A Model Context Protocol server for browser automation using Python scripts. For use with Cline

<a href="https://glama.ai/mcp/servers/0aqrsbhx3z"><img width="380" height="200" src="https://glama.ai/mcp/servers/0aqrsbhx3z/badge" alt="Browser Use Server MCP server" /></a>

## Features

### Browser Operations
- `screenshot`: Capture a screenshot of a webpage (full page or viewport)
- `get_html`: Retrieve the HTML content of a webpage
- `execute_js`: Execute JavaScript on a webpage
- `get_console_logs`: Get console logs from a webpage

All operations support custom interaction steps (e.g., clicking elements, scrolling) after page load.

## Prerequisites

1. (Optional but recommended) Install Xvfb for headless browser automation:
```bash
# Ubuntu/Debian
sudo apt-get install xvfb

# CentOS/RHEL
sudo yum install xorg-x11-server-Xvfb

# Arch Linux
sudo pacman -S xorg-server-xvfb
```
Xvfb (X Virtual Frame Buffer) creates a virtual display, allowing browser automation without detection as a bot. Learn more about Xvfb [here](https://www.x.org/releases/X11R7.6/doc/man/man1/Xvfb.1.xhtml).

2. Install Miniconda or Anaconda
3. Create a Conda environment:
```bash
conda create -n browser-use python=3.11
conda activate browser-use
pip install browser-use
```

4. Set up LLM configuration:

The server supports multiple LLM providers. You can use any of the following API keys:
```bash
# Required: Set at least one of these API keys
export GLHF_API_KEY=your_api_key
export GROQ_API_KEY=your_api_key
export OPENAI_API_KEY=your_api_key
export OPENROUTER_API_KEY=your_api_key
export GITHUB_API_KEY=your_api_key
export DEEPSEEK_API_KEY=your_api_key
export GEMINI_API_KEY=your_api_key

# Optional: Override default configuration
export MODEL=your_preferred_model  # Override the default model
export BASE_URL=your_custom_url    # Override the default API endpoint
```

The server will automatically use the first available API key it finds. You can optionally customize the model and base URL for any provider using the environment variables.

## Installation

1. Clone this repository
2. Install dependencies:
```bash
npm install
```

3. Build the server:
```bash
npm run build
```

## MCP Configuration

Add the following configuration to your Cline MCP settings:

```json
"browser-use": {
  "command": "node",
  "args": [
    "/home/YOUR_HOME/Documents/Cline/MCP/browser-use-server/build/index.js"
  ],
  "env": {
    // Required: Set at least one API key
    "GLHF_API_KEY": "your_api_key",
    "GROQ_API_KEY": "your_api_key",
    "OPENAI_API_KEY": "your_api_key",
    "OPENROUTER_API_KEY": "your_api_key",
    "GITHUB_API_KEY": "your_api_key",
    "DEEPSEEK_API_KEY": "your_api_key",
    "GEMINI_API_KEY": "your_api_key",
    // Optional: Configuration overrides
    "MODEL": "your_preferred_model",
    "BASE_URL": "your_custom_url"
  },
  "disabled": false,
  "autoApprove": []
}
```

Replace:
- `YOUR_HOME` with your actual home directory name
- `your_api_key` with your actual API keys

## Usage

Run the server:
```bash
node build/index.js
```

The server will be available on stdio and supports the following operations:

### Screenshot
Parameters:
- url: The webpage URL (required)
- full_page: Whether to capture the full page or just the viewport (optional, default: false)
- steps: Comma-separated actions or sentences describing steps to take after page load (optional)

### Get HTML
Parameters:
- url: The webpage URL (required)
- steps: Comma-separated actions or sentences describing steps to take after page load (optional)

### Execute JavaScript
Parameters:
- url: The webpage URL (required)
- script: JavaScript code to execute (required)
- steps: Comma-separated actions or sentences describing steps to take after page load (optional)

### Get Console Logs
Parameters:
- url: The webpage URL (required)
- steps: Comma-separated actions or sentences describing steps to take after page load (optional)

## Example Cline Usage

Here are some example tasks you can accomplish using the browser-use server with Cline:

### Modifying Web Page Elements during Development
To change the color of a heading on a page that requires authentication:
```
Change the colour of the headline with the text "Alle Foren im Überblick." to deep blue on https://localhost:3000/foren/ page

To check/see the page, use browser-use MCP server to:
Open https://localhost:3000/auth,
Login with ztobs:Password123,
Navigate to https://localhost:3000/foren/,
Accept cookies if required

hint: execute all browser actions in one command with multiple comma-separated steps
```

This task demonstrates:
- Multi-step browser automation using comma-separated steps
- Authentication handling
- Cookie acceptance
- DOM manipulation
- CSS styling changes

The server will execute these steps sequentially, handling any required interactions along the way.

## Configuration

### LLM Configuration
The server supports multiple LLM providers with their default configurations:

- GLHF: Uses deepseek-ai/DeepSeek-V3 model
- Groq: Uses deepseek-r1-distill-llama-70b model
- OpenAI: Uses gpt-4o-mini model
- Openrouter: Uses deepseek/deepseek-chat model
- Github: Uses gpt-4o-mini model
- DeepSeek: Uses deepseek-chat model
- Gemini: Uses gemini-2.0-flash-exp model

You can override these defaults using environment variables:
- `MODEL`: Set a custom model name for any provider
- `BASE_URL`: Set a custom API endpoint URL (if the provider supports it)

### Xvfb Support
The server automatically detects if Xvfb is installed and:
- Uses xvfb-run when available, enabling better browser automation without bot detection
- Falls back to direct execution when Xvfb is not installed
- Sets RUNNING_UNDER_XVFB environment variable accordingly

### Timeout
Default timeout is 5 minutes (300000 ms). Modify the TIMEOUT constant in `build/index.js` to change this.

## Error Handling
The server provides detailed error messages for:
- Python script execution failures
- Browser operation timeouts
- Invalid parameters

## Debugging
Use the MCP Inspector for debugging:
```bash
npm run inspector
```

## Citation

```
@software{browser_use2024,
  author = {Müller, Magnus and Žunič, Gregor},
  title = {Browser Use: Enable AI to control your browser},
  year = {2024},
  publisher = {GitHub},
  url = {https://github.com/browser-use/browser-use}
}
```

## License
MIT
