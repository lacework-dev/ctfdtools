from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.shortcuts import checkboxlist_dialog
from prompt_toolkit.shortcuts import input_dialog


def choose_option(data, entity):
    choices = []
    results = ''
    if entity == 'ctfd_url':
        results = input_dialog(
            title='Enter CTFd URL',
            text='https://xxx.xxx.xxx.xxx:port').run()

    elif entity == 'ctfd_api_key':
        results = input_dialog(
            password=True,
            title='Enter CTFd API Key',
            text='Provide API key from a CTFd admin account').run()

    return results


def build_config(config, lw):
    config['ctfd_url'] = choose_option('', 'ctfd_url')
    config['ctfd_api_key'] = choose_option('', 'ctfd_api_key')
    return config
