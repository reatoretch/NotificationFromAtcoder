# For Google Calendar API
from __future__ import print_function
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

# For Debugging
from IPython import embed
from IPython.terminal.embed import InteractiveShellEmbed

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

    for event in events:
        if event['summary'] == title:
            logger.debug(f"already event name '{title}' exist\n")
            return
    
    event = service.events().insert(calendarId='primary', body=schedule).execute()
    logger.debug(f"[NEW] add event '{title}'\n")

def main():
    bs_obj = make_bs_obj(TARGET_URL)
    next_contest_list = [TARGET_URL + a_bs_obj.find('a').attrs['href'] for a_bs_obj in bs_obj.select('#main-container > section:nth-child(2) > div.f-flex.f-flex_mg5.f-flex_mg0_s.f-flex_mb5_s > div:nth-child(1) > div > ul > li > div.m-list_contest_ttl')]

    for i in range(len(next_contest_list)):
        url = next_contest_list[i]
        bs_obj = make_bs_obj(url + QUERY_PARAM)
        
        pattern = re.compile(r"var.*Time = .")
        
        script_tag_text = bs_obj.find('script',text=pattern).string
        
        title = bs_obj.select_one('#main-container > div.row > div:nth-child(2) > div.insert-participant-box > h1').string
        start = re.sub(r'["moment(,)"]', "", re.search('var startTime = (.+)[,;]{1}', script_tag_text).group(1))
        end = re.sub(r'["moment(,)"]', "", re.search('var endTime = (.+)[,;]{1}', script_tag_text).group(1))

        create_schedule(title,start,end)

if __name__ == '__main__':
    main()