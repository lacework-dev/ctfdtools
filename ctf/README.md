# CTFd Structure  

## Configuration  

The build script looks for a `config.yml` in the root of the `ctf` directory. All configuration options within this file will be submitted to CTFd.  

```
---  
config:  
  ctf_theme: core-beta  
  user_mode:  users  
  account_visibility: private  
  score_visibility: private  
  registration_visibility: private  
  registration_code: private by design  
  paused: 1  
  ctf_name: "{{ CONFIG_ACCOUNT.title() }} CTF"  
  ctf_description: "Capture the Flag event hosted by Lacework for {{ CONFIG_ACCOUNT }} on the {{ CONFIG_SUBACCOUNT }} subaccount. Scope includes the following AWS accounts: {{ CONFIG_AWS_ACCOUNTS }}"  
```  

## Categories  

Every directory within this `ctf` directory will become a category. Prefix with a `number_` for sorting purposes.  i.e. `1_getting to know you`  

## Challenges  

Inside of each category directory create a `challenges.yml` with the challenge structure. The field structure follows what the CTFd API expects.  

```
---
challenges:
- name: compliance
  value: 5
  type: standard
  state: visible
  description: |
    description text
  flags:
  - type: static
    data: case_insensitive
    content: private by design

- name: oh really?
  value: 100
  type: standard
  connection_info: 'https://memecentral.org/wp-content/uploads/2019/08/really-seriously-meme.jpg'
  description: |
    Do you believe the user account **{{ CONFIG_AWS_USER }}** is problematic?  Why or why not?
  flags:
  - type: regex
    content: .*
```  

## Global built in variables  

The following variables can be used via Jinja templating.  i.e. `{{ CONFIG_AWS_USER }}`  
```
CONFIG_AWS_USER  
CONFIG_AWS_PRINCIPAL_ID  
CONFIG_ACCOUNT  
CONFIG_SUBACCOUNT  
CONFIG_AWS_ACCOUNTS  
```

## parse_challenge function  

To make the challenge descriptions and flags dynamic you can add a `parse_challenge` function into a `__init__.py` file in the category directory.  Each challenge for that category will be passed through this function. Example function signature below.  

```
def parse_challenge(challenge, config, lw):  
    # modify challenge details  
    return challenge  
```  

Here is another example using the passed in Lacework `lw` object to run LQL and dynamically add in flags.  

```
def parse_challenge(challenge, config, lw):  
    if challenge['name'] == 'weakest link':  
        iam_write_idents = lw.run_lw_query('ciem_iam_write.yml')  
        challenge['flags'] = []  
        for result in iam_write_idents:  
            flag = {'type': 'static', 'data': 'case_insensitive', 'content': result['PRINCIPAL_ID']}  
            challenge['flags'].append(flag) 
    return challenge  
```
