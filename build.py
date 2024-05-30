#!/usr/bin/env python3

import argparse
import json
import logging
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
    parser = argparse.ArgumentParser(description=f'A tool for working with CTFd.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-g', '--generate-config', action='store_true', help='Generate CTF build configuration from schema.')
    parser.add_argument('-s', '--schema', help='Path to CTF schema directory.')
    group.add_argument('-c', '--config', type=argparse.FileType('r'), help='Use specified configuration file.')
    parser.add_argument('-b', '--build', action='store_true', help='Use configuration to build CTF')
    parser.add_argument('-a', '--answers', action='store_true', help='Use configuration to pull latest flags from CTFd instance.')
    parser.add_argument('-e', '--export-schema', action='store_true', help='Use configuration to export running CTFd instance to schema.')
    parser.add_argument('-E', '--export-csv', action='store_true', help='Use configuration to export running CTFd challenges to CSV.')
    parser.add_argument('-C', '--category', help='Specify a directory name (or names in a comma separated list) within the schema to limit build to just that category. Defaults to All')
    return parser.parse_args()


def main():
    args = parse_args()

    if args.schema and not args.export_schema:
        logger.debug(f'Using schema directory of \'{args.schema}\' from CLI arguments.')
        if not isdir(args.schema):
            raise Exception('Invalid CTF schema directory supplied: {args.schema}')
        if not isfile(f'{args.schema}/config.yml'):
            raise Exception('No config.yml file found in the CTF schema directory {args.schema}')

    if args.generate_config:
        if not args.schema:
            raise Exception('Must specify a --schema when generating a configuration.')
        cb = CTFBuilder(None, {'schema': args.schema})
        config = cb.generate_config()
        print(json.dumps(config))
        sys.exit(0)

    if not args.build and not args.answers and not args.export_schema and not args.export_csv:
        raise Exception('Specify one of -b/--build or -a/--answer or -e/--export-schema or -E/--export-csv arguments to take further action.')
        sys.exit(0)

    logger.debug(f"Using provided config {args.config}")
    config = json.loads(args.config.read())
    if args.schema:
        config['schema'] = args.schema
    ctfd = CTFd(config['ctfd_api_key'], config['ctfd_url'])
    cb = CTFBuilder(ctfd, config)

    if args.build:
        if args.category:
            cb.build_ctf(config['schema'], args.category)
        else:
            cb.build_ctf(config['schema'])

    elif args.answers:
        print(cb.get_answers())

    elif args.export_csv:
        print(cb.get_csv())

    elif args.export_schema:
        if not args.schema:
            raise Exception('Must specify a --schema when generating a configuration.')
        cb.export_ctf(config['schema'])


if __name__ == "__main__":
    main()
