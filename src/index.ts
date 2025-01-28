#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import { spawn, spawnSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Increase timeout to 5 minutes
const TIMEOUT = 300000;

class BrowserUseServer {
  private server: Server;

  constructor() {
    this.server = new Server(
      {
        name: 'browser-use-server',
        version: '0.1.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    
    // Error handling
    this.server.onerror = (error) => console.error('[MCP Error]', error);
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  private hasXvfb(): boolean {
    const result = spawnSync('which', ['xvfb-run']);
    return result.status === 0;
  }

  private runPythonScript(args: object): Promise<any> {
    return new Promise((resolve, reject) => {
      const pythonScript = path.join(__dirname, 'browser_handler.py');
      const hasXvfb = this.hasXvfb();
      const command = hasXvfb ? 'xvfb-run' : 'conda';
      const commandArgs = hasXvfb 
        ? ['--auto-servernum', 'conda', 'run', '-n', 'browser-use', 'python', pythonScript, JSON.stringify(args)]
        : ['run', '-n', 'browser-use', 'python', pythonScript, JSON.stringify(args)];
      
      const pythonProcess = spawn(command, commandArgs, {
        env: {
          ...process.env,
          PYTHONUNBUFFERED: '1',
          DISPLAY: process.env.DISPLAY || ':0',
          XAUTHORITY: process.env.XAUTHORITY || `${process.env.HOME}/.Xauthority`,
          RUNNING_UNDER_XVFB: this.hasXvfb() ? 'true' : 'false',
          GEMINI_API_KEY: process.env.GEMINI_API_KEY,
          DEEPSEEK_API_KEY: process.env.DEEPSEEK_API_KEY, // Keep for backwards compatibility
        }
      });

      let stdoutChunks: Buffer[] = [];
      let stderrChunks: Buffer[] = [];

      pythonProcess.stdout.on('data', (chunk: Buffer) => {
        console.error('[Python stdout chunk]', chunk.toString('utf8'));
        stdoutChunks.push(chunk);
      });

      pythonProcess.stderr.on('data', (chunk: Buffer) => {
        console.error('[Python stderr chunk]', chunk.toString('utf8'));
        stderrChunks.push(chunk);
      });

      // Set timeout for Python script execution
      const timeout = setTimeout(() => {
        pythonProcess.kill();
        reject(new Error('Python script execution timed out'));
      }, TIMEOUT);

      pythonProcess.on('close', (code) => {
        clearTimeout(timeout);
        if (code !== 0) {
          const stderr = Buffer.concat(stderrChunks).toString('utf8');
          reject(new Error(`Python script failed with code ${code}: ${stderr}`));
          return;
        }

        try {
          const stdout = Buffer.concat(stdoutChunks).toString('utf8');
          const stderr = Buffer.concat(stderrChunks).toString('utf8');
          
          console.error('[Final stdout]', stdout);
          console.error('[Final stderr]', stderr);

          try {
            // Try to find JSON in the output
            const lines = stdout.split('\n');
            const jsonStr = lines.find(line => {
              try {
                const parsed = JSON.parse(line.trim());
                return parsed && typeof parsed === 'object';
              } catch {
                return false;
              }
            });

            if (!jsonStr) {
              reject(new Error('No JSON output found in:\n' + stdout));
              return;
            }

            const result = JSON.parse(jsonStr);
            console.error('[Parsed result]', result);
            resolve(result);
          } catch (error) {
            reject(new Error('Failed to parse JSON from output'));
          }
        } catch (error) {
          const stdout = Buffer.concat(stdoutChunks).toString('utf8');
          reject(new Error(`Failed to parse Python script output: ${error}\nOutput was: ${stdout}`));
        }
      });
    });
  }

  private setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'screenshot',
          description: 'Take a screenshot of a webpage',
          inputSchema: {
            type: 'object',
            properties: {
              url: {
                type: 'string',
                description: 'The URL to navigate to',
              },
              full_page: {
                type: 'boolean',
                description: 'Whether to capture the full page or just the viewport',
                default: false,
              },
              steps: {
                type: 'string',
                description: 'Comma-separated actions or sentences describing steps to take after page load (e.g., "click #submit, scroll down" or "Fill the login form and submit")',
              },
            },
            required: ['url'],
          },
        },
        {
          name: 'get_html',
          description: 'Get the HTML content of a webpage',
          inputSchema: {
            type: 'object',
            properties: {
              url: {
                type: 'string',
                description: 'The URL to navigate to',
              },
              steps: {
                type: 'string',
                description: 'Comma-separated actions or sentences describing steps to take after page load (e.g., "click #submit, scroll down" or "Fill the login form and submit")',
              },
            },
            required: ['url'],
          },
        },
        {
          name: 'execute_js',
          description: 'Execute JavaScript code on a webpage',
          inputSchema: {
            type: 'object',
            properties: {
              url: {
                type: 'string',
                description: 'The URL to navigate to',
              },
              script: {
                type: 'string',
                description: 'The JavaScript code to execute',
              },
              steps: {
                type: 'string',
                description: 'Comma-separated actions or sentences describing steps to take after page load (e.g., "click #submit, scroll down" or "Fill the login form and submit")',
              },
            },
            required: ['url', 'script'],
          },
        },
        {
          name: 'get_console_logs',
          description: 'Get the console logs of a webpage',
          inputSchema: {
            type: 'object',
            properties: {
              url: {
                type: 'string',
                description: 'The URL to navigate to',
              },
              steps: {
                type: 'string',
                description: 'Comma-separated actions or sentences describing steps to take after page load (e.g., "click #submit, scroll down" or "Fill the login form and submit")',
              },
            },
            required: ['url'],
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const validCommands = ['screenshot', 'get_html', 'execute_js', 'get_console_logs'];
      if (!validCommands.includes(request.params.name)) {
        throw new McpError(
          ErrorCode.MethodNotFound,
          `Unknown tool: ${request.params.name}`
        );
      }

      const args = request.params.arguments as Record<string, any>;
      if (typeof args.url !== 'string') {
        throw new McpError(
          ErrorCode.InvalidParams,
          'URL must be a string'
        );
      }

      if (request.params.name === 'execute_js' && typeof args.script !== 'string') {
        throw new McpError(
          ErrorCode.InvalidParams,
          'Script must be a string'
        );
      }

      try {
        const result = await this.runPythonScript({
          command: request.params.name,
          ...args,
        });

        if (!result.success) {
          throw new Error(result.error);
        }

        if (request.params.name === 'screenshot') {
          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify({
                  status: `Screenshot successful.`,
                  path: result.filepath,
                  // screenshot: 'Data: ' + result.screenshot
                })
              },
            ],
          };
        } else if (request.params.name === 'get_html') {
          return {
            content: [
              {
                type: 'text',
                text: result.html,
              },
            ],
          };
        } else if (request.params.name === 'get_console_logs') {
          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify(result.logs, null, 2),
              },
            ],
          };
        } else {
          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify(result.result, null, 2),
              },
            ],
          };
        }
      } catch (error) {
        if (error instanceof Error) {
          throw new McpError(
            ErrorCode.InternalError,
            `Browser operation failed: ${error.message}`
          );
        }
        throw error;
      }
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Browser Use MCP server running on stdio');
  }
}

const server = new BrowserUseServer();
server.run().catch(console.error);
