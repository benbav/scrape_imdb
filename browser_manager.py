import asyncio
import json
import sys
import os
from playwright.async_api import Playwright, async_playwright
from typing import Dict, Any
from config import IMDBConfig, IMDBConstants, SCRIPT_DIR
from logger import get_logger
from file_manager import FileManager

logger = get_logger(__name__)

class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
    
    async def create_stealth_browser(self):
        """Create a stealth browser with anti-detection measures"""
        import platform
        
        # Set temp directory for Playwright only on Linux
        if platform.system() == "Linux":
            temp_dir = os.path.expanduser('~/tmp')
            os.makedirs(temp_dir, exist_ok=True)
            os.environ['TMPDIR'] = temp_dir
        
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
            accept_downloads=True,
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
        # Validate config values before attempting login
        if not config.login or not config.password:
            raise ValueError("Login credentials are missing. Please check your .env file.")
        
        self.page = await self.context.new_page()
        
        try:
            logger.info("Navigating to IMDB login page...")
            # First try to navigate to the main IMDB page to test connectivity
            await self.page.goto("https://www.imdb.com/", timeout=30000)
            await asyncio.sleep(2)
            logger.info("Successfully loaded main IMDB page")
            
            # Now navigate to the login page
            await self.page.goto("https://www.imdb.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.imdb.com%2Fregistration%2Fap-signin-handler%2Fimdb_us&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=imdb_us&openid.mode=checkid_setup&siteState=eyJvcGVuaWQuYXNzb2NfaGFuZGxlIjoiaW1kYl91cyIsInJlZGlyZWN0VG8iOiJodHRwczovL3d3dy5pbWRiLmNvbS8_cmVmXz1sb2dpbiJ9&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&tag=imdbtag_reg-20", timeout=30000)
            await asyncio.sleep(3)  # Wait longer for page to load
            
            logger.info("Waiting for login form to appear...")
            # Wait for the login form to be visible
            await self.page.wait_for_selector('input[name="email"]', timeout=10000)
            await asyncio.sleep(2)
            
            logger.info("Filling in login credentials...")
            # Fill in login credentials
            await self.page.get_by_role("textbox", name="Email or mobile phone number").fill(config.login)
            await asyncio.sleep(1)
            await self.page.get_by_role("textbox", name="Password").fill(config.password)
            await asyncio.sleep(2)
            
            logger.info("Clicking sign in button...")
            # Click sign in button
            await self.page.get_by_role("button", name="Sign in").click() 
            await asyncio.sleep(5)  # Wait longer for login to complete
            
            logger.info("Login successful")
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            # Take a screenshot for debugging
            screenshot_path = os.path.join(SCRIPT_DIR, 'login_error.jpg')
            await self.page.screenshot(path=screenshot_path)
            logger.error(f"Screenshot saved to {screenshot_path}")
            raise

    async def get_cookies(self, config: IMDBConfig) -> Dict[str, str]:
        """Get cookies after login"""
        logger.info("Getting cookies...")
        try:
            # Wait a bit longer after login before checking for cookies
            await asyncio.sleep(3)
            
            cookies = await self.context.cookies()
            cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}

            # Log what cookies we have initially
            logger.info(f"Initial cookies found: {list(cookies_dict.keys())}")

            try_count = 0
            while not cookies_dict.get('ci'):
                if try_count > IMDBConstants.MAX_COOKIE_RETRIES:
                    logger.info(f'try count greater than {try_count}, exiting and taking screenshot')
                    page = await self.context.new_page()
                    # screenshot_path = os.path.join(SCRIPT_DIR, 'test1.jpg')
                    await page.screenshot(path=screenshot_path)
                    logger.error("Failed to get required cookies after maximum retries")
                    logger.error(f"Available cookies: {list(cookies_dict.keys())}")
                    raise Exception("Failed to get required cookies after maximum retries")
                await asyncio.sleep(IMDBConstants.COOKIE_RETRY_DELAY)
                cookies = await self.context.cookies()
                cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
                try_count += 1
                logger.info(f"Cookie check attempt {try_count}/{IMDBConstants.MAX_COOKIE_RETRIES}, cookies: {list(cookies_dict.keys())}")
                
                # Check if we have the ci cookie
                if cookies_dict.get('ci'):
                    logger.info(f"Found 'ci' cookie: {cookies_dict['ci']}")
                    break

            # Save cookies to file
            FileManager.save_json(cookies_dict, IMDBConstants.COOKIES_FILE)
            logger.info("Cookies saved to file")
            
            return cookies_dict
        except Exception as e:
            logger.error(f"Error getting cookies: {e}")
            if self.page:
                screenshot_path = os.path.join(SCRIPT_DIR, 'cookies_error.jpg')
                await self.page.screenshot(path=screenshot_path)
                logger.error(f"Screenshot saved to {screenshot_path}")
            raise

    async def get_export_csv(self, config: IMDBConfig) -> None:
        """Get export csv after login"""
        logger.info("Getting export csv...")
         # go to watchlist page
        await self.page.goto('https://www.imdb.com/user/ur155626863/watchlist/?ref_=exp_nv_urwls_all')

        # wait for page to load with fallback options
        try:
            logger.info("Waiting for page to load (networkidle)...")
            await self.page.wait_for_load_state('networkidle', timeout=15000)
            logger.info("Page loaded successfully (networkidle)")
        except Exception as e:
            logger.warning(f"Networkidle timeout, trying domcontentloaded: {e}")
            try:
                await self.page.wait_for_load_state('domcontentloaded', timeout=10000)
                logger.info("Page loaded successfully (domcontentloaded)")
            except Exception as e2:
                logger.warning(f"Domcontentloaded timeout, using sleep fallback: {e2}")
                await asyncio.sleep(5)
                logger.info("Using sleep fallback for page load")
        
        await asyncio.sleep(3)

        # Try to find the Export button with multiple approaches
        logger.info("Looking for Export button...")
        export_button = None
        
        try:
            # First try: Look for Export button by role
            export_button = self.page.get_by_role('button', name='Export')
            await export_button.wait_for(timeout=5000)
            logger.info("Found Export button by role")
        except Exception as e:
            logger.warning(f"Could not find Export button by role: {e}")
            try:
                # Second try: Look for any button with "Export" text
                export_button = self.page.locator('button:has-text("Export")')
                await export_button.wait_for(timeout=5000)
                logger.info("Found Export button by text")
            except Exception as e2:
                logger.warning(f"Could not find Export button by text: {e2}")
                try:
                    # Third try: Look for link with "Export" text
                    export_button = self.page.locator('a:has-text("Export")')
                    await export_button.wait_for(timeout=5000)
                    logger.info("Found Export link by text")
                except Exception as e3:
                    logger.error(f"Could not find any Export button/link: {e3}")
                    # Take a screenshot for debugging
                    screenshot_path = os.path.join(SCRIPT_DIR, 'export_button_not_found.jpg')
                    await self.page.screenshot(path=screenshot_path)
                    logger.error(f"Screenshot saved to {screenshot_path}")
                    raise Exception("Export button not found on page")

        # Click the Export button
        await export_button.click()
        logger.info("Clicked Export button")

        await asyncio.sleep(5)

        await self.page.get_by_role("link", name="Open exports page").click()

        # go to export page

        # while this is visible, refresh the page, wait to load : await page.get_by_text("In progress").click()
        while await self.page.get_by_text("In progress").is_visible():
            logger.info("In progress is visible, refreshing page")
            await self.page.reload()
            await asyncio.sleep(5)

            # wait for page to load with fallback options
            try:
                logger.info("Waiting for export page to load (networkidle)...")
                await self.page.wait_for_load_state('networkidle', timeout=15000)
                logger.info("Export page loaded successfully (networkidle)")
            except Exception as e:
                logger.warning(f"Export page networkidle timeout, trying domcontentloaded: {e}")
                try:
                    await self.page.wait_for_load_state('domcontentloaded', timeout=10000)
                    logger.info("Export page loaded successfully (domcontentloaded)")
                except Exception as e2:
                    logger.warning(f"Export page domcontentloaded timeout, using sleep fallback: {e2}")
                    await asyncio.sleep(5)
                    logger.info("Using sleep fallback for export page load")

        # # wait for 10 seconds
        await asyncio.sleep(10)

        try:
            logger.info("Waiting for export page to load (networkidle)...")
            await self.page.wait_for_load_state('networkidle', timeout=15000)
            logger.info("Export page loaded successfully (networkidle)")
        except Exception as e:
            logger.warning(f"Export page networkidle timeout, trying domcontentloaded: {e}")
            try:
                await self.page.wait_for_load_state('domcontentloaded', timeout=10000)
                logger.info("Export page loaded successfully (domcontentloaded)")
            except Exception as e2:
                logger.warning(f"Export page domcontentloaded timeout, using sleep fallback: {e2}")
                await asyncio.sleep(5)
                logger.info("Using sleep fallback for export page load")

        await asyncio.sleep(10)
        try:
            async with self.page.expect_download() as download_info:
                await self.page.get_by_test_id("export-status-button").first.click()
            download = await download_info.value

            await download.save_as(f"{SCRIPT_DIR}/scraped_data/imdb_cleaned_upload.csv")
        except Exception as e:
            logger.error(f"Error downloading export: {e}")
            screenshot_path = os.path.join(SCRIPT_DIR, 'export_error.jpg')
            await self.page.screenshot(path=screenshot_path)
            logger.error(f"Screenshot saved to {screenshot_path}")
    
    async def get_sha_hash(self, config: IMDBConfig) -> None:
        """Get sha hash from network requests after clicking on elements"""
        logger.info("Getting sha hash from network requests...")
        
        # Set up network request interception
        graphql_hashes = []
        
        def handle_request(request):
            if 'api.graphql.imdb.com' in request.url or 'caching.graphql.imdb.com' in request.url:
                try:
                    url = request.url
                    # logger.info(f"GraphQL request detected: {url}")
                    
                    # Look for any GraphQL request with sha256Hash
                    if 'sha256Hash' in url:
                        import re
                        # Try multiple patterns to extract the hash
                        patterns = [
                            r'sha256Hash["\']:\s*["\']([^"\']+)["\']',  # JSON format
                            r'sha256Hash=([a-f0-9]{64})',  # URL parameter format
                            r'sha256Hash%22%3A%22([a-f0-9]{64})',  # URL encoded format
                        ]
                        
                        hash_val = None
                        for pattern in patterns:
                            match = re.search(pattern, url)
                            if match:
                                hash_val = match.group(1)
                                break
                        
                        if hash_val:
                            # logger.info(f"Found GraphQL hash: {hash_val}")
                            
                            # Check if this is a Title_Summary_Prompt_From_Base operation
                            if 'Title_Summary_Prompt_From_Base' in url:
                                logger.info("Found Title_Summary_Prompt_From_Base operation!")
                                graphql_hashes.append(hash_val)
                            elif 'PersonalizedUserData' in url:
                                logger.info("Found PersonalizedUserData operation!")
                                graphql_hashes.append(hash_val)
                            else:
                                # Store other hashes as backup
                                graphql_hashes.append(hash_val)
                except Exception as e:
                    logger.warning(f"Error parsing request URL: {e}")
        
        # Add the request handler
        self.page.on('request', handle_request)

        try:
            # Navigate to watchlist page
            logger.info("Navigating to watchlist page...")
            try:
                
                # First try to find and click on a watchlist link
                await asyncio.sleep(3)
                await self.page.goto("https://www.imdb.com/user/ur155626863/watchlist/?ref_=hm_nv_urwls_all", timeout=30000)
                logger.info("Successfully navigated to watchlist page")
            except Exception as e:
                logger.warning(f"Could not navigate to watchlist page: {e}")

            
            await asyncio.sleep(3)
            
            # Wait for page to load
            try:
                await self.page.wait_for_load_state('networkidle', timeout=15000)
                logger.info("Watchlist page loaded successfully")
            except:
                await asyncio.sleep(5)
            
            # Click on "See more information about Breaking Bad" button
            logger.info("Clicking on 'See more information about Breaking Bad' button...")

            try:
                await self.page.get_by_role("button", name="See more information about Breaking Bad").click()
                logger.info("Successfully clicked Breaking Bad button")
            except Exception as e:
                logger.warning(f"Could not click Breaking Bad button: {e}")
                # Try alternative selectors for Breaking Bad
                try:
                    await self.page.get_by_role("link", name="1. Breaking Bad").click(timeout=5000)
                    logger.info("Clicked on Breaking Bad link using alternative selector")
                except Exception as e2:
                    logger.warning(f"Could not click Breaking Bad link with alternative selector: {e2}")
                    # Try navigating directly to Breaking Bad page
                   
            # Wait for network requests to complete
            await asyncio.sleep(5)
            
            # Wait for any additional requests
            try:
                await self.page.wait_for_load_state('networkidle', timeout=15000)
            except:
                await asyncio.sleep(5)


            # Check if we found any hashes
            if graphql_hashes:
                logger.info(f"Found {len(graphql_hashes)} GraphQL hashes:")
                for i, hash_val in enumerate(graphql_hashes):
                    logger.info(f"  Hash {i+1}: {hash_val}")
                
                # Save the hashes to a JSON file
                hash_data = {
                    'graphql_hashes': graphql_hashes,
                    'timestamp': asyncio.get_event_loop().time()
                }
                FileManager.save_json(hash_data, IMDBConstants.GRAPHQL_HASH_FILE)
                logger.info("GraphQL hashes saved to JSON file")
                
                # Check if we have the specific hash we need
                target_hash = "8b4249ea40b309e5bc4f32ae7e618c77c9da1ed155ffd584b3817f980fb29dd3"
                if target_hash in graphql_hashes:
                    logger.info(f"✓ Found target hash: {target_hash}")
                else:
                    logger.warning(f"✗ Target hash not found: {target_hash}")
            else:
                logger.warning("No GraphQL hashes found in network requests")
                
        except Exception as e:
            logger.error(f"Error getting sha hash: {e}")
            screenshot_path = os.path.join(SCRIPT_DIR, 'sha_hash_error.jpg')
            await self.page.screenshot(path=screenshot_path)
            logger.error(f"Screenshot saved to {screenshot_path}")
            raise
    
    async def get_playwright_data(self, config: IMDBConfig) -> None:
        """Get playwright data after login and save cookies to scraped_data folder"""

        # login
        await self.login(config)

        # get cookies
        await self.get_cookies(config)

        # get sha hash
        await self.get_sha_hash(config)

        # get export csv
        await self.get_export_csv(config) 
    
    async def close(self):
        """Close browser and context"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop() 