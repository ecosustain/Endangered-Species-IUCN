from json import loads, dumps
species = set()

ID_LIST_FILE = ""
ASSESSMENTS_FILE = ""
NEW_ID_LIST_FILE = ""

total_species = set()
with open(ID_LIST_FILE, 'r') as f:
    l = f.read().split("\n")
    
    #exclude non-species links
    total_species = {int(s.strip().split("/")[-2]) for s in l if s.strip().split("/")[-3] == "species"}

pulled_species = set()
with open(ASSESSMENTS_FILE, 'r') as sample:
    for line in sample:
        if len(line) > 0:
            d = loads(line)
            pulled_species.add(d["taxon"]["sis_id"])

with open(NEW_ID_LIST_FILE, "w") as f:
    for i in total_species.difference(pulled_species):
        f.write(f"{i}\n")
