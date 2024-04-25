# CTFd tools

Tools to aid in the creation and management of CTFd CTFs.

## Setup environment  

```
% git clone https://github.com/lacework-dev/ctfdtools
% cd ctfdtools/  
% python3 -m venv .venv  
% source .venv/bin/activate  
% pip install -r requirements.txt  
```  

## [Setup CTF structure](ctf/README.md)

## Generate a build configuration
```
# save output as config.json
% ./build.py -g -s ctf
```

## Build CTF
```
# use generated configuration to build CTF
% ./build.py -c config.json -b
```

## Print flags from live CTF
```
# this can be combined with the build flag
% ./build.py -c config.json -a
```


## Build script help

```
% ./build.py -h
usage: build.py [-h] (-c CONFIG | -g) [-s SCHEMA] [-b] [-a] [-C CATEGORY]

Create a prospect/customer Lacework CTF in CTFd.

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Use specified CTF build configuration.
  -g, --generate-config
                        Generate CTF build configuration from schema.
  -s SCHEMA, --schema SCHEMA
                        Path to CTF schema directory.
  -b, --build           Use specified build configuration to build CTF
  -a, --answers         Use specified build configuration and pull latest flags from CTFd instance.
  -C CATEGORY, --category CATEGORY
                        Specify a directory name (or names in a comma separated list) within the schema to limit build to just
                        that category. Defaults to All
```
