from __future__ import print_function
import pytz
import datetime
import os.path
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import speech_recognition as sr
import pyttsx3
import webbrowser
import pyautogui
import openai
from langdetect import detect
from googletrans import Translator

engine = pyttsx3.init()
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
apikey = "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"
chatStr = ""
websites = {
        "youtube": "https://www.youtube.com",
        "wikipedia": "https://www.wikipedia.org",
        "google": "https://www.google.com",
        "gmail": "https://mail.google.com",
        "calender": "https://calendar.google.com/calendar/u/0/r"
    }
MONTHS = ['january','february','march','april','may','june','july','august','september','october','november','december']
DAYS = ['monday','teusday','wednesday','thursday','friday','saturday','sunday']
DAY_EXTENSIONS = ['th','rd','st']
bro_active = False

def chat(query):
    global chatStr
    openai.api_key = apikey
    chatStr += f"user: {query}\n Bro: "
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=chatStr,
        temperature=0.7,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    ai_response = response["choices"][0]["text"]
    chatStr = ""
    return ai_response
def speak_tamil(text):
    translator = Translator()
    translated_text = translator.translate(text, src='en', dest='ta').text

    engine.setProperty('voice', 'ta')  # Set the voice to Tamil
    engine.say(translated_text)
    engine.runAndWait()


def say(text):
    user_language = detect(text)
    print("Bro:", text)
    if user_language == 'ta':
        speak_tamil(text)
    else:
        engine.say(text)
        engine.runAndWait()


def takeCommand():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.pause_threshold = 1
        print("Listening...")
        try:
            audio = r.listen(source)
            query = r.recognize_google(audio, language="en-in").lower()
            print(f"user: {query}")
            return query
        except sr.UnknownValueError:
            print("Sorry, I didn't catch that. Please try again.")
            return ""
        except sr.RequestError as e:
            print(f"Error occurred during speech recognition: {e}")
            return ""


def image_generation(prompt):
    openai.api_key = apikey
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    image_url = response['data'][0]['url']
    return image_url


def authenticate_google_calendar():
    global creds
    global service
    creds = None
    scopes = ['https://www.googleapis.com/auth/calendar.events']
    if (os.path.exists('credentials.json')):
        print('good')
        creds = Credentials.from_authorized_user_file('credentials.json', scopes)
        service = build('calendar', 'v3', credentials=creds)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", scopes)
            creds = flow.run_local_server(port=0)
        with open('credentials.json', 'w') as token:
            token.write(creds.to_json())


def create_event(service, summary, start_time, end_time):
    event = {
        'summary': summary,
        'start': {'dateTime': start_time, 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end_time, 'timeZone': 'Asia/Kolkata'}
    }
    event = service.events().insert(calendarId='primary', body=event).execute()
    print(f'Event created: {event.get("summary")}, Start: {event.get("start").get("dateTime")}')

def main():
    bro_active = False
    creds = authenticate_google_calendar()
    calendar_service = service

    print('started')
    say("Hello, I am Bro A.I.")
    websites = {
        "youtube": "https://www.youtube.com",
        "wikipedia": "https://www.wikipedia.org",
        "google": "https://www.google.com",
        "gmail": "https://mail.google.com",
        "calender": "https://calendar.google.com/calendar/u/0/r"
    }
    tabs_open = {website: False for website in websites}

    while True:
        try:
            text = takeCommand()

            if "bro" in text:
                if "quit" in text:
                    say("Goodbye.")
                    break
                if not bro_active:
                    say("Yes, I'm listening. How can I help you?")
                    bro_active = True
                else:
                    say("I'm already active. How can I assist you?")
            elif bro_active:
                if "speak in tamil" in text:
                    say("நலமாக பேசியிருக்கின்றேன்")
                elif "generate image" in text:
                    say("Sure, please provide the image prompt.")
                    prompt = takeCommand()
                    if prompt:
                        image_url = image_generation(prompt)
                        say("Here is the generated image. You can view it at " + image_url)
                    else:
                        say("Sorry, I didn't catch the image prompt. Please try again.")
                elif "open" in text or "close" in text:
                    handled = False
                    for website, url in websites.items():
                        if f"open {website}" in text:
                            say(f"Opening {website.capitalize()}.")
                            webbrowser.open(url)
                            tabs_open[website] = True
                            handled = True
                            break
                        elif f"close {website}" in text and tabs_open[website]:
                            say(f"Closing {website.capitalize()}.")
                            pyautogui.hotkey("ctrl", "w")
                            tabs_open[website] = False
                            handled = True
                            break
                    if not handled:
                        say("Sorry, I didn't catch that. Please try again.")

                elif "create an event" in text:
                    say("Sure, please provide the event details.")
                    event_details = takeCommand()
                    if event_details:
                        now = datetime.datetime.now()
                        start_time = now + datetime.timedelta(hours=1)
                        end_time = start_time + datetime.timedelta(hours=2)
                        create_event(calendar_service, event_details, start_time.isoformat(), end_time.isoformat())
                        say(f"Event '{event_details}' has been created.")
                    else:
                        say("Sorry, I didn't catch the event details. Please try again.")
                elif "upcoming events" in text:
                    now = datetime.datetime.utcnow().isoformat() + 'Z'
                    events_result = calendar_service.events().list(calendarId='primary', timeMin=now,
                                                                   maxResults=5, singleEvents=True,
                                                                   orderBy='startTime').execute()
                    events = events_result.get('items', [])

                    if not events:
                        say("You have no upcoming events.")
                    else:
                        say("Here are your upcoming events:")
                        for event in events:
                            start = event['start'].get('dateTime', event['start'].get('date'))
                            event_summary = event['summary']
                            say(f"On {start}, you have: {event_summary}")
                else:
                    ai_response = chat(text)
                    say(ai_response)

        except sr.UnknownValueError:
            print("Sorry, I didn't catch that. Please try again.")
        except sr.RequestError as e:
            print(f"Error occurred during speech recognition: {e}")


if __name__ == "__main__":
    bro_active = False
    main()
