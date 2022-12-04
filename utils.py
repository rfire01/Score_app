import requests as req

from config import USERNAME, PASSWORD


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
    token = resp.json()['access_token']
    headers = {'Authorization': 'Bearer ' + token, 'X-Role': 'Chair', 'Accept': 'application/json'}
    return headers