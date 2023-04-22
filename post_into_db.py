import pickle
import requests
import glob
import os
from tqdm import tqdm
import logging
import schedule
import time
import pandas as pd
import location_finder
from datetime import datetime, timedelta
print("Loaded all packages")


def upload_file(path, file):
    with open(path, 'wb') as f:
        pickle.dump(file, f)

def download_file(path):
    with open(path, 'rb') as f:
        loaded_dict = pickle.load(f)
    return loaded_dict

"""Function to parse data from Osapiens Api into list of lists"""
def parse_raw_string(raw_string):
  data=[]
  for rowno,i in enumerate(tqdm(raw_string.split("\r\n"))):
    text=''
    a=[]
    #z is indicator variable if the string contains ""
    z=False
    for j in i.split(","):
      #some columns may be empty
      if j!="":
        #accounting for ""
        #we continue concatenating all parts to the text until we encounter another"
        if j[0]=='"' or z==True:
          text=text+j
          z=True
        else:
          a.append(j)
        try:
          if j[-1]=='"' and j[-2]!='"':
            a.append(text)
            text=''
            z=False
        except:
          if j[-1]=='"':
            a.append(text)
            # print(rowno)
            # print(text)
            text=''
            z=False
      else:
        a.append("")
    data.append(a)
  return data




"""Function to extract locations from a given file i.e. list of dictionaries"""
def le(file,file_path):
    logging.basicConfig(filename="location.log",format="%(asctime)s %(message)s",encoding="utf-8",level=logging.INFO,filemode='w')
    location_list=[]
    print(file_path)
    oldcitylen=len(location_finder.city_dict)
    oldstatelen=len(location_finder.state_dict)
    oldcountrylen=len(location_finder.countries_dict)
    for count,j in enumerate(tqdm(file)):
        fl=""
        if j["content"]!="" and j["content"]!=None:
            locations=location_finder.location_recogniser(j["content"])
            fl=location_finder.final_locations(locations,j["id"])
            if fl.empty==True:
                locations=location_finder.location_recogniser(j["title"])
                fl=location_finder.final_locations(locations,j["id"])
            if fl.empty==False:
                fl["RSS"]=j["RSS"]
                fl["ts"]=j["ts"]
                fl["RssID"]=j["id"]
                fl=fl.to_dict('records')
                location_list=location_list+fl
        else:
            locations=location_finder.location_recogniser(j["title"])
            fl=location_finder.final_locations(locations,j["id"])
            if fl.empty==False:
                fl["RSS"]=j["RSS"]
                fl["ts"]=j["ts"]
                fl["RssID"]=j["id"]
                fl=fl.to_dict('records')
                location_list=location_list+fl
        
    location_list=pd.DataFrame(location_list)
    location_list.columns
    #location_list.drop_duplicates(subset=['Country', 'State', 'City','RSS', 'ts'],inplace=True)
    location_list=location_list.to_dict("records")

    location_finder.upload_all_files()
    print(oldstatelen)
    print(oldcitylen)
    print(oldcountrylen)
    print(len(location_finder.state_dict))
    print(len(location_finder.city_dict))
    print(len(location_finder.countries_dict))
    
    upload_file(file_path, location_list)
    
    return location_list


"""Function to post articles as well as locations extracted into db"""
def posting():
    logging.basicConfig(filename="posting.log",
                        format="%(asctime)s %(message)s",
                        encoding="utf-8",
                        level=logging.INFO,filemode='w')

    #get latest file
    list_of_files = glob.glob('data/*')
    latest_file = max(list_of_files, key=os.path.getctime)
    print(latest_file)
    list_of_articles = download_file(latest_file)
    
    print("Starting posting")
    for j in tqdm(list_of_articles):
        j["label"]=int(j["label"])
            
        x=[j]
        try:
            z=requests.post('http://127.0.0.1:9001/items', json=x).status_code
        except:
            z=0
        if z==410:
            logging.info("item id %s exists in db",j["id"])
            pass       
    print("Posting done")

    print("Getting locations data")
    start = str((datetime.now()- timedelta(days= 1)).timestamp()*1000)
    end = str(datetime.now().timestamp()*1000)
    
    url = f"https://preprod.osapiens.cloud/data/integration/supplier-os-hub/supplier-os-data-provider/ExternalNewsExport?username=discovery-system-uni-mannheim@osapiens.com&password=CRHcb4i7uiNKHuA4E&type=ALL&from={start}&to={end}"
    raw_string = requests.get(url).text

    print("Parsing locations data")
    loc_data = parse_raw_string(raw_string)
    try:
        header = ['id', 'ts', 'lang', 'RSS', 'title', 'content', 'label']
        loc_data_df=pd.DataFrame(loc_data, columns=header)
    except:
        header = ['id', 'ts', 'lang', 'RSS', 'title', 'content', 'label','Extra_column']
        loc_data_df=pd.DataFrame(loc_data, columns=header)
       
    loc_data_df.drop(len(loc_data_df)-1,axis=0,inplace=True)
    loc_data_df=loc_data_df[~((loc_data_df["title"].isna()) & (loc_data_df["content"].isna()))]
    loc_data_df=loc_data_df.to_dict("records")

    loc_data_file_path=f"locations/locationdata_{start}&to={end}.pkl"
    upload_file(loc_data_file_path, loc_data_df)
    
    print("Extracting locations")
    file_path=f"locations/location_{start}&to={end}.pkl"
    locations_extracted=le(loc_data_df,file_path)
    
    print("Starting posting of locations")
    maxVal = requests.get('http://127.0.0.1:9001/numLocations').json()['max']
    
    if maxVal==None:
        maxVal=0
    
    for j in tqdm(locations_extracted):
        j['ID'] =  maxVal + 1
        maxVal = maxVal+ 1
        x = [j]
        try:
            requests.post('http://127.0.0.1:9001/locations', json=x)
        except:
            print("item id ", j["ID"]," exists in db")
            pass

    
schedule.every().day.at("23:00").do(posting)
while True:
    schedule.run_pending()
    time.sleep(10)
