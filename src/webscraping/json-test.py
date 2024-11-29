from json import loads, dumps
species = set()

# File paths
ID_LIST_FILE = ""  # File containing original species IDs
ASSESSMENTS_FILE = ""  # JSON file containing pulled species data
NEW_ID_LIST_FILE = ""  # Output file for missing species IDs

# Set to store all species IDs from the original file
total_species = set()

# Read the ID list file and extract species IDs
with open(ID_LIST_FILE, 'r') as f:
    l = f.read().split("\n")
    
    # Exclude non-species links
    total_species = {int(s.strip().split("/")[-2]) for s in l if s.strip().split("/")[-3] == "species"}

# Set to store species IDs already pulled
pulled_species = set()

# Read the assessments JSON file and collect pulled species IDs
with open(ASSESSMENTS_FILE, 'r') as sample:
    for line in sample:
        if len(line) > 0: # Skip empty lines
            d = loads(line)
            pulled_species.add(d["taxon"]["sis_id"])

# Find the difference between all species and pulled species
# Write missing species IDs to a new file
with open(NEW_ID_LIST_FILE, "w") as f:
    for i in total_species.difference(pulled_species):
        f.write(f"{i}\n")
