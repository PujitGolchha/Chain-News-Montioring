import pickle
import requests
import glob
import os
from tqdm import tqdm

def download_file(path):
    with open(path, 'rb') as f:
        loaded_dict = pickle.load(f)
    return loaded_dict



def posting():
    #get latest file
    list_of_files = glob.glob('/data/*')
    latest_file = max(list_of_files, key=os.path.getctime)
    #print(latest_file)
    onlyfiles = [f for f in list_of_files if "list_of_dictionary" in f]
    
    list_of_articles=[]
   

    for i in tqdm(onlyfiles):
        print(i)
        with open(i, "rb") as jfile:
            loaded_links=pickle.load(jfile)
        list_of_articles=list_of_articles+loaded_links
    
    #list_of_articles = download_file(latest_file)
    print("Starting posting")
    
    # for j in tqdm(list_of_articles):
    #     j["label"]=int(j["label"])
    #     x=[j]
        
    #     try:
    #         requests.post('http://127.0.0.1:9001/items', json=x)
    #     except:
    #         print("item id ", j["id"]," exists in db")
    #         pass

posting()