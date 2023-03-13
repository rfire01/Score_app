import pandas as pd
import dictdatabase as DDB
from io import StringIO
import requests as req
import smtplib
from copy import deepcopy
from email.mime.text import MIMEText

from config import USERNAME, PASSWORD, EMAIL_APPCODE, USERS, Bids


class ForbiddenException(Exception):
    pass


def create_headers():
    payload = {'username': USERNAME,
               'password': PASSWORD,
               'client_id': 'ecaitest2023',
               'scope': 'openid cmtapi offline_access',
               'grant_type': 'password'}

    url = 'https://cmtaccount.research.microsoft.com/connect/token'
    resp = req.post(url, payload)
    with open("header_out", "a+") as f:
        f.write("#"*20)
        f.write(str(resp.status_code))
        f.write(resp.text)
        f.write("#"*20)

    token = resp.json()['access_token']
    headers = {'Authorization': 'Bearer ' + token, 'X-Role': 'Chair', 'Accept': 'application/json'}
    return headers


def update_users(headers=None):
    if headers is None:
        headers = create_headers()
    url = 'https://cmt3.research.microsoft.com/api/odata/ECAITest2023/Users/ExportTabDelimited'
    resp = req.post(url, headers=headers)
    user_df = pd.read_csv(StringIO(resp.content.decode('utf-8')), sep='\t').iloc[:,3]
    if not DDB.at('users').exists():
        DDB.at('users').create({user: [] for user in user_df})
    else:
        current_users =  DDB.at('users').read()
        with DDB.at("users").session() as (user_session, users):
            for user in user_df:
                if user not in current_users:
                    users[user] = {bid_value: [] for bid_value in [Bids.PINCH.value, Bids.WILLING.value, Bids.EAGER.value]}
            user_session.write()


def update_prices(headers=None):
    if headers is None:
        headers = create_headers()

    url = 'https://cmt3.research.microsoft.com/api/odata/ECAITest2023/SubmissionModels'
    submissions = req.get(url, headers=headers).json()['value']
    if not DDB.at('iprices').exists():
        prices = {str(submission['Id']): 100 for submission in submissions}
        all_prices = {user: deepcopy(prices) for user in USERS}
        DDB.at('iprices').create(all_prices)
    else:
        current_prices = DDB.at("iprices").read()
        prices = {str(submission['Id']): 100 for submission in submissions if
                      not DDB.at('iprices', key=str(submission['Id'])).exists()}
        with DDB.at("iprices").session() as (session, iprices):
            for user in current_prices:
                iprices[user] = {**current_prices[user], **deepcopy(prices)}

            prices = {str(submission['Id']): 100 for submission in submissions}
            for user in set(USERS) - set(current_prices):
                iprices[user] = deepcopy(prices)
            session.write()
    print("update over")
                

def send_password(email, password):
    def send_email(subject, body, sender, recipients, password):
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = ', '.join(recipients)
        smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, recipients, msg.as_string())
        smtp_server.quit()

    subject = 'ECAI bidding summary password'
    body = f'Your password is {password}'
    recipients = [email]
    send_email(subject, body, USERNAME, recipients, EMAIL_APPCODE)
