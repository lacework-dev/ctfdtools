# Dyanmic Lacework CTF  

Builds CTF based off prospect or customers data.  You can point the build script at a profile from your Lacework CLI install and it will pull data from that tenant, give you some choices, and then build the CTF on the CTFd platform.  

## Setup environment  

```
% git clone https://github.com/lacework-dev/dyn-lw-ctf  
% cd dyn-lw-ctf/  
% python3 -m venv .venv  
% source .venv/bin/activate  
% pip install -r requirements.txt  
```  

## [Setup CTF structure](ctf/README.md)


## Build script  

```
% ./build.py -h
usage: build.py [-h] (-c CONFIG | -g) [-p PROFILE] [-s SCHEMA] [-a]

Create a prospect/customer Lacework CTF in CTFd.

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Use specified CTF build configuration.
  -g, --generate-config
                        Generate CTF build configuration from schema.
  -p PROFILE, --profile PROFILE
                        Specify profile to use from lacework CLI configuration. Defaults to 'default'.
  -s SCHEMA, --schema SCHEMA
                        Path to CTF schema directory. Defaults to 'ctf'.
  -a, --answers         Print out challenge names and anwers/flags.
```
