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
usage: build.py [-h] [-v] [-p PROFILE] [-g] [-c CONFIG]  
  
Create a prospect/customer Lacework CTF in CTFd. Default behavior with no arguments creates a config and builds the CTF in CTFd.  
  
options:  
  -h, --help            show this help message and exit  
  -v, --version         show program's version number and exit  
  -p PROFILE, --profile PROFILE  
                        Specify profile to use from lacework CLI configuration. Defaults to 'default'.  
  -g, --generate-config  
                        Generate CTF config and exit.  
  -c CONFIG, --config CONFIG  
                        Use specified config to build CTF in CTFd.  
```
