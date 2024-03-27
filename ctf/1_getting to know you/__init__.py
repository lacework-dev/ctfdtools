import json
from datetime import datetime, timedelta

def parse_challenge(challenge, config, lw):
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
        * lw - is a Lacework object that wraps the Lacework CLI and allows you to query data for the supplied profile in config

        In the examples below the lw object is used to run a CLI command and retrieve compliance details, an API call to retrieve
        vulnerability details, and an LQL query from the ../lql/ directory.
        
    '''
    if challenge['name'] == "it's called vuln management, heard of it?":
        vuln_json = {
            "filters": [
                {
                    "field": "fixInfo.fix_available",
                    "expression": "eq",
                    "value": "1"
                },
                {
                    "field": "severity",
                    "expression": "in",
                    "values": [
                        "High"
                    ]
                }
            ],
            "returns": [
                "mid",
                "machineTags"
            ]
        }
        vuln_results = lw.api(path='/api/v2/Vulnerabilities/Hosts/search', method='POST', json=vuln_json)
        challenge['flags'] = []
        host_vulns = {}

        for result in vuln_results.get('data', []):
            hostname = result.get('machineTags', {}).get('Hostname')
            host_entry = host_vulns.setdefault(hostname, 0)
            host_vulns[hostname] = host_entry + 1
        
        mx = max(host_vulns.values()) if host_vulns else 0
        final_hosts = [k for k, v in host_vulns.items() if v == mx]

        for host in final_hosts:
            flag = {'type': 'static', 'data': 'case_insensitive', 'content': host}
            challenge['flags'].append(flag)

    if challenge['name'] == "sure. we'll pass the audit":
        report = json.loads(lw.cli(['compliance', 'aws', 'get-report', '--report_name',
                                    'CIS Amazon Web Services Foundations Benchmark v1.4.0',
                                    config['aws_accounts'][0], '--json']))
        summary = report['summary'][0]
        count = int(summary['NUM_SEVERITY_1_NON_COMPLIANCE']) + int(summary['NUM_SEVERITY_2_NON_COMPLIANCE'])
        challenge['flags'] = [{'type': 'static', 'content': str(count)}]
        challenge['description'] = challenge['description'].replace("{framework}",
                                                                    "CIS Amazon Web Services Foundations Benchmark v1.4.0")
        challenge['description'] = challenge['description'].replace("{cloudaccount}", config['aws_accounts'][0])
    
    if challenge['name'] == "There's a difference between knowing the path and walking the path":
        attack_paths = lw.run_lw_query('attack_path_beginner.yml')
        challenge['flags'] = []
        flag = {'type': 'static', 'data': 'case_insensitive', 'content': str(len(attack_paths))}
        challenge['flags'].append(flag)
    return challenge
