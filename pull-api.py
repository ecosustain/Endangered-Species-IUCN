from threading import Thread
from requests import get
from time import sleep
from json import dumps

with open("next.txt", 'r') as f:
    l = f.read().split("\n")
    species = [int(i.strip()) for i in l]
    #print(len(species))

taxon_keys = ["scientific_name","sis_id","kingdom_name","phylum_name","class_name","order_name","family_name"]

#print(species)
def chill_out(thread_id, formatted_list):
    with open(f"{thread_id}.json", "a+") as file:
        for json in formatted_list:
            file.write(dumps(json))
            file.write("\n")

    sleep(60)
    url = f"https://api.iucnredlist.org/api/v4/taxa/sis/49830106"
    headers = {"Authorization":"DLs37MphZCVDG322JPfLNfTRxhjs1QibcQCt"}
    response = get(url, headers=headers)
    return int(response.status_code) == 200

def formatted_json(response):
    formatted = dict()
    formatted["year_published"] = response["year_published"]
    formatted["taxon"] = {i: response["taxon"][i] for i in taxon_keys}
    formatted["locations"] = [{"country":i["description"]["en"], "presence":i["presence"]} for i in response["locations"]]
    formatted["use_and_trade"] = [i["description"]["en"] for i in response["use_and_trade"]]
    formatted["threats"] = [i["description"]["en"] for i in response["threats"]]
    formatted["red_list_category"] = response["red_list_category"]["code"]
    
    return formatted

def thread_func(start, end, result, idx):
    j = 0
    headers = {"Authorization":"DLs37MphZCVDG322JPfLNfTRxhjs1QibcQCt"}
    formatted_list = []

    i = start
    while i < end:
        species_id = species[i];
        url = f"https://api.iucnredlist.org/api/v4/taxa/sis/{species_id}"
        print(url)
        response = get(url, headers=headers)
        
        if int(response.status_code) != 200:
            print(response.status_code)
            r = chill_out(idx, formatted_list)
            if not r:
                result[idx] = j
                print("1 min nao foi suficiente")
                return
            formatted_list = []
            if int(response.status_code) == 404:
                j += 1
            continue
              
        j += 1
        species_response = response.json()
        assessment_list = [int(x["assessment_id"]) for x in species_response["assessments"]]     

        m = len(assessment_list)
        k = 0
        while k < m:
            url = f"https://api.iucnredlist.org/api/v4/assessment/{assessment_list[k]}"
            #print(k)
            response = get(url, headers=headers)
            if int(response.status_code) != 200:
                print(response.status_code)
                r = chill_out(idx, formatted_list)
                if not r:
                    result[idx] = j
                    print("1 min nao foi suficiente")
                    return  
                formatted_list = []
                if int(response.status_code) == 404:
                    k += 1
                continue
            
            formatted_list.append(formatted_json(response.json()))
            j += 1
            k += 1
        #print(i)
        i += 1
    result[idx] = j
    chill_out(idx, formatted_list)
    return

n = len(species)
thread_count = 1
threads = []
result = [0 for i in range(thread_count)]
for i in range(thread_count):
    threads.append(Thread(target=thread_func,args=(int(i * n / thread_count), int((i+1) * n / thread_count), result, i)))
    threads[i].start()

for i in range(thread_count):
    threads[i].join()

print(result)