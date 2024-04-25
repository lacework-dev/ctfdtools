#!/usr/bin/env python3

import argparse
import importlib
import json
import logging
import os
import sys
from ctfbuilder import CTFBuilder
from ctfd import CTFd
from os.path import isdir, isfile


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
    parser = argparse.ArgumentParser(description=f'Create a prospect/customer Lacework CTF in CTFd.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', '--config', type=argparse.FileType('r'), help='Use specified CTF build configuration.')
    group.add_argument('-g', '--generate-config', action='store_true', help='Generate CTF build configuration from schema.')
    parser.add_argument('-s', '--schema', help='Path to CTF schema directory.')
    parser.add_argument('-b', '--build', action='store_true', help='Use specified build configuration to build CTF')
    parser.add_argument('-a', '--answers', action='store_true', help='Use specified build configuration and pull latest flags from CTFd instance.')
    parser.add_argument('-C', '--category', default='All', help='Specify a directory name (or names in a comma separated list) within the schema to limit build to just that category. Defaults to All')
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
        if not args.schema:
            raise Exception('Must specify a --schema when generating a configuration.')

        # At a minimum config must contain CTFd details and Lacework profile/account
        config = { 'ctfd_api_key': '', 'ctfd_url': '', 'schema': args.schema }
        if isfile(f'{args.schema}/__init__.py'):
            logger.info(f'Loading module from schema: {args.schema}')
            ctf = importlib.machinery.SourceFileLoader('schema', f'{args.schema}/__init__.py').load_module()
            # Change working directory so that loaded function can access correct lql directory
            saved_dir = os.getcwd()
            os.chdir(f'{saved_dir}/{args.schema}')
            if hasattr(ctf, 'build_config'):
                config = ctf.build_config(config)
            os.chdir(saved_dir)
        print(json.dumps(config))
        sys.exit(0)


    logger.debug(f"Using provided config {args.config}")
    config = json.loads(args.config.read())
    if args.schema:
        config['schema'] = args.schema
    if not config.get('subaccount'):
        config['subaccount'] = config['account']
    categories = ['All']
    ctfd = CTFd(config['ctfd_api_key'], config['ctfd_url'])
    cb = CTFBuilder(ctfd, config)

    if args.build:
        if args.category != 'All':
            try:
                categories = args.category.split(',')
            except:
                raise Exception(f'Invalid category specification "{args.category}", must be comma separated list')
            for category in categories:
                bad_categories = []
                if not isdir(f"{config['schema']}/{category}"):
                    bad_categories.append(f"{config['schema']}/{category}")
            if len(bad_categories) > 0:
                raise Exception(f"The catory|ies] {bad_categories} is|are not valid")
        # Build out the CTF using the above configuration
        cb.build_ctf(config['schema'], categories)

    if args.answers:
        print(cb.get_answers())


if __name__ == "__main__":
    main()
