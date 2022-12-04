import time

import requests as req

import dictdatabase as DDB

from config import NUMBER_REVIEWERS, REQUIRED_BIDS, IPRICE_UPDATE_INTERVAL
from utils import create_headers


def init_prices():
    if not DDB.at('iprices').exists():
        headers = create_headers()
        url = 'https://cmt3.research.microsoft.com/api/odata/ECAITest2023/SubmissionModels'
        submissions = req.get(url, headers=headers).json()['value']
        prices = {str(submission['Id']): 100 for submission in submissions}
        DDB.at('iprices').create(prices)


def main(repeat_time=IPRICE_UPDATE_INTERVAL):
    init_prices()

    ids = DDB.at('iprices').read().keys()
    while True:
        paper_bids = DDB.at('papers').read()
        bidded_users = len(DDB.at('users').read().keys())
        with DDB.at("iprices").session() as (session, prices):
            for id in ids:
                bids_on_paper = paper_bids.get(str(id), 0)
                demand = bids_on_paper + (NUMBER_REVIEWERS - bidded_users) *\
                         (REQUIRED_BIDS / NUMBER_REVIEWERS)
                price = 100 * min(1, REQUIRED_BIDS / demand)
                prices[id] = price

            session.write()

        time.sleep(repeat_time)


if __name__ == '__main__':
    main()