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

# schema passed in from config will be overridden if specified with the -s/--schema flag
% ./build.py -c config.json -b -s ctfschema
```

## Print flags from live CTF
```
% ./build.py -c config.json -a
```

## Create schema from running CTFd instance
```
# the -s/--schema flag is used as the output directory for generated schema
# schema directory cannot exist
% ./build.py -c config.json --export-schema -s ctfschema
```

## Create challenges CSV from running CTFd instance
```
% ./build.py -c config.json --export-csv
```

## Build script help

```
% ./build.py -h
usage: build.py [-h] [-g] [-s SCHEMA] [-c CONFIG] [-b] [-a] [-e] [-E] [-C CATEGORY]

A tool for working with CTFd.

options:
  -h, --help            show this help message and exit
  -g, --generate-config
                        Generate CTF build configuration from schema.
  -s SCHEMA, --schema SCHEMA
                        Path to CTF schema directory.
  -c CONFIG, --config CONFIG
                        Use specified configuration file.
  -b, --build           Use configuration to build CTF
  -a, --answers         Use configuration to pull latest flags from CTFd instance.
  -e, --export-schema   Use configuration to export running CTFd instance to schema.
  -E, --export-csv      Use configuration to export running CTFd challenges to CSV.
  -C CATEGORY, --category CATEGORY
                        Specify a directory name (or names in a comma separated list) within the schema to limit build to just that category.
                        Defaults to All
```
