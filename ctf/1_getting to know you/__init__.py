# import libraries for solvers

def parse_challenge(schema, challenge, config):
    '''
        This function will be ran on any challenge in this category at build time.

        * challenge - is a JSON representation of each individual challenge defined as YAML in challenges.yml
          {
              "name": "it's called vuln management, heard of it?",
              "value": 5,
              "type": "standard",
              "state": "visible",
              "description": "The CISO just agreed to present rolling updates on the new vulnerability management program to the board of directors over the next quarter. For the next update, the CISO wants to highlight a particular host that has been prioritized to be the top work item using Lacework data.  Which means, someone is now responsible for identifying the host that will be showcased in the CISO's next report. Any guesses on who that person is?  \n\nNavigate to the Host Vulnerabilities dossier and make sure you landed on the Host tab on the top of your screen. Filter the list of hosts to find the hostname that has the most vulnerabilities that are:  \n- Fixable  \n- Active package status  \n- Critical or High severity  \n",
              "flags": [
                  {
                      "type": "static",
                      "data": "case_insensitive",
                      "content": "defiantly answering"
                  }
              ]
          }
        * config - is a JSON representation of the supplied config.json when the build.py script was ran
    '''
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
