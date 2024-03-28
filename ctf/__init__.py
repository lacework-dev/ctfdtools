from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.shortcuts import checkboxlist_dialog
from prompt_toolkit.shortcuts import input_dialog


def build_config(config, lw):
    config['ctfd_url'] = input_dialog(
        title='Enter CTFd URL',
        text='https://xxx.xxx.xxx.xxx:port').run()
    config['ctfd_api_key'] = input_dialog(
        password=True,
        title='Enter CTFd API Key',
        text='Provide API key from a CTFd admin account').run()
    return config
