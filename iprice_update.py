import time
import traceback
from copy import deepcopy
from datetime import datetime

import requests as req
from requests import ConnectionError

import dictdatabase as DDB

from config import NUMBER_REVIEWERS, REQUIRED_BIDS, IPRICE_UPDATE_INTERVAL, FORBIDDEN_CODE, \
    SAVE_IPRICES, SERVICE_UNAVAILABLE, USERS
from utils import create_headers, ForbiddenException, update_prices


def init_prices(headers, users):
    if not DDB.at('iprices').exists():
        url = 'https://cmt3.research.microsoft.com/api/odata/ECAITest2023/SubmissionModels'
        submissions = req.get(url, headers=headers).json()['value']
        prices = {str(submission['Id']): 100 for submission in submissions}
        #DDB.at('iprices').create(prices)
        all_prices = {user: deepcopy(prices) for user in users}
        DDB.at('iprices').create(all_prices)


def update_new_submissions(headers):
    url = 'https://cmt3.research.microsoft.com/api/odata/ECAITest2023/SubmissionModels'
    resp = req.get(url, headers=headers)
    if resp.status_code == FORBIDDEN_CODE:
        raise ForbiddenException("Error with token, got status 403")
    if resp.status_code == SERVICE_UNAVAILABLE:
        raise ForbiddenException("Error with token, got status 503")
 
    try:
        submissions = resp.json()['value']
    except Exception as e:
        with open('iprice_failure','w') as f:
            f.write(str(resp.status_code))
    #print([s['Id'] for s in submissions]);exit()

    new_submissions = [str(submission['Id']) for submission in submissions
                       if not DDB.at('iprices', key=str(submission['Id'])).exists()]
    with DDB.at("iprices").session() as (session, db):
        for paper in new_submissions:
            db[str(paper)] = 100
        session.write()

    if len(new_submissions) > 0:
        return True

    return False


def update_cmt_prices(users, price_requests, headers):
    #requests = [dict(price_request, email=user) for user in users for price_request in price_requests]
    request = {'Request': {'CustomFields': price_requests}}
    url = 'https://cmt3.research.microsoft.com/api/odata/ECAITest2023/BiddingModels/ImportCustomFields'
    try:
        resp = req.post(url, json=request, headers=headers)
    except:
        raise ForbiddenException("Error with token, got status 403")
    #print(resp.text)
    # print(request)
    if resp.status_code == FORBIDDEN_CODE:
        raise ForbiddenException("Error with token, got status 403")


def count_bidders(user_bids):
    #users = DDB.at('users').read()
    #return sum(1 for user, bids in users.items() if sum(len(papers) for papers in bids.values()) > 0)
    return sum(1 for user, bids in user_bids.items() if sum(len(papers) for papers in bids.values()) > 0)


def calc_prices(users, user_bids, demand, paper_id):
    bids = [sum(user_bids.get(user, {}).values(), []) for user in users]
    users_approved_paper = [1 if int(paper_id) in bid else 0 for bid in bids]
    #users_approved_paper = [1 if int(paper_id) in sum(user_bids.get(user,{}).values(), []) else 0 for user in users]
    price_calc = lambda x: int(100 * min(1, REQUIRED_BIDS / x))
    users_prices = [price_calc(demand - approved) for approved in users_approved_paper]
    price_requests = [{'email': user, 'SubmissionId': paper_id, 'NumberField1': price}
                      for price, user in zip(users_prices, users)]
    return price_requests, users_prices


def main(users, repeat_time=IPRICE_UPDATE_INTERVAL):
    headers = create_headers()
    #init_prices(headers, users)
    update_prices(headers)

    #ids = DDB.at('iprices').read().keys()
    while True:
        ids = list(DDB.at('iprices').read().values())[0].keys()
        price_requests = []
        paper_bids = DDB.at('papers').read()
        #bidded_users = count_bidders()
        user_bids = DDB.at('users').read()
        bidded_users = count_bidders(user_bids)
        with DDB.at("iprices").session() as (session, prices):
            for id in ids:
                bids_on_paper = paper_bids.get(str(id), 0)
                demand = bids_on_paper + (NUMBER_REVIEWERS - bidded_users) * \
                         (REQUIRED_BIDS / NUMBER_REVIEWERS)
                price = int(100 * min(1, REQUIRED_BIDS / demand))
                #prices[id] = price
                #price_requests.append({'email': '', 'SubmissionId': id, 'NumberField1': price})
                #price_requests += create_requests(users, user_bids, demand, id)
                project_requests, users_prices = calc_prices(users, user_bids, demand, id)
                price_requests += project_requests
                for price, user in zip(users_prices, users):
                    prices[user][id] = price

            session.write()

        if SAVE_IPRICES:
            update_time = datetime.now().strftime("%H%M%S-%d%m%Y")
            DDB.at('prices_record', update_time).create(DDB.at("iprices").read())

        try:
            update_cmt_prices(users, price_requests, headers)

        except ForbiddenException:
            headers = create_headers()
            update_cmt_prices(users, price_requests, headers)
            continue

        time.sleep(repeat_time)

        try:
            if update_new_submissions(headers):
                ids = DDB.at('iprices').read().keys()
        except ForbiddenException:
            headers = create_headers()
            if update_new_submissions(headers):
                ids = DDB.at('iprices').read().keys()



if __name__ == '__main__':
    users = USERS# ['reshefm@ie.technion.ac.il', 'royfa@post.bgu.ac.il']
    #main(users)
    #try:
    #    main(users)
    #except Exception as e:
    #    with open("iprice_out",'w') as f:
    #        f.write(traceback.format_exc())
    #    raise e
    while True:
        try:
            main(users)
        except Exception as e:
            with open("iprice_out",'w') as f:
                f.write(traceback.format_exc())
            raise e
        except ConnectionError as e:
            with open('iprice_out','a+') as f:
                f.write("#"*20)
                f.write(f"{time.ctime()} Connection error received, sleeping for 10 seconds")
                f.write("#"*20)
                time.sleep(10)
