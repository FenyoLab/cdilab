#!C:\WinPython-32bit-2.7.6.3\python-2.7.6\python

import sys
import os
import json
import numpy as np
import glob

#read in gel dimensions as json files and output average width over all gels, also output deviation for ranges
dir_ = 'C:\\Projects\\Boeke\\Gel Dimensions Averaging'
dimens = []
files = glob.glob(dir_ + "/*.json")
for cur_file in files:
    f = open(cur_file, 'r')
    gel_dimens = json.load(f)
    f.close()

    
    for gel in gel_dimens.keys():
        if(gel != 'gel-format'):
            dimens.append(gel_dimens[gel][1])
    
print np.mean(dimens)
print np.std(dimens)
print np.min(dimens)
print np.max(dimens)
