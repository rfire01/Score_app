import time

import requests as req

import dictdatabase as DDB

from config import NUMBER_REVIEWERS, REQUIRED_BIDS, IPRICE_UPDATE_INTERVAL, FORBIDDEN_CODE
from utils import create_headers, ForbiddenException


def init_prices(headers):
    if not DDB.at('iprices').exists():
        url = 'https://cmt3.research.microsoft.com/api/odata/ECAITest2023/SubmissionModels'
        submissions = req.get(url, headers=headers).json()['value']
        prices = {str(submission['Id']): 100 for submission in submissions}
        DDB.at('iprices').create(prices)


def update_cmt_prices(users, price_requests, headers):
    requests = [dict(price_request, email=user) for user in users for price_request in price_requests]
    request = {'Request': {'CustomFields': requests}}
    url = 'https://cmt3.research.microsoft.com/api/odata/ECAITest2023/BiddingModels/ImportCustomFields'
    resp = req.post(url, json=request, headers=headers)
    if resp.status_code == FORBIDDEN_CODE:
        raise ForbiddenException("Error with token, got status 403")


def main(users, repeat_time=IPRICE_UPDATE_INTERVAL):
    headers = create_headers()
    init_prices(headers)

    price_requests = []
    ids = DDB.at('iprices').read().keys()
    while True:
        paper_bids = DDB.at('papers').read()
        bidded_users = len(DDB.at('users').read().keys())
        with DDB.at("iprices").session() as (session, prices):
            for id in ids:
                bids_on_paper = paper_bids.get(str(id), 0)
                demand = bids_on_paper + (NUMBER_REVIEWERS - bidded_users) *\
                         (REQUIRED_BIDS / NUMBER_REVIEWERS)
                price = int(100 * min(1, REQUIRED_BIDS / demand))
                prices[id] = price
                price_requests.append({'email': '', 'SubmissionId': id, 'NumberField1': price})

            session.write()

        try:
            update_cmt_prices(users, price_requests, headers)

        except ForbiddenException:
            headers = create_headers()
            update_cmt_prices(users, price_requests, headers)
            continue

        time.sleep(repeat_time)


if __name__ == '__main__':
    users = ['kobig@bgu.ac.il', 'reshefm@ie.technion.ac.il', 'royfa@post.bgu.ac.il']
    main(users)