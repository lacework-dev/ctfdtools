import configparser
import json
import logging
import os.path
import requests
import subprocess
from jinja2 import Template
from os.path import isfile


class Lacework:

    def __init__(self, profile, subaccount=None):
        self.profile = profile
        self._logger = logging.getLogger(__name__)

        self.account, self._token = self._get_access_token(profile)
        if subaccount:
            self.subaccount = subaccount
        else:
            self.subaccount = self.account
        self._session = requests.Session()
        self._base_url  = f'https://{self.account}.lacework.net'


    def get_aws_accounts(self):
        """
        https://docs.lacework.net/api/v2/docs/#tag/CloudAccounts/paths/~1api~1v2~1CloudAccounts/get
        /api/v2/CloudAccounts
        """
        self._logger.debug('Retrieving AWS accounts from CloudAccounts endpoint.')
        headers = {'Content-Type':'application/json', 'Authorization':f'Bearer {self._token}', 'Account-Name': self.subaccount}
        url = f'{self._base_url}/api/v2/CloudAccounts'
        results = requests.get(url, headers=headers)
        accounts = []
        try:
            csp_accounts = results.json().get('data', [])
        except:
            return accounts
        for csp_account in csp_accounts:
            if csp_account['type'] == 'AwsCfg':
                accounts.append({'name': csp_account['name'], 'account': csp_account['data']['awsAccountId']})
        return accounts


    def get_lw_subaccounts(self):
        """
        https://docs.lacework.net/api/v2/docs/#tag/UserProfile
        /api/v2/UserProfile
        """
        self._logger.debug('Retrieving Lacework sub-accounts from UserProfile endpoint.')
        url = f'{self._base_url}/api/v2/UserProfile'
        headers = {'Content-Type':'application/json', 'Authorization':f'Bearer {self._token}', 'Account-Name': self.account}
        results = requests.get(url, headers=headers)
        try:
            subaccounts = results.json().get('data', [])
        except:
            return [] 
        return subaccounts


    def api(self, path, method='GET', json=None):
        self._logger.debug(f'Making Lacework API call to {path} with {method} method.')
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Account-Name": f"Bearer {self.subaccount}",
            "Content-Type": "application/json"
        }
        results = self._session.request(
            method,
            f"{self._base_url}{path}",
            headers=headers,
            json=json
        )
        # If no results are returned then return an empty dictionary for use downstream
        try:
            results = results.json()
        except:
            return {}

        if results.get("paging", {}).get("urls", {}).get("nextPage"):
            url = results.get("paging", {}).get("urls", {}).get("nextPage")
            additional_results = results
            while additional_results.get("paging", {}).get("urls", {}).get("nextPage"):
                new_additional_results = self._session.request(
                    'GET',
                    url,
                    headers=headers
                )
                additional_results = new_additional_results.json()
                url = additional_results.get("paging", {}).get("urls", {}).get("nextPage")
                results.get('data', []).extend(additional_results.get('data', []))
        return results


    def cli(self, args):
        self._logger.debug(f'Making Lacework CLI command with these arguments: {args}')
        cli_args = ['lacework', '-p', self.profile, '--noninteractive', '--subaccount', self.subaccount]
        cli_args = cli_args + args
        results = subprocess.run(cli_args, capture_output=True, text=True, check=False)
        return results.stdout


    def run_lw_query(self, query, template='', range=None):
        self._logger.debug(f'Running Lacework LQL query with {query} file')
        with open(f'lql/{query}', 'r') as file:
            lql = Template(file.read())
        stdin = lql.render(template=template)
        args = ['lacework', '-p', self.profile, 'query', 'run', '--noninteractive', '--subaccount', self.subaccount]
        if range:
            args.append('--range')
            args.append(range)
        p = subprocess.Popen(args, stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        results, stderr = p.communicate(stdin)
        try:
            return json.loads(results)
        except:
            raise Exception(f'Lacework LQL query failed. Message: {stderr}')


    def _get_access_token(self, profile):
        self._logger.debug(f'Retrieving access token for {profile} Lacework profile.')
        # Read in lacework cli config file and pull details for specified profile
        home = os.path.expanduser('~')
        if not isfile(f'{home}/.lacework.toml'):
            raise Exception('Lacework CLI configuration not found.')
        config = configparser.ConfigParser()
        config.read(home + "/.lacework.toml")
        if not config.has_section(profile):
            raise Exception(f'Lacework CLI profile {profile} was not found.')
        # Use API key and secret to get access token / bearer token
        api_key = config[profile]['api_key'].strip('"')
        api_secret = config[profile]['api_secret'].strip('"')
        account = config[profile]['account'].strip('"')
        url = f'https://{account}.lacework.net/api/v2/access/tokens'
        headers = {'Content-Type': 'application/json', 'X-LW-UAKS': api_secret}
        data = {'keyId': api_key, 'expiryTime': 7200}
        results = requests.post(url, headers=headers, data=json.dumps(data))
        try:
            token = results.json()['token']
        except:
            raise Exception('Failure to retrieve Lacework access token.')
        return account, token
