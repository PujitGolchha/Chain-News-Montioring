# Chain News Monitoring (Team Project)

## Technologies Used:

### RSS Feed Scraping:
- Scrapy (Python Framework)
- Feedparser (Python Library)
- GoogleNews (Python Library) 

### Translation:
- Multiple Open Source Translator APIs such as My Memory Translator, QcriTranslator, LibreTranslate (Python Libraries) 
- Google Translate API

### Document Embeddings:
- Gensim (Python Library)
- Google News Vectors (https://drive.google.com/file/d/0B7XkCwpI5KDYNlNUTTlSS21pQmM/edit?resourcekey=0-wjGZdNAUop6WykTtMip30g)

### Database:
- MariaDB
- Sqlite
- Sqlalchemy (Python Library)
- FastAPI (Python Library)

### Application Hosting Server:
- Uvicorn (Python Library)
- Ngrok (https://ngrok.com/)


## API Documentation:
The documentation for the Fast Api endpoints is available at 
(https://8970-2001-7c0-2900-8050-5652-ff-fe00-18.eu.ngrok.io/docs)

## Setup of server/infrastructure
This part outlines how our system works, how to set it up and run it.
First you need to download the files belonging to this project from github and extract them.
Then open a terminal and navigate to the root of the project, i.e. the folder in which you just placed the extracted files.
This can be done with the command cd (short for change directory).
The command ls will list the contents of the current directory.
You can check that you are in the correct folder by checking that ls shows you the same files as the project website on github.

### Virtual Environment Setup
Firstly you need to create a "virtual environment". A virtual environment is a folder containing the python packages required for the current project.
This allows us to easily install all packages we need.
To set it up, open a command line (e.g. powershell) and navigate to the root folder of the project and run
```
python -m venv newsmontioring_venv
source newsmontioring_venv/bin/activate
```

This command creates the virtual environment in the folder newsmontioring_venv which is placed in the root of the project, the second line activates the environment (so that it instead of the normal system packages are used).
You will need to run the second line in the terminal, whenever you want to activate the environment, as without the environment you cannot run the python files required to get the system running as they will not be able to find the packages it needs.
You can see, if the environment is active by checking if there is a "(newsmontioring_venv)" at the beginning of the terminal lines.

The final step is to install the packages named in the file requirements.txt by running the command
```
pip install -r requirements.txt
```

### Database Server Setup

To setup a MariaDb server follow the instructions mentioned here (https://www.digitalocean.com/community/tutorials/how-to-install-mariadb-on-ubuntu-18-04).
Once this done you need to create a Database, in our case we named it "ChainNewsMonitoring" and create a table to store the scraped data. In our case it is the "Relevant Article". You need to create the table with the following schema:


| Column name |	Column type |	Description |
| ------------| ------------| ------------|
| id	        | String, Primary Key	| GUID or URL of the article |
| ts	| String |	Timestamp |
|	source| String | The link to the article |
| title	 | String |	The title of the article |
| content	| String | The content of the RSS feed |
| RSS |	String | Link to the RSS feeds |
| label |	Integer	0 or 1 | (0: non relevant article, 1: relevant article). Relevance in our case is defined by whether the article talks about a potential la violation or not.|


### Running and hosting the API
To run the Fast API, simply run the main.py script. This hosts the API locally on the VM (on port=9000). This can be done using:

```
python3 main.py 
```
Now the API is running, we require to host the API to be accessible outside the VM. In order to do so, we utilise the Ngrok (https://ngrok.com/). Install instructions for Ngrok can be found here: (https://ngrok.com/download). Once downloaded simply run the following command:
```
ngrok http <port-number>
```
In our case, we have set the ```<port-number>``` to 9000. However, this argument can be changed in main.py file. Once ngrok is running, a http address for accessing the API becomes available. 
  
Note: We advise to run Uvicorn server, and the ngrok tunnel in seperate screens in the backgroud. Details to run screen are mentioned in section below.


### Running the scraper

Before running the scarper you need to make sure that the following files are available on your system.
- Google News Vectors (https://drive.google.com/file/d/0B7XkCwpI5KDYNlNUTTlSS21pQmM/edit?resourcekey=0-wjGZdNAUop6WykTtMip30g)
- Pretrained PCA model (available in this repository)
- Pretrained Classification Model (available in this repository)
- keywords for Google News Api Search (available in this repository)

The scraper needs these extra files to classify the articles as well as scrape articles from Google News. 

Note:

1) The path to the Google new Vectors need to updated in the __init__.py file in the automatize/helper folder. 
2) By default the output from the scarper is stored in the automatize/data folder but this too can be updated if you need to store them somewhere else.

The scraper can be run automatically everyday at the specified time (can be changed in the automatize/automation.py file) by running the following commands

```
screen
```
This will open a screen session, create a new window, and start a shell in that window.
Screen or GNU Screen is a terminal multiplexer and processes running in Screen will continue to run when their window is not visible even if you get disconnected.

Once in new window activate the virtual environment "newsmontioring_venv" and navigate to automatize folder of the project. Once done run the command:
```
python3 automation.py
```

Once all packages are loaded you should get a message saying the same and this means your program has started and scraping will happen everyday at the specified time. 

You can then detach from the screen session at any time by typing:
```
Ctrl+a d
```

You will now return to your old terminal window and the scraper is running on the background. If you need to check if everything is working fine you can again resume your screen session using the following command:
```
screen -r
```


The scraper will run everday and create mutiple dictionary of dictionaries files as well as a list of dictionaries file in the output folder. You may need to delete the files in the output folder from time to time as every day new files are created and you may run out of memory space. 

Note: Do not delete the files for the past 5 days as the scraper looks up those files and only scrapes those articles which are not part of these files.


### Feeding the scraped articles into the database

Similar to the scraper the articles scraped can be fed into the database everyday at a specified time (can be changed in the automatize/post_into_db.py file). The port in which the database is hosted should also be updated in this file.

You can then start another screen and run the following command:
```
python3 post_into_db.py
```

Once up and running you can detach the screen and this process will also happen automatically in the background.
Note: Keep atleast 10 hour gap between scraping and posting, because we look up for the recent most updated file in the outputs folder and feed that data into the database. The scraper on average runs for 8 hours and hence 10 hours whould be a good enough time interval between the steps.

Now that you have multiple screens running you list all running screens using:
```
screen -ls
```
and  open a particular screen using:
```
screen -r Screen ID
```
If you need any more information about screen commands you can refer to  (https://linuxize.com/post/how-to-use-linux-screen/)


## Description of Key components

### Law Violations Classifier

We implement a logistic-regression based classifier with boosting. The classifier is used distinguish between new articles talking about law violations. The pipeline for the classifier is as follows:

[Insert pipeline]

Preprocessing performs removal of punctuations, numbers and additional white spaces. Additionaly, stopwords are removed following tokenisation. Note tokenisation and stop word removal is performed using the NLTK library.

Input into the classifier is a document embedding for the content of each article. Document embedding are created by computing the mean of word2vec embedding of words in the content. Dense vector embeddings are created using the Google News Vectors. The embeddings are computed using a word2vec model pre-trained on Google News Corpus (containing 3 billion running words). The model outputs dense vector representation with d=300. 

Next we applied PCA, for dimensionality reduction. Empirically, we found n=100 produces the best accuracy scores. We present the results in 

The model itself perform binary classification. Given document features, the model outputs 1 if law violations are not mentioned else it predicts 0. We defined the model’s purpose to be an efficient, coarse filter to remove obviously irrelevant articles. Therefore, we require a high recall score, to avoid missing relevant articles. For this purpose, we used the logistic-regression based classifier with boosting. This is an ensemble learning method where the base model is trained iteratively, with each iteration model assigning higher weights to misclassified instances. On prediction time, weighted average from all models is used to determine the final prediction. 

We present the results of our model in the following table. Here we experiment with PCA dimension size. Additionally, ’New data’ presents the results of the trained model on extended dataset. The Baseline model is a simple keyword model, which marks articles relevant if a keyword is present. The keyword corpus is compiled through 100 frequent words occuring in the relevant articles. Meta-cost is a risk based prediction algorithm which augments model prediction based on the risk associated with incorrectly predicting the class.

| Model |	Recall Score |	Precision |F1-score|
| ------------| ------------| ------------|------------|
| Baseline | 0.36	| 0.04 | 0.07|
| XG-boost w/w Meta-Cost @r=5, m=50 | 0.1 | 0.53 | 0.17 |
| Support Vector Classification (SVC)| 0.72	| 0.05 | 0.09|
| SVC w/w Meta-Cost| 0.98	| 0.02 | 0.04|
|Log. Regression w/w Boosting, n=30 embeding_dim = 300 | 0.80| 0.09| 0.17|

## Access to VM:

VM-Host: demaq3.informatik.uni-mannheim.de

Contact Institute for Enterprise Systems (InES) for accessing the VM.
