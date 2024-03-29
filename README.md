[![New Relic Experimental header](https://github.com/newrelic/opensource-website/raw/master/src/images/categories/Experimental.png)](https://opensource.newrelic.com/oss-category/#new-relic-experimental)

# nrpy

Python wrapper scripts for Nerdgraph and REST API

## Installation

### Pre-requisites

- [x] Python 3.7
- [x] pip3 install requests

  ### Install

- [x] Download and unzip a release of nrpy project

## Getting Started

The table below lists the scripts that can be used for different use cases.

No. | Use Case         | Scripts
--- | ---------------- | -----------------------------------------------------------
1.  | Update Tag value | entitytags --delTagValues "key:value" --addTags "key:value"
2.  | Dashboards       | 
3.  | Alerts AI        |
4.  | CCU Consumption  |
## Usage

### 1) python3 entitytags.py

`usage: entitytags.py [-h] --personalApiKey PERSONALAPIKEY [--delTagValues DELTAGVALUES] [--addTags ADDTAGS] [--rmAllInfraHostTags] [--getAllInfraHostTags]`

Parameter           | Note
------------------- | ---------------------------------------------------
personalApiKey      | Personal API key of a user who can edit tags
delTagValues        | Tag Values to be deleted : owner:John
addTags             | Tags to be added : owner:Jack
getAllInfraHostTags | pass to list all mutable tags for all infra hosts
rmAllInfraHostTags  | pass to delete all mutable tags for all infra hosts

### 2) python3 dashboards.py

Supports two actions --download or --copy

`usage: dashboards.py [-h] --fromAccount FROMACCOUNT --fromApiKey FROMAPIKEY --entityGuid ENTITYGUID [--download] [--copy] [--toAccount TOACCOUNT] [--toApiKey TOAPIKEY] [--toName TONAME]`

Parameter   | Note
----------- | -------------------------------------------------------------------------------
fromAccount | Account from which dashboard is sourced
fromApiKey  | User API Key fromAccount
entityGuid  | entityGuid of dashboard (copy this from NR1 UI view metadata and tags option)
download    | Downloads the dashboard json to current directory accountId-dashboardName.json
copy        | Copies dashboard to options provided in following to... parameters
toAccount   | copy toAccount
toApiKey    | (optional) if not provided fromApiKey is used and assumed to work for toAccount
toName      | (optional) copy toName if not then copied as 'Copy of ' source dashboard name

### 3) python3 alertsai.py


### 4) python3 ccuconsumption.py
This script will generate a report of all conditions CCU consumption between the given `SINCE` and `UNTIL` date from all the accounts the user has access to.

#### Pre-requisites:
Update the `ccuconsumption.json` file with the following details:
- `nr_user_api_key`: User API key
- `since`: The start date for the report in the format `YYYY-MM-DDTHH:MM:SSZ`
- `until`: The end date for the report in the format `YYYY-MM-DDTHH:MM:SSZ`



### Logging

Logs are stored in logs/nrpy.log Logging level can be set in nrpylogger.py. Default level for file and stdout is INFO

## Contributing

We encourage your contributions to improve nrpy! Keep in mind when you submit your pull request, you'll need to sign the CLA via the click-through using CLA-Assistant. You only have to sign the CLA one time per project. If you have any questions, or to execute our corporate CLA, required if your contribution is on behalf of a company, please drop us an email at opensource@newrelic.com.

**A note about vulnerabilities**

As noted in our [security policy](../../security/policy), New Relic is committed to the privacy and security of our customers and their data. We believe that providing coordinated disclosure by security researchers and engaging with the security community are important means to achieve our security goals.

If you believe you have found a security vulnerability in this project or any of New Relic's products or websites, we welcome and greatly appreciate you reporting it to New Relic through [HackerOne](https://hackerone.com/newrelic).

## License

nr-account-migration is licensed under the [Apache 2.0](http://apache.org/licenses/LICENSE-2.0.txt) License.
