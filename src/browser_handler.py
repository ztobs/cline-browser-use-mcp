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

# Load environment variables from .env file
load_dotenv()

async def handle_command(command, args):
    """Handle different browser commands"""
    print("[DEBUG] Starting command handling")
    api_key = os.getenv('GEMINI_API_KEY')
    print(f"[DEBUG] Got API key: {'Yes' if api_key else 'No'}")
    if not api_key:
        return {
            'success': False,
            'error': 'GEMINI_API_KEY is not set'
        }

    # DeepSeek implementation (commented out)
    # api_key = os.getenv('DEEPSEEK_API_KEY')
    # if not api_key:
    #     return {
    #         'success': False,
    #         'error': 'DEEPSEEK_API_KEY is not set'
    #     }
    # llm = ChatOpenAI(
    #     base_url='https://api.deepseek.com/v1',
    #     model='deepseek-reasoner',
    #     api_key=SecretStr(api_key),
    # )

    # Gemini implementation (active)
    print("[DEBUG] Initializing Gemini LLM")
    try:
        llm = ChatGoogleGenerativeAI(
            model='gemini-2.0-flash-exp',
            api_key=SecretStr(api_key),
        )
        print("[DEBUG] LLM initialized successfully")
    except Exception as e:
        print(f"[DEBUG] Error initializing LLM: {str(e)}")
        raise

    print("[DEBUG] Configuring browser")
    # Configure browser with longer timeouts
    context_config = BrowserContextConfig(
        minimum_wait_page_load_time=2.0,
        wait_for_network_idle_page_load_time=5.0,
        maximum_wait_page_load_time=120.0
    )
    config = BrowserConfig(
        headless=True,
        new_context_config=context_config
    )
    browser = Browser(config=config)
    try:
        if command == 'screenshot':
            if not args.get('url'):
                return {
                    'success': False,
                    'error': 'URL is required for screenshot command'
                }
            
            task = f"1. Go to {args['url']}\n2. Take a screenshot"
            if args.get('full_page'):
                task += " of the full page"
            
            print(f"[DEBUG] Creating agent for task: {task}")
            agent = Agent(task=task, llm=llm, use_vision=False, browser=browser)
            print("[DEBUG] Running agent")
            await agent.run()
            print("[DEBUG] Agent run completed")
            
            # Get the screenshot from the browser context
            context = await browser.new_context()
            try:
                await context.navigate_to(args['url'])
                screenshot = await context.take_screenshot(full_page=args.get('full_page', False))
                return {
                    'success': True,
                    'screenshot': screenshot
                }
            finally:
                await context.close()
                
        elif command == 'get_html':
            if not args.get('url'):
                return {
                    'success': False,
                    'error': 'URL is required for get_html command'
                }
                
            task = f"1. Go to {args['url']}\n2. Get the page HTML"
            agent = Agent(task=task, llm=llm, use_vision=False, browser=browser)
            await agent.run()
            
            # Get the HTML from the browser context
            context = await browser.new_context()
            try:
                await context.navigate_to(args['url'])
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
                
            task = f"1. Go to {args['url']}\n2. Execute JavaScript: {args['script']}"
            agent = Agent(task=task, llm=llm, use_vision=False, browser=browser)
            await agent.run()
            
            # Execute JavaScript in the browser context
            context = await browser.new_context()
            try:
                await context.navigate_to(args['url'])
                result = await context.execute_javascript(args['script'])
                return {
                    'success': True,
                    'result': result
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
