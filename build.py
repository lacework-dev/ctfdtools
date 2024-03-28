#!/usr/bin/env python3

import argparse
import json
import logging
import sys
from ctfbuilder import CTFBuilder
from ctfd import CTFd
from lacework import Lacework
from os.path import isdir, isfile
from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.shortcuts import checkboxlist_dialog
from prompt_toolkit.shortcuts import input_dialog


VERSION = '0.0.2'


# Uncomment the following line for debug information on 3rd party modules
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setLevel(logging.WARNING)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def parse_args():
    logger.debug('Parsing command line arguments')
    parser = argparse.ArgumentParser(description=f'Create a prospect/customer Lacework CTF in CTFd. Default behavior with no arguments creates a config and builds the CTF in CTFd.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', '--config', type=argparse.FileType('r'), help='Use specified config to build CTF in CTFd.')
    group.add_argument('-g', '--generate-config', action='store_true', help='Generate CTF config and exit.')
    parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {VERSION}')
    parser.add_argument('-p', '--profile', default='default', help='Specify profile to use from lacework CLI configuration. Defaults to \'default\'.')
    parser.add_argument('-s', '--schema', default='ctf', help='Path to CTF schema directory. Defaults to \'ctf\'.')
    return parser.parse_args()


def choose_option(data, entity):
    choices = []
    results = ''
    if entity == 'subaccount':
        for account in data[0]['accounts']:
            choices.append((account['accountName'], account['accountName']))
        results = radiolist_dialog(
            title='Subaccounts',
            text='Which subaccount would you like to use?',
            values=choices
        ).run()

    elif entity == 'aws_accounts':
        for account in data:
            text = f"{account['account']} ({account['name']})"
            choices.append((account['account'], text))
        results = checkboxlist_dialog(
            title='AWS Accounts',
            text='Which AWS account(s) would you like to use?',
            values=choices
        ).run()

    elif entity == 'identity':
        identities = sorted(data, reverse=True, key=lambda x: x['METRICS']['risk_score'])
        for identity in identities:
            user = identity['PRINCIPAL_ID'].split('/')[1]
            risk_score = identity['METRICS']['risk_score']
            risks = []
            for risk in identity['METRICS']['risks']:
                risks.append(f'    {risk}')
            risks = "\n".join(risks)
            text = f'{user}  Score: {risk_score}\n{risks}\n'
            choices.append((identity['PRINCIPAL_ID'], text))
        results = radiolist_dialog(
            title='Identities',
            text='Which identity would you like to use?',
            values=choices
        ).run()

    elif entity == 'ctfd_url':
        results = input_dialog(
            title='Enter CTFd URL',
            text='https://xxx.xxx.xxx.xxx:port').run()

    elif entity == 'ctfd_api_key':
        results = input_dialog(
            password=True,
            title='Enter CTFd API Key',
            text='Provide API key from a CTFd admin account').run()

    return results


def build_config(lw):
    config = {'account': lw.account, 'profile': lw.profile}
    config['subaccount'] = choose_option(lw.get_lw_subaccounts(), 'subaccount')
    lw.subaccount = config['subaccount']
    config['aws_accounts'] = choose_option(lw.get_aws_accounts(), 'aws_accounts')
    template = '('
    for aws_account in config['aws_accounts']:
        template = template + f'I.PRINCIPAL_ID LIKE "%::{aws_account}:%" OR '
    template = template + '0=1)'
    config['aws_principal_id'] = choose_option(lw.run_lw_query('identities.yml', template), 'identity')
    config['aws_user'] = config['aws_principal_id'].split('/')[1]
    config['ctfd_url'] = choose_option('', 'ctfd_url')
    config['ctfd_api_key'] = choose_option('', 'ctfd_api_key')
    return config


def main():
    args = parse_args()

    if args.schema:
        logger.debug(f'Using schema directory of \'{args.schema}\' from CLI arguments.')
        if not isdir(args.schema):
            raise Exception('Invalid CTF schema directory supplied: {args.schema}')
        if not isfile(f'{args.schema}/config.yml'):
            raise Exception('No config.yml file found in the CTF schema directory {args.schema}')

    # Build or load configuration
    if args.config:
        logger.debug('Using provided config.json')
        config = json.loads(args.config.read())
        lw = Lacework(config['profile'], config['subaccount'])
    else:
        logger.debug(f'Build new configuration using the {args.profile} profile.')
        lw = Lacework(args.profile)
        config = build_config(lw)
        lw.subaccount = config['subaccount']

    logger.info(json.dumps(config))
    if args.generate_config:
        print(json.dumps(config))
        sys.exit(0)

    ctfd = CTFd(config['ctfd_api_key'], config['ctfd_url'])
    cb = CTFBuilder(ctfd, lw, config)

    # Build out the CTF using the above configuration
    cb.build_ctf(args.schema)


if __name__ == "__main__":
    main()
