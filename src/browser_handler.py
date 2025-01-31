from browser_use import Agent, Browser
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from pydantic import SecretStr
from browser_use.browser.browser import BrowserConfig
from browser_use.browser.context import BrowserContextConfig
from dotenv import load_dotenv
import json
import base64
import sys
import asyncio
import os
import time

# Load environment variables from .env file
load_dotenv()

SCREENSHOT_DIR = os.path.join('.', 'screenshots')

async def handle_command(command, args):
    """Handle different browser commands"""

    # Ensure screenshot directory exists
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    # Define LLM configurations
    llm_configs = {
        'OLLAMA_API_KEY': {
            'class': ChatOllama,
            'params': {
                'base_url': 'http://localhost:11434',
                'model': 'qwen2.5:32b-instruct-q4_K_M',
                'num_ctx': 32000
            }
        },
        'GLHF_API_KEY': {
            'class': ChatOpenAI,
            'params': {
                'base_url': 'https://glhf.chat/api/openai/v1',
                'model': 'deepseek-ai/DeepSeek-V3'
            }
        },
        'GROQ_API_KEY': {
            'class': ChatOpenAI,
            'params': {
                'base_url': 'https://api.groq.com/openai/v1',
                'model': 'deepseek-r1-distill-llama-70b'
            }
        },
        'OPENAI_API_KEY': {
            'class': ChatOpenAI,
            'params': {
                'base_url': 'https://api.openai.com/v1',
                'model': 'gpt-4o-mini'
            }
        },
        'OPENROUTER_API_KEY': {
            'class': ChatOpenAI,
            'params': {
                'base_url': 'https://openrouter.ai/api/v1',
                'model': 'deepseek/deepseek-chat'
            }
        },
        'GITHUB_API_KEY': {
            'class': ChatOpenAI,
            'params': {
                'base_url': 'https://models.inference.ai.azure.com',
                'model': 'gpt-4o-mini'
            }
        },
        'DEEPSEEK_API_KEY': {
            'class': ChatOpenAI,
            'params': {
                'base_url': 'https://api.deepseek.com/v1',
                'model': 'deepseek-chat'
            }
        },
        'GEMINI_API_KEY': {
            'class': ChatGoogleGenerativeAI,
            'params': {
                'model': 'gemini-2.0-flash-exp'
            }
        }
    }

    # Check for available API keys and select the first one found
    for env_key, config in llm_configs.items():
        api_key = os.getenv(env_key)
        if api_key:
            print(f"[DEBUG] Using {env_key}")
            llm_class = config['class']
            params = config['params'].copy()  # Create a copy to avoid modifying the original
            
            # Check if MODEL env var is set and override the default model
            custom_model = os.getenv('MODEL')
            if custom_model:
                print(f"[DEBUG] Using custom model: {custom_model}")
                params['model'] = custom_model
            
            # Check if BASE_URL env var is set and override the default base_url
            custom_base_url = os.getenv('BASE_URL')
            if custom_base_url and 'base_url' in params:
                print(f"[DEBUG] Using custom base URL: {custom_base_url}")
                params['base_url'] = custom_base_url
            
            params['api_key'] = SecretStr(api_key)
            llm = llm_class(**params)
            break
    else:
        return {
            'success': False,
            'error': 'No API key found. Please set one of the following environment variables: ' + ', '.join(llm_configs.keys())
        }

    # Configure browser with longer timeouts
    context_config = BrowserContextConfig(
        save_recording_path="../generated/recordings/",
        cookies_file="../generated/cookies.json",
        wait_for_network_idle_page_load_time=3.0,
        browser_window_size={'width': 1280, 'height': 1100},
        locale='en-US',
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
        highlight_elements=True,
        viewport_expansion=500,
        # allowed_domains=['google.com', 'wikipedia.org'],
    )
    
    # Check if running under xvfb-run
    running_under_xvfb = os.getenv('RUNNING_UNDER_XVFB') == 'true'
    
    config_args = {
        'headless': True,
        'disable_security': True,
        'new_context_config': context_config
    }
    
    # Only include chrome_instance_path when running under xvfb
    if running_under_xvfb:
        config_args['chrome_instance_path'] = '/usr/bin/google-chrome'
        config_args['headless'] = False

    
    config = BrowserConfig(**config_args)
    browser = Browser(config=config)
    context = await browser.new_context()
    
    try:
        if command == 'screenshot':
            if not args.get('url'):
                return {
                    'success': False,
                    'error': 'URL is required for screenshot command'
                }
            
            task = f"1. Go to {args['url']}"
            if args.get('steps'):
                steps = args['steps'].split(',')
                for i, step in enumerate(steps, 2):
                    task += f"\n{i}. {step.strip()}"
                task += f"\n{len(steps) + 2}. Take a screenshot"
            else:
                task += "\n2. Take a screenshot"
            if args.get('full_page'):
                task += " of the full page"
            
            print(f"[DEBUG] Creating agent for task: {task}")
            use_vision = os.getenv('USE_VISION', 'false').lower() == 'true'
            agent = Agent(task=task, llm=llm, use_vision=use_vision, browser_context=context)
            print("[DEBUG] Running agent")
            await agent.run()
            print("[DEBUG] Agent run completed")
            
            # Get the screenshot from the browser context
            try:
                # await context.navigate_to(args['url'])
                screenshot_base64 = await context.take_screenshot(full_page=args.get('full_page', False))
                filename = f"screenshot_{int(time.time())}.png"
                filepath = os.path.join(SCREENSHOT_DIR, filename)
                
                # Decode base64 and save image
                screenshot_bytes = base64.b64decode(screenshot_base64)
                with open(filepath, 'wb') as f:
                    f.write(screenshot_bytes)
                    
                return {
                    'success': True,
                    'screenshot': screenshot_base64, # Keep base64 for potential direct display
                    'filepath': os.path.abspath(filepath) # Include full file path in response
                }
            finally:
                await context.close()
                
        elif command == 'get_html':
            if not args.get('url'):
                return {
                    'success': False,
                    'error': 'URL is required for get_html command'
                }
                
            task = f"1. Go to {args['url']}"
            if args.get('steps'):
                steps = args['steps'].split(',')
                for i, step in enumerate(steps, 2):
                    task += f"\n{i}. {step.strip()}"
                task += f"\n{len(steps) + 2}. Get the page HTML"
            else:
                task += "\n2. Get the page HTML"
            use_vision = os.getenv('USE_VISION', 'false').lower() == 'true'
            agent = Agent(task=task, llm=llm, use_vision=use_vision, browser_context=context)
            await agent.run()
            
            try:
                html = await context.get_page_html()
                return {
                    'success': True,
                    'html': html
                }
            finally:
                await context.close()
                
        elif command == 'execute_js':
            if not args.get('url') or not args.get('script'):
                return {
                    'success': False,
                    'error': 'URL and script are required for execute_js command'
                }

            task = f"1. Go to {args['url']}"
            if args.get('steps'):
                steps = args['steps'].split(',')
                for i, step in enumerate(steps, 2):
                    task += f"\n{i}. {step.strip()}"
                task += f"\n{len(steps) + 2}. Execute JavaScript: {args['script']}"
            else:
                task += f"\n2. Execute JavaScript: {args['script']}"
            use_vision = os.getenv('USE_VISION', 'false').lower() == 'true'
            agent = Agent(task=task, llm=llm, use_vision=use_vision, browser_context=context)
            await agent.run()

            try:
                result = await context.execute_javascript(args['script'])
                return {
                    'success': True,
                    'result': result
                }
            finally:
                await context.close()
        elif command == 'get_console_logs':
            if not args.get('url'):
                return {
                    'success': False,
                    'error': 'URL is required for get_console_logs command'
                }

            console_messages = []
            def on_console_message(msg):
                console_messages.append(f"type: {msg.type}, text: {msg.text}, location: {msg.location}")

            task = f"1. Go to {args['url']}"
            if args.get('steps'):
                steps = args['steps'].split(',')
                for i, step in enumerate(steps, 2):
                    task += f"\n{i}. {step.strip()}"
                task += f"\n{len(steps) + 2}. Get the console logs"
            else:
                task += f"\n2. Get the console logs"
            use_vision = os.getenv('USE_VISION', 'false').lower() == 'true'
            agent = Agent(task=task, llm=llm, use_vision=use_vision, browser_context=context)
            await agent.run()

            try:
                # Execute JavaScript to get console logs
                await context.execute_javascript("""
                    window._consoleLogs = [];
                    const originalConsole = window.console;
                    ['log', 'info', 'warn', 'error'].forEach(level => {
                        window.console[level] = (...args) => {
                            window._consoleLogs.push({type: level, text: args.join(' ')});
                            originalConsole[level](...args);
                        };
                    });
                """)
                
                # Wait a bit for any console logs to be captured
                await asyncio.sleep(1)
                
                # Get the captured logs
                logs = await context.execute_javascript("window._consoleLogs")
                return {
                    'success': True,
                    'logs': logs
                }
            finally:
                await context.close()


        else:
            return {
                'success': False,
                'error': f'Unknown command: {command}'
            }
    finally:
        await browser.close()

async def main():
    # Read command line arguments as JSON
    args = json.loads(sys.argv[1])
    command = args.get('command')

    try:
        result = await handle_command(command, args)
    except Exception as e:
        result = {
            'success': False,
            'error': str(e)
        }

    # Output result as JSON
    print(json.dumps(result))

if __name__ == "__main__":
    asyncio.run(main())
