#!/usr/bin/env python
import json, requests, yaml

output_json =  yaml.load(open('stefan.json'))
# json.dumps(file_input, ensure_ascii=False)  


headers = {'content-type': 'application/json'}
for i in output_json:
        
	for k in output_json[i]:
                        data=json.dumps(k,ensure_ascii=False)
                        new_data=data.encode("utf-8")
                        
                        r = requests.post("https://superadmin:Ezuce123@10.3.0.150/sipxconfig/api/users/", data=new_data,verify=False,headers=headers)
                        print r.status_code

