#!/usr/bin/env python
import json, requests, yaml

output_json =  yaml.load(open('/var/log/dialplan.json'))
headers = {'content-type': 'application/json'}
for i in output_json:
        
	for k in output_json[i]:
                        data=json.dumps(k,ensure_ascii=False)
                        new_data=data.encode("utf-8")
                       
                        r = requests.post("https://superadmin:Ezuce123@localhost/sipxconfig/api/rules/", data=new_data,verify=False,headers=headers)
                    

