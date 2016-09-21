#!/usr/bin/env python

import codecs, json
from pprint import pprint
with open("stefan.json") as data_file:
    data=json.load(data_file)
    pprint(data)
