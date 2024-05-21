# import libraries for solvers

def parse_challenge(schema, challenge, config):
    """
        This function will be ran on any challenge in this category at build time.
        * schema - is an object imported from schema/__init__.py
        * challenge - is a JSON representation of each individual challenge defined as YAML in challenges.yml
          {
              "name": "it's called vuln management, heard of it?",
              "value": 5,
              "type": "standard",
              "state": "visible",
              "description": "The CISO just agreed to present rolling updates on the new vulnerability management ... ",
              "flags": [
                  {
                      "type": "static",
                      "data": "case_insensitive",
                      "content": "defiantly answering"
                  }
              ]
          }
        * config - is a JSON representation of the supplied config.json
    """
    if challenge['name'] == "it's called vuln management, heard of it?":
        # solver logic goes here
        # add flag(s) to challenge json
        challenge['flags'] = []
        flag = {'type': 'static', 'data': 'case_insensitive', 'content': 'flag goes here'}
        challenge['flags'].append(flag)

    if challenge['name'] == "sure. we'll pass the audit":
        # solver logic goes here
        # add flag(s) to challenge json
        challenge['flags'] = []
        flag = {'type': 'regex', 'data': 'case_insensitive', 'content': '^flag.goes.here'}
        challenge['flags'].append(flag)

    # remember to return the challenge JSON
    return challenge
