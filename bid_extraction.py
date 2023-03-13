import os.path
import time
import traceback
from copy import deepcopy
from datetime import datetime

import requests as req
#from requests import ConnectionError
from requests.exceptions import ConnectionError

import pandas as pd
import dictdatabase as DDB

from config import FORBIDDEN_CODE, BID_EXTRACTION_INTERVAL, DF_BACKUP_PATH, DF_BACKUP_INTERVAL, \
    SAVE_BIDS, Bids, SERVICE_UNAVAILABLE
from utils import create_headers, ForbiddenException, update_users


def init_db(headers):
    #url = 'https://cmt3.research.microsoft.com/api/odata/ECAITest2023/Users/ExportTabDelimited'
    #resp = req.post(url, headers=headers)
    #user_df = pd.read_csv(StringIO(resp.content.decode('utf-8')), sep='\t').iloc[:,3]
    #if not DDB.at('users').exists():
    #    DDB.at('users').create({user: [] for user in user_df})
    #else:
    #    current_users =  DDB.at('users').read()
    #    with DDB.at("users").session() as (user_session, users):
    #        for user in user_df:
    #            if user not current_users:
    #                users[user] = {bid_value: [] for bid_value in [Bids.PINCH.value, Bids.WILLING.value, Bids.EAGER.value]}
    #        user_session.write()
    update_users(headers)        

    if not DDB.at('papers').exists():
        DDB.at('papers').create({})

    if not DDB.at('scores').exists():
        DDB.at('scores').create({})

    if not DDB.at('bids').exists():
        DDB.at('bids').create({})

    if not DDB.at('accesses').exists():
        DDB.at('accesses').create({})
  
    if not DDB.at('accounts').exists():
        DDB.at('accounts').create({})

    #if not DDB.at('iprices').exists():
    #    url = 'https://cmt3.research.microsoft.com/api/odata/ECAITest2023/SubmissionModels'
    #    submissions = req.get(url, headers=headers).json()['value']
    #    prices = {str(submission['Id']): 100 for submission in submissions}
    #    #DDB.at('iprices').create(prices)
    #    all_prices = {user: deepcopy(prices) for user in users}
    #    DDB.at('iprices').create(all_prices)


def get_bids(headers):
    url = 'https://cmt3.research.microsoft.com/api/odata/ECAITest2023/BiddingModels/ExportXml'
    resp = req.post(url, headers=headers)
    if resp.status_code == FORBIDDEN_CODE:
        raise ForbiddenException("Error with token, got status 403")
    if resp.status_code == SERVICE_UNAVAILABLE:
        raise ForbiddenException("Error with token, got status 503")

    try:
        bid_table = pd.read_xml(resp.text, xpath='.//*').dropna(how='all', axis=1).assign(
        submissionId=lambda df: df.submissionId.ffill())#.dropna(subset='email')
        if 'email' in bid_table:
            bid_table = bid_table.dropna(subset='email')
        else:
            return None
    except Exception as e:
        with open('bid_failure','w') as f:
            f.write(resp.text)
            print(resp.text)
            f.write('\n')
        with open('bid_failure','w') as f:
            f.write(str(resp.status_code))
            print(resp.status_code)
            f.write('#'*50)
        with open('bid_failure','w') as f:
            f.write(pd.read_xml(resp.text, xpath='.//*').to_string(header=False, index=False))
            print(pd.read_xml(resp.text, xpath='.//*'))
            f.write('#'*50)
        with open('bid_failure','w') as f:
            f.write(pd.read_xml(resp.text, xpath='.//*').dropna(how='all', axis=1).to_string(header=False, index=False))
            f.write('#'*50)
        with open('bid_failure','w') as f:
            f.write(pd.read_xml(resp.text, xpath='.//*').dropna(how='all', axis=1).assign(submissionId=lambda df: df.submissionId.ffill()).to_string(header=False, index=False))
        raise e
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
                    try:
                        user_score[bid_value] = sum(prices[email][str(paper)] for paper in papers)
                    except KeyError:
                        with open('bid_out','a+') as f:
                            f.write("There is non exist file, taking it as 100 price\n")
                        papers_price = [prices[email][str(paper)] if email in prices and str(paper) in prices[email]
                                        else 100 for paper in papers]
                        user_score[bid_value] = sum(papers_price)

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
    headers = create_headers()
    init_db(headers)
    current_bids = load_df()
    #headers = create_headers()

    last_backup_time = time.time()
    while True:
        try:
            new_bids = get_bids(headers)
            if new_bids is None:
                continue

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
    while True:
        try:
            main()
        except Exception as e:
            with open("bid_out",'w') as f:
                f.write(traceback.format_exc())
            raise e
        except ConnectionError as e:
            with open('bid_out','a+') as f:
                f.write("#"*20)
                f.write(f"{time.ctime()} Connection error received, sleeping for 10 seconds")
                f.write("#"*20)
                time.sleep(10)
