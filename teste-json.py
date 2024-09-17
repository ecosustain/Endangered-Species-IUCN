from json import loads, dumps
from ast import literal_eval
species = set()
import re
p = re.compile('(?<!\\\\)\'')

total_species = set()
with open("IUCN-Project/id.txt", 'r') as f:
    l = f.read().split("\n")
    total_species = {int(s.strip().split("/")[-2]) for s in l if s.strip().split("/")[-3] == "species"}

pulled_species = set()
with open("uniqs/sample2.json", 'r') as sample:
    for line in sample:
        if len(line) > 0:
            #print(p.sub('\"', line.strip()))
            #print(line)
            d = loads(line)
            #print(dumps(d))
            pulled_species.add(d["taxon"]["sis_id"])

for i in total_species.difference(pulled_species):
    print(i)
