import spacy
from spacy import displacy
import pandas as pd
from OSMPythonTools.nominatim import Nominatim
from geopy.geocoders import Nominatim as noma
import re
from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline
import warnings
warnings.filterwarnings("ignore")
import pickle
import logging



tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
transformer_model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")
NER = spacy.load("en_core_web_sm")
nominatim = Nominatim()
geolocator = noma(user_agent="geoapiExercises")


def upload_file(path, file):
    with open(path, 'wb') as f:
        pickle.dump(file, f)



def download_file(path):
    with open(path, 'rb') as f:
        loaded_dict = pickle.load(f)
    return loaded_dict


countries_dict=download_file(r"locations/countries_dict.pkl")
state_dict=download_file(r"locations/states_dict.pkl")
city_dict=download_file(r"locations/cities_dict.pkl")

def location_recogniser(raw_text):
    planets=["mars","mercury","venus","earth","jupyter","saturn","uranus","neptune","pluto"]
    directions=["north","south","east","west"]
    #spacy
    text2= NER(raw_text)
    named_entities_1=[]
    for word in text2.ents:
        # if word.label_=="LOC" or word.label_=="GPE" or word.label_=="ORG":
        if word.label_=="LOC" or word.label_=="GPE":
            named=word.text.lower()
            named_entities_1.append(named)
    
    #transformers
    nlp = pipeline("ner", model=transformer_model, tokenizer=tokenizer)
    ner_results = nlp(raw_text)

    size=0
    named_entities_2=[]
    while size<len(ner_results):
        if ner_results[size]["entity"]=="B-LOC":
            flag=True
            named=ner_results[size]["word"]
            while flag:
                if size<len(ner_results)-1:
                    size=size+1
                else:
                    size=size+1
                    break

                if ner_results[size]["entity"]!="I-LOC":
                    flag=False
                    break
                named=named+" "+ner_results[size]["word"]
            named=re.sub(" *#+","",named).lower()    
            named_entities_2.append(named)
        else:    
            size=size+1


    named_entities=set(named_entities_1).union(set(named_entities_2))
    named_entities=set(named_entities)-set(planets)
    named_entities=set(named_entities)-set(directions)
    return named_entities


def final_locations(locations,ids):
    area_types=["administrative","town","state"]
    try:
        places=[]
        rec_countries=[]
        rec_states=[]
        for location in locations:
            #checking if we alrady have details for a place
            if location in list(city_dict.keys()):
                #unique city
                if len(city_dict[location])==1:
                    places.append(city_dict[location][0])
                else:
                    for cities in city_dict[location]:
                        if cities["Country"] in locations or cities["State"] in locations:
                            places.append(cities)
            elif location in list(state_dict.keys()):
                rec_states.append(location)
            elif location in list(countries_dict.keys()):
                rec_countries.append(location)
            else:
                area=""
                try:
                    #get top result
                    print("new location",location)
                    area = nominatim.query(location).toJSON()[0]

                    #check type and get details
                    if area["type"]=="city":
                        location = geolocator.reverse(str(area["lat"])+","+str(area["lon"]),language="en")
                        address=location.raw['address']
                        state = address.get('state', '').lower()
                        country = address.get('country', '').lower()
                        city = address.get('city', '').lower()
                        places.append({"Latitude":area["lat"],"Longitude":area["lon"],"Country":country,"State":state,"City":city})
                        city_dict[location]=[]
                        logging.info("Updating city dict")
                        print("Updating city dict",location)
                        #updating the city dict
                        city_dict[location].append({"Latitude":area["lat"],"Longitude":area["lon"],"Country":country,"State":state,"City":city})

                    elif area["type"] in area_types:
                        location = geolocator.reverse(str(area["lat"])+","+str(area["lon"]),language="en")
                        address=location.raw['address']
                        state = address.get('state', '').lower()
                        country = address.get('country', '').lower()
                        places.append({"Latitude":area["lat"],"Longitude":area["lon"],"Country":country,"State":state,"City":""})
                        if state!='':
                            if state not in list(state_dict.keys()):
                                state_dict[state]=[]
                                #updating the state dict
                                logging.info("Updating state dict")
                                print("Updating state dict",location)
                                state_dict[state].append({"Latitude":area["lat"],"Longitude":area["lon"],"Country":country,"State":state,"City":""})

                except:
                    print("error in id",ids)
                    #logging.info("error in id",ids)

         
        places=pd.DataFrame(places)
        if places.empty==True:
            places=pd.DataFrame(columns=["Latitude","Longitude","Country","State","City"])

        for state in rec_states:
            if state not in list(places["State"]):
                if len(state_dict[state])==1:
                    places=places.append(state_dict[state][0],ignore_index=True)
                else:
                    for x in state_dict[state]:
                        if x["Country"] in locations:
                            places.append(x,ignore_index=True)
    
        #adding countries not in the list
        for country in rec_countries:
            if country not in list(places["Country"]):
                places=places.append(countries_dict[country],ignore_index=True)
        places=places.drop_duplicates(subset=["State","Country"])
        return places
    except:
        return pd.DataFrame([])

    

def upload_all_files():
    upload_file(r"locations/countries_dict.pkl",countries_dict)
    upload_file(r"locations/states_dict.pkl",state_dict)
    upload_file(r"locations/cities_dict.pkl",city_dict)