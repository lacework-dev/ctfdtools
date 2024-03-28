#!/usr/bin/env python3

import argparse
import importlib
import json
import logging
import os
import sys
from ctfbuilder import CTFBuilder
from ctfd import CTFd
from lacework import Lacework
from os.path import isdir, isfile
from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.shortcuts import checkboxlist_dialog
from prompt_toolkit.shortcuts import input_dialog


# Uncomment the following line for debug information on 3rd party modules
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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
    group.add_argument('-c', '--config', type=argparse.FileType('r'), help='Use specified CTF build configuration.')
    group.add_argument('-g', '--generate-config', action='store_true', help='Generate CTF build configuration from schema.')
    parser.add_argument('-p', '--profile', default='default', help='Specify profile to use from lacework CLI configuration. Defaults to \'default\'.')
    parser.add_argument('-s', '--schema', default='ctf', help='Path to CTF schema directory. Defaults to \'ctf\'.')
    return parser.parse_args()


def main():
    args = parse_args()

    if args.schema:
        logger.debug(f'Using schema directory of \'{args.schema}\' from CLI arguments.')
        if not isdir(args.schema):
            raise Exception('Invalid CTF schema directory supplied: {args.schema}')
        if not isfile(f'{args.schema}/config.yml'):
            raise Exception('No config.yml file found in the CTF schema directory {args.schema}')

    if args.generate_config:
        logger.debug(f'Build new configuration using the {args.profile} profile.')
        lw = Lacework(args.profile)
        # At a minimum config must contain CTFd details and Lacework profile/account
        config = {'ctfd_api_key': '', 'ctfd_url': '', 'profile': args.profile, 'account': lw.account}
        if isfile(f'{args.schema}/__init__.py'):
            logger.info(f'Loading module from schema: {args.schema}')
            ctf = importlib.machinery.SourceFileLoader('schema', f'{args.schema}/__init__.py').load_module()
            # Change working directory so that loaded function can access correct lql directory
            saved_dir = os.getcwd()
            os.chdir(f'{saved_dir}/{args.schema}')
            if hasattr(ctf, 'build_config'):
                config = ctf.build_config(config, lw)
            os.chdir(saved_dir)
        print(json.dumps(config))
        sys.exit(0)


    logger.debug('Using provided config.json')
    config = json.loads(args.config.read())
    lw = Lacework(config['profile'], config['subaccount'])
    ctfd = CTFd(config['ctfd_api_key'], config['ctfd_url'])
    cb = CTFBuilder(ctfd, lw, config)

    # Build out the CTF using the above configuration
    cb.build_ctf(args.schema)


if __name__ == "__main__":
    main()
