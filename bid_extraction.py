import os.path
import time

import requests as req

import pandas as pd
import dictdatabase as DDB

from config import FORBIDDEN_CODE, BID_EXTRACTION_INTERVAL, DF_BACKUP_PATH, DF_BACKUP_INTERVAL
from utils import create_headers, ForbiddenException


def init_db():
    if not DDB.at('users').exists():
        DDB.at('users').create({})

    if not DDB.at('papers').exists():
        DDB.at('papers').create({})

    if not DDB.at('scores').exists():
        DDB.at('scores').create({})


def get_bids(headers):
    url = 'https://cmt3.research.microsoft.com/api/odata/ECAITest2023/BiddingModels/ExportXml'
    resp = req.post(url, headers=headers)
    if resp.status_code == FORBIDDEN_CODE:
        raise ForbiddenException("Error with token, got status 403")

    bid_table = pd.read_xml(resp.text, xpath='.//*').dropna(how='all', axis=1).assign(
        submissionId=lambda df: df.submissionId.ffill()).dropna(subset='email')
    # Filter bids that are not positive
    bid_table = bid_table[bid_table.bid.str.slice(0,1).astype(int) > 2]
    bid_table['submissionId'] = bid_table.submissionId.astype(int)
    # Remove the text of the bid
    del bid_table['bid']

    return bid_table


def update_db(current_table, new_table):
    prices = DDB.at('iprices').read()

    diffs = pd.concat([current_table, new_table]).drop_duplicates(keep=False)
    emails = diffs.email.unique()
    with DDB.at("users").session() as (user_session, users):
        with DDB.at("scores").session() as (score_session, scores):
            for email in emails:
                user_bids = new_table[new_table.email == email]
                papers = user_bids.submissionId.tolist()
                users[email] = papers
                scores[email] = sum(prices[str(paper)] for paper in papers)

            user_session.write()
            score_session.write()

    paper_ids = diffs.submissionId.unique()
    with DDB.at("papers").session() as (session, papers):
        for paper_id in paper_ids:
            paper_bids = new_table[new_table.submissionId == paper_id]
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
