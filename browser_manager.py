import asyncio
import json
import sys
from playwright.async_api import Playwright, async_playwright
from typing import Dict, Any
from config import IMDBConfig, IMDBConstants
from logger import get_logger
from file_manager import FileManager

logger = get_logger(__name__)

class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
    
    async def create_stealth_browser(self):
        """Create a stealth browser with anti-detection measures"""
        self.playwright = await async_playwright().start()
        
        # Use a more recent Chrome version
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=VizDisplayCompositor',
                '--disable-web-security',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-field-trial-config',
                '--disable-back-forward-cache',
                '--disable-default-apps',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-translate',
                '--hide-scrollbars',
                '--mute-audio',
                '--disable-background-networking',
                '--disable-sync',
                '--disable-default-apps',
                '--no-default-browser-check',
                '--disable-client-side-phishing-detection',
                '--disable-component-update',
                '--disable-domain-reliability',
                '--disable-features=AudioServiceOutOfProcess',
                '--disable-hang-monitor',
                '--disable-prompt-on-repost',
            ]
        )
        
        self.context = await self.browser.new_context(
            user_agent=user_agent,
            viewport={'width': 1920, 'height': 1080},
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
            locale='en-US',
            timezone_id='America/New_York',
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},  # NYC coordinates
            permissions=['geolocation'],
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'max-age=0',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
            }
        )
        
        # Add JavaScript to remove webdriver traces
        await self.context.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Mock Chrome runtime
            window.chrome = {
                runtime: {},
            };
            
            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Mock connection
            Object.defineProperty(navigator, 'connection', {
                get: () => ({
                    effectiveType: '4g',
                    downlink: 10,
                    rtt: 50
                }),
            });
            
            // Remove automation indicators
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        """)
    
    async def login(self, config: IMDBConfig) -> None:
        """Login to IMDB"""
        page = await self.context.new_page()
        
        await page.goto("https://www.imdb.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.imdb.com%2Fregistration%2Fap-signin-handler%2Fimdb_us&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=imdb_us&openid.mode=checkid_setup&siteState=eyJvcGVuaWQuYXNzb2NfaGFuZGxlIjoiaW1kYl91cyIsInJlZGlyZWN0VG8iOiJodHRwczovL3d3dy5pbWRiLmNvbS8_cmVmXz1sb2dpbiJ9&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&tag=imdbtag_reg-20")
        await asyncio.sleep(1)
        await page.get_by_role("textbox", name="Email or mobile phone number").fill(config.login)
        await page.get_by_role("textbox", name="Password").fill(config.password)
        await asyncio.sleep(1)
        await page.get_by_role("button", name="Sign in").click() 
        await asyncio.sleep(1)
        logger.info("Login successful")
    
    async def get_cookies(self, config: IMDBConfig) -> Dict[str, str]:
        """Get cookies after login"""
        await self.login(config)
        
        cookies = await self.context.cookies()
        cookies_dict = {}

        try_count = 0
        while not cookies_dict.get('ci'):
            if try_count > IMDBConstants.MAX_COOKIE_RETRIES:
                logger.info(f'try count greater than {try_count}, exiting and taking screenshot')
                page = await self.context.new_page()
                await page.screenshot(path='test1.jpg')
                sys.exit()
            await asyncio.sleep(IMDBConstants.COOKIE_RETRY_DELAY)
            cookies = await self.context.cookies()
            cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            try_count += 1

        # Save cookies to file
        FileManager.save_json(cookies_dict, IMDBConstants.COOKIES_FILE)
        logger.info("Cookies saved to file")
        
        return cookies_dict
    
    async def close(self):
        """Close browser and context"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop() 