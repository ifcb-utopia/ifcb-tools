"""
Predict taxonomic/categorical labels of pngs using a trained CNN model

A. Chase June 2023, modified from code written by E. Culhane in 2019
"""


import pandas as pd
import numpy as np
from numpy import array
from numpy import argmax
import os, re
import cv2
import locale
import zipfile

# import keras
import tensorflow.keras as keras
from keras.preprocessing.image import ImageDataGenerator
from keras.models import model_from_json
from sklearn.preprocessing import LabelBinarizer
# -- 
# user defined functions 

def preprocess_input(image):
    fixed_size = 128
    image_size = image.shape[:2] 
    ratio = float(fixed_size)/max(image_size)
    new_size = tuple([int(x*ratio) for x in image_size])
    img = cv2.resize(image, (new_size[1], new_size[0]))
    delta_w = fixed_size - new_size[1]
    delta_h = fixed_size - new_size[0]
    top, bottom = delta_h//2, delta_h-(delta_h//2)
    left, right = delta_w//2, delta_w-(delta_w//2)
    color = [0, 0, 0]
    ri = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    gray_image = cv2.cvtColor(ri, cv2.COLOR_BGR2GRAY)
    gimg = np.array(gray_image).reshape(128,128,1)
    img_n = cv2.normalize(gimg, gimg, 0, 255, cv2.NORM_MINMAX)
    return(img_n)

def get_full_path(row, DATA_PATH): 
    _id = str(row['ImageId']).zfill(5)
    comps = row['bucket_id'].split('_')
    png = comps[1] + comps[0] + 'P' + _id +'.png'
    base = DATA_PATH
    out = base + row['bucket_id'] + '/' + png
    return out

def get_top_2(row):
    preds = [row[str(i)] for i in range(11)]
    top_2 = sorted(zip(preds, range(11)), reverse=True)[:2]
    index = top_2[1][1]
    return index

def get_percent(row, df): 
    n = float(row['n_examples'])
    d = float(sum(df.n_examples))
    return n / d

def change_class(row, cd): 
    l = row['label_group']
    if l in cd.keys(): 
        out = cd[l]
    else: 
        out = l 
    return out

DATA_PATH = '/Users/alisonchase/Documents/IFCB/NAAMES/NAAMES_ml/'
#DATA_PATH = '/Users/alisonchase/Dropbox/UTOPIA/test/ml/'
MODEL_PATH = '/Users/alisonchase/Dropbox/UTOPIA/ml-workflow/model_ckpt/'
MODEL = 'model-cnn-v1-b3'
MODEL_SUMMARY = 'model-summary-cnn-v1-b3.csv'
OUTPUT_FILE = '/Users/alisonchase/Documents/IFCB/NAAMES/NAAMES-predicted-labels-model-cnn-v1-b3.csv'  #'test-predicted-labels-model-cnn-v1-b3.csv'

""" 
Build the data from the directory of pngs

"""

# get image paths by traversing directory 

buckets = os.listdir(DATA_PATH)
image_paths = []
i = 0
for b in buckets: 
    i += 1
    base = DATA_PATH + b +'/'
    if 'DS_Store' in base: 
        continue 
    else : 
        for p in os.listdir(base): 
            if '.png' in p:
                image_paths.append(base + p)
            # - 
    print('completed ' + str(i) + ' of ' + str(len(buckets)))


len(image_paths)

image_paths = pd.DataFrame(image_paths)
image_paths.columns = ['image_path']


""" 
Generate image label predictions using previously trained model

"""
# -- 
# load saved model architecture and weights 

json_file = open(MODEL_PATH + MODEL + '.json', 'r')
loaded_model_json = json_file.read()
json_file.close()
loaded_model = model_from_json(loaded_model_json)
loaded_model.load_weights(MODEL_PATH + MODEL + '.h5')
loaded_model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

# make predictions on testing data using saved model 

n_splits = 50
test_split = np.array_split(image_paths, n_splits)
test_preds = []

# make predcitions 

n = 1
for df in test_split: 
    image_data = []
    for i in range(len(df)): 
        row = df.iloc[i]
        input_path = row['image_path']
        image_data.append(preprocess_input(cv2.imread(input_path)))
        # - 
    test_input = np.array(image_data)
    predictions = loaded_model.predict(test_input)
    pred_frame = pd.DataFrame(predictions)
    pred_frame['image_path'] = df['image_path'].values.tolist()
    top_1 = [np.argmax(i) for i in predictions]
    pred_frame['pred_label'] = top_1
    test_preds.append(pred_frame)
    print('completed ' + str(n) + ' of ' + str(n_splits) + ' testing subsets')
    n +=1 
    del image_data

    test_eval = pd.concat(test_preds)

if len(test_eval) == len(image_paths):
    print('generated predictions for all valid examples in dataset')

# get string labels for predicted numerical labels (this is read in from the trained model) 

trained_model = pd.read_csv(MODEL_PATH + MODEL_SUMMARY)

class_ref = trained_model.loc[trained_model['is_correct'] == 1]
class_ref = class_ref.groupby('true_label').agg({'high_group' : 'max'})
class_ref.reset_index(inplace=True)
class_ref.columns = ['pred_label', 'pred_class']

predicted_labels = test_eval[['image_path', 'pred_label']]#, 'top_2_label']]
predicted_labels = pd.merge(predicted_labels, class_ref, on='pred_label', how='left')

# print out table of image paths and predicted labels (both numerical and string labels)
predicted_labels.to_csv(OUTPUT_FILE)
