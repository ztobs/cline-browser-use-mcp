from browser_use import Agent, Browser
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
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

    api_key = os.getenv('GEMINI_API_KEY')
    print(f"[DEBUG] Got API key: {'Yes' if api_key else 'No'}")
    if not api_key:
        return {
            'success': False,
            'error': 'API_KEY is not set'
        }

    # DeepSeek implementation (commented out) DEEPSEEK_API_KEY
    # llm = ChatOpenAI(
    #     base_url='https://api.deepseek.com/v1',
    #     model='deepseek-chat',
    #     api_key=SecretStr(api_key),
    # )

    # Gemini implementation (active) GEMINI_API_KEY
    llm = ChatGoogleGenerativeAI(
        model='gemini-2.0-flash-exp',
        api_key=SecretStr(api_key),
    )

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
    config = BrowserConfig(
        headless=True,
        disable_security=True,
        new_context_config=context_config
    )
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
            agent = Agent(task=task, llm=llm, use_vision=False, browser_context=context)
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
            agent = Agent(task=task, llm=llm, use_vision=False, browser_context=context)
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
            agent = Agent(task=task, llm=llm, use_vision=False, browser_context=context)
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
            agent = Agent(task=task, llm=llm, use_vision=False, browser_context=context)
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
