# -*- coding: utf-8 -*-
"""news_cw.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1N3OXDtuQOGZcPY-lwG0Xs3gCmMruwcQI
"""

import os
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.feature_selection import VarianceThreshold
import re
import numpy as np

import operator
import nltk
from nltk.corpus import stopwords
import argparse

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

from scipy.sparse import csr_matrix
from scipy.sparse import hstack


parser = argparse.ArgumentParser(description="Arg1 : dimensions of n-gram, Arg2 : variance threshold")
parser.add_argument("n", type=int, help='First argument')
parser.add_argument("t", type=float, help='Second argument')
args = parser.parse_args()

categories = ["business", "entertainment", "politics", "sport", "tech"]
current_directory = os.getcwd()
path = current_directory + "/bbc/"

def load_data(folder_path):
    documents = []
    labels = []
    for category in os.listdir(folder_path):
        count = 0
        category_path = os.path.join(folder_path, category)
        if os.path.isdir(category_path):
            for file_name in os.listdir(category_path):
                file_path = os.path.join(category_path, file_name)
                with open(file_path, 'r', encoding='latin1') as file:
                    content = file.read()
                    documents.append(content)
                    labels.append(category)
                    count += 1
    return documents, labels

def clean_text(text):
    #remove - and replace with " "
    text = re.sub(r'(\w+)-(\w+)', r'\1 \2', text)
    #remove special character, punctuation
    text = re.sub(r'[^\w\s]', '', text)
    #remove digits
    text = re.sub(r'\b\d+\b', '', text)
    #remove extra whitespaces
    text = ' '.join(text.split())

    return text

lemmatizer = nltk.stem.WordNetLemmatizer()

def get_list_tokens(string):
    #split text into sentences
  sentence_split=nltk.tokenize.sent_tokenize(string)
  list_tokens=[]
  for sentence in sentence_split:
      #split words in sentences
    list_tokens_sentence=nltk.tokenize.word_tokenize(sentence)
    for token in list_tokens_sentence:
        #reduce token to root word and append to list
      list_tokens.append(lemmatizer.lemmatize(token).lower())
  return list_tokens

def tokenize_words(texts, stop_words):
  token_list = []
  for i in texts:
    text_tokens = get_list_tokens(clean_text(i))
    #remove any words that are contained in the stop words list
    filtered_text_tokens = [w for w in text_tokens if not w in stop_words]
    token_list.append(filtered_text_tokens)
  return token_list

def freq_dictionary(tokens):
  freq_dict = {}
  for i in tokens:
    for word in i:
        #if word not in dictionary create index
      if word not in freq_dict:
        freq_dict[word] = 1
      else:
          #if word exists increase count by 1
        freq_dict[word] += 1
    #sort the dictionary and reduce to the top 1000 words
  freq_dict_sorted = sorted(freq_dict.items(), key=operator.itemgetter(1), reverse=True)[:1000]

  return freq_dict_sorted

def get_vocabulary(tokens):
  vocabulary = []
  freq_dict = freq_dictionary(tokens)
  #remove the count from the frequency dictionary and create a vocabulary
  for word, frequency in freq_dict:
    vocabulary.append(word)

  return vocabulary

def get_vector_text(tokens, list_vocab):
    #create a numpy array of length equal to vocab
  vector_text=np.zeros(len(list_vocab))
  for i, word in enumerate(list_vocab):
    if word in tokens:
        #count how many times each word in the vocab is present in the tokens of the article
      vector_text[i]=tokens.count(word)
  return vector_text

#load documents and respective labels
documents, labels = load_data(path)

#split data into 80% training, 20% testing data
X_train, X_test, y_train, y_test = train_test_split(documents, labels, test_size=0.2, random_state=42)

token_list = []
stop_words = set(stopwords.words('english'))
token_list = tokenize_words(X_train, stop_words)
vocab = get_vocabulary(token_list)

X_train_bow, X_test_bow = [], []
#create bag of words vector set
for i in X_train:
  X_train_bow.append(get_vector_text(i, vocab))

for i in X_test:
  X_test_bow.append(get_vector_text(i, vocab))

#Create n-gram vector set
vectorizer = CountVectorizer(ngram_range=(args.n, args.n))
X_train_vectors = vectorizer.fit_transform(X_train)
X_test_vectors = vectorizer.transform(X_test)

# Create TF-IDF vectors
tfidf_vectorizer = TfidfVectorizer(max_features=5000, stop_words='english', ngram_range=(1, 1))
X_train_tfidf = tfidf_vectorizer.fit_transform(X_train)
X_test_tfidf = tfidf_vectorizer.transform(X_test)

#convert list into sparce matrix so that its dimensions are equal to the other vectors and can be stacked
X_train_bow = csr_matrix(np.array(X_train_bow))
X_test_bow = csr_matrix(np.array(X_test_bow))

X_train_combined = hstack([X_train_bow, X_train_vectors, X_train_tfidf])
X_test_combined = hstack([X_test_bow, X_test_vectors, X_test_tfidf])

threshold = args.t
selector = VarianceThreshold(threshold)

#variance filter for feature selection
X_train_filtered = selector.fit_transform(X_train_combined)
X_test_filtered = selector.transform(X_test_combined)

#model to be trained
model = MultinomialNB()
model.fit(X_train_filtered, y_train)

#testing prediction
y_pred = model.predict(X_test_filtered)

accuracy = accuracy_score(y_test, y_pred)
print("Accuracy: ", accuracy)

report = classification_report(y_test, y_pred)
print("Classification Report:\n", report)