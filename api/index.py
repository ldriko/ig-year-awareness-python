import os
from dotenv import load_dotenv
from http.server import BaseHTTPRequestHandler
from instagrapi import Client
from instagrapi.mixins.challenge import ChallengeChoice
import email
import imaplib
import re
from datetime import datetime, date
import calendar


load_dotenv()

GMAIL_USERNAME = os.environ.get('GMAIL_USERNAME')
GMAIL_PASSWORD = os.environ.get('GMAIL_PASSWORD')
ACCOUNT_USERNAME = os.environ.get('ACCOUNT_USERNAME')
ACCOUNT_PASSWORD = os.environ.get('ACCOUNT_PASSWORD')


def get_total_number_of_days(year=datetime.now().year):
    return 365 + calendar.isleap(year)


def get_current_day_number(start=date(datetime.now().year, 1, 1), end=date.today()):
    print(f'start date: {start}', f'end date: {end}')
    return (end - start).days


def get_progresss_percentage():
    days = get_total_number_of_days()
    current_day = get_current_day_number()
    percentage = (current_day / days) * 100
    rounded_percentage = round(percentage, 2)

    return f'{rounded_percentage}%'


def get_code_from_email(username):
    mail = imaplib.IMAP4_SSL("imap.gmail.com")

    mail.login(GMAIL_USERNAME, GMAIL_PASSWORD)
    mail.select("inbox")

    result, data = mail.search(None, "(UNSEEN)")
    assert result == "OK", "ERR(1) get_code_from_email: %s" % result
    ids = data.pop().split()

    for num in reversed(ids):
        mail.store(num, "+FLAGS", "\\Seen")  # mark as read

        result, data = mail.fetch(num, "(RFC822)")
        assert result == "OK", "ERR(2) get_code_from_email: %s" % result
        msg = email.message_from_string(data[0][1].decode())
        payloads = msg.get_payload()

        if not isinstance(payloads, list):
            payloads = [msg]

        code = None

        for payload in payloads:
            body = payload.get_payload(decode=True).decode()

            if "<div" not in body:
                continue

            match = re.search(">([^>]*?({u})[^<]*?)<".format(u=username), body)

            if not match:
                continue

            match = re.search(r">(\d{6})<", body)

            if not match:
                continue

            code = match.group(1)

            if code:
                return code
    return False


def challenge_code_handler(username, choice):
    if choice == ChallengeChoice.EMAIL:
        return get_code_from_email(username)

    return False


def update_bio():
    year = datetime.now().year
    percentage = get_progresss_percentage()

    cl = Client()
    cl.challenge_code_handler = challenge_code_handler
    cl.login(ACCOUNT_USERNAME, ACCOUNT_PASSWORD)

    cl.account_edit(
        biography=f'{year} is {percentage} complete (Automatically Updated)')


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        update_bio()

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write({'message': 'Successful'})
