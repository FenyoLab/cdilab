#!/usr/bin/python

from skimage import io
import numpy as np
import matplotlib.pyplot as plt
import math
import glob
import shutil
import os
import seaborn as sns
import pandas as pd

dir_ = 'C:\Users\snkeegan76\Desktop\images\IP'

#read in file
files = glob.glob(dir_ + '/*.png')

#images = {}
#images_count = {}
#heights_list = []
#i = 0
#for file_ in files:
#    img = io.imread(file_)
#    h = len(img)
#    w = len(img[0])
#    
#    key = str(h) + 'h_' + str(w) + 'w'
#    if not key in images:
#        images[key] = []
#    images[key].append(file_)
#    images_count[key] = [len(images[key]), h, w]
#    
#    heights_list.append(h)
#    
#    i += 1
#    #if(i > 30): break

#fig1 = plt.figure()
#plt.hist(heights_list, bins=len(images.keys()))
#fig1.savefig(dir_ + '/by_height.png')

#df = pd.DataFrame(columns=['dimens','count','h','w'])
#for i, key_ in enumerate(images_count.keys()):
#    df.loc[i] = [key_, images_count[key_][0],images_count[key_][1],images_count[key_][2]]
#df_sorted = df.sort(columns="h")
#fig1 = plt.figure()
#sns.countplot(x="dimens", data=df_sorted, palette="Greens_d");
#fig1.savefig(dir_ + '/by_height.png')

#create dir for every set that has more than one image
#for key in images.keys():
#    if(len(images[key]) > 1):
#        if(os.path.exists):
#            shutil.rmtree(dir_ + '/' + key)
#        os.mkdir(dir_ + '/' + key)
#        for file_ in images[key]:
#            path, file_name = os.path.split(file_)
#            shutil.move(file_, dir_ + '/' + key + '/' + file_name)
        
        

