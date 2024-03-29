import requests
import json
import os
import library.utils as utils
import library.localstore as store
import library.nrpylogger as nrpy_logger
import library.clients.gql as nerdgraph

logger = nrpy_logger.get_logger(os.path.basename(__file__))


class CCUConsumption:

    def __init__(self):
        pass

    @staticmethod
    def get_ccu_consumption(nr_user_api_key, accountId, start, end):
        payload = CCUConsumption.get_ccu_consumption_payload(accountId, start, end)
        logger.debug(json.dumps(payload))
        return nerdgraph.GraphQl.post(nr_user_api_key, payload)

    @staticmethod
    def get_current_user_all_accounts(nr_user_api_key):
        payload = CCUConsumption.get_all_accounts_payload()
        logger.debug(json.dumps(payload))
        return nerdgraph.GraphQl.post(nr_user_api_key, payload)


    @staticmethod
    def get_condition_details(nr_user_api_key,accountId, conditionId):
        payload = CCUConsumption.get_condition_details_payload(accountId, conditionId)
        logger.debug(json.dumps(payload))
        return nerdgraph.GraphQl.post(nr_user_api_key, payload)

    @staticmethod
    def get_ccu_consumption_payload(accountId, start, end):
        ccu_consumption_query = '''query($accountId: [Int!]!) {
                                  actor {
                                    nrql(
                                      query: "FROM NrComputeUsage SELECT sum(usage) WHERE dimension_productCapability = 'Alert Conditions' FACET dimension_conditionId SINCE '%s' UNTIL '%s' LIMIT MAX"
                                      accounts: $accountId
                                    ) {
                                      results
                                    }
                                  }
                                }''' % (start, end)
        return {'query': ccu_consumption_query, 'variables': {'accountId': accountId}}

    @staticmethod
    def get_all_accounts_payload():
        all_accounts_query = '''query {
                                  actor {
                                    accounts {
                                      id
                                      name
                                    }
                                  }
                                }'''
        return {'query': all_accounts_query}

    @staticmethod
    def get_condition_details_payload(accountId, conditionId):
        condition_details_query = '''query ($accountId: [Int!]!) {
                                      actor {
                                        account(id: $accountId) {
                                          alerts {
                                            nrqlCondition(id: "%s") {
                                              policyId
                                              name
                                              nrql {
                                                query
                                              }
                                            }
                                          }
                                        }
                                      }
                                    }''' % conditionId
        return {'query': condition_details_query, 'variables': {'accountId': accountId}}
