import asyncio
import re
from playwright.async_api import Playwright, async_playwright, expect
import requests
import os
import json
import time
import logging
import sys
import pandas as pd
from sheets_upload_download import upload_to_sheets, download_from_sheets

# logging that goes to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'), # also add cron.log later
        logging.StreamHandler()
    ]
)

from dotenv import load_dotenv

def setup_env():

    # update playwright
    os.system('playwright install chromium')

    # Set main logging to INFO level
    logging.getLogger().setLevel(logging.INFO)
    
    # Suppress HTTP request logs from requests library
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

    load_dotenv()

    global imdb_login
    global imdb_pass

    imdb_login = os.getenv('imdb_login')
    imdb_pass = os.getenv('imdb_pass')

def get_session_id_time():
    return f"{int(time.time())}l"

def get_base_data(cookies_dict):

    cookies = {
        'session-id': cookies_dict['session-id'],
        'ubid-main': cookies_dict['ubid-main'],
        'ad-oo': cookies_dict['ad-oo'],
        'ci': cookies_dict['ci'],
        'at-main': cookies_dict['at-main'],
        'sess-at-main': cookies_dict['sess-at-main'],
        'uu': cookies_dict['uu'],
        'session-id-time': get_session_id_time(),
        'gpc-cache': '1',
        'x-main': cookies_dict['x-main'],
        'session-token': cookies_dict['session-token']
    }

    headers = {
        'accept': 'application/graphql+json, application/json',
        'accept-language': 'en-US,en;q=0.6',
        'content-type': 'application/json',
        'dnt': '1',
        'origin': 'https://www.imdb.com',
        'priority': 'u=1, i',
        'referer': 'https://www.imdb.com/',
        'sec-ch-ua': '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        'x-amzn-sessionid': '145-8382313-6076133',
        'x-imdb-client-name': 'imdb-web-next-localized',
        'x-imdb-client-rid': 'BJ8WQBM1FPS50N4FSAPE',
        'x-imdb-user-country': 'US',
        'x-imdb-user-language': 'en-US',
        'x-imdb-weblab-treatment-overrides': '{"IMDB_NAV_PRO_FLY_OUT_1254137":"T1"}',
    }

    params = {
        'operationName': 'RatingsPage',
        'variables': '{"filter":{"certificateConstraint":{},"explicitContentConstraint":{"explicitContentFilter":"INCLUDE_ADULT"},"genreConstraint":{},"keywordConstraint":{},"releaseDateConstraint":{"releaseDateRange":{}},"singleUserRatingConstraint":{"filterType":"INCLUDE","userId":"ur155626863"},"titleTextConstraint":{"searchTerm":""},"titleTypeConstraint":{"anyTitleTypeIds":["movie"]},"userRatingsConstraint":{"aggregateRatingRange":{},"ratingsCountRange":{}},"watchOptionsConstraint":{}},"first":250,"isInPace":false,"jumpToPosition":1,"locale":"en-US","sort":{"sortBy":"SINGLE_USER_RATING_DATE","sortOrder":"ASC"}}',
        'extensions': '{"persistedQuery":{"sha256Hash":"52aeb10821503d123f19bdd9207be68fa8163178c9ffc450d577d5c4baabe307","version":1}}',
    }

    response = requests.get('https://api.graphql.imdb.com/', params=params, cookies=cookies, headers=headers)

    if response.status_code != 200:
        logging.error(f"Error: {response.status_code}, exiting...")
        os.system('exit 1')
    
    else:
        # save response to file
        with open('imdb_ratings.json', 'w') as f:
            json.dump(response.json(), f, indent=4)

        logging.info("Data saved to file")

    if os.path.exists('imdb_ratings.json'):


        # create base_data csv
        with open('imdb_ratings.json', 'r') as f:
            j = json.load(f)
        
        cols = ['title', 'id', 'release_year', 'genres']
        df = pd.DataFrame(columns=cols)

        r = j['data']['advancedTitleSearch']['edges']

        for i in range(len(r)):
            id = r[i]['node']['title']['id']
            title = r[i]['node']['title']['titleText']['text']
            year = r[i]['node']['title']['releaseYear']['year']
            genre = ", ".join([genre['genre']['text'] for genre in r[i]['node']['title']['titleGenres']['genres']])
            df.loc[i] = [title, id, year, genre]

        df.to_csv('base_data.csv', index=False)
    else:
        logging.error('error downloading base data (imdb_ratings.json)')

async def login(page, imdb_login, imdb_pass):
    await page.goto("https://www.imdb.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.imdb.com%2Fregistration%2Fap-signin-handler%2Fimdb_us&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=imdb_us&openid.mode=checkid_setup&siteState=eyJvcGVuaWQuYXNzb2NfaGFuZGxlIjoiaW1kYl91cyIsInJlZGlyZWN0VG8iOiJodHRwczovL3d3dy5pbWRiLmNvbS8_cmVmXz1sb2dpbiJ9&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&tag=imdbtag_reg-20")
    await asyncio.sleep(1)
    await page.get_by_role("textbox", name="Email or mobile phone number").fill(imdb_login)
    await page.get_by_role("textbox", name="Password").fill(imdb_pass)
    await asyncio.sleep(1)
    await page.get_by_role("button", name="Sign in").click() 
    await asyncio.sleep(1)
    logging.info("Login successful")

async def create_stealth_browser():
    playwright = await async_playwright().start()
    
    # Use a more recent Chrome version
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    
    browser = await playwright.chromium.launch(
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
    
    context = await browser.new_context(
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
    await context.add_init_script("""
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
    
    return browser, context

async def get_cookies(playwright: Playwright) -> None:

    browser, context = await create_stealth_browser()

    # browser = await playwright.chromium.launch(headless=True)
    # context = await browser.new_context(
    #     user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    #     viewport={'width': 1920, 'height': 1080},
    #     extra_http_headers={
    #         'Accept-Language': 'en-US,en;q=0.9',
    #         'Accept-Encoding': 'gzip, deflate, br',
    #         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    #         'Connection': 'keep-alive',
    #         'Upgrade-Insecure-Requests': '1',
    #     }
    # )
    page = await context.new_page()

    await login(page, imdb_login, imdb_pass)
    
    cookies = await page.context.cookies()

    cookies_dict = {}

    try_count = 0
    while not cookies_dict.get('ci'):
        if try_count > 20:
            logging.info(f'try count greater than {try_count}, exiting and taking screenshot')
            await page.screenshot(path='test1.jpg')
            sys.exit()
        await asyncio.sleep(2)
        cookies = await page.context.cookies()
        cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        # print("Waiting for 'ci' cookie...")
        try_count +=1

    # save cookies to file
    with open('cookies.json', 'w') as f:
        json.dump(cookies_dict, f)

    logging.info("Cookies saved to file")
        # ---------------------
    await context.close()
    await browser.close()

async def playwright_get_cookies() -> None:
    async with async_playwright() as playwright:
        await get_cookies(playwright)

def get_user_data(cookies_dict):

    df = pd.read_csv('base_data.csv')

    if len(df) == 0:
        logging.error('base_data.csv has length 0, exiting')
        sys.exit()

    ids = df['id'].to_list()

    cookies = {
        'session-id': cookies_dict['session-id'],
        'ubid-main': cookies_dict['ubid-main'],
        'ad-oo': cookies_dict['ad-oo'],
        'ci': cookies_dict['ci'],
        'at-main': cookies_dict['at-main'],
        'sess-at-main': cookies_dict['sess-at-main'],
        'uu': cookies_dict['uu'],
        'session-id-time': get_session_id_time(),
        'gpc-cache': '1',
        'x-main': cookies_dict['x-main'],
        'session-token': cookies_dict['session-token']
    }

    headers = {
        'accept': 'application/graphql+json, application/json',
        'accept-language': 'en-US,en;q=0.6',
        'content-type': 'application/json',
        'dnt': '1',
        'origin': 'https://www.imdb.com',
        'priority': 'u=1, i',
        'referer': 'https://www.imdb.com/',
        'sec-ch-ua': '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        'x-amzn-sessionid': '142-2495455-9444962',
        'x-imdb-client-name': 'imdb-web-next-localized',
        'x-imdb-client-rid': 'BA1D67DHHAW7GGHP9M6Y',
        'x-imdb-user-country': 'US',
        'x-imdb-user-language': 'en-US',
        'x-imdb-weblab-treatment-overrides': '{"IMDB_NAV_PRO_FLY_OUT_1254137":"T1"}',
    }

    json_data = {
        'operationName': 'PersonalizedUserData',
        'variables': {
            'locale': 'en-US',
            'idArray': ids,
            'includeUserData': True,
            'location': {
                'postalCodeLocation': {
                    'country': 'US',
                    'postalCode': '30004',
                },
            },
            'fetchOtherUserRating': False,
        },
        'extensions': {
            'persistedQuery': {
                'version': 1,
                'sha256Hash': 'afebb5841a7a0072bc4d4c3eb29c64832e531a0846c564caf482f814e8ce12c7',
            },
        },
    }

    response = requests.post('https://api.graphql.imdb.com/', cookies=cookies, headers=headers, json=json_data)

    with open('user_data.json', 'w') as f:
        json.dump(response.json(), f, indent=4)

    with open('user_data.json', 'r') as f:
        r = json.load(f)

    base_json = r['data']['titles']

    df = pd.DataFrame(columns=['id', 'user_rating'])

    user_data = {}
    for i in range(len(base_json)):
        id = base_json[i]['id']
        user_rating = base_json[i]['userRating']['value']

        df.loc[i] = [id, user_rating]

    df.to_csv('user_ratings.csv', index=False)

def get_platform_data(cookies_dict):
    df = pd.read_csv('base_data.csv')
    ids = df['id'].to_list()

    # Add platforms column if it doesn't exist
    if 'platforms' not in df.columns:
        df['platforms'] = None

    cookies = {
        'session-id': cookies_dict['session-id'],
        'ubid-main': cookies_dict['ubid-main'],
        'ad-oo': cookies_dict['ad-oo'],
        'ci': cookies_dict['ci'],
        'at-main': cookies_dict['at-main'],
        'sess-at-main': cookies_dict['sess-at-main'],
        'uu': cookies_dict['uu'],
        'session-id-time': get_session_id_time(),
        'gpc-cache': '1',
        'x-main': cookies_dict['x-main'],
        'session-token': cookies_dict['session-token']
    }

    headers = {
        'accept': 'application/graphql+json, application/json',
        'accept-language': 'en-US,en;q=0.6',
        'content-type': 'application/json',
        'dnt': '1',
        'origin': 'https://www.imdb.com',
        'priority': 'u=1, i',
        'referer': 'https://www.imdb.com/',
        'sec-ch-ua': '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        'x-amzn-sessionid': '142-2495455-9444962',
        'x-imdb-client-name': 'imdb-web-next-localized',
        'x-imdb-client-rid': 'XR3E646TECN2QDAKHFW2',
        'x-imdb-user-country': 'US',
        'x-imdb-user-language': 'en-US',
        'x-imdb-weblab-treatment-overrides': '{"IMDB_NAV_PRO_FLY_OUT_1254137":"T1"}',
    }

    for id in ids:
        variables = {
            'id': id,
            'includeUserPreferredServices': False,
            'isInPace': False,
            'isProPage': False,
            'locale': 'en-US',
            'location': {
                'postalCodeLocation': {
                    'country': 'US',
                    'postalCode': '30004'
                }
            }
        }
        
        params = {
            'operationName': 'Title_Summary_Prompt_From_Base',
            'variables': f'{{"id":"{id}","includeUserPreferredServices":false,"isInPace":false,"isProPage":false,"locale":"en-US","location":{{"postalCodeLocation":{{"country":"US","postalCode":"30004"}}}}}}',
            'extensions': '{"persistedQuery":{"sha256Hash":"8b4249ea40b309e5bc4f32ae7e618c77c9da1ed155ffd584b3817f980fb29dd3","version":1}}',
        }
        

        response = requests.get('https://caching.graphql.imdb.com/', params=params, cookies=cookies, headers=headers)
        
        response_data = response.json()
        if response_data['data']['title']['watchOptionsByCategory']['categorizedWatchOptionsList']:   
            # Get the first streaming option's provider name
            watch_options = response_data['data']['title']['watchOptionsByCategory']['categorizedWatchOptionsList'][0]['watchOptions']
            if watch_options:
                # Extract provider names and join them
                providers = [option['provider']['name']['value'] for option in watch_options]
                # print(f"Found providers for {id}: {providers}")
                df.loc[df['id'] == id, 'platforms'] = ', '.join(providers)
            else:
                df.loc[df['id'] == id, 'platforms'] = None
        else:
            df.loc[df['id'] == id, 'platforms'] = None

        # Save after every iteration
        df.to_csv('base_data.csv', index=False)

        time.sleep(0.5)




def process_data():
    # Load the dataframes
    base_df = pd.read_csv('base_data.csv')
    user_df = pd.read_csv('user_ratings.csv')

    # Drop the user_rating column from base_df if it exists (since we'll get it from user_df)
    if 'user_rating' in base_df.columns:
        base_df = base_df.drop('user_rating', axis=1)

    # Merge the dataframes
    df = pd.merge(base_df, user_df, on='id', how='left')

    # Reorder columns to have a logical order
    column_order = ['title', 'id', 'user_rating', 'platforms']
    # Only include columns that exist
    final_columns = [col for col in column_order if col in df.columns]
    # Add any remaining columns
    remaining_columns = [col for col in df.columns if col not in final_columns]
    final_columns.extend(remaining_columns)
    
    df = df[final_columns]

    df.to_csv('imdb_cleaned_upload.csv', index=False)
    logging.info(f"Processed data saved to imdb_cleaned_upload.csv with {len(df)} rows")

def cleanup_dir():
    '''
    cleans temp py files, pycachem and maybe later deletes json and extra csvs we don't need
    '''
    try:
        os.system('rm tempCodeRunnerFile.py')
        os.system('rm *.json')
        os.system('rm -rf __pycache__')
        os.system('rm *.csv')

    except Exception as e:
        pass
if __name__ == "__main__":
    time0=time.time()
    setup_env()
    # asyncio.run(playwright_get_cookies())
    
    # with open('cookies.json', 'r') as f:
    #     cookies_dict = json.load(f)

    # get_base_data(cookies_dict)
    # get_user_data(cookies_dict)
    # get_platform_data(cookies_dict)
    # process_data()
    # upload_to_sheets(worksheet_name='test', spreadsheet_id=os.getenv('spreadsheet_id'), csv_upload_path='imdb_cleaned_upload.csv', service_account_path=os.getenv('service_account_path'))

    cleanup_dir()

    logging.info(f"Time taken: {round((time.time() - time0)/60)} minutes")


# TODO:

# upload to github
# add it pi and cron it evernight - see if it gets blocked
# see if I can refactor this later to be less code