#!/local/apps/python/2.7.7/bin/python
##C:\WinPython-64bit-2.7.5.3\python-2.7.5.amd64\python

import os
import sys
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import pandas as pd
import shutil
import numpy as np
import datetime
import re
import glob
import zipfile
import tifffile as tf
from skimage import io
import json

def smooth(x,window_len=11,window='hanning'):
    if x.ndim != 1:
            raise ValueError, "smooth only accepts 1 dimension arrays."
    if x.size < window_len:
            raise ValueError, "Input vector needs to be bigger than window size."
    if window_len<1:
            return x
    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
            raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"
    if window == 'flat': 
            w=np.ones(2*window_len+1,'d')
    else:
            w=eval('np.'+window+'(2*window_len+1)')
    y=np.convolve(w/w.sum(),x,'valid')
    return np.r_[[y[0]]*int(window_len),y,[y[-1]]*int(window_len)]

def find_peaks(x,y,peak_count,bin,blank,signal_min=0):
    #bin: the size of the bin +/- in which to sum the y-values to find the peaks
    #blank: the default range over which, when the a peak is found, it will cover, uses peak_range to find a possibly larger range
    
    #signal_min = 5
    sum=np.zeros(len(x))
    sum_xy=np.zeros(len(x))
    for i in range(0,len(x)):
            sum[i]=y[i]
            sum_xy[i]=x[i]*y[i]
            for j in range(bin):
                    if i+j<len(x):
                            sum[i]+=y[i+j]
                            sum_xy[i]+=x[i+j]*y[i+j]
                    if i-j>=0:
                            sum[i]+=y[i-j]
                            sum_xy[i]+=x[i-j]*y[i-j]
    sum_=np.zeros((len(x),2))
    for i in range(0,len(x)):
            sum_[i]=(sum[i],i)
    sum_sorted=sorted(sum_,reverse=True,key=lambda tup: tup[0])
    peaks_x=[]
    peaks_y=[]
    done=np.zeros(len(x))
    for i in range(0,len(x)):
            (sum__,ii)=sum_sorted[i]
            ii=int(ii)
            #print i,ii,done[ii],x[ii]
            if (done[ii]==0) and (len(peaks_x)<peak_count) and (y[ii]>0) and y[ii] > signal_min:
                    peaks_x.append(x[ii])
                    peaks_y.append(y[ii])
                    (min_x,max_x)=peak_range(x,y,x[ii],0.2)
                    for j in range(0,blank):
                            if ii+j<len(done):
                                    done[ii+j]=1
                            if ii-j>=0:
                                    done[ii-j]=1
                    for j in range(0,len(done)):
                            if min_x<x[j]<max_x:
                                    done[j]=1
    return peaks_x,peaks_y

#find 8 low points, with alteast 150 pixels between them...reverse from ends if it's still at the lowest...
def find_valleys():
    pass

#look for a minimum before/after peak - must be atleast x% of the peak before the peak ends
def peak_range2(x,y,peak_x,delta=0.5):
    pass


#find start/end of the given peak - looks for a max before/ after the peak
def peak_range(x,y,peak_x,delta=0.05):
    
    index=0
    for i in range(0,len(x)):
        if x[i]<peak_x:
            index=i
    done=0
    minimum=y[index]
    index_minus=-1
    for i in range(0,index):
            if y[index-i]<minimum*(1.0+delta) and done==0:
                    index_minus=index-i
                    if minimum>y[index-i]:
                            minimum=y[index-i]
            else:
                    done=1
    if index_minus==-1:
            index_minus=index
    done=0
    minimum=y[index]
    index_plus=-1
    for i in range(index,len(x)):
            if y[i]<minimum*(1.0+delta) and done==0:
                    index_plus=i
                    if minimum>y[i]:
                            minimum=y[i]
            else:
                    done=1
    if index_plus==-1:
            index_plus=index
    #print index,index_minus,index_plus
    return (x[index_minus],x[index_plus])

image_magick_dir = 'C:/ImageMagick-6.8.9-16bit-HDRI/VisualMagick/bin' 
image_file = "C:\\Projects\\Boeke\\New Gel examples\\8-5-14(1)\\tiff\\red-green-2.tif"
temp_dir = "C:\\Projects\\Boeke\\New Gel examples\\8-5-14(1)\\tiff\\temp"

os.chdir(image_magick_dir)
convert_cmd = 'convert'
                
tif = tf.TiffFile(image_file)
true_length = tif.pages[0].image_length
true_width = tif.pages[0].image_width
        
#the vertical cutoffs between gels
#scaling down y-axis to 3 values - this sums the value on y-axis into 3 'bins' (?)
os.system(convert_cmd + ' "' + image_file + '" -scale 3x' + str(true_length) + '! "' + temp_dir + '/y-flat.txt"')

#read in image data (from scaled down image above)
df = pd.read_table(temp_dir + '/y-flat.txt', header=None, skiprows=1, comment='#', sep='[,:()]')

if('X2' in df.columns): #<--check this works!  different versions of pandas?
        df=df.drop(['X2','X6'], axis=1) 
else:
        df=df.drop([2,6], axis=1)
df.columns=['x','y','r','g','b']

#create a table with, for each x-value and each y-value (0,1,2), the r,g and b values can be retrieved
dfp=df.pivot_table(rows=['y'], cols=['x'], aggfunc=np.sum)

#create column in table that, for each x-value, is the product of the y-values (one for each of red, green (no blue))
dfp['peak_detection_r']=1
for i in range(3):
        dfp['peak_detection_r']*=dfp[('r',i)]
dfp['peak_detection_g']=1
for i in range(3):
        dfp['peak_detection_g']*=dfp[('g',i)]
dfp['peak_detection_rg'] = dfp['peak_detection_r']+dfp['peak_detection_g']

#reverse the pixels
dfp['peak_detection_rg_rev'] = max(dfp['peak_detection_rg']) - dfp['peak_detection_rg']

#smoothed_data = smooth(dfp['peak_detection_rg'])
#find peaks using 'peak_detection_rg' column...
(peaks_x_r_temp, peaks_y_r_temp) = find_peaks(dfp.index,
                                         dfp['peak_detection_rg_rev'], #smoothed_data, #dfp['peak_detection_rg'],
                                         8,
                                         1,
                                         150)

fig, (ax1) = plt.subplots(1,figsize=(6,6))
ax1.plot(dfp.index,dfp.peak_detection_rg_rev,c='black')
#ax1.plot(dfp.index,dfp.peak_detection_r,c='red')
#ax1.plot(dfp.index,dfp.peak_detection_g,c='green')
#ax1.plot(dfp.index,smoothed_data,c='blue')

ax1.set_xlim([0,len(dfp)])
ax1.set_ylim([0,1.05*max(dfp.peak_detection_rg_rev)]) #[max(dfp.peak_detection_r),max(dfp.peak_detection_rg),max(dfp.peak_detection_g)])]) #

#for k in range(0,len(peaks_x_r_temp)):
#    min_x=0
#    max_x=0
#    (min_x,max_x)=peak_range(dfp.index,dfp.peak_detection_rg,peaks_x_r_temp[k])
#    
#ax1.plot([min_x,max_x],[peaks_y_r_temp[k],peaks_y_r_temp[k]],c='blue')
#
ax1.scatter(peaks_x_r_temp,peaks_y_r_temp,c='blue')

fig.savefig(temp_dir+'/peaks.png',dpi=72,bbox_inches='tight')
fig.clf()
plt.close(fig)