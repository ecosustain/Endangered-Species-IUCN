from threading import Thread
from requests import get
from time import sleep
from json import dumps

AUTH_TOKEN = "" # Authorization token for API
ID_LIST_FILE = ""
THREAD_COUNT = 16

# Load species IDs from the input file
with open(ID_LIST_FILE, 'r') as f:
    l = f.read().split("\n")
    species = [int(i.strip()) for i in l]

taxon_keys = ["scientific_name","sis_id","kingdom_name","phylum_name","class_name","order_name","family_name"]

def write_to_file(thread_id, formatted_list):
    """
    Writes a list of formatted JSON objects to a file.

    Parameters:
        thread_id (int): The ID of the thread writing the file.
        formatted_list (list): List of formatted JSON objects to write.
    """
    with open(f"{thread_id}.json", "a+") as file:
        for json in formatted_list:
            file.write(dumps(json))
            file.write("\n")

def wait_timeout(thread_id, formatted_list):
    """
    Implements a timeout mechanism when an API request limit is reached.

    Parameters:
        thread_id (int): ID of the current thread.
        formatted_list (list): List of formatted JSON objects collected so far.

    Returns:
        bool: True if the API is responsive after the timeout, False otherwise.
    """
    write_to_file(thread_id, formatted_list) # Save progress before waiting

    sleep(60)
    #random url just to test if timeout has ended and we can fetch the API again
    url = f"https://api.iucnredlist.org/api/v4/taxa/sis/49830106"
    headers = {"Authorization":AUTH_TOKEN}
    response = get(url, headers=headers)
    return int(response.status_code) == 200

def formatted_json(response):
    """
    Formats the API response data into a structured JSON object.

    Parameters:
        response (dict): Raw API response.

    Returns:
        dict: Formatted JSON object with selected fields.
    """
    formatted = dict()
    
    formatted["year_published"] = response["year_published"]
    formatted["taxon"] = {i: response["taxon"][i] for i in taxon_keys}
    formatted["locations"] = [{"country":i["description"]["en"], "presence":i["presence"]} for i in response["locations"]]
    formatted["use_and_trade"] = [i["description"]["en"] for i in response["use_and_trade"]]
    formatted["threats"] = [i["description"]["en"] for i in response["threats"]]
    formatted["red_list_category"] = response["red_list_category"]["code"]
    
    return formatted

def thread_func(start, end, result, idx):
    """
    Fetches data for a range of species IDs using the API and formats the responses.

    Parameters:
        start (int): Start index of species IDs for the thread.
        end (int): End index of species IDs for the thread.
        result (list): Shared list to store the count of successful requests for each thread.
        idx (int): Thread index.
    """
    j = 0 # Counter for successful requests
    headers = {"Authorization":AUTH_TOKEN}

    formatted_list = []
    i = start
    while i < end:
        species_id = species[i]
        url = f"https://api.iucnredlist.org/api/v4/taxa/sis/{species_id}"
        print(url)
        response = get(url, headers=headers)
        
        if int(response.status_code) != 200:
            print(response.status_code)
            r = wait_timeout(idx, formatted_list)
            if not r:
                result[idx] = j
                print("1 min nao foi suficiente")
                return
            
            formatted_list = [] # Reset the list after waiting
            
            if int(response.status_code) == 404:
                j += 1 # Skip to the next ID
            continue
              
        # Process assessments for the species
        j += 1
        species_response = response.json()
        assessment_list = [int(x["assessment_id"]) for x in species_response["assessments"]]     

        m = len(assessment_list)
        k = 0
        while k < m:
            url = f"https://api.iucnredlist.org/api/v4/assessment/{assessment_list[k]}"
            response = get(url, headers=headers)
            if int(response.status_code) != 200:
                print(response.status_code)
                r = wait_timeout(idx, formatted_list)
                if not r:
                    result[idx] = j
                    print("1 min was not long enough")
                    return  
                formatted_list = [] # Reset the list after waiting
                if int(response.status_code) == 404:
                    k += 1 # Skip to the next assessment
                continue
            
            formatted_list.append(formatted_json(response.json()))
            j += 1
            k += 1
        i += 1
    result[idx] = j  # Save the count of successful requests
    write_to_file(idx, formatted_list) # Save collected data to file

# Split the workload across threads
n = len(species)
threads = []
result = [0 for i in range(THREAD_COUNT)]
for i in range(THREAD_COUNT):
    threads.append(Thread(target=thread_func,args=(int(i * n / THREAD_COUNT), int((i+1) * n / THREAD_COUNT), result, i)))
    threads[i].start()

# Wait for all threads to complete
for i in range(THREAD_COUNT):
    threads[i].join()

print(result)
