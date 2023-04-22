from sklearn.metrics import precision_score
from sklearn.metrics import accuracy_score
from sklearn.metrics import recall_score, f1_score
from sklearn.base import clone
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re
import numpy as np
import pandas as pd
import gensim
from gensim.models import KeyedVectors
from gensim import models
import nltk
import dateutil.parser



try:
    lemmatizer = WordNetLemmatizer()
    stop_words = list(stopwords.words('english'))
    manual_input = ["say", "worker", "company", "said"]
    stop_words = stop_words+manual_input

except:
    nltk.download('stopwords')
    nltk.download('punkt')
    nltk.download('wordnet')
    nltk.download('omw-1.4')

    lemmatizer = WordNetLemmatizer()
    stop_words = list(stopwords.words('english'))
    manual_input = ["say", "worker", "company", "said"]
    stop_words = stop_words+manual_input


print("Loading model 1")
model_path="GoogleNews-vectors-negative300.bin"
#w2v_model = models.KeyedVectors.load_word2vec_format(model_path, binary=True)
w2v_model = models.KeyedVectors.load_word2vec_format(model_path, binary=True)
print("Loaded successfully 2")

#### Embedding Creation helper ####
def document_vector(doc):
    # remove out-of-vocabulary words
    doc = [word for word in doc if word in w2v_model.index_to_key]
    return np.mean(w2v_model[doc], axis=0)

def preprocessing(document):
    stop_words = list(stopwords.words('english'))
    # Remove punctuation and numbers
    try:

        document = re.sub(r"[^A-Za-z\u00c0-\u017e\s]+", " ", document)

        # Remove extra white spaces
        doc = re.sub(r"[\s]{2,}", " ", document)

        doc = doc.lower()
        doc = word_tokenize(doc)

        doc = [lemmatizer.lemmatize(word) for word in doc]
        doc = [word for word in doc if word not in stop_words]
    except:
        doc = []
    return doc

# Clean df col. without tokenizing
def cleanContent(document):
    stop_words = list(stopwords.words('english'))
    # Remove punctuation and numbers
    try:
        document = re.sub(r"[^A-Za-z\u00c0-\u017e ]+", " ", document)

        # Remove extra white spaces
        doc = re.sub(r"[\s]{2,}", " ", document)
        doc = doc.lower()

    except:
        doc = []
    return doc

#### Classifier Helper ####
def output_metrics(true, pred):
    # precision tp / (tp + fp)
    precision = precision_score(true, pred)
    print('Precision: %f' % precision)
    # recall: tp / (tp + fn)
    recall = recall_score(true, pred)
    print('Recall: %f' % recall)
    # f1: 2 tp / (2 tp + fp + fn)
    f1 = f1_score(true, pred)
    print('F1 score: %f' % f1)


def parse_date(date_string):
  parsed_str = ''
  if not date_string:
    return parsed_str

  parsed_str = pd.to_datetime(date_string, errors='coerce', infer_datetime_format=True)

  if pd.isnull(parsed_str):
    # 06-09-2022 or 06/09/2022
    if len(date_string.split('-')) > 2 or len(date_string.split('/')) > 2: 
      parsed_str = re.search(r'[\d]+[-|/][\d]+[-|/][\d]+', date_string).group()
      return dateutil.parser.parse(parsed_str).date()
    else:
      try:
        # 04 Aug 2022 or Aug, 04 2022 or August 18,2022
        parsed_str = re.search(r'[\d]+ [a-zA-Z]+,* +[\d]+|[a-zA-Z]+,* [\d]+,* [\d]+ | [a-zA-Z]+,* [\d]+,* *[\d]+', date_string).group()
        return dateutil.parser.parse(parsed_str).date()
      except:
        try:  
          # 20220408.... -> 2022 04 08 
          parsed_str = re.search(r'\d{8}', date_string).group()
          parsed_str = parsed_str[0:4] + '-' + parsed_str[4:6] + '-' + parsed_str[6:8]
          return dateutil.parser.parse(parsed_str).date()
        except:
          return ''
  else:
     return parsed_str.date()

class MetaCost(object):

    """A procedure for making error-based classifiers cost-sensitive
    >>> from sklearn.datasets import load_iris
    >>> from sklearn.linear_model import LogisticRegression
    >>> import pandas as pd
    >>> import numpy as np
    >>> S = pd.DataFrame(load_iris().data)
    >>> S['target'] = load_iris().target
    >>> LR = LogisticRegression(solver='lbfgs', multi_class='multinomial')
    >>> C = np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
    >>> model = MetaCost(S, LR, C).fit('target', 3)
    >>> model.predict_proba(load_iris().data[[2]])
    >>> model.score(S[[0, 1, 2, 3]].values, S['target'])
    .. note:: The form of the cost matrix C must be as follows:
    +---------------+----------+----------+----------+
    |  actual class |          |          |          |
    +               |          |          |          |
    |   +           | y(x)=j_1 | y(x)=j_2 | y(x)=j_3 |
    |       +       |          |          |          |
    |           +   |          |          |          |
    |predicted class|          |          |          |
    +---------------+----------+----------+----------+
    |   h(x)=j_1    |    0     |    a     |     b    |
    |   h(x)=j_2    |    c     |    0     |     d    |
    |   h(x)=j_3    |    e     |    f     |     0    |
    +---------------+----------+----------+----------+
    | C = np.array([[0, a, b],[c, 0 , d],[e, f, 0]]) |
    +------------------------------------------------+
    """

    def __init__(self, S, L, C, m=50, n=1, p=True, q=True):
        """
        :param S: The training set
        :param L: A classification learning algorithm
        :param C: A cost matrix
        :param q: Is True iff all resamples are to be used  for each examples
        :param m: The number of resamples to generate
        :param n: The number of examples in each resample
        :param p: Is True iff L produces class probabilities
        """
        if not isinstance(S, pd.DataFrame):
            raise ValueError('S must be a DataFrame object')
        new_index = list(range(len(S)))
        S.index = new_index
        self.S = S
        self.L = L
        self.C = C
        self.m = m
        self.n = len(S) * n
        self.p = p
        self.q = q
        self.newlabel = []

    def fit(self, flag, num_class):
        """
        :param flag: The name of classification labels
        :param num_class: The number of classes
        :return: Classifier
        """
        col = [col for col in self.S.columns if col != flag]
        S_ = {}
        M = []

        for i in range(self.m):
            # Let S_[i] be a resample of S with self.n examples
            S_[i] = self.S.sample(n=self.n, replace=True)

            X = S_[i][col].values
            y = S_[i][flag].values

            # Let M[i] = model produced by applying L to S_[i]
            model = clone(self.L)
            M.append(model.fit(X, y))

        label = []
        S_array = self.S[col].values
        for i in range(len(self.S)):
            if not self.q:
                k_th = [k for k, v in S_.items() if i not in v.index]
                M_ = list(np.array(M)[k_th])
            else:
                M_ = M

            if self.p:
                P_j = [model.predict_proba(S_array[[i]]) for model in M_]
            else:
                P_j = []
                vector = [0] * num_class
                for model in M_:
                    # for SVC classifier
                    #vector[model.predict(S_array[[i]])[0]] = 1
                    vector[model.predict(S_array[[i]])] = 1
                    P_j.append(vector)

            # Calculate P(j|x)
            P = np.array(np.mean(P_j, 0)).T

            # Relabel
            label.append(np.argmin(self.C.dot(P)))

        # Model produced by applying L to S with relabeled y
        X_train = self.S[col].values
        y_train = np.array(label)
        model_new = clone(self.L)
        model_new.fit(X_train, y_train)
        self.newlabel = y_train

        return model_new
