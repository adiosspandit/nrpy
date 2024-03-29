import os
import argparse
import json
import csv
from datetime import date
from library import utils
import library.clients.ccuconsumptionclient as ccuconsumptionclient
import library.localstore as store
import library.nrpylogger as nrpylogger

ccuconsumptionclient = ccuconsumptionclient.CCUConsumption()
logger = nrpylogger.get_logger(os.path.basename(__file__))

config = store.load_json_from_file(".", "ccuconsumption.json")
nr_user_api_key = config['nr_user_api_key']
since = config['since']
until = config['until']


def get_all_accounts(nr_user_api_key):
    all_accounts_dicts = []
    all_accounts_list = []
    result = ccuconsumptionclient.get_current_user_all_accounts(nr_user_api_key)
    accounts = result['response']['data']['actor']['accounts']
    for account in accounts:
        all_accounts_list.append(account['id'])
        all_accounts_dicts.append({
            "id": account['id'],
            "name": account['name']
        })
    return all_accounts_list, all_accounts_dicts


def generate_ccu_consumption_report_for_all_accounts(nr_user_api_key):
    all_accounts_list, all_accounts_dicts = get_all_accounts(nr_user_api_key)
    ccu_consumption_report = []
    for account in all_accounts_list:
        result = get_ccu_consumption_per_condition(nr_user_api_key, account, since, until)
        for condition in result:
            condition_details = get_condition_details(nr_user_api_key, account, condition["conditionId"])
            if condition_details:
                ccu_consumption_report.append({
                    "accountId": account,
                    "conditionId": condition["conditionId"],
                    "conditionName": condition_details["conditionName"],
                    "policyId": condition_details["policyId"],
                    "conditionQuery": condition_details["query"],
                    "ccuConsumption": condition["ccuConsumption"]
                })
    store.save_list_of_dict_as_csv(ccu_consumption_report, "ccu_consumption_report_%s_%s.csv" % (since, until))
    logger.info("CCU consumption report has been generated.")


def get_condition_details(nr_user_api_key, accountId, conditionId):
    condition_details = {}
    result = ccuconsumptionclient.get_condition_details(nr_user_api_key, accountId, conditionId)
    if 'error' in result:
        logger.error(json.dumps(result))
        return
    elif result['response']['data']['actor']['account']['alerts']['nrqlCondition']:
        conditions_data = result['response']['data']['actor']['account']['alerts']['nrqlCondition']
        if conditions_data['name']:
            condition_details["conditionName"] = conditions_data['name']
        else:
            condition_details["conditionName"] = ""
        condition_details["policyId"] = conditions_data['policyId']
        condition_details["query"] = conditions_data['nrql']['query']
        return condition_details
    else:
        logger.info("Condition id " + str(conditionId) + " is invalid.")
        return

def get_ccu_consumption_per_condition(nr_user_api_key, accountId, since, until):
    condition_ccu_consumption = []
    result = ccuconsumptionclient.get_ccu_consumption(nr_user_api_key, accountId, since, until)
    ccu_per_conidition = result['response']['data']['actor']['nrql']['results']
    for condition in ccu_per_conidition:
        condition_ccu_consumption.append({
            "conditionId": condition['dimension_conditionId'],
            "ccuConsumption": condition['sum.usage']
        })
    return condition_ccu_consumption


def load_ccu_tier_prices():
    ccu_tier_list = store.load_csv_to_list_of_dicts("ccu_tier.csv")
    return ccu_tier_list


def load_ccu_discounts():
    ccu_discount_list = store.load_csv_to_list_of_dicts("ccu_discount.csv")
    return ccu_discount_list


if __name__ == '__main__':
    generate_ccu_consumption_report_for_all_accounts(nr_user_api_key)
