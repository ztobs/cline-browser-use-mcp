# Browser Use Server

A Model Context Protocol server for browser automation using Python scripts. For use with Cline

<a href="https://glama.ai/mcp/servers/0aqrsbhx3z"><img width="380" height="200" src="https://glama.ai/mcp/servers/0aqrsbhx3z/badge" alt="Browser Use Server MCP server" /></a>

## Features

### Browser Operations
- `take_screenshot`: Capture a screenshot of a webpage
- `get_html`: Retrieve the HTML content of a webpage
- `execute_js`: Execute JavaScript on a webpage

## Prerequisites

1. Install Miniconda or Anaconda
2. Create a Conda environment:
```bash
conda create -n browser-use python=3.11
conda activate browser-use
pip install browser-use
```

3. Set required API keys as environment variables:
```bash
export GEMINI_API_KEY=your_api_key
export DEEPSEEK_API_KEY=your_api_key
```

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
    "GEMINI_API_KEY": "your_api_key",
    "DEEPSEEK_API_KEY": "your_api_key"
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

### Take Screenshot
Parameters:
- url: The webpage URL
- selector: CSS selector for the element to capture

### Get HTML
Parameters:
- url: The webpage URL
- selector: CSS selector for the element to extract

### Execute JavaScript
Parameters:
- url: The webpage URL
- script: JavaScript code to execute

## Configuration

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

## License
MIT
