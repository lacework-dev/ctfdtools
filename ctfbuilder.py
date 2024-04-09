import importlib
import json
import logging
import os
import re
import yaml
from jinja2 import Template, DebugUndefined
from os import listdir
from os.path import isdir, isfile


class CTFBuilder:

    def __init__(self, ctfd, lw, config=None):
        self._config = config 
        self._ctfd = ctfd 
        self._lw = lw 
        self._logger = logging.getLogger(__name__)
        self._schema = None
        self._files = None
        self._challenges = self._get_existing_challenges()
        self._pages = self._get_existing_pages()


    def build_ctf(self, schema):
        self._schema = schema
        self._files = self._upload_files()
        self._build_pages()
        self._build_configuration()
        self._build_challenges()


    def _get_existing_pages(self):
       ctf_pages = {}
       pages = self._ctfd.get_page_list()
       for page in pages['data']:
           ctf_pages[page['route']] = self._ctfd.get_page_details(page['id'])['data']['id']
       return ctf_pages


    def _get_existing_challenges(self):
        ctf_challenges = {}
        challenges = self._ctfd.get_challenge_list()
        for challenge in challenges['data']:
            data = { 'id': challenge['id'], 'flags': [], 'hints': [] }
            flags = self._ctfd.get_challenge_flags(challenge['id'])['data']
            for flag in flags: data['flags'].append(flag['id'])
            hints = self._ctfd.get_challenge_hints(challenge['id'])['data']
            for hint in hints: data['hints'].append(hint['id'])
            ctf_challenges[challenge['name']] = data
        return ctf_challenges


    def _build_pages(self):
       if not isfile(f'{self._schema}/pages.yml'):
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


    def _build_configuration(self):
        self._logger.info(f'Setting initial configuration from {self._schema}/config.yml')
        # Set initial configuration items in CTFd
        with open(f'{self._schema}/config.yml', 'r') as file:
            ctfd_config = yaml.safe_load(file)['config']
        ctfd_config = self._replace_vars(ctfd_config)
        self._ctfd.patch_config_list(ctfd_config)


    def _build_challenges(self):
        # Build challenge board
        self._logger.info('Building CTF categories and challenges.')
        challenges = self._get_challenges()
        for category in challenges.keys():
            for challenge in challenges[category]:
                self._logger.debug(f"Parsing {challenge['name']} challenge: {challenge}")
                challenge['category'] = category.split('_')[1]
                # Check for flags, move to variable for seperate submission, delete flags from challenge object
                flags = challenge.get('flags', [])
                if len(flags) > 0: del challenge['flags']
                # Check for hints, move to variable for seperate submission, delete hints from challenge object
                hints = challenge.get('hints', [])
                if len(hints) > 0: del challenge['hints']
                # Replace challenge names listed in requirements with their id
                if challenge.get('requirements', {}).get('prerequisites'):
                   prerequisites = []
                   for requirement in challenge['requirements']['prerequisites']:
                       prerequisites.append(self._challenges[requirement]['id'])
                   challenge['requirements']['prerequisites'] = prerequisites
                if challenge['name'] in self._challenges:
                    # Update existing challenge instead of creating new
                    self._logger.info(f"Updating existing challenge named {challenge['name']}")
                    self._ctfd.patch_challenge(challenge, self._challenges[challenge['name']]['id'])
                    # Remove existing flags and hints
                    for flag in self._challenges[challenge['name']]['flags']:
                        self._ctfd.delete_flag(flag)
                    for hint in self._challenges[challenge['name']]['hints']:
                        self._ctfd.delete_hint(hint)
                else:
                    self._logger.info(f"Creating new challenge named {challenge['name']}")
                    data = { 'id': '', 'flags': [], 'hints': [] }
                    data['id'] = self._ctfd.post_challenge(challenge)['data']['id']
                    self._challenges[challenge['name']] = data
                for flag in flags:
                    self._logger.debug(f"Posting flag to {challenge['name']} challenge: {flag}")
                    flag['challenge_id'] = self._challenges[challenge['name']]['id']
                    self._ctfd.post_flag(flag)
                for hint in hints:
                    self._logger.debug(f"Posting hint to {challenge['name']} challenge: {hint}")
                    hint['challenge_id'] = self._challenges[challenge['name']]['id']
                    self._ctfd.post_hint(hint)


    def _upload_files(self):
        ctf_files = []
        if not isdir(f'{self._schema}/files'):
            return ctf_files
        files = sorted([f for f in listdir(f'{self._schema}/files') if isfile(f'{self._schema}/files/{f}')])
        self._logger.info(f'Uploading files from {self._schema}/files.')
        self._logger.debug(f'Retrieved the following files for the CTF: {files}')
        for file in files:
            file = open(f"{self._schema}/files/{file}", "rb")
            ctf_files.append(self._ctfd.post_file({'file': file})['data'][0])
        return ctf_files


    def _get_challenges(self):
        # Only use directories in the schema that start with a digit and underscore
        # ie: 1_getting to know you
        categories = sorted([d for d in listdir(self._schema) if isdir(f'{self._schema}/{d}') and re.search('^\d{1,3}\_', d)])
        self._logger.debug(f'Retrieved the following categories from {self._schema}: {categories}')
        challenges = {}
        for category in categories:
            with open(f'{self._schema}/{category}/challenges.yml', 'r') as file:
                self._logger.debug(f'Loading challenges from {self._schema}/{category}/challenges.yml')
                challenges[category] = yaml.safe_load(file)['challenges']
        challenges = self._parse_challenges(challenges)
        return challenges


    def _replace_vars(self, data):
        for file in self._files:
            if data.get('ctf_logo'):
                data = json.loads(json.dumps(data).replace('{{ ' + file['location'].split('/')[1] + ' }}', file['location']))
            else:
                data = json.loads(json.dumps(data).replace('{{ ' + file['location'].split('/')[1] + ' }}', '/files/' + file['location']))
        template = Template(json.dumps(data), undefined=DebugUndefined)
        replace_vars = {}
        for key, value in self._config.items():
            replace_vars[f'CONFIG_{key.upper()}'] = value
        data = json.loads(template.render(self._config))
        return data


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
                    ctf = importlib.machinery.SourceFileLoader(category, f'{category}/__init__.py').load_module()
                    if hasattr(ctf, 'parse_challenge'):
                        challenge = ctf.parse_challenge(challenge, self._config, self._lw)
                except Exception as error:
                    self._logger.warning(f"Failed parsing '{challenge['name']}' challenge in custom parse_challenge function: Error: {error}")
                finally:
                    os.chdir(saved_dir)
                # If challenge has no flags, it is unsolvable. Print a warning and hide the challenge.
                if len(challenge.get('flags', [])) < 1:
                    self._logger.warning(f"'{challenge['name']}' has no flags and is not solvable. Setting visiblity to hidden.")
                    challenge['state'] = 'hidden'
                parsed[category].append(challenge)
        return parsed
