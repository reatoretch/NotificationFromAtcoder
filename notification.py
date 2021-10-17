# For Google Calendar API
from __future__ import print_function
import pybase64
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# For Log
from logging import getLogger, StreamHandler, DEBUG
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False

# For Scraping
import re
import requests
from bs4 import BeautifulSoup

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']
# Target
TARGET_URL = 'https://atcoder.jp'
# User-Agent
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
# to Japanese Page
QUERY_PARAM = '?lang=ja'

def make_bs_obj(url):
    """
    create BeautifulSoupObject
    """
    while True:
        try:
            html = requests.get(url + QUERY_PARAM, headers={'User-Agent': UA}, timeout=3)
        except Exception as e:
            continue
        break
    logger.debug(f"access {url} ...")

    return BeautifulSoup(html.content,'html.parser')

# ref:https://stackoverflow.com/questions/2941995/python-ignore-incorrect-padding-error-when-base64-decoding
def decode_base64(data, altchars=b'+/'):
    """Decode base64, padding being optional.

    :param data: Base64 data as an ASCII byte string
    :returns: The decoded byte string.

    """
    data = re.sub(rb'[^a-zA-Z0-9%s]+' % altchars, b'', data)  # normalize
    missing_padding = len(data) % 4
    if missing_padding:
        data += b'='* (4 - missing_padding)
    return pybase64.b64decode(data, altchars)

# ref: https://developers.google.com/calendar/quickstart/python
def create_schedule(title,start,end):
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    events_result = service.events().list(calendarId='primary', timeMin=start,
                                    maxResults=5, singleEvents=True,
                                    orderBy='startTime').execute()
    
    events = events_result.get('items', [])

    schedule = {
        'summary': title,
        'location': 'online',
        'start': {
            'dateTime': start,
            'timeZone': 'Japan',
        },
        'end': {
            'dateTime': end,
            'timeZone': 'Japan',
        },
    }

    if not events:
        event = service.events().insert(calendarId='primary', body=schedule).execute()
        return

    string = '[NEW]'
    for event in events:
        if event['summary'] == title:
            b64_ids = event['htmlLink'].split('?eid=')[1]
            e_id,c_id = map(lambda x:str(x)[2:-1],decode_base64(b64_ids.encode()).split())
            service.events().delete(calendarId='primary', eventId=e_id).execute()
            string = "[REMAKE]"
            break
    
    event = service.events().insert(calendarId='primary', body=schedule).execute()
    logger.debug(f"{string} add event '{title}'\n")

def main():
    bs_obj = make_bs_obj(TARGET_URL)
    next_contest_list = [TARGET_URL + a_bs_obj.find('a').attrs['href'] for a_bs_obj in bs_obj.select('#main-container > section:nth-child(2) > div.f-flex.f-flex_mg5.f-flex_mg0_s.f-flex_mb5_s > div:nth-child(1) > div > ul > li > div.m-list_contest_ttl')]

    for url in next_contest_list:
        bs_obj = make_bs_obj(url + QUERY_PARAM)
        
        pattern = re.compile(r"var.*Time = .")
        
        script_tag_text = bs_obj.find('script',text=pattern).string
        
        title = bs_obj.select_one('#main-container > div.row > div:nth-child(2) > div.insert-participant-box > h1').string
        start = re.sub(r'["moment(,)"]', "", re.search('var startTime = (.+)[,;]{1}', script_tag_text).group(1))
        end = re.sub(r'["moment(,)"]', "", re.search('var endTime = (.+)[,;]{1}', script_tag_text).group(1))

        create_schedule(title,start,end)

if __name__ == '__main__':
    main()