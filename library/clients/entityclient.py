import requests
import json
import os
import library.utils as utils
import library.nrpylogger as nrpy_logger
import library.clients.gql as nerdgraph

SHOW_APM_APP_URL = 'https://api.newrelic.com/v2/applications/'
GET_APM_APP_URL = 'https://api.newrelic.com/v2/applications.json'
GET_BROWSER_APP_URL = 'https://api.newrelic.com/v2/browser_applications.json'
SHOW_MOBILE_APP_URL = 'https://api.newrelic.com/v2/mobile_applications/'
SHOW_APM_KT_URL = 'https://api.newrelic.com/v2/key_transactions/'
GET_APM_KT_URL = 'https://api.newrelic.com/v2/key_transactions.json'
KEY_TRANSACTIONS = 'key_transactions'
PUT_LABEL_URL = 'https://api.newrelic.com/v2/labels.json'
APM_APP = 'APM_APP'
APM_KT = 'APM_KT'
BROWSER_APP = 'BROWSER_APP'
APM_EXT_SVC = 'APM_EXT_SVC'
MOBILE_APP = 'MOBILE_APP'
MONITOR = 'MONITOR'
DASHBOARD = 'DASHBOARD'

logger = nrpy_logger.get_logger(os.path.basename(__file__))


class EntityClient:

    def __init__(self):
        pass

    def get_matching_kt(self, tgt_api_key, kt_name):
        filter_params = {'filter[name]': kt_name}
        result = {'entityFound': False}
        response = requests.get(GET_APM_KT_URL, headers=self._rest_api_headers(tgt_api_key), params=filter_params)
        result['status'] = response.status_code
        if response.text:
            response_json = response.json()
            if KEY_TRANSACTIONS in response_json:
                if len(response_json[KEY_TRANSACTIONS]) > 0:
                    result['entityFound'] = True
                    result['entity'] = response_json[KEY_TRANSACTIONS][0]
        return result

    def gql_get_matching_entity(self, api_key, entity_type, src_entity, tgt_account_id):
        logger.info('looking for matching entity ' + src_entity['name'] + ' in account ' + tgt_account_id)
        payload = self._entity_by_name_payload(entity_type, src_entity['name'])
        result = {'entityFound': False}
        response = requests.post(nerdgraph.URL, headers=nerdgraph.GraphQl.headers(api_key), data=json.dumps(payload))
        result['status'] = response.status_code
        if response.text:
            response_json = response.json()
            if 'errors' in response_json:
                if response.text:
                    result['error'] = response_json['errors']
                logger.error(result)
            else:
                result['count'] = response_json['data']['actor']['entitySearch']['count']
                result['entities'] = self._extract_entities(response_json)
                if result['count'] > 0:
                    self._set_matched_entity(result['entities'], entity_type, result, src_entity, tgt_account_id)
        else:
            logger.warn('No response for this query response received ' + str(response))
        logger.info('entity match result : ' + str(result))
        return result

    def gql_get_matching_entity_by_name(self, api_key, entity_type, name, tgt_acct_id):
        logger.info('Searching matching entity for type:' + entity_type + ', name:' + name + ', acct:' + tgt_acct_id)
        payload = self._entity_by_name_payload(entity_type, name)
        result = {'entityFound': False}
        response = requests.post(nerdgraph.URL, headers=nerdgraph.GraphQl.headers(api_key), data=json.dumps(payload))
        result['status'] = response.status_code
        if response.text:
            response_json = response.json()
            if 'errors' in response_json:
                if response.text:
                    result['error'] = response_json['errors']
                logger.error(result)
            else:
                result['count'] = response_json['data']['actor']['entitySearch']['count']
                result['entities'] = self._extract_entities(response_json)
                if result['count'] > 0:
                    self._set_matched_entity_by_name(tgt_acct_id, entity_type, name, result)
        else:
            logger.warn('No response for this query response received ' + str(response))
        logger.info('entity match result : ' + str(result))
        return result

    def get_entity(self, api_key, entity_type, entity_id):
        if entity_type in [APM_APP, MOBILE_APP]:
            return self.get_app_entity(api_key, entity_type, entity_id)
        if entity_type == BROWSER_APP:
            return self.get_browser_entity(api_key, entity_id)
        if entity_type == APM_KT:
            return self.get_apm_kt(api_key, entity_id)
        logger.warn('Skipping non APM entities ' + entity_type)
        return {'entityFound': False}

    def get_app_entity(self, api_key, entity_type, app_id):
        result = {'entityFound': False}
        get_url = self._show_url_for_app(entity_type, app_id)
        response = requests.get(get_url, headers=self._rest_api_headers(api_key))
        result['status'] = response.status_code
        if response.status_code != 200:
            if response.text:
                logger.error("Error getting application info for app_id " + app_id)
                result['error'] = response.text
        else:
            result['entityFound'] = True
            result['entity'] = response.json()['application']
        return result

    def get_apm_entity_by_name(self, api_key, app_name):
        params = {'filter[name]': app_name}
        result = {'entityFound': False}
        response = requests.get(GET_APM_APP_URL, headers=self._rest_api_headers(api_key), params=params)
        result['status'] = response.status_code
        if response.status_code != 200:
            if response.text:
                logger.error("Error getting application info for app_name " + app_name)
                result['error'] = response.text
        else:
            if response.text:
                response_json = response.json()
                if 'applications' in response_json:
                    for app in response_json['applications']:
                        if app['name'] == app_name:
                            result['entityFound'] = True
                            result['entity'] = app
        return result

    def get_browser_entity(self, api_key, app_id):
        params = {'filter[ids]': [app_id]}
        result = {'entityFound': False}
        get_url = GET_BROWSER_APP_URL
        response = requests.get(get_url, headers=self._rest_api_headers(api_key), params=params)
        logger.info(response.url)
        result['status'] = response.status_code
        if response.status_code != 200:
            if response.text:
                logger.error("Error getting application info for app_id " + app_id)
                result['error'] = response.text
        else:
            response_json = response.json()
            if 'browser_applications' in response_json.keys() and len(response_json['browser_applications']) == 1:
                result['entityFound'] = True
                result['entity'] = response_json['browser_applications'][0]
                # remove unnecessary key values just retaining id and name
                result['entity'].pop('browser_monitoring_key')
                result['entity'].pop('loader_script')
            else:
                logger.error("Did not find browser_applications in response for " + app_id)
        return result

    def get_apm_kt(self, api_key, kt_id):
        result = {'entityFound': False}
        get_url = SHOW_APM_KT_URL + kt_id + '.json'
        response = requests.get(get_url, headers=self._rest_api_headers(api_key))
        result['status'] = response.status_code
        if response.status_code != 200:
            if response.text:
                logger.error("Error getting application info for app_id " + kt_id)
                result['error'] = response.text
        else:
            result['entityFound'] = True
            result['entity'] = response.json()['key_transaction']
        return result

    def put_apm_settings(self, api_key, app_id, app_settings):
        logger.debug(app_settings)
        updated_settings = {
            "application": {
                "settings": {
                    "app_apdex_threshold": str(app_settings['application']['settings']['app_apdex_threshold']),
                    "end_user_apdex_threshold": str(
                        app_settings['application']['settings']['end_user_apdex_threshold']),
                    "enable_real_user_monitoring": str(
                        app_settings['application']['settings']['enable_real_user_monitoring'])
                }
            }
        }
        result = {}
        update_app_url = SHOW_APM_APP_URL + str(app_id) + '.json'
        response = requests.put(update_app_url, headers=self._rest_api_headers(api_key),
                                data=json.dumps(updated_settings))
        result['status'] = response.status_code
        if response.status_code in [200, 204] and response.text:
            result['application'] = response.json()['application']
        elif response.text:
            result['error'] = response.text
        return result

    def gql_mutate_add_tags(self, per_api_key, entity_guid, arr_label_keys):
        payload = self._apply_tags_payload(entity_guid, arr_label_keys)
        return nerdgraph.GraphQl.post(per_api_key, payload)

    def gql_mutate_delete_tag_values(self, per_api_key, entity_guid, arr_tags):
        payload = self._delete_tag_values_payload(entity_guid, arr_tags)
        return nerdgraph.GraphQl.post(per_api_key, payload)

    def gql_mutate_delete_tag_keys(self, per_api_key, entity_guid, arr_keys):
        payload = self._delete_tag_keys_payload(entity_guid, arr_keys)
        return nerdgraph.GraphQl.post(per_api_key, payload)

    def gql_mutate_replace_tags(self, per_api_key, entity_guid, arr_label_keys):
        payload = self._replace_tags_payload(entity_guid, arr_label_keys)
        return nerdgraph.GraphQl.post(per_api_key, payload)

    def gql_get_tags(self, per_api_key, entity_guid):
        entity_tags_query = '''query($entityGuid: EntityGuid!) { 
                                    actor {
                                        entity(guid: $entityGuid) {
                                            tags {
                                                key
                                                values
                                            }
                                        }
                                    } 
                                }'''
        variables = {'entityGuid': entity_guid}
        payload = {'query': entity_tags_query, 'variables': variables}
        return nerdgraph.GraphQl.post(per_api_key, payload)

    def gql_get_tags_with_metadata(self, per_api_key, entity_guid):
        entity_tags_query = '''query($entityGuid: EntityGuid!) { 
                                    actor {
                                        entity(guid: $entityGuid) {
                                            tagsWithMetadata {
                                                key
                                                values {
                                                    mutable
                                                    value
                                                }
                                            }
                                        }
                                    } 
                                }'''
        variables = {'entityGuid': entity_guid}
        payload = {'query': entity_tags_query, 'variables': variables}
        return nerdgraph.GraphQl.post(per_api_key, payload)

    def gql_get_entities_of_type(self, per_api_key, domain, ent_type):
        query = '''query($domain: String!, $ent_type: String!) { 
                        actor {
                                entitySearch(queryBuilder: {domain: $domain, type: $ent_type}) {
                                  count
                                  results {
                                    nextCursor
                                    entities {
                                      accountId
                                      guid
                                      name
                                      type
                                    }
                                  }
                                }
                        }
                    }'''
        variables = {'domain': domain, 'ent_type': ent_type}
        payload = {'query': query, 'variables': variables}
        response = nerdgraph.GraphQl.post(per_api_key, payload)
        result = {'status': response['status']}
        if 'errors' in response:
            result['error'] = response['errors']
            return result
        result['count'] = response['response']['data']['actor']['entitySearch']['count']
        result['entities'] = response['response']['data']['actor']['entitySearch']['results']['entities']
        return result

    def gql_get_entities_with_tags(self, per_api_key, tags_arr):
        payload = self._entities_by_tags_payload(tags_arr)
        result = {}
        response = nerdgraph.GraphQl.post(per_api_key, payload)
        result['status'] = response['status']
        if 'error' in response:
            result['error'] = response['error']
            return result
        result['count'] = response['response']['data']['actor']['entitySearch']['count']
        result['entities'] = response['response']['data']['actor']['entitySearch']['results']['entities']
        return result

    @staticmethod
    def get_permalink(per_api_key, guid):
        query = '''query($guid: EntityGuid!) { 
                    actor {
                        entity(guid: $guid) {
                            permalink
                        }
                     }
                    }'''
        payload = {"query": query, "variables": {"guid": guid }}
        result = nerdgraph.GraphQl.post(per_api_key, payload)
        logger.debug(json.dumps(result))
        if "entity" in result["response"]["data"]["actor"]:
            return result["response"]["data"]["actor"]["entity"]["permalink"]
        else:
            return "GUID_NOT_FOUND " + guid

    @staticmethod
    def _rest_api_headers(api_key):
        return {'X-Api-Key': api_key, 'Content-Type': 'Application/JSON'}

    @staticmethod
    def _entity_outline(entity_type):
        if entity_type == APM_APP:
            return ''' ... on ApmApplicationEntityOutline {
                            guid
                            applicationId
                            name
                            accountId
                            type
                            language
                            entityType                            
                        } '''
        if entity_type == BROWSER_APP:
            return ''' ... on BrowserApplicationEntityOutline {
                                    guid
                                    applicationId
                                    name
                                    accountId
                                    type
                                    entityType                                    
                                } '''
        if entity_type == MOBILE_APP:
            return ''' ... on MobileApplicationEntityOutline {
                            guid
                            applicationId
                            name
                            accountId
                            type                        
                            entityType                            
                        } '''
        if entity_type == MONITOR:
            return ''' ... on SyntheticMonitorEntityOutline {
                                guid
                                entityType
                                accountId
                                monitorId
                                name                            
                                monitorType                                
                            }  '''

    @classmethod
    def _entity_by_name_payload(cls, entity_type, entity_name):
        return cls._matching_condition_payload(entity_type, "name = '" + entity_name)

    @classmethod
    def _entities_by_tags_payload(cls, tags_arr):
        matching_tags = ""
        for i, tag in enumerate(tags_arr):
            tag_parts = tag.split(":")
            if i == 0:
                matching_tags = "tags." + tag_parts[0] + "='" + tag_parts[1] + "'"
            else:
                matching_tags = matching_tags + " AND tags." + tag_parts[0]
        return cls._all_entities_payload_for(matching_tags)

    @classmethod
    def _all_entities_payload_for(cls, matching_condition):
        entity_search_query = '''query($matchingCondition: String!) { 
                                            actor { 
                                                entitySearch(query: $matchingCondition)  { 
                                                    count 
                                                    results { 
                                                        entities {
                                                              entityType
                                                              guid
                                                              name          
                                                        } 
                                                    } 
                                                } 
                                            } 
                                        }
                                        '''
        variables = {'matchingCondition': matching_condition}
        payload = {'query': entity_search_query, 'variables': variables}
        return payload

    @classmethod
    def _matching_condition_payload(cls, entity_type, matching_condition):
        entity_search_query = '''query($matchingCondition: String!) { 
                                        actor { 
                                            entitySearch(query: $matchingCondition)  { 
                                                count 
                                                results { 
                                                    entities { ''' + cls._entity_outline(entity_type) + '''
                                                    } 
                                                } 
                                            } 
                                        } 
                                    }
                                    '''
        variables = {'matchingCondition': matching_condition + "' AND type = '"+entity_type+"'"}
        payload = {'query': entity_search_query, 'variables': variables}
        return payload

    @staticmethod
    def _matched_apm_app(entity, tgt_account_id, src_entity):
        matched = False
        if entity['entityType'] == 'APM_APPLICATION_ENTITY' and \
           str(entity['accountId']) == str(tgt_account_id) and \
           entity['name'] == src_entity['name'] and \
           entity['language'] == src_entity['language']:
            matched = True
        return matched

    @staticmethod
    def _matched_mobile_app(entity, tgt_account_id, src_entity):
        matched = False
        if entity['entityType'] == 'MOBILE_APPLICATION_ENTITY' and \
           str(entity['accountId']) == str(tgt_account_id) and \
           entity['name'] == src_entity['name']:
            matched = True
        return matched

    @staticmethod
    def _matched_apm_app_name(entity, tgt_account_id, name):
        logger.info(entity['entityType'] + " : " + str(entity['accountId']) + ' : ' + str(tgt_account_id) + ':' + entity['name'] + ':' + name)
        matched = False
        if entity['entityType'] == 'APM_APPLICATION_ENTITY' and \
           str(entity['accountId']) == str(tgt_account_id) and \
           entity['name'] == name:
            matched = True
        return matched

    @staticmethod
    def _matched_mobile_app_name(entity, tgt_account_id, name):
        matched = False
        if entity['entityType'] == 'MOBILE_APPLICATION_ENTITY' and \
           str(entity['accountId']) == str(tgt_account_id) and \
           entity['name'] == name:
            matched = True
        return matched

    @staticmethod
    def _matched_synth_monitor_name(entity, tgt_account_id, name):
        matched = False
        if entity['entityType'] == 'SYNTHETIC_MONITOR_ENTITY' and \
           str(entity['accountId']) == str(tgt_account_id) and \
           entity['name'] == name:
            matched = True
        return matched

    @staticmethod
    def _matched_browser_app(entity, tgt_account_id, src_entity):
        matched = False
        if entity['entityType'] == 'BROWSER_APPLICATION_ENTITY' and \
           str(entity['accountId']) == str(tgt_account_id) and \
           entity['name'] == src_entity['name']:
            matched = True
        return matched

    @staticmethod
    def _matched_browser_app_name(entity, tgt_account_id, name):
        matched = False
        if entity['entityType'] == 'BROWSER_APPLICATION_ENTITY' and \
           str(entity['accountId']) == str(tgt_account_id) and \
           entity['name'] == name:
            matched = True
        return matched

    @staticmethod
    def _extract_entities(gql_rsp_json):
        rsp_entities = gql_rsp_json['data']['actor']['entitySearch']['results']['entities']
        return list(filter(None, rsp_entities))  # remove empty dicts from list

    @classmethod
    def _set_matched_entity(cls, entities, entity_type, result, src_entity, tgt_account_id):
        for entity in entities:
            if entity_type == APM_APP and cls._matched_apm_app(entity, tgt_account_id, src_entity):
                result['entityFound'] = True
                result['entity'] = entity
                break
            if entity_type == BROWSER_APP and cls._matched_browser_app(entity, tgt_account_id, src_entity):
                result['entityFound'] = True
                result['entity'] = entity
                break
            if entity_type == MOBILE_APP and cls._matched_mobile_app(entity, tgt_account_id, src_entity):
                result['entityFound'] = True
                result['entity'] = entity
                break

    @classmethod
    def _set_matched_entity_by_name(cls, acct_id, entity_type, name, result):
        logger.info('matching ' + entity_type + ':' + name)
        for entity in result['entities']:
            if entity_type == APM_APP and cls._matched_apm_app_name(entity, acct_id, name):
                result['entityFound'] = True
                result['entity'] = entity
            if entity_type == BROWSER_APP and cls._matched_browser_app_name(entity, acct_id, name):
                result['entityFound'] = True
                result['entity'] = entity
            if entity_type == MOBILE_APP and cls._matched_mobile_app_name(entity, acct_id, name):
                result['entityFound'] = True
                result['entity'] = entity
            if entity_type == MONITOR and cls._matched_synth_monitor_name(entity, acct_id, name):
                result['entityFound'] = True
                result['entity'] = entity

    @staticmethod
    def _show_url_for_app(entity_type, app_id):
        if MOBILE_APP == entity_type:
            show_url = SHOW_MOBILE_APP_URL
        if APM_APP == entity_type:
            show_url = SHOW_APM_APP_URL
        if show_url:
            return show_url + app_id + '.json'
        logger.error('Only supported for ' + MOBILE_APP + ' and ' + APM_APP)

    # input : key_values - dict with key and array of values as value
    @staticmethod
    def _tagvalues_payload(arr_tagvalues):
        tags_arr = []
        for tag in arr_tagvalues:
            tag_parts = tag.split(':')
            tag_key_values = {'key': tag_parts[0], 'value': tag_parts[1]}
            tags_arr.append(tag_key_values)
        return tags_arr

    # input : key_values - dict with key and array of values as value
    @staticmethod
    def _tags_arr_from(arr_tags):
        tags_arr = []
        for tag in arr_tags:
            tag_parts = tag.split(':')
            tag_key_values = {'key': tag_parts[0], 'values': [tag_parts[1]]}
            tags_arr.append(tag_key_values)
        return tags_arr

    @classmethod
    def _delete_tag_values_payload(cls, entity_guid, arr_tag_values):
        del_tagvalues_query = '''mutation($entityGuid: EntityGuid!, $tagValues: [TaggingTagValueInput!]!) 
                                    { taggingDeleteTagValuesFromEntity (guid: $entityGuid, tagValues: $tagValues) {
                                                errors { 
                                                    message
                                                    type 
                                                } 
                                            }
                                  }'''
        tag_values = cls._tagvalues_payload(arr_tag_values)
        variables = {'entityGuid': entity_guid, 'tagValues': tag_values}
        payload = {'query': del_tagvalues_query, 'variables': variables}
        return payload

    @classmethod
    def _delete_tag_keys_payload(cls, entity_guid, tag_keys):
        del_tagkeys_query = '''mutation($entityGuid: EntityGuid!, $tagKeys: [String!]!) { 
                                    taggingDeleteTagFromEntity (guid: $entityGuid, tagKeys: $tagKeys) {
                                        errors { 
                                            message
                                            type 
                                        } 
                                    }
                                }'''
        variables = {'entityGuid': entity_guid, 'tagKeys': tag_keys}
        payload = {'query': del_tagkeys_query, 'variables': variables}
        return payload

    @classmethod
    def _mutate_tags_payload(cls, entity_guid, arr_label_keys, mutate_action):
        apply_tags_query = '''mutation($entityGuid: EntityGuid!, $tags: [TaggingTagInput!]!) 
                                {''' + mutate_action + '''(guid: $entityGuid, tags: $tags) {
                                            errors { 
                                                message
                                                type 
                                            } 
                                        }
                              }'''
        arr_tags = cls._tags_arr_from(arr_label_keys)
        variables = {'entityGuid': entity_guid, 'tags': arr_tags}
        payload = {'query': apply_tags_query, 'variables': variables}
        return payload

    @classmethod
    def _apply_tags_payload(cls, entity_guid, arr_label_keys):
        return cls._mutate_tags_payload(entity_guid, arr_label_keys, 'taggingAddTagsToEntity')

    @classmethod
    def _replace_tags_payload(cls, entity_guid, arr_label_keys):
        return cls._mutate_tags_payload(entity_guid, arr_label_keys, 'taggingReplaceTagsOnEntity')

    APM_APP = 'APM_APP'
    APM_KT = 'APM_KT'
    BROWSER_APP = 'BROWSER_APP'
    APM_EXT_SVC = 'APM_EXT_SVC'
    MOBILE_APP = 'MOBILE_APP'
    MONITOR = 'SYNTH_MONITOR'
