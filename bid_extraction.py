import os.path
import time
from datetime import datetime

import requests as req

import pandas as pd
import dictdatabase as DDB

from config import FORBIDDEN_CODE, BID_EXTRACTION_INTERVAL, DF_BACKUP_PATH, DF_BACKUP_INTERVAL, \
    SAVE_BIDS, Bids
from utils import create_headers, ForbiddenException


def init_db():
    if not DDB.at('users').exists():
        DDB.at('users').create({})

    if not DDB.at('papers').exists():
        DDB.at('papers').create({})

    if not DDB.at('scores').exists():
        DDB.at('scores').create({})

    if not DDB.at('bids').exists():
        DDB.at('bids').create({})


def get_bids(headers):
    url = 'https://cmt3.research.microsoft.com/api/odata/ECAITest2023/BiddingModels/ExportXml'
    resp = req.post(url, headers=headers)
    if resp.status_code == FORBIDDEN_CODE:
        raise ForbiddenException("Error with token, got status 403")

    bid_table = pd.read_xml(resp.text, xpath='.//*').dropna(how='all', axis=1).assign(
        submissionId=lambda df: df.submissionId.ffill()).dropna(subset='email')
    # Filter bids that are not positive
    bid_table['bid'] = bid_table.bid.str.slice(0,1)
    # bid_table = bid_table[bid_table.bid.str.slice(0,1).astype(int) > 2]
    bid_table['submissionId'] = bid_table.submissionId.astype(int)
    # Remove the text of the bid
    # del bid_table['bid']

    return bid_table


def save_user_bid(user, bids):
    if SAVE_BIDS:
        update_time = datetime.now().strftime("%H%M%S-%d%m%Y")
        DDB.at('user_bids', user, update_time).create(bids)


def update_db(current_table, new_table):
    prices = DDB.at('iprices').read()

    diffs = pd.concat([current_table, new_table]).drop_duplicates(keep=False)
    emails = diffs.email.unique()
    # update users current bids and scores
    with DDB.at("users").session() as (user_session, users):
        with DDB.at("scores").session() as (score_session, scores):
            for email in emails:
                user_bid_table = new_table[new_table.email == email]
                user_bids = {}
                user_score = {}
                for bid_value in [Bids.PINCH.value, Bids.WILLING.value, Bids.EAGER.value]:
                    papers = user_bid_table[user_bid_table.bid == bid_value].submissionId.tolist()
                    user_bids[bid_value] = papers
                    user_score[bid_value] = sum(prices[str(paper)] for paper in papers)

                users[email] = user_bids
                scores[email] = user_score

                save_user_bid(email, user_bids)

            user_session.write()
            score_session.write()

    # update how many bids each paper have
    paper_ids = diffs.submissionId.unique()
    with DDB.at("papers").session() as (session, papers):
        for paper_id in paper_ids:
            paper_bids = new_table[new_table.submissionId == paper_id]
            paper_bids = paper_bids[paper_bids.bid >= Bids.PINCH.value]
            papers[str(paper_id)] = len(paper_bids.submissionId)
            session.write()


def load_df():
    if not os.path.isfile(DF_BACKUP_PATH):
        return pd.DataFrame()

    return pd.read_pickle(DF_BACKUP_PATH)


def main(repeat_time=BID_EXTRACTION_INTERVAL):
    init_db()
    current_bids = load_df()
    headers = create_headers()

    last_backup_time = time.time()
    while True:
        try:
            new_bids = get_bids(headers)

        except ForbiddenException:
            headers = create_headers()
            continue

        update_db(current_bids, new_bids)
        current_bids = new_bids
        # print("finished iteration")
        # print(DDB.at('users').read())
        # print(DDB.at('papers').read())
        # print(DDB.at('scores').read())
        # print(DDB.at('iprices').read())

        if time.time() - last_backup_time > DF_BACKUP_INTERVAL:
            current_bids.to_pickle(DF_BACKUP_PATH)
            last_backup_time = time.time()

        time.sleep(repeat_time)

        # print("Starting new iteration", "#"*100)


if __name__ == '__main__':
    main()
