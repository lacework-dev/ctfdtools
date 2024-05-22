import importlib
import json
import logging
import os
import re
import yaml
import traceback
from jinja2 import Template, DebugUndefined
from os import listdir
from os.path import isdir, isfile


class CTFBuilder:

    def __init__(self, ctfd=None, config=None):
        self._config = config
        self._ctfd = ctfd
        self._logger = logging.getLogger(__name__)
        self._schema = None
        self._files = None
        self._challenges = {}
        self._pages = {}
        self._category = None

    def build_ctf(self, schema, category=None):
        if category is None:
            category = ['All']
        self._schema = schema
        self._challenges = self._get_existing_challenges()
        self._pages = self._get_existing_pages()
        self._category = category
        if category != ['All']:
            try:
                self._category = self._category.split(',')
            except AttributeError:
                raise Exception(f'Invalid category specification "{self._category}", must be comma separated list')
            bad_categories = []
            for category in self._category:
                if not isdir(f"{self._config['schema']}/{category}"):
                    bad_categories.append(f"{self._config['schema']}/{category}")
            if len(bad_categories) > 0:
                raise Exception(f"One or more category is not valid")
        self._files = self._upload_files()
        self._build_pages()
        self._build_configuration()
        self._build_challenges()

    def generate_config(self):
        # At a minimum config must contain CTFd details and schema
        config = {'ctfd_api_key': '', 'ctfd_url': '', 'schema': self._config['schema']}
        if isfile(f"{self._config['schema']}/__init__.py"):
            self._logger.info(f"Loading module from schema: {self._config['schema']}")
            saved_dir = os.getcwd()
            os.chdir(f"{saved_dir}/{self._config['schema']}")
            ctf = importlib.machinery.SourceFileLoader('schema', f'__init__.py').load_module()
            if hasattr(ctf, 'build_config'):
                config = ctf.build_config(config)
            os.chdir(saved_dir)
        return config

    def get_answers(self):
        answers = '''
                      _
                     | |
                     | |===( )   //////
                     |_|   |||  | o o|
                            ||| ( c  )                  ____
                             ||| \= /                  ||   \_
                              ||||||                   ||     |
                              ||||||                ...||__/|-"
                              ||||||             __|________|__
                                |||             |______________|
                                |||             || ||      || ||
                                |||             || ||      || ||
        ------------------------|||-------------||-||------||-||-------
                                |__>            || ||      || ||


        can i haz flags?

        .:. challenges .:.
        '''
        challenges = self._ctfd.get_challenge_list()
        for challenge in challenges['data']:
            answers = f"{answers}\n        name: {challenge['name']}"
            answers = f"{answers}\n        category: {challenge['category']}"
            answers = f"{answers}\n        flags:"
            flags = self._ctfd.get_challenge_flags(challenge['id'])['data']
            for flag in flags:
                answers = f"{answers} {flag['content']},"
            answers = f'{answers[:-1]}\n'
        return answers

    def _build_challenges(self):
        self._logger.info('Building CTF categories and challenges.')
        challenges = self._parse_challenges(self._get_challenges())
        for category in challenges.keys():
            for challenge in challenges[category]:
                self._logger.debug(f"Parsing {challenge['name']} challenge: {challenge}")
                challenge['category'] = category.split('_')[1]
                # Check for flags, move to variable for separate submission
                flags = challenge.get('flags', [])
                if len(flags) > 0:
                    del challenge['flags']
                # Check for hints, move to variable for separate submission
                hints = challenge.get('hints', [])
                if len(hints) > 0:
                    del challenge['hints']
                # Check for tags, move to variable for separate submission
                tags = challenge.get('tags', [])
                if len(tags) > 0:
                    del challenge['tags']
                if challenge.get('next_id'):
                    del challenge['next_id']
                if challenge['name'] in self._challenges:
                    # Update existing challenge instead of creating new
                    self._logger.info(f"Updating challenge named {challenge['name']}")
                    self._ctfd.patch_challenge(challenge, self._challenges[challenge['name']]['id'])
                    # Remove existing flags, hints, and tags
                    # If game in progress, players will keep their existing solves
                    for flag in self._challenges[challenge['name']]['flags']:
                        self._ctfd.delete_flag(flag)
                    # this is problematic if game is in progress as player will lose
                    # hints they have already unlocked
                    for hint in self._challenges[challenge['name']]['hints']:
                        self._ctfd.delete_hint(hint)
                    for tag in self._challenges[challenge['name']]['tags']:
                        self._ctfd.delete_tag(tag)
                else:
                    self._logger.info(f"Creating new challenge named {challenge['name']}")
                    data = {'id': self._ctfd.post_challenge(challenge)['data']['id'], 'flags': [], 'hints': []}
                    self._challenges[challenge['name']] = data
                for flag in flags:
                    self._logger.debug(f"Posting flag to {challenge['name']} challenge: {flag}")
                    flag['challenge_id'] = self._challenges[challenge['name']]['id']
                    self._ctfd.post_flag(flag)
                for hint in hints:
                    self._logger.debug(f"Posting hint to {challenge['name']} challenge: {hint}")
                    hint['challenge_id'] = self._challenges[challenge['name']]['id']
                    self._ctfd.post_hint(hint)
                for tag in tags:
                    self._logger.debug(f"Posting tag to {challenge['name']} challenge: {tag}")
                    tag['challenge_id'] = self._challenges[challenge['name']]['id']
                    self._ctfd.post_tag(tag)

        # now that challenges have been submitted, and we have IDs, read yaml back in and add the
        # prerequisite requirements IDs and next challenge ID in place of challenge names
        challenges = self._get_challenges()
        for category in challenges.keys():
            for challenge in challenges[category]:
                self._logger.debug(f"Checking requirements and next_id for {challenge['name']} challenge: {challenge}")
                update_challenge = {}
                # Replace challenge names listed next_id with their id
                if challenge.get('next_id'):
                    self._logger.debug('Updating next_id with challenge id')
                    update_challenge['next_id'] = self._challenges[challenge['next_id']]['id']
                if challenge.get('requirements', {}).get('prerequisites'):
                    self._logger.debug('Updating requirements with challenge ids')
                    update_challenge['requirements'] = {}
                    prerequisites = []
                    for requirement in challenge['requirements']['prerequisites']:
                        self._logger.debug(f"Adding challenge id {self._challenges[requirement]['id']}")
                        prerequisites.append(self._challenges[requirement]['id'])
                    update_challenge['requirements']['prerequisites'] = prerequisites
                if len(update_challenge) > 0:
                    self._logger.debug(f"Posting {challenge['name']} challenge: {update_challenge}")
                    self._ctfd.patch_challenge(update_challenge, self._challenges[challenge['name']]['id'])

    def _build_configuration(self):
        self._logger.info(f'Setting initial configuration from {self._schema}/config.yml')
        with open(f'{self._schema}/config.yml', 'r') as file:
            ctfd_config = yaml.safe_load(file)['config']
        ctfd_config = self._replace_vars(ctfd_config)
        self._ctfd.patch_config_list(ctfd_config)

    def _build_pages(self):
        if not isfile(f'{self._schema}/pages.yml'):
            # if pages.yml does not exist in schema, ignore
            return
        self._logger.info(f'Loading pages from {self._schema}/pages.yml')
        with open(f'{self._schema}/pages.yml', 'r') as file:
            pages = yaml.safe_load(file)['pages']
        for page in pages:
            page = self._replace_vars(page)
            if page['route'] in self._pages:
                self._ctfd.patch_page(page, self._pages[page['route']])
            else:
                page = self._ctfd.post_page(page)['data']
                self._pages[page['route']] = page['id']

    def _get_challenges(self):
        # Only use directories in the schema that start with a digit and underscore
        # ie: 1_getting to know you
        if self._category != ['All']:
            dir_list = self._category
        else:
            dir_list = listdir(self._schema)
        categories = sorted([d for d in dir_list if isdir(f'{self._schema}/{d}') and re.search('^\d{1,3}\_', d)])
        self._logger.debug(f'Retrieved the following categories from {self._schema}: {categories}')
        challenges = {}
        for category in categories:
            with open(f'{self._schema}/{category}/challenges.yml', 'r') as file:
                self._logger.debug(f'Loading challenges from {self._schema}/{category}/challenges.yml')
                challenges[category] = yaml.safe_load(file)['challenges']
        return challenges

    def _get_existing_challenges(self):
        ctf_challenges = {}
        challenges = self._ctfd.get_challenge_list()
        for challenge in challenges['data']:
            data = {'id': challenge['id'], 'flags': [], 'hints': [], 'tags': []}
            flags = self._ctfd.get_challenge_flags(challenge['id'])['data']
            for flag in flags:
                data['flags'].append(flag['id'])
            hints = self._ctfd.get_challenge_hints(challenge['id'])['data']
            for hint in hints:
                data['hints'].append(hint['id'])
            tags = self._ctfd.get_challenge_tags(challenge['id'])['data']
            for tag in tags:
                data['tags'].append(tag['id'])
            ctf_challenges[challenge['name']] = data
        return ctf_challenges

    def _get_existing_pages(self):
        ctf_pages = {}
        pages = self._ctfd.get_page_list()
        for page in pages['data']:
            ctf_pages[page['route']] = self._ctfd.get_page_details(page['id'])['data']['id']
        return ctf_pages

    def _parse_challenges(self, challenges):
        challenges = self._replace_vars(challenges)
        parsed = {}
        saved_dir = os.getcwd()
        for category in challenges.keys():
            parsed[category] = []
            for challenge in challenges[category]:
                try:
                    # Look for a custom parse_challenge function in schema/1_category/__init__.py for each category
                    os.chdir(f'{saved_dir}/{self._schema}')
                    # everything initialized in the schema module will get passed into parse_challenge
                    schema = importlib.machinery.SourceFileLoader('schema', '__init__.py').load_module()
                    if hasattr(schema, 'init_schema'):
                        schema.init_schema(self._config)
                    ctf = importlib.machinery.SourceFileLoader(category, f'{category}/__init__.py').load_module()
                    if hasattr(ctf, 'parse_challenge'):
                        challenge = ctf.parse_challenge(schema, challenge, self._config)
                except Exception as error:
                    traceback.print_exc()
                    self._logger.warning(
                        f"Failed parsing '{challenge['name']}' challenge in custom parse_challenge function: Error: {error}")
                finally:
                    os.chdir(saved_dir)
                # If challenge has no flags, it is unsolvable. Print a warning and hide the challenge.
                if len(challenge.get('flags', [])) < 1:
                    self._logger.warning(
                        f"'{challenge['name']}' has no flags and is not solvable. Setting visibility to hidden.")
                    challenge['state'] = 'hidden'
                parsed[category].append(challenge)
        return parsed

    def _replace_vars(self, data):
        """
        This function replaces the templating variables throughout the YAML
        Any file that exists in schema/files can be referenced {{ Filename.png }}
        Any config variable can be referenced {{ CONFIG_VAR_NAME }}
        """
        for file in self._files:
            if data.get('ctf_logo'):
                data = json.loads(
                    json.dumps(data).replace('{{ ' + file['location'].split('/')[1] + ' }}', file['location']))
            else:
                data = json.loads(json.dumps(data).replace('{{ ' + file['location'].split('/')[1] + ' }}',
                                                           '/files/' + file['location']))
        template = Template(json.dumps(data), undefined=DebugUndefined)
        replace_vars = {}
        for key, value in self._config.items():
            replace_vars[f'CONFIG_{key.upper()}'] = value
        data = json.loads(template.render(replace_vars))
        return data

    def _upload_files(self):
        ctf_files = []
        if not isdir(f'{self._schema}/files'):
            # if files directory does not exist in schema, ignore
            return ctf_files
        # sort files by leading number
        files = sorted([f for f in listdir(f'{self._schema}/files') if isfile(f'{self._schema}/files/{f}')])
        self._logger.info(f'Uploading files from {self._schema}/files.')
        self._logger.debug(f'Retrieved the following files for the CTF: {files}')
        for file in files:
            file = open(f"{self._schema}/files/{file}", "rb")
            results = self._ctfd.post_file({'file': file})['data'][0]
            ctf_files.append(results)
        return ctf_files
