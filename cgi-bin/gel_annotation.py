#!/local/apps/python/2.7.7/bin/python

#    Copyright (C) 2017  Sarah Keegan
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

devel_info = False #if set to True, temporary directories won't be removed

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
import image_tools as it
from skimage import io
import json
import copy
#import codecs
#from subprocess import call

min_peaks_marker_lane = 0

full_ladder = (250,150,100,75,50,37,25,20,15,10)
display_ladder = (250,150,100,75,50,37)

full_ladder_new_gels = (250,150,100,75,50,37,25,20)
display_ladder_new_gels = (250,150,100,75,50,37)

default_label_variables = {"DOXYCYCLINE":(0, 50, 1000, 1000, 50, 1000, 1000), "CELL-LINE":"HeLa", "INPUT-PERCENT":"20"}

#these are the ratios for the difference-between-peaks (i.e. bands) for the ladder lane
#these are used to determine which lanes are the ladder lanes - if we find bands with
#these ratios, then it is the ladder lane
ratio_comp_min_1=[[0.7,1.015,0.84,1.435,0.91,1.14],[0.7,1.015,0.84,1.435]]
ratio_comp_max_1=[[1.3,1.885,1.56,2.665,1.69,2.47],[1.3,1.885,1.56,2.665]]
ratio_comp_min_2=[[0.7,0.644,0.91,0.63,0.945,0.3],[0.7,0.644,0.91,0.63]]
ratio_comp_max_2=[[1.3,1.196,1.72,1.4,1.755,0.75],[1.3,1.196,1.72,1.4]] # [1.3,1.196,1.69,1.4,1.755,0.75]
#ratio_comp_min/max_2 correspond to difs between bands representing ladder masses 150,100,75,50,37,25,15

caption_text_red1 = 'Tet-ON HeLa cells were transfected with construct encoding '
#GENE NAME01 (AN01)
caption_text_red2 = ' with an N-terminal fusion of FLAG, YFP (Venus) and V5 tags under a tet-inducible promoter. These cells were stimulated with 0, 50 or 1000 ng/ml doxycycline. Immunoprecipitation (IP) was carried out using 5ug of either IgG, CDI mAb Anti-'
#GENE NAME01 (cloneID# JH*01)
caption_text_red3 = ' or 1 ug of FLAG-M2. Immunoblotting was performed using rabbit Anti-FLAG (1:1000, Cell Signaling #2368).'

caption_text_green1 = 'Tet-ON HeLa cells were transfected with construct encoding '
#GENE NAME01 (AN01)
caption_text_green2 = ' with an N-terminal fusion of FLAG, YFP (Venus) and V5 tags under a tet-inducible promoter. These cells were stimulated with 0, 50 or 1000 ng/ml doxycycline. Immunoprecipitation (IP) was carried out using 5ug of either IgG, CDI mAb Anti-'
#GENE NAME01 (cloneID# JH*01)
caption_text_green3 = ' or 1 ug of FLAG-M2. Immunoblotting was performed using 0.2ug/ml CDI mouse mAb Anti-'
#GENE NAME01 (cloneID# JH*01)
caption_text_green4 = '. HC=Heavy chain.'

def find_peaks(x,y,peak_count,bin,blank,signal_min=0,peak_range_delta=0.2):
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
			(min_x,max_x)=peak_range(x,y,x[ii],peak_range_delta) 
			for j in range(0,blank):
				if ii+j<len(done):
					done[ii+j]=1
				if ii-j>=0:
					done[ii-j]=1
			for j in range(0,len(done)):
				if min_x<x[j]<max_x:
					done[j]=1
	return peaks_x,peaks_y
	
def gel_range(x,y,min_=0):
	begin = 0
	for i in range(len(y)):
		if(y[i] > min_):
			begin = i
			break
	end = len(y)-1
	y_len = len(y)
	for i in range(len(y)):
		if(y[y_len-i-1] > min_):
			end = y_len-i-1
			break
	return (begin,end)
	
#find start/end of the given peak - looks for a minimum before and after the peak
def peak_range(x,y,peak_x,delta=0.05,ret_type=1):
	index=0
	for i in range(0,len(x)):
		if x[i]<=peak_x:
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
	if(ret_type==1):
		return (x[index_minus],x[index_plus])
	else:
		return (index_minus, index_plus)

#filter
def smooth(x,window_len=11,window='hanning'):
	if x.ndim != 1:
		raise ValueError, "smooth only accepts 1 dimension arrays."
	if x.size < window_len:
		raise ValueError, "Input vector needs to be bigger than window size."
	if window_len<1:
		return x
	if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
		raise ValueError, "Window is one of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"
	if window == 'flat': 
		w=np.ones(2*window_len+1,'d')
	else:
		w=eval('np.'+window+'(2*window_len+1)')
	y=np.convolve(w/w.sum(),x,'valid')
	return np.r_[[y[0]]*int(window_len),y,[y[-1]]*int(window_len)]

#removes items from a list, 1 item, 2 items or 3 items
#returns generator
def remove_n(x,n):
	if n==1:
		for i in range(len(x)):
			y=np.ones(len(x))
			y[i]=0
			yield x[y==1]
	if n==2:
		for i in range(len(x)-1):
			for j in range(i+1,len(x)):
				y=np.ones(len(x))
				y[[i,j]]=0
				yield x[y==1]
	if n==3:
		for i in range(len(x)-1):
			for j in range(i+1,len(x)):
				for k in range(j+1,len(x)):
					y=np.ones(len(x))
					y[[i,j,k]]=0
					yield x[y==1]

def match_peak_ratios(peaks_x_sorted_):
	num_peaks = len(peaks_x_sorted_)
	if(num_peaks < 5): return 0
	if(num_peaks >= 7):
		test=7
		ratios_index = 0
	else:
		test=5
		ratios_index = 1
	
	ok_=0
	if test==num_peaks: #same number of peaks found as we are looking for in the ratios
		num_matched_ratios_1 = 0
		num_matched_ratios_2 = 0
		diff=peaks_x_sorted_[1:]-peaks_x_sorted_[:-1]
		ratio=diff/(1.0*diff[0])
		ok_=1
		for j in range(1,len(ratio_comp_max_1[ratios_index])): #compare ratios for ratio set #1
			if (ratio[j]<ratio_comp_min_1[ratios_index][j]) or (ratio_comp_max_1[ratios_index][j]<ratio[j]):
				ok_=0
			else: num_matched_ratios_1 += 1
		
		if ok_==0:
			ok_=2
			for j in range(1,len(ratio_comp_max_2[ratios_index])): #compare ratios for ratio set #2
				if (ratio[j]<ratio_comp_min_2[ratios_index][j]) or (ratio_comp_max_2[ratios_index][j]<ratio[j]):
					ok_=0
				else: num_matched_ratios_2 += 1
		return max(num_matched_ratios_1,num_matched_ratios_2)
			
	#if we find more actual peaks than we have theoretical - take out N=(#actual-#theoretical) peaks at a time,
	#and attempt the comparison (same as above) until we find a valid set of bands (or not)
	else:
		max_num_matched_ratios = 0
		for ii in range(len(peaks_x_sorted_)-test): #reduce the peak list by N-1 [N=(#actual-#theoretical)]
			if(ok_ != 0): break
			for peaks_x_sorted__ in remove_n(peaks_x_sorted_[ii:test+ii+1],1): #removes one more from the reduced list, one at a time (generator is returned)
				if(ok_ != 0): break
				num_matched_ratios_1 = 0
				num_matched_ratios_2 = 0
				diff=peaks_x_sorted__[1:]-peaks_x_sorted__[:-1]
				ratio=diff/(1.0*diff[0])
				ok_=1
				for j in range(1,len(ratio_comp_max_1[ratios_index])):
					if (ratio[j]<ratio_comp_min_1[ratios_index][j]) or (ratio_comp_max_1[ratios_index][j]<ratio[j]):
						ok_=0
					else: num_matched_ratios_1 += 1
				if ok_==0:
					ok_=2
					for j in range(1,len(ratio_comp_max_2[ratios_index])):
						if (ratio[j]<ratio_comp_min_2[ratios_index][j]) or (ratio_comp_max_2[ratios_index][j]<ratio[j]):
							ok_=0
						else: num_matched_ratios_2 += 1
				if(max(num_matched_ratios_1,num_matched_ratios_2) > max_num_matched_ratios): max_num_matched_ratios = max(num_matched_ratios_1,num_matched_ratios_2)		
		return max_num_matched_ratios
					
def check_spacing(peak_list, pixel_pos, lane_width, bin_x):
	#check peak at pixel_pos will not conflict with peaks already in peak_list
	min_gel_width = int((8.0*(lane_width*3.0/2.0))/bin_x)
	for p in peak_list:
		if((p + min_gel_width) > pixel_pos and p < pixel_pos):
			return False
		if((p - min_gel_width) < pixel_pos and p > pixel_pos):
			return False
	return True

#####################################################################################################################
def clip_and_mark_gels(json_filename, gel_choices, hdr_filename_r, hdr_filename_g, labels_filename, im_dir, os_type, scale_x=272, scale_y=468, bin_x=5, lane_width=14, max_ladder_peaks = 10):
#clips the gels from the collage using the rect coords in the json file
#tries to find the bands on each gel that correspond to the ladder masses and outputs json file with rect coordinates
	labels = pd.read_table(labels_filename)
	num_rows_labels = len(labels.index)
	
	#organize files/directories and variables
	(head, tail) = os.path.split(json_filename)
	date=datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
	out_dir = head 
	temp_dir = head + '/_clip-gels-' + date + '-' + 'TEMP'
	os.mkdir(temp_dir)
	
	jpg_collage_file = head + '/sectioned_collage.jpg'
	
	if(os_type == 'WINDOWS'):
		os.chdir(im_dir)
		convert_cmd = 'convert'
	else:
		convert_cmd = im_dir + '/convert'
	
	image_hdr_r = it.load_image(hdr_filename_r)
	image_hdr_g = it.load_image(hdr_filename_g)
	
	#load from json file
	f = open(json_filename, 'r')
	gel_marker_info = json.load(f)
	f.close()
	
	if('gel-format' in gel_marker_info and gel_marker_info['gel-format'] == 'new'):
		new_gel_format = True
	else: new_gel_format = False
	
	if(new_gel_format):
		#new gels
		lane_width=12
		max_ladder_peaks=8
		#scale_x*=.7
		scale_y = 180 #*=.5
		
	result_scale_x = scale_x
	result_scale_y = scale_y
	
	gel_choices = gel_choices.split(',')
	for gel_id in gel_choices:
		gel_i = int(gel_id)
		if(len(gel_id) == 1):
			gel_id = 'gel-0' + gel_id
		else:
			gel_id = 'gel-' + gel_id
		
		if(gel_i >= num_rows_labels):
		#user put wrong number of gels in the dialog box so program thinks there's more gels than there actually are
		#metadata file has 1 row per gel, so if we have "more" gels than there are rows, ignore the ones at the end
			continue
		
		cropped_gel_file = gel_id + '-cropped.tif'
		cropped_markers_file = gel_id + '-markers.txt'
		##################################
		#clip out gels
		os.system(convert_cmd + ' "' + jpg_collage_file + '" -auto-level -crop ' +
			  str(gel_marker_info[gel_id][1]) + 'x' + str(gel_marker_info[gel_id][3]) +
			  '+' + str(gel_marker_info[gel_id][0]) + '+' + str(gel_marker_info[gel_id][2]) +
			  ' "' + temp_dir + '/' + cropped_gel_file + '"')
		
		#save cropped gel as _gel-xx-r-d.jpg (red channel only) for use with densitometric analysis
		os.system(convert_cmd + ' -separate -channel R "' + temp_dir + '/' + cropped_gel_file + '" "' + temp_dir + '/' + cropped_gel_file + '_RGB-%d.jpg"')
		os.system(convert_cmd + ' -auto-level -negate "' + temp_dir + '/' + cropped_gel_file + '_RGB-0.jpg" "' + out_dir + '/_' + gel_id + '-r-d.jpg"')
		os.unlink(temp_dir + '/' + cropped_gel_file + '_RGB-0.jpg')
		
		#stretch
		os.system(convert_cmd + ' "' + temp_dir + '/' + cropped_gel_file + '" -scale ' +
			  str(result_scale_x) + 'x' + str(result_scale_y) +
			  '! "' + out_dir + '/' + gel_id + '.tif"')
		
		#images used for densitometric analysis#############################
		#cut out and copy HDRI gel to output directory - note removed autolevel from hdr crop b/c not sure if it will work correctly
		#NOTE* change this to manually crop since ImageMagick crop is introducing invalid information in the txt file!
		hdr_filename_r_txt = out_dir + '/_' + gel_id + '_hdr_r.txt'
		hdr_filename_g_txt = out_dir + '/_' + gel_id + '_hdr_g.txt'
		os.system(convert_cmd + ' "' + hdr_filename_r + '" -crop ' +
			  str(gel_marker_info[gel_id][1]) + 'x' + str(gel_marker_info[gel_id][3]) +
			  '+' + str(gel_marker_info[gel_id][0]) + '+' + str(gel_marker_info[gel_id][2]) + 
			  ' "' + hdr_filename_r_txt + '"')
		os.system(convert_cmd + ' "' + hdr_filename_g + '" -crop ' +
			  str(gel_marker_info[gel_id][1]) + 'x' + str(gel_marker_info[gel_id][3]) +
			  '+' + str(gel_marker_info[gel_id][0]) + '+' + str(gel_marker_info[gel_id][2]) + 
			  ' "' + hdr_filename_g_txt + '"')
		
		it.crop_image_json(int(gel_marker_info[gel_id][1]), int(gel_marker_info[gel_id][3]), int(gel_marker_info[gel_id][0]), int(gel_marker_info[gel_id][2]), out_dir + '/_' + gel_id + '-r.json', image_hdr_r)
		it.crop_image_json(int(gel_marker_info[gel_id][1]), int(gel_marker_info[gel_id][3]), int(gel_marker_info[gel_id][0]), int(gel_marker_info[gel_id][2]), out_dir + '/_' + gel_id + '-g.json', image_hdr_g)
		
		#######################################
		#locate the bands for the marker lane
		
		#locate the marker peaks for this gel
		true_length = gel_marker_info[gel_id][3] 
		true_width = gel_marker_info[gel_id][1] 
		scale_x = true_width
		scale_y = true_length
		scale_x_=int(true_width/(1.0*bin_x)) 
		scale_y_=int(3)
		
		#convert to text and read in the image data
		#scaling down y-axis to 3 values - this sums the value on y-axis into 3 'bins' 
		os.system(convert_cmd + ' "' + hdr_filename_r_txt + '" -scale ' +
			  str(scale_x_) + 'x' + str(scale_y_) + '! "' + temp_dir + '/' + cropped_gel_file + '.txt"')
		df = pd.read_table(temp_dir + '/' + cropped_gel_file + '.txt', header=None, skiprows=1, comment='#', sep='[,:()]',
				   converters={'r':p2f, 'g':p2f, 'b':p2f}, names=('x','y','e1','r','g','b','e2'))
		df=df.drop(['e1','e2'], axis=1)
		os.unlink(temp_dir + '/' + cropped_gel_file + '.txt')
		
		#create a table with, for each x-value and each y-value (0,1,2), the r,g and b values can be retrieved
		dfp=df.pivot_table(rows=['x'], cols=['y'], aggfunc=np.sum)
		
		#create column in table that, for each x-value, is the product of the y-values (one for each of red, green and blue)
		dfp['peak_detection_r']=1
		for i in range(3):
			dfp['peak_detection_r']*=dfp[('r',i)]
		dfp['peak_detection_g']=1
		for i in range(3):
			dfp['peak_detection_g']*=dfp[('g',i)]
		dfp['peak_detection_b']=1
		for i in range(3):
			dfp['peak_detection_b']*=dfp[('b',i)]
		dfp['peak_detection_rg']=1
		for i in range(3):
			dfp['peak_detection_rg']*=dfp[('r',i)]-dfp[('g',i)]
		
		#find peaks in the red color, using 'peak_detection_r' column...
		(peaks_x_r_temp, peaks_y_r_temp) = find_peaks(dfp.index, dfp['peak_detection_r'], 4, 1, 10)
		#SORT peaks_x_r_temp 
		peaks_x_r_sorted = sorted(peaks_x_r_temp)
		#the first red color peak (sorted going across image) should indicate the marker lane
		x_pos_mid_marker_lane = peaks_x_r_sorted[0]
		
		#cut out marker lane
		scale_x__=x_pos_mid_marker_lane*bin_x
		scale_x__-=lane_width
		scale_x____=2*lane_width + .5*lane_width #cut out extra for slanted lanes to get entire lane
		if scale_x__<0:
			scale_x____+=scale_x__
			scale_x__=0
			
		#cut out the marker lane (using the current peak location)
		
		#os.system(convert_cmd + ' "' + hdr_filename_r_txt + '" -crop ' +
		#	  str(scale_x____) + 'x' + str(scale_y) + '+' + str(scale_x__+gel_marker_info[gel_id][0]) +
		#	  '+' + str(gel_marker_info[gel_id][2]) + ' "' + temp_dir + '/' + cropped_markers_file + '"')
		#(in above, must crop from pixel offset of the original image b/c when cropping ImageMagick uses virtual canvas
		#for the cropped image)
		
		os.system(convert_cmd + ' "' + hdr_filename_r_txt + '" -crop ' +
			  str(scale_x____) + 'x' + str(scale_y) + '+' + str(scale_x__) +
			  '+0 "' + temp_dir + '/' + cropped_markers_file + '"')
		os.system(convert_cmd + ' "' + temp_dir + '/' + cropped_markers_file + '" ' +
			  '-scale 1x' + str(scale_y) + '! "' + temp_dir + '/' + cropped_markers_file + '_.txt"')
		
		#read in the 1x image text file of the marker lane, generated above
		df_test = pd.read_table(temp_dir + '/' + cropped_markers_file + '_.txt', header=None, skiprows=1, comment='#', sep='[,:()]',
					converters={'r':p2f, 'g':p2f, 'b':p2f}, names=('x','y','e1','r','g','b','e2'))
		df_test.index = df_test.y
		df_test=df_test.drop(['x', 'y', 'e1','e2'], axis=1)
		os.unlink(temp_dir + '/' + cropped_markers_file + '_.txt')
		
		#smoothing and background subtraction of red signal - now we are reading vertically
		if(new_gel_format):
			df_test.r=smooth(df_test.r,1,'flat')
			df_test.r-=min(df_test.r)
			#df_test.r-=sorted(df_test.r)[int(len(df_test.r)*0.10)]   #*0.10)] 
			df_test['r'][df_test.r<0]=0
			df_test['background']=smooth(df_test.r,13,'flat') #adjusted smoothing by half since using hdri #13
			df_test['rg']=df_test.r-df_test.background 
			#df_test['rg'][df_test.rg<0.08*max(df_test.rg)]=0
		else:
			df_test.r_orig = df_test.r
			df_test.r=smooth(df_test.r,1,'flat')
			df_test.r-=min(df_test.r)
			df_test.r-=sorted(df_test.r)[int(len(df_test.r)*0.25)]
			df_test['r'][df_test.r<0]=0
			df_test['background']=smooth(df_test.r,26,'flat') #adjusted smoothing by half since using hdri
			df_test['rg']=df_test.r-df_test.background 
			df_test['rg'][df_test.rg<0.08*max(df_test.rg)]=0
		
		#read the current ladder configuration from the labels file, set cur_ladder
		if 'Ladder' in labels.columns:
			labels_ladder = labels['Ladder'][gel_i]
			if(type(labels_ladder) == type('')):
				labels_ladder = labels_ladder.split(',')
			elif(np.isnan(labels_ladder)):
				labels_ladder = []
			else:
				labels_ladder = str(labels_ladder)
				labels_ladder = labels_ladder.split(',')
		else:
			labels_ladder = []
		
		cur_ladder = []
		if(new_gel_format):
			cur_full_ladder = full_ladder_new_gels
			cur_display_ladder = display_ladder_new_gels
		else:
			cur_full_ladder = full_ladder
			cur_display_ladder = display_ladder
		for mass in cur_display_ladder: #full_ladder:
			remove = False
			for rem_mass in labels_ladder:
				if(int(float(rem_mass)) == mass):
					remove = True
					break
			if(not remove):cur_ladder.append(mass)
		num_labels = len(cur_ladder)
		
		peaks_x_=[]
		peaks_y_=[]
		
		#find peaks in the marker lane - these correspond to the bands - take the top 'num_labels' peaks
		if(new_gel_format):
			#(peaks_x_,peaks_y_)=find_peaks(df_test.index, df_test.rg, num_labels, 0,5,0,0.10)
			(peaks_x_,peaks_y_)=find_peaks(df_test.index, df_test.rg, num_labels, 0,5,0,0.1) #test this right here!
		else:
			(peaks_x_,peaks_y_)=find_peaks(df_test.index, df_test.rg, num_labels, 0,10,0)
		
		if(devel_info):
			fig, (ax1) = plt.subplots(1,figsize=(6,6))
			ax1.plot(df_test.index,df_test.rg,c='black')
			ax1.plot(df_test.index,df_test.background,c='gray')
			ax1.plot(df_test.index,df_test.r,c='r')
			#ax1.plot(df_test.index,df_test.r_orig,c='b')
			
			ax1.set_xlim([0,len(df_test)])
			ax1.set_ylim([0,1.05*max([max(df_test.r),max(df_test.rg)])])
			ax1.scatter(peaks_x_,peaks_y_,c='r')
			fig.savefig(temp_dir+'/marker_peaks-'+gel_id+'.png',dpi=72,bbox_inches='tight')
			fig.clf()
			plt.close(fig)
		
		peaks_x_ = sorted(peaks_x_)
		
		#save peak positions and masses for labeling
		marker_labels = {}
		for p_i, peak in enumerate(peaks_x_):
			marker_labels[cur_ladder[p_i]] = int(peak)
		p_i = num_labels - (num_labels - len(peaks_x_))
		while(p_i < num_labels):
			marker_labels[cur_ladder[p_i]] = -1
			p_i += 1
			
		f = open(out_dir + '/_' + gel_id + '-markers.json', 'w')
		json.dump(marker_labels, f)
		f.close()
	#delete temp directory
	if(not devel_info):
		shutil.rmtree(temp_dir)
	return num_rows_labels

#to convert % to float in pandas read_table
def p2f(x):
	if(x == None):
		return 0.01
	elif("inf" in x or "INF" in x):
		return 1
	else:
		return float(x.strip('%'))/100

def mark_collage(new_gel_format, filename_hdri_red, filename_hdri_gr, labels_filename, im_dir, os_type, num_gels=12, num_x=5, num_y=3, scale_x=272, scale_y=468, bin_x=5, lane_width=14, max_ladder_peaks = 10):
# else vice versa
#tries to find demarcations between gels in the gell collage
#outputs json file indicating where the boxes should be drawn on the image for the user to adjust
#and where the markers in the marker lanes are located

	#new_gel_format = True
	new_way_gel_width = True
	if(new_gel_format):
		#new gels
		lane_width=12
		max_ladder_peaks=8
		new_gels_min_gel_height=150
		background_smooth_window = 26
		background_smooth_window = 13
	else:
		background_smooth_window = 51
		background_smooth_window = 26
	
	labels = pd.read_table(labels_filename)
	
	#these will be the dicts to store the rect positions to outlie the gels
	#these will be saved as json files
	gel_markers = {}
	
	if(os_type == 'WINDOWS'):
		os.chdir(im_dir)
		convert_cmd = 'convert'
	else:
		convert_cmd = im_dir + '/convert'
	
	# (0) organize files/directories and variables
	(head, tail) = os.path.split(filename_hdri_red)
	date=datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
	out_dir = head #+ '/gels (' + date + ')'
	#os.mkdir(out_dir)
	temp_dir = head + '/_gels-' + date + '-' + 'TEMP'
	os.mkdir(temp_dir)
	
	#combine red/green hdri's and output single hdri and also jpg file for browser display
	filename = head + '/_sectioned_collage.tif'
	filename_ = head + '/sectioned_collage.tif'
	(true_length, true_width) = it.hdri_to_tiff_and_combine(filename_hdri_gr, filename_hdri_red, filename, filename_)
	
	#convert tiff to jpg using ImageMagick
	os.system(convert_cmd + ' "' + filename_ + '" "' + filename_.replace(".tif", ".jpg") + '"')
	if(not devel_info):
		os.unlink(filename_)
	
	
	#below lines will set it up so that there's no rescaling at the beginning, only at the end before producing image to be used for labeling
	#I don't want rescaling at the beginning b/c I want to use the gel end points to cut the original image for densitometric analysis
	result_scale_x = scale_x
	result_scale_y = scale_y
	scale_x = true_width/num_x
	scale_y = true_length/num_y
	
	###scale_x_=int(num_y*num_x*scale_x/(1.0*bin_x)) # <-- not sure reason for bin_x rescale
	scale_x_=int(num_y*true_width/(1.0*bin_x)) # <-- not sure reason for bin_x rescale
	scale_y_=int(3)
	
	if(os_type == 'WINDOWS'):
		os.chdir(im_dir)
		convert_cmd = 'convert'
	else:
		convert_cmd = im_dir + '/convert'
	
	# (1) resizing image, creating one long image instead of rows of gels
	if(new_gel_format):
	#find separation points between rows, in the new gels they are not always evenly separated so we must examine the image to find this
		#scaling down y-axis to 3 values - this sums the value on y-axis into 3 'bins' (?)
		os.system(convert_cmd + ' "' + filename + '" -scale 3x' + str(true_length) + '! "' + temp_dir + '/y-flat.txt"')
		
		#df = pd.read_table(temp_dir + '/y-flat.txt', header=None, skiprows=1, comment='#', sep='[,:()]',
		#			names=('x','y','e1','r','g','b','e2'))
		#
		#if(devel_info): df.to_csv(head + '/df_file1.csv')
		
		#read in image data (from scaled down image above)
		# 0,556: (4012.91%,inf%,0%)  #FFFFFFFF0000  srgb(4012.91%,inf%,0%)
		# 0,556: (4012.91%,1.#INF%,0%)  #FFFFFFFF0000  srgb(4012.91%,1.#inf%,0%)
		df = pd.read_table(temp_dir + '/y-flat.txt', header=None, skiprows=1, comment='#', sep='[,:()]',
				   converters={'r':p2f, 'g':p2f, 'b':p2f}, names=('x','y','e1','r','g','b','e2'))
		
		#if(devel_info): df.to_csv(head + '/df_file2.csv')
		
		df=df.drop(['e1','e2'], axis=1)
		
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
		
		#reverse the pixels - finding valleys
		dfp['peak_detection_rg_rev'] = max(dfp['peak_detection_rg']) - dfp['peak_detection_rg']
		
		#find peaks using 'peak_detection_rg' column...
		(peaks_x_r_temp, peaks_y_r_temp) = find_peaks(dfp.index,
							 dfp['peak_detection_rg_rev'], 
							 num_y+1,
							 1,
							 new_gels_min_gel_height)
		delta = 0.1
		try_=1
		while(len(peaks_x_r_temp) < num_y+1 and try_ < 10):
			(peaks_x_r_temp, peaks_y_r_temp) = find_peaks(dfp.index,
							 dfp['peak_detection_rg_rev'], 
							 num_y+1,
							 1,
							 new_gels_min_gel_height,
							 signal_min=0,
							 peak_range_delta=delta)
			delta=delta/2
			try_+=1
			
		#add in "peaks" at the top and bottom of image, correcting if it wants to cut off before top/bottom
		#it is safer this way
		peaks_x_r_temp.remove(min(peaks_x_r_temp))
		peaks_x_r_temp.append(0)
		peaks_x_r_temp.remove(max(peaks_x_r_temp))
		peaks_x_r_temp.append(len(dfp.index)-1)
		
		if(devel_info):
			fig, (ax1) = plt.subplots(1,figsize=(6,6))
			ax1.plot(dfp.index,dfp.peak_detection_rg_rev,c='black')
			ax1.set_xlim([0,len(dfp)])
			ax1.set_ylim([0,1.05*max(dfp.peak_detection_rg_rev)]) 
			ax1.scatter(peaks_x_r_temp,peaks_y_r_temp,c='blue')
			
			fig.savefig(temp_dir+'/collage-y-reversed_peaks.png',dpi=72,bbox_inches='tight')
			fig.clf()
			plt.close(fig)
		#the peaks tell us where to cut out the rows
		if(len(peaks_x_r_temp) != num_y+1):
			pass #will need to put something here if it doesn't find the peaks
		
		#cutting out the rows
		gel_rows = sorted(peaks_x_r_temp) #store this for cutting and also for later when we cut out the individual gels
		max_height = 0
		for i in range(num_y):
			cur_height = gel_rows[i+1]-gel_rows[i]
			if(max_height < cur_height): max_height = cur_height
			os.system(convert_cmd + ' "' + filename + '" -crop '+str(true_width)+'x'+str(cur_height)+'+0+'+str(gel_rows[i])+' "'+temp_dir+'/cut'+str(i)+'.tif"')
			if(devel_info):
				os.system(convert_cmd + ' "' + filename_ + '" -crop '+str(true_width)+'x'+str(cur_height)+'+0+'+str(gel_rows[i])+' "'+temp_dir+'/cut'+str(i)+'_.tif"')
		#combining the cut out rows into one long row
		shutil.copy(temp_dir + '/cut0.tif', temp_dir + '/one-row.tif')
		if(devel_info):
			shutil.copy(temp_dir + '/cut0_.tif', temp_dir + '/one-row_.tif')
		for i in range(1,num_y):
			os.system(convert_cmd + ' "' + temp_dir + '/one-row.tif" "' + temp_dir + '/cut' + str(i) + '.tif" -background black +append "' + temp_dir + '/one-row.tif"')
			if(devel_info):
				os.system(convert_cmd + ' "' + temp_dir + '/one-row_.tif" "' + temp_dir + '/cut' + str(i) + '_.tif" -background black +append "' + temp_dir + '/one-row_.tif"')
			if(not devel_info): os.unlink(temp_dir + '/cut' + str(i) + '.tif')
	else:
		#cutting out the 3 rows
		for i in range(num_y):
			os.system(convert_cmd + ' "' + filename + '" -crop '+str(true_width)+'x'+str(scale_y)+'+0+'+str(i*scale_y)+' "'+temp_dir+'/cut'+str(i)+'.tif"')
		
		#combining the 3 cut out rows into one long row
		shutil.move(temp_dir + '/cut0.tif', temp_dir + '/one-row.tif')
		for i in range(1,num_y):
			os.system(convert_cmd + ' "' + temp_dir + '/one-row.tif" "' + temp_dir + '/cut' + str(i) + '.tif" +append "' + temp_dir + '/one-row.tif"')
			os.unlink(temp_dir + '/cut' + str(i) + '.tif')
			
	#(2) finding the ladder lanes
	#scaling down y-axis to 3 values - this sums the value on y-axis into 3 'bins' (?)
	if(devel_info):
		os.system(convert_cmd + ' "' + temp_dir + '/one-row_.tif" -scale ' + str(scale_x_) + 'x' + str(int(max_height/(1.0*bin_x))) + '! "' + temp_dir + '/one-row_scaled.tif"')
	
	os.system(convert_cmd + ' "' + temp_dir + '/one-row.tif" -scale ' + str(scale_x_) + 'x' + str(scale_y_) + '! "' + temp_dir + '/one-row.txt"')
	
	#read in image data (from scaled down image above)
	df = pd.read_table(temp_dir + '/one-row.txt', header=None, skiprows=1, comment='#', sep='[,:()]',
				   converters={'r':p2f, 'g':p2f, 'b':p2f}, names=('x','y','e1','r','g','b','e2'))
	df=df.drop(['e1','e2'], axis=1)
	df.replace(0,{'r':1, 'g':1},True)
	
	if(not devel_info):
		os.unlink(temp_dir + '/one-row.txt')
	
	#create a table with, for each x-value and each y-value (0,1,2), the r,g and b values can be retrieved
	dfp=df.pivot_table(rows=['x'], cols=['y'], aggfunc=np.sum)
	
	#print dfp
	
	#create column in table that, for each x-value, is the product of the y-values (one for each of red, green and blue)
	dfp['peak_detection_r']=1
	for i in range(scale_y_):
		dfp['peak_detection_r']*=dfp[('r',i)]
	dfp['peak_detection_g']=1
	for i in range(scale_y_):
		dfp['peak_detection_g']*=dfp[('g',i)]
	dfp['peak_detection_b']=1
	for i in range(scale_y_):
		dfp['peak_detection_b']*=dfp[('b',i)]
	dfp['peak_detection_rg']=1
	for i in range(scale_y_):
		dfp['peak_detection_rg']*=dfp[('r',i)]-dfp[('g',i)]
		
	#also create column for red minus green
	dfp['peak_detection_rg']=dfp['peak_detection_r']-dfp['peak_detection_g']
	dfp[dfp['peak_detection_rg']<0]['peak_detection_rg']=0
	d_=int(scale_x_/(num_x*num_y))
	
	#find peaks in the red color, using 'peak_detection_r' column...cutting off the end a little for the blank area at the end ??
	(peaks_x_r_temp, peaks_y_r_temp) = find_peaks(dfp[dfp.index<int((num_gels-0.5)/num_gels*len(dfp))].index,
						 dfp[dfp.index<int((num_gels-0.5)/num_gels*len(dfp))]['peak_detection_r'],
						 4*num_gels,
						 1,
						 10)
	
	#before sorting, remember peaks_y_r_temp for the plot
	peaks_y_dict = {}
	for x_i, x in enumerate(peaks_x_r_temp):
		peaks_y_dict[x] = peaks_y_r_temp[x_i]
	
	#SORT peaks_x_r_temp 
	peaks_x_r_temp = sorted(peaks_x_r_temp)
	
	#loop through each red color peak (going across the image) - each one may indicate a marker lane
	peaks_found = []
	marker_peaks_lists = {}
	max_var = 0
	max_green_ratio = 0
	max_num_peaks = 0
	max_band_ratios_match = 0
	for i in range(len(peaks_x_r_temp)):
		scale_x__=peaks_x_r_temp[i]*bin_x
		scale_x__-=lane_width
		scale_x____=2*lane_width + .5*lane_width #cut out extra for slanted lanes to get entire lane
		if scale_x__<0:
			scale_x____+=scale_x__
			scale_x__=0
			
		#cut out the marker lane (using the current peak location)
		os.system(convert_cmd + ' "' + temp_dir+'/one-row.tif" -crop '+str(scale_x____)+'x'+str(scale_y)+'+'+str(scale_x__)+'+0 "'+temp_dir+'/test-'+str(peaks_x_r_temp[i])+'-markers.tif"')
		if(devel_info):
			os.system(convert_cmd + ' "' + temp_dir+'/one-row_.tif" -crop '+str(scale_x____)+'x'+str(scale_y)+'+'+str(scale_x__)+'+0 "'+temp_dir+'/test-'+str(peaks_x_r_temp[i])+'-markers_.tif"')
		os.system(convert_cmd + ' "' + temp_dir+'/test-'+str(peaks_x_r_temp[i])+'-markers.tif" ' + '-scale 1x'+str(scale_y)+'! "'+temp_dir+'/test-'+str(peaks_x_r_temp[i])+'-markers.txt"')
		
		#read in the 1x image text file of the marker lane, generated above
		df_test = pd.read_table(temp_dir + '/test-' + str(peaks_x_r_temp[i]) + '-markers.txt', header=None, skiprows=1, comment='#', sep='[,:()]',
				   converters={'r':p2f, 'g':p2f, 'b':p2f}, names=('x','y','e1','r','g','b','e2'))
		df_test.index = df_test.y
		df_test=df_test.drop(['x', 'y', 'e1','e2'], axis=1)
		if(not devel_info):
			os.unlink(temp_dir + '/test-' + str(peaks_x_r_temp[i]) + '-markers.txt')
		
		#smoothing and background subtraction of red signal - now we are reading vertically
		df_test.r=smooth(df_test.r,1,'flat')
		df_test.r-=min(df_test.r)
		df_test.r-=sorted(df_test.r)[int(len(df_test.r)*0.25)]
		df_test['r'][df_test.r<0]=0
		df_test['background']=smooth(df_test.r,background_smooth_window,'flat')
		df_test['rg']=df_test.r-df_test.background
		df_test['rg'][df_test.rg<0.08*max(df_test.rg)]=0
		
		df_test.g=smooth(df_test.g,1,'flat')
		df_test.g-=min(df_test.g)
		df_test.g-=sorted(df_test.g)[int(len(df_test.g)*0.25)]
		df_test['g'][df_test.g<0]=0
		df_test['background_g']=smooth(df_test.g,51,'flat')
		df_test['gg']=df_test.g-df_test.background_g
		df_test['gg'][df_test.gg<0.08*max(df_test.gg)]=0
		
		#get pixels where green is above red background
		s_green_above_rb = df_test.gg - df_test.background
		s_green_above_rb = s_green_above_rb[s_green_above_rb>0]
		green_ratio = float(len(s_green_above_rb))/len(df_test.gg)
		
		peaks_x_=[]
		peaks_y_=[]
		
		#find peaks in the marker lane - these correspond to the bands
		(peaks_x_,peaks_y_)=find_peaks(df_test.index,df_test.rg,max_ladder_peaks,0,10,0)
			
		#rearrange:
		peaks_x_y = []
		for i_v,v in enumerate(peaks_x_):
			peaks_x_y.append([v, peaks_y_[i_v]])
		marker_peaks_lists[peaks_x_r_temp[i]] = peaks_x_y #[peaks_x_, peaks_y_]
		
		if len(peaks_x_)>min_peaks_marker_lane:
			#plot the signal and the background, with the peaks and peak range also plotted, for current marker lane
			#print i,peaks_x_,peaks_y_
			peaks_x_sorted_=np.array(sorted(peaks_x_))
			if(devel_info):
				fig, (ax1) = plt.subplots(1,figsize=(6,6))
				ax1.plot(df_test.index,df_test.rg,c='black')
				#ax1.plot(df_test.index,df_test.gg,c='blue')
				ax1.plot(df_test.index,df_test.background,c='gray')
				ax1.plot(df_test.index,df_test.r,c='r')
				ax1.plot(df_test.index,df_test.g,c='yellow')
				ax1.plot(df_test.index,df_test.gg,c='green')
				ax1.set_xlim([0,len(df_test)])
				ax1.set_ylim([0,1.05*max([max(df_test.r),max(df_test.rg),max(df_test.b),max(df_test.g),max(df_test.gg)])])
			for k in range(0,len(peaks_x_)):
				min_x=0
				max_x=0
				(min_x,max_x)=peak_range(df_test.index,df_test.rg,peaks_x_[k])
				if(devel_info): ax1.plot([min_x,max_x],[peaks_y_[k],peaks_y_[k]],c='r')
			if(devel_info):ax1.scatter(peaks_x_,peaks_y_,c='r')
			
			std_norm = np.std(peaks_y_)/np.mean(peaks_y_)
			band_ratios_match = match_peak_ratios(peaks_x_sorted_)
			if(max_var < std_norm): max_var = std_norm
			if(max_green_ratio < green_ratio): max_green_ratio = green_ratio
			if(max_num_peaks < len(peaks_x_)): max_num_peaks = len(peaks_x_)
			if(max_band_ratios_match < band_ratios_match): max_band_ratios_match = band_ratios_match
			
			peaks_found.append([i,len(peaks_x_),std_norm,green_ratio,band_ratios_match])	
		else:
			if(devel_info):
				fig, (ax1) = plt.subplots(1,figsize=(6,6))
				ax1.plot(df_test.index,df_test.rg,c='black')
				#ax1.plot(df_test.index,df_test.gg,c='blue')
				ax1.plot(df_test.index,df_test.background,c='gray')
				ax1.plot(df_test.index,df_test.r,c='r')
				ax1.plot(df_test.index,df_test.g,c='yellow')
				ax1.plot(df_test.index,df_test.gg,c='green')
				ax1.set_xlim([0,len(df_test)])
				ax1.set_ylim([0,1.05*max([max(df_test.r),max(df_test.rg),max(df_test.b),max(df_test.g),max(df_test.gg)])])
				
		if(devel_info):
			fig.savefig(temp_dir+'/test-'+str(peaks_x_r_temp[i])+'-peaks.png',dpi=72,bbox_inches='tight')
			fig.clf()
			plt.close(fig)
	
	#marker lanes are the top lanes in peaks_found (those with most peaks found)
	peaks_x_r = []
	peaks_y_r = []
	for pf in peaks_found:
		score = (float(pf[1])/max_num_peaks)/4 + (1-pf[2]/max_var)/4 + (1-pf[3]/max_green_ratio)/4 + (float(pf[4])/max_band_ratios_match)/4
		pf.append(score)
	peaks_found = sorted(peaks_found, key=lambda x: x[5], reverse=True)
	
	for peaks in peaks_found:
		if len(peaks_x_r) >= num_gels: break
		if(check_spacing(peaks_x_r, peaks_x_r_temp[peaks[0]], lane_width, bin_x)):
			peaks_x_r.append(peaks_x_r_temp[peaks[0]]) #pixel location of peak
			peaks_y_r.append(peaks_y_dict[peaks_x_r_temp[peaks[0]]]) #peaks_y_r_temp[peaks[0]])
	peaks_x_r_sorted=sorted(peaks_x_r)
	
	if(devel_info):
		f_peaks_found = open(temp_dir + '/peaks_found.txt', 'w')
		pf_i = 1
		for pf in peaks_found:
			f_peaks_found.write(str(pf_i) + "\t")
			pf_i += 1
			f_peaks_found.write(str(peaks_x_r_temp[pf[0]]) + "\t")
			for pf_ in pf:
				f_peaks_found.write(str(pf_) + "\t")
			
			f_peaks_found.write("\n")
		f_peaks_found.write("\n")
		pf_i = 1
		for pxr in peaks_x_r_sorted:
			f_peaks_found.write(str(pf_i) + "\t")
			pf_i += 1
			f_peaks_found.write(str(pxr) + "\n")
		f_peaks_found.close()
			
	#plotting the validated peaks - those that have be found to represent marker lanes
	
	if(devel_info):
		fig, (ax1) = plt.subplots(1,figsize=(6,6))
		ax1.plot(dfp.index,dfp['peak_detection_r'],c='r')
		ax1.plot(dfp.index,dfp['peak_detection_g'],c='g')
		ax1.scatter(peaks_x_r,peaks_y_r,c='r')
		ax1.set_xlim([0,len(dfp)])
		ax1.set_ylim([0,1.05*max(dfp.peak_detection_r)])
		fig.savefig(temp_dir+'/peaks.png',dpi=72,bbox_inches='tight')
		fig.clf()
		plt.close(fig)
		
	#finding/cropping the gels...
	max_gel_size=0
	for i in range(len(peaks_x_r_sorted)):
		scale_x__=peaks_x_r_sorted[i]*bin_x #midpoint of current marker lane (1st lane of gel we wish to cut)
		if (i+1<num_gels) and (i+1<len(peaks_x_r_sorted)): #not at the last lane
			scale_x___=peaks_x_r_sorted[i+1]*bin_x-scale_x__ #size of the region we should cut (size of the gel)
		else: #at the last lane
			scale_x___=max_gel_size #num_gels*scale_x-scale_x__
		if max_gel_size<scale_x___: #keeping track of max gel size found
			max_gel_size=scale_x___
		scale_x__-=lane_width #subtracting back to the beginning of the marker lane
		marker_offset=lane_width
		scale_x____=2*lane_width #size of a lane
		if scale_x__<0:
			scale_x____+=scale_x__
			scale_x__=0
			marker_offset=0
		scale_x___-=lane_width #subtracting back before the NEXT marker
		
		#crop the current gel
		if(devel_info):
			#the cropped gel image - version 0 - with full height
			os.system(convert_cmd + ' "' +temp_dir+'/one-row.tif" -crop '+str(scale_x___)+'x'+str(scale_y)+'+'+str(scale_x__)+'+0 "'+temp_dir+'/gel'+str(i)+'.tif"')
			if(devel_info):
				os.system(convert_cmd + ' "' +temp_dir+'/one-row_.tif" -crop '+str(scale_x___)+'x'+str(scale_y)+'+'+str(scale_x__)+'+0 "'+temp_dir+'/gel'+str(i)+'_.tif"')

		#finding top and bottom of the marker lane - cut off bands at top/bottom that aren't part of ladder
		
		#read the current ladder configuration from the labels file, set cur_ladder
		if 'Ladder' in labels.columns:
			labels_ladder = labels['Ladder'][i]
			
			if(type(labels_ladder) == type('')):
				labels_ladder = labels_ladder.split(',')
			elif(np.isnan(labels_ladder)):
				labels_ladder = []
			else:
				labels_ladder = str(labels_ladder)
				labels_ladder = labels_ladder.split(',')
		else:
			labels_ladder = []
		
		cur_ladder = []
		if(new_gel_format):
			cur_full_ladder = full_ladder_new_gels
			cur_display_ladder = display_ladder_new_gels
		else:
			cur_full_ladder = full_ladder
			cur_display_ladder = display_ladder
		for mass in cur_full_ladder:
			remove = False
			for rem_mass in labels_ladder:
				if(int(float(rem_mass)) == mass):
					remove = True
					break
			if(not remove):cur_ladder.append(mass)
			
		peaks_x_y = marker_peaks_lists[peaks_x_r_sorted[i]]
		
		#sort by intensity and cut off any beyond what is listed in ladder
		peaks_x_y = sorted(peaks_x_y, key=lambda x: x[1], reverse=True)
		peaks_x_sorted___ = []
		if(len(cur_ladder) < len(peaks_x_y)): len_ = len(cur_ladder)
		else: len_ = len(peaks_x_y)
		for i_v in range(len_):
			peaks_x_sorted___.append(peaks_x_y[i_v][0])
			
		#then sort by pixel top to bottom
		peaks_x_sorted___=np.array(sorted(peaks_x_sorted___))
		
		#peaks_x_ = marker_peaks_lists[peaks_x_r_sorted[i]][0]
		#peaks_x_sorted_=np.array(sorted(peaks_x_))
		#peaks_x_sorted___=peaks_x_sorted_[:]
		
		for l_i in range(len(cur_full_ladder)):
			if(cur_full_ladder[l_i] == cur_ladder[0]):
				break
		#l_i is the number of bands away from top band of 250.  we want to show a little above 250
		start_peak=0
		if(len(peaks_x_sorted___) < 2): top = 0
		else:
			top=peaks_x_sorted___[start_peak] - (l_i)*(peaks_x_sorted___[start_peak+1]-peaks_x_sorted___[start_peak]) - .75*(peaks_x_sorted___[start_peak+1]-peaks_x_sorted___[start_peak])
		if(top < 0): top = 0
		
		found_37 = False
		for l_i in range(len(cur_ladder)):
			if(cur_ladder[l_i] == 37):
				end_peak = l_i
				found_37 = True
				break
		if(not found_37 or end_peak > (len(peaks_x_sorted___)-1)):
			if(len(peaks_x_sorted___) < len(cur_ladder)): end_peak = len(peaks_x_sorted___)-1
			else: end_peak = len(cur_ladder)-1
		
		#l_i is the number of bands away from  band of 37  we want to show the band at 37, but not much further below
		bottom = peaks_x_sorted___[end_peak] + .75*(peaks_x_sorted___[end_peak]-peaks_x_sorted___[end_peak-1])
		
		#the cropped gel image - version 1
		os.system(convert_cmd + ' "' +temp_dir+'/one-row.tif" -crop '+str(scale_x___)+'x'+str(bottom-top)+'+'+str(scale_x__)+'+'+str(top)+' "'+temp_dir+'/gel'+str(i)+'-cropped.tif"')
		##
		if(devel_info):
			os.system(convert_cmd + ' "' +temp_dir+'/one-row_.tif" -crop '+str(scale_x___)+'x'+str(bottom-top)+'+'+str(scale_x__)+'+'+str(top)+' "'+temp_dir+'/gel'+str(i)+'-cropped_.tif"')
		##
		#read in cropped gel image as txt (y-axis collapsed)
		os.system(convert_cmd + ' "' +temp_dir+'/gel'+str(i)+'-cropped.tif" -scale '+str(int(scale_x___))+'x1! "'+temp_dir+'/gel'+str(i)+'-cropped.txt"')
		df__ = pd.read_table(temp_dir+'/gel'+str(i)+'-cropped.txt',header=None,skiprows=1,comment='#',sep='[,:()]',
				   converters={'r':p2f, 'g':p2f, 'b':p2f}, names=('x','y','e1','r','g','b','e2'))
		df__.index = df__.x
		df__=df__.drop(['x', 'y', 'e1','e2'], axis=1)
		
		os.unlink(temp_dir+'/gel'+str(i)+'-cropped.txt')
		
		#smoothing and background subtraction
		df__.r-=min(df__.r)
		df__.g-=min(df__.g)
		df__.r-=sorted(df__.r)[int(len(df__.r)*0.25)]
		df__.g-=sorted(df__.g)[int(len(df__.g)*0.25)]
		df__['r'][df__.r<0]=0
		df__['g'][df__.g<0]=0
		df__['background_g']=smooth(df__.g,11,'flat')
		df__['background_r']=smooth(df__.r,11,'flat')
		df__['g_']=df__.g-df__.background_g
		df__['r_']=df__.r-df__.background_r
		
		#
		df__['r_'][df__.r_<0]=0
		df__['g_'][df__.g_<0]=0
		
		#find peaks corresponding to the lanes of the gel
		if(new_way_gel_width):
			(min_gel_r,max_gel_r) = gel_range(df__.index,df__.r_)
			(min_gel_g,max_gel_g) = gel_range(df__.index,df__.g_)
			gel_width = max(max_gel_r,max_gel_g) - min(min_gel_r,min_gel_g)
			scale_x__ = scale_x__ + min(min_gel_r,min_gel_g)
			
			if((2*lane_width*3/4*8)>gel_width):
				gel_width = 2*lane_width*3/4*8
			elif((2*lane_width*8/7*8)<gel_width):
				gel_width = 2*lane_width*8/7*8
				
			if (i+1<num_gels) and (i+1<len(peaks_x_r_sorted)): 
				if(gel_width > scale_x___):
					gel_width = scale_x___
				
		else:
			x_r= df__.index[df__.index<0.95*len(df__)]
			y_r= df__.r_[df__.index<0.95*len(df__)]
			x_g= df__.index[df__.index<0.97*len(df__)]
			y_g= df__.g_[df__.index<0.97*len(df__)]
			(peaks_x_r,peaks_y_r)=find_peaks(x_r,y_r,8,11,int(scale_x/8*3/4)) # * 1/2 instead?? - it adds this to both sides of found peak !
			(peaks_x_g,peaks_y_g)=find_peaks(x_g,y_g,7,11,int(scale_x/8*3/4)) # * 1/2 instead??
			peaks_x_r=np.array(peaks_x_r)
			peaks_y_r=np.array(peaks_y_r)
			peaks_x_g=np.array(peaks_x_g)
			peaks_y_g=np.array(peaks_y_g)
			
			#deciding on the lane width
			peaks_x_r_sorted_=np.array(sorted(peaks_x_r))
			peaks_x_g_sorted=np.array(sorted(peaks_x_g))
			peaks_x_r_sorted_=peaks_x_r_sorted_[peaks_x_r_sorted_<0.93*len(df__)]
			peaks_x_g_sorted=peaks_x_g_sorted[peaks_x_g_sorted<0.96*len(df__)]
			if(len(peaks_x_g_sorted) > 1): lane_width_=np.mean(peaks_x_g_sorted[1:]-peaks_x_g_sorted[:-1]) #lane width -> min. peak separation
			else: lane_width_=2*lane_width
			if (len(peaks_x_g)>0 and (marker_offset+lane_width_*8)<max(peaks_x_g)+1.5*lane_width): #checks if lane width is not wide enough, ie. calculated width not reaching end of peaks (green)
				lane_width_=int((max(peaks_x_g)+1.5*lane_width-marker_offset)/8)
			if (len(peaks_x_r)>0 and (marker_offset+lane_width_*8)<max(peaks_x_r)+1.5*lane_width): #same as above for red
				lane_width_=int((max(peaks_x_r)+1.5*lane_width-marker_offset)/8)
			
			if (lane_width_<2*lane_width*3/4) or (2*lane_width*8/7<lane_width_): #checks if lane width too small/large as compared to standard (land_width (==14))
				if(len(peaks_x_r_sorted_) > 1):
					lane_width_=np.mean(peaks_x_r_sorted_[1:]-peaks_x_r_sorted_[:-1])
					if (lane_width_<2*lane_width*3/4) or (2*lane_width*8/7<lane_width_):
						lane_width_=2*lane_width
				else: lane_width_=2*lane_width
			if (i+1<num_gels) and (i+1<len(peaks_x_r_sorted)): #checks if calculated width of gel (based on lane width) will overrun the next gel's starting point
				if (marker_offset+lane_width_*8)>scale_x___:
					lane_width_=int((scale_x___-marker_offset)/8)
			gel_width = marker_offset+lane_width_*8
		
		#make the plots of the signal (red and green) and peaks found
		if(devel_info):
			fig, (ax1) = plt.subplots(1,figsize=(6,6))
			ax1.plot(df__.index,df__.r,c='r')
			ax1.plot(df__.index,df__.g,c='g')
			ax1.plot(df__.index,df__.background_r,c='gray')
			ax1.plot(df__.index,df__.background_g,c='black')
			if(not new_way_gel_width):
				ax1.scatter(peaks_x_r,peaks_y_r,c='r')
				ax1.scatter(peaks_x_g,peaks_y_g,c='g')
			ax1.set_xlim([0,len(df__.index)])
			ax1.set_ylim([0,1.05*max([max(df__.r),max(df__.g)])])
			
			fig.savefig(temp_dir+'/gel'+str(i)+'-lanes.png',dpi=72,bbox_inches='tight')
			fig.clf()
			plt.close(fig)
			
		######################################################################################################
		#now, we have the dimensions where we should draw the demarcation lines for this gel
		if(i < 10): gel_root = 'gel-0' + str(i)
		else: gel_root = 'gel-' + str(i)
		
		#convert gel_y_offset to the correct y offset since it varies for each row
		cur_offset = 0
		gel_offset = 0
		width_correction = 0
		while(cur_offset < num_y):
			if(scale_x__ <= (cur_offset+1)*true_width):
				if((scale_x__+gel_width) <= (cur_offset+1)*true_width):
					gel_offset = cur_offset
				else:
					if((cur_offset+1)*true_width-scale_x__ > (scale_x__+gel_width)-(cur_offset+1)*true_width):
						gel_offset = cur_offset
						width_correction = (scale_x__+gel_width)-(cur_offset+1)*true_width
					else:
						gel_offset = (cur_offset+1)
						scale_x__ = (cur_offset+1)*true_width+1
				break
			cur_offset += 1
		gel_x_offset = true_width*gel_offset
		if(new_gel_format):
			gel_y_offset = gel_rows[gel_offset]
		else:
			gel_y_offset = scale_y*gel_offset
		
		#save gel marking information
		gel_markers[gel_root] = [int(scale_x__-gel_x_offset), int(gel_width-width_correction), #,int(marker_offset+lane_width_*8-width_correction),
					 int(top+gel_y_offset),int(bottom-top)]
		if(devel_info):
			#the cropped gel image - version 2
			os.system(convert_cmd + ' "' +temp_dir+'/one-row.tif" -crop '+str(gel_width)+'x'+str(bottom-top)+'+'+str(scale_x__)+'+'+str(top)+' "'+temp_dir+'/gel'+str(i)+'-cropped_2.tif"')
			if(devel_info):
				os.system(convert_cmd + ' "' +temp_dir+'/one-row_.tif" -crop '+str(gel_width)+'x'+str(bottom-top)+'+'+str(scale_x__)+'+'+str(top)+' "'+temp_dir+'/gel'+str(i)+'-cropped_2_.tif"')
			
	if(new_gel_format):
		gel_markers['gel-format'] = 'new'
	else:
		gel_markers['gel-format'] = 'old'
	f = open(out_dir + '/_gel_marker_lines.json', 'w')
	json.dump(gel_markers, f)
	f.close()
	
	#delete temp directory
	if(not devel_info): shutil.rmtree(temp_dir)
		
def label_gels2(directory, labels_filename, annotation_filename, exposure_filename, im_dir, os_type, scale_x=272, scale_y=468):
	
	f = open(directory + '/_gel_marker_lines.json', 'r')
	gel_marker_info = json.load(f)
	f.close()
	
	if('gel-format' in gel_marker_info and gel_marker_info['gel-format'] == 'new'):
		new_gel_format = True
	else: new_gel_format = False
	
	if(new_gel_format):
		#scale_x*=.7
		scale_y = 180 #*=.5
		
		#removed, now using same annotation file for both
		#(head, tail) = os.path.split(annotation_filename)
		#tail = tail.replace(".png", "_new.png")
		#annotation_filename = head + '/' + tail
		
		
	date=datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
	out_dir = directory + '/' + 'labeled (' + date + ')'
	os.mkdir(out_dir)
	temp_dir = directory + '/' + '_labeled-' + date + '-' + 'TEMP'
	os.mkdir(temp_dir)
	
	#copy metadata file
	shutil.copy(labels_filename, out_dir + '/metadata.txt')
	
	#load exposure settings:
	exp_dict = {}
	try:
		f = open(exposure_filename, 'r')
		for line in f:
			line = line.strip()
			vals = line.split('\t')
			if(vals and vals[0]):
				exp_dict[vals[0]] = [vals[1], vals[2], vals[3], vals[4]]
		f.close()
	except IOError:
		pass
	
	if(os_type == 'WINDOWS'):
		os.chdir(im_dir)
		convert_cmd = 'convert'
	else:
		convert_cmd = im_dir + '/convert'
	
	file_list = glob.glob(directory + '/*.tif')
	labels = pd.read_table(labels_filename)
	num_rows_labels = len(labels.index)
	for fname in file_list:
		if(fname.startswith('_')): continue
		(head, tail) = os.path.split(fname)
		(root, ext) = os.path.splitext(tail)
		mo = re.search('gel-(\d\d).tif', tail)
		if(mo):
			i = int(mo.group(1))
		else:
			continue
		
		if(i >= num_rows_labels):
			continue
		
		if(os_type == 'WINDOWS'):
			batch_file = temp_dir + '/' + root + '.bat'
		else:
			batch_file = temp_dir + '/' + root + '.sh'
			
		orig_red_gel = head + '/_' + root + '-r.json'
		orig_green_gel = head + '/_' + root + '-g.json'
		
		red_gel_tif = temp_dir + '/_' + root + '-r.tif'
		red_gel = temp_dir + '/_' + root + '-r.jpg'
		green_gel_tif = temp_dir + '/_' + root + '-g.tif'
		green_gel = temp_dir + '/_' + root + '-g.jpg'
		
		red_gel_masses = temp_dir + '/_' + root + '-r_masses.jpg'
		green_gel_masses = temp_dir + '/_' + root + '-g_masses.jpg'
		red_gel_ann = temp_dir + '/_' + root + '-r_masses_ann.jpg'
		green_gel_ann = temp_dir + '/_' + root + '-g_masses_ann.jpg'
		temp_red_caption_fname = temp_dir + '/red_caption.jpg'
		temp_green_caption_fname = temp_dir + '/green_caption.jpg'
		red_gel_ann_cap = temp_dir + '/_' + root + '-r_masses_ann_cap.jpg'
		green_gel_ann_cap = temp_dir + '/_' + root + '-g_masses_ann_cap.jpg'
		temp_toplabel_fname = temp_dir + '/toplabel.jpg'
		red_gel_ann_cap_top = temp_dir + '/_' + root + '-r_masses_ann_cap_top.jpg'
		green_gel_ann_cap_top = temp_dir + '/_' + root + '-g_masses_ann_cap_top.jpg'
		
		cdi_num = str(labels['CDI#'][i])
		filter_ip = str(labels['Filter_IP'][i])
		filter_wb = str(labels['Filter_WB'][i])
			
		labels_filename_final_r = out_dir + '/' + cdi_num + '_' + filter_ip + '_IP.png'
		labels_filename_final_g = out_dir + '/' + cdi_num + '_' + filter_wb + '_WB.png'
		
		#create gel images, apply min/max pixel and mapping, and stretch the image -> jpg
		if(tail in exp_dict):
			(image_width, image_height, new_image_r) = it.load_and_filter(orig_red_gel, exp_dict[tail][0], exp_dict[tail][1])
			(image_width, image_height, new_image_g) = it.load_and_filter(orig_green_gel, exp_dict[tail][2], exp_dict[tail][3])
		else:
			(image_width, image_height, new_image_r) = it.load_and_filter(orig_red_gel, '-1', '-1')
			(image_width, image_height, new_image_g) = it.load_and_filter(orig_green_gel, '-1', '-1')
		io.imsave(red_gel_tif, new_image_r)
		os.system(convert_cmd + ' "' + red_gel_tif + '" -scale '+str(scale_x)+'x'+str(scale_y)+'! "' + red_gel + '"') 
		io.imsave(green_gel_tif, new_image_g)
		os.system(convert_cmd + ' "' + green_gel_tif + '" -scale '+str(scale_x)+'x'+str(scale_y)+'! "' + green_gel + '"')
		
		#start of command to add in the mass ladder labels on the left side
		
		#add in padding around image 
		os.system(convert_cmd + ' "' + red_gel + '" -background white -splice 100x0 "' + red_gel_masses + '"')
		os.system(convert_cmd + ' "' + green_gel + '" -background white -splice 100x0 "' + green_gel_masses + '"')
		os.system(convert_cmd + ' "' + red_gel_masses + '" -gravity east -background white -splice 75x0 "' + red_gel_masses + '"')
		os.system(convert_cmd + ' "' + green_gel_masses + '" -gravity east -background white -splice 75x0 "' + green_gel_masses + '"')
		
		#load the json markers file for the ladder information
		f_markers = open(directory + '/_' + root + '-markers.json', 'r')
		gel_marker_info = json.load(f_markers)
		f_markers.close()
		
		gel_markers = {}
		for marker in gel_marker_info:
			px = int(float(gel_marker_info[marker]))
			if(px >= 0): gel_markers[int(float(marker))] = px
			
		cur_ladder = []
		ladder_peaks = []
		for marker in sorted(gel_markers.keys(), reverse=True): 
		    cur_ladder.append(marker)
		    ladder_peaks.append(int(gel_markers[marker]))
		    
		cur_cmd = convert_cmd + ' "' + red_gel_masses + '" -font Arial -pointsize 18 '
		for k in range(0,len(cur_ladder)):
			this=float(ladder_peaks[k])
			cur_cmd += '-annotate +50+' + str(int(8+scale_y*(this/image_height))) + ' "' + str(cur_ladder[k]) + '" '
			cur_cmd += '-fill black -draw "rectangle 90,' + str(int(scale_y*(this/image_height))) + ' 104,' + str(int(4+(scale_y)*(this/image_height))) + '" '
		cur_cmd += '"' + red_gel_masses + '"'
		os.system(cur_cmd)
		
		cur_cmd = convert_cmd + ' "' + green_gel_masses + '" -font Arial -pointsize 18 '
		for k in range(0,len(cur_ladder)):
			this=float(ladder_peaks[k])
			#cur_cmd += '-annotate +50+' + str(8+(scale_y)*(this-top)/(bottom-top)) + ' "' + str(cur_ladder[k]) + '" '
			#cur_cmd += '-fill black -draw "rectangle 90,' + str((scale_y)*(this-top)/(bottom-top)) + ' 104,' + str(4+(scale_y)*(this-top)/(bottom-top)) + '" '
			cur_cmd += '-annotate +50+' + str(int(8+scale_y*(this/image_height))) + ' "' + str(cur_ladder[k]) + '" '
			cur_cmd += '-fill black -draw "rectangle 90,' + str(int(scale_y*(this/image_height))) + ' 104,' + str(int(4+scale_y*(this/image_height))) + '" '
		cur_cmd += '"' + green_gel_masses + '"'
		os.system(cur_cmd)
		
		#add arrows
		pred_mw = float(labels['Predicted Molecular weight'][i])
		this = 0
		if cur_ladder[0]+(cur_ladder[0]-cur_ladder[1]) > pred_mw:
			pos1=ladder_peaks[0]
			pos2=ladder_peaks[1]
			
			if cur_ladder[0] <= pred_mw:
				this=(np.log(pred_mw)-np.log(cur_ladder[0]))/(np.log(cur_ladder[0])-np.log(cur_ladder[1]))*(pos1-pos2)+pos1
			else:
				if cur_ladder[1] <= pred_mw:
					this=(np.log(pred_mw)-np.log(cur_ladder[1]))/(np.log(cur_ladder[0])-np.log(cur_ladder[1]))*(pos1-pos2)+pos2
				else:
					for k in range(0,len(cur_ladder)):
						if cur_ladder[k]<=pred_mw:
							pos1=ladder_peaks[k-1] 
							pos2=ladder_peaks[k] 
							this=(np.log(pred_mw)-np.log(cur_ladder[k]))/(np.log(cur_ladder[k-1])-np.log(cur_ladder[k]))*(pos1-pos2)+pos2
							break
			
		if this > 0:
			os.system(convert_cmd + ' "' + red_gel_masses + '" -fill black -draw "stroke black fill black path \'M 41,' + str(int(scale_y*(this/image_height))) + ' l -20,-8  +4,+8  -4,+8  +20,-8 z\'" "' + red_gel_masses + '"')
			os.system(convert_cmd + ' "' + green_gel_masses + '" -fill black -draw "stroke black fill black path \'M 41,' + str(int(scale_y*(this/image_height))) + ' l -20,-8  +4,+8  -4,+8  +20,-8 z\'" "' + green_gel_masses + '"')
			
		#add arrow (green only, at 53)
		pred_mw = 53.
		for k in range(0,len(cur_ladder)):
			if cur_ladder[k]<=pred_mw:
				pos1=ladder_peaks[k-1]
				pos2=ladder_peaks[k]
				this=(np.log(pred_mw)-np.log(cur_ladder[k]))/(np.log(cur_ladder[k-1])-np.log(cur_ladder[k]))*(pos1-pos2)+pos2
				break
		y_pos = int(scale_y*(this/image_height))
		#change 470-10 above to scale_y ? (468)
		os.system(convert_cmd + ' "' + green_gel_masses + '" -font Arial -pointsize 18 -annotate +420+' + str(y_pos+5) + ' "HC" -fill black -draw "line 390,' + str(y_pos) + ',418,' + str(y_pos) + '" -draw "stroke black fill black translate 380,' + str(y_pos) + ' rotate 180 scale .7,.7 path \'M 0,0 l -20,-8  +4,+8  -4,+8  +20,-8 z\'" "' + green_gel_masses + '"')
		
		#end of command - the mass ladder labels have been added
		
		#add annotation above lanes
		os.system(convert_cmd + ' "' + annotation_filename + '" "' + red_gel_masses + '" -gravity east -append "' + red_gel_ann + '"') 
		os.system(convert_cmd + ' "' + annotation_filename + '" "' + green_gel_masses + '" -gravity east -append "' + green_gel_ann + '"')
		
		#fill in doxycycline amounts for the annotation:  
		#use default or if given in metadata file, then use the amounts from there...
		#read in the density guidebox positions to get pixel position to place the amounts above each lane
		f = open(directory + '/_' + root + '_hdr_r.band_info.json', 'r') 
		band_info = json.load(f)
		f.close()
		
		label_variables = copy.deepcopy(default_label_variables)
		for label_var in label_variables.keys():
			found_label = ""
			for label in labels.columns:
				if(label.upper() == label_var):
					found_label = label
					break
			if(found_label):
				label_value = labels[found_label][i]
				if(type(label_value) == type('') or not np.isnan(label_value)):
					if(label_var == "DOXYCYCLINE"):
						label_value = label_value.split(',')
					if(label_value):
						label_variables[label_var] = label_value
			
		cur_red_cmd = convert_cmd + ' "' + red_gel_ann + '" -font Arial -pointsize 24 '
		cur_gr_cmd = convert_cmd + ' "' + green_gel_ann + '" -font Arial -pointsize 24 '
		draw_line_pos_v = [] #the bottom positions of the vertial lines, the top positions are +10 px from bottom
		draw_line_pos_v2 = [] #the bottom positions of the shorter vertial lines, the top positions are +5 px from bottom
		draw_line_pos_h_st = {} #the left positions of the horizontal lines
		draw_line_pos_h_end = {} #the right positions of the horizontal lines
		doxy_labels = label_variables["DOXYCYCLINE"]
		for k,amt in enumerate(doxy_labels):
			x_pos = (float(band_info[str(k+2)][0]) + float(band_info[str(k+2)][1])) / 2
			x_pos = int(scale_x*(x_pos/image_width))
			x_pos = (x_pos+155)-10
			if(k == 0):
				draw_line_pos_v.append((x_pos-5,145))
				draw_line_pos_h_st['1'] = (x_pos-5,135)
			if(k == 2):
				draw_line_pos_v.append((x_pos+20,145))
				draw_line_pos_h_end['1'] = (x_pos+20,135)
			if(k == 3):
				draw_line_pos_v.append((x_pos-5,50))
				draw_line_pos_h_st['3'] = (x_pos-5,40)
				draw_line_pos_v2.append((x_pos+10,145))
			if(k == 4):
				draw_line_pos_v.append((x_pos-5,145))
				draw_line_pos_h_st['2'] = (x_pos-5,135)
			if(k == 5):
				draw_line_pos_v.append((x_pos+20,145))
				draw_line_pos_h_end['2'] = (x_pos+20,135)
			if(k == 6):
				draw_line_pos_v.append((x_pos+20,50))
				draw_line_pos_h_end['3'] = (x_pos+20,40)
				draw_line_pos_v2.append((x_pos+10,145))
				
			amt = str(amt)
			amt = amt.strip()
			
			x_pos = x_pos + 20
			cur_red_cmd += '-annotate 270x270+' + str(x_pos) + '+205 "' + amt + '" '
			cur_gr_cmd += '-annotate 270x270+' + str(x_pos) + '+205 "' + amt + '" '
			
		cur_red_cmd +=  '"' + red_gel_ann + '"'
		cur_gr_cmd +=  '"' + green_gel_ann + '"'
		os.system(cur_red_cmd)
		os.system(cur_gr_cmd)
		
		#create the rest of the amounts labeling
		#(the part above the doxy amounts)
		#the lines:
		#convert annotation2.png -stroke black -strokewidth 3 -draw "line 50,150 50,140" annotation2_.png
		cur_red_cmd = convert_cmd + ' "' + red_gel_ann + '" -stroke black -strokewidth 3 '
		cur_gr_cmd = convert_cmd + ' "' + green_gel_ann + '" -stroke black -strokewidth 3 '
		for pos in draw_line_pos_v:
			cur_red_cmd += '-draw "line ' + str(pos[0]) + ',' + str(pos[1]) + ' ' + str(pos[0]) + ',' + str(pos[1]-10) + '" '
			cur_gr_cmd += '-draw "line ' + str(pos[0]) + ',' + str(pos[1]) + ' ' + str(pos[0]) + ',' + str(pos[1]-10) + '" '
		
		for pos in draw_line_pos_v2:
			cur_red_cmd += '-draw "line ' + str(pos[0]) + ',' + str(pos[1]) + ' ' + str(pos[0]) + ',' + str(pos[1]-5) + '" '
			cur_gr_cmd += '-draw "line ' + str(pos[0]) + ',' + str(pos[1]) + ' ' + str(pos[0]) + ',' + str(pos[1]-5) + '" '
		
		for line in draw_line_pos_h_st.keys():
			pos_st = draw_line_pos_h_st[line]
			pos_end = draw_line_pos_h_end[line]
			cur_red_cmd += '-draw "line ' + str(pos_st[0]) + ',' + str(pos_st[1]) + ' ' + str(pos_end[0]) + ',' + str(pos_end[1]) + '" '
			cur_gr_cmd += '-draw "line ' + str(pos_st[0]) + ',' + str(pos_st[1]) + ' ' + str(pos_end[0]) + ',' + str(pos_end[1]) + '" '
		
		cur_red_cmd +=  '"' + red_gel_ann + '"'
		cur_gr_cmd +=  '"' + green_gel_ann + '"'
		os.system(cur_red_cmd)
		os.system(cur_gr_cmd)
		
		#the text:
		input_perc = label_variables["INPUT-PERCENT"]
		if(int(input_perc) == float(input_perc)):
			input_perc = int(input_perc)
		cur_red_cmd = convert_cmd + ' "' + red_gel_ann + '" -font Arial -pointsize 26 '
		cur_gr_cmd = convert_cmd + ' "' + green_gel_ann + '" -font Arial -pointsize 26 '
		#20%
		mid = (draw_line_pos_v[0][0] + draw_line_pos_v[1][0]) / 2
		cur_red_cmd += '-annotate 0x0+' + str(mid-25) + '+100 "' + str(input_perc) + '%" '
		cur_gr_cmd += '-annotate 0x0+' + str(mid-25) + '+100 "' + str(input_perc) + '%" '
		#Input
		cur_red_cmd += '-annotate 0x0+' + str(mid-30) + '+125 "Input" '
		cur_gr_cmd += '-annotate 0x0+' + str(mid-30) + '+125 "Input" '
		#IP
		mid = (draw_line_pos_v[2][0] + draw_line_pos_v[5][0]) / 2
		cur_red_cmd += '-annotate 0x0+' + str(mid-12) + '+35 "IP" '
		cur_gr_cmd += '-annotate 0x0+' + str(mid-12) + '+35 "IP" '
		#CDI Ab
		mid = (draw_line_pos_v[3][0] + draw_line_pos_v[4][0]) / 2
		cur_red_cmd += '-annotate 270x270+' + str(mid+10) + '+130 "CDI Ab" '
		cur_gr_cmd += '-annotate 270x270+' + str(mid+10) + '+130 "CDI Ab" '
		#IgG
		mid = draw_line_pos_v2[0][0]
		cur_red_cmd += '-annotate 270x270+' + str(mid+10) + '+130 "IgG" '
		cur_gr_cmd += '-annotate 270x270+' + str(mid+10) + '+130 "IgG" '
		#FLAG
		mid = draw_line_pos_v2[1][0]
		cur_red_cmd += '-annotate 270x270+' + str(mid+10) + '+130 "FLAG" ' 
		cur_gr_cmd += '-annotate 270x270+' + str(mid+10) + '+130 "FLAG" '
		
		cur_red_cmd +=  '"' + red_gel_ann + '"'
		cur_gr_cmd +=  '"' + green_gel_ann + '"'
		os.system(cur_red_cmd)
		os.system(cur_gr_cmd)
		
		#create/add caption -  red
		gene_name = str(labels['Gene name'][i])
		acession = str(labels['Acession number'][i])
		caption_text_red1_ = caption_text_red1.replace("HeLa", label_variables["CELL-LINE"])
		caption_text = (caption_text_red1_ + gene_name + ' (' + acession + ')' + 
				caption_text_red2 + gene_name + ' (cloneID# ' + cdi_num + ')' +
				caption_text_red3) #+ labels['Gene name'][i] + ' (Catalog #' + cdi_num + ')' +
				#caption_text4 + labels['Gene name'][i] + caption_text5)
		os.system(convert_cmd + ' -font Arial -pointsize 21 -size 560x -gravity west caption:"' + caption_text + '" "' + temp_red_caption_fname + '"') #create caption
		os.system(convert_cmd + ' "' + temp_red_caption_fname + '" -background white -splice 0x20 "' + temp_red_caption_fname + '"') #space top of caption
		
		#create/add caption -  green
		caption_text_green1_ = caption_text_green1.replace("HeLa", label_variables["CELL-LINE"])
		caption_text = (caption_text_green1_ + gene_name + ' (' + acession + ')' + 
				caption_text_green2 + gene_name + ' (cloneID# ' + cdi_num + ')' +
				caption_text_green3 + gene_name + ' (cloneID# ' + cdi_num + ')' +
				caption_text_green4) # + labels['Gene name'][i] + caption_text5)
		os.system(convert_cmd + ' -font Arial -pointsize 21 -size 560x -gravity west caption:"' + caption_text + '" "' + temp_green_caption_fname + '"') #create caption
		os.system(convert_cmd + ' "' + temp_green_caption_fname + '" -background white -splice 0x20 "' + temp_green_caption_fname + '"') #space top of caption
		
		#fix captions by addig space so they are the same size
		red_cap_img = io.imread(temp_red_caption_fname)
		gr_cap_img = io.imread(temp_green_caption_fname)
		if(len(red_cap_img) > len(gr_cap_img)):
			#add space to green
			to_add = len(red_cap_img) - len(gr_cap_img)
			os.system(convert_cmd + ' "' + temp_green_caption_fname + '" -gravity south -background white -splice 0x' + str(to_add) + ' "' + temp_green_caption_fname + '"')
		elif(len(gr_cap_img) > len(red_cap_img)):
			#add space to red
			to_add = len(gr_cap_img) - len(red_cap_img)
			os.system(convert_cmd + ' "' + temp_red_caption_fname + '" -gravity south -background white -splice 0x' + str(to_add) + ' "' + temp_red_caption_fname + '"')
		
		#add fixed captions to red and green
		os.system(convert_cmd + ' "' + red_gel_ann + '" "' + temp_red_caption_fname + '" -gravity west -append "' + red_gel_ann_cap + '"') #add caption to bottom of gel image		
		os.system(convert_cmd + ' "' + green_gel_ann + '" "' + temp_green_caption_fname + '" -gravity west -append "' + green_gel_ann_cap + '"') #add caption to bottom of gel image		
		
		#create/add top label - red #label
		toplabel_text = 'Anti-FLAG\\n(' + gene_name + ')'
		os.system(convert_cmd + ' -font Arial -pointsize 36 -size 560x -gravity Center caption:"' + toplabel_text + '" "' + temp_toplabel_fname + '"') #create top label
		os.system(convert_cmd + ' "' + temp_toplabel_fname + '" "' + red_gel_ann_cap + '" -append "' + red_gel_ann_cap_top + '"') #add top label to image
		
		#create/add top label - green
		toplabel_text = 'Anti-' + gene_name + '\\n(CloneID#' + cdi_num + ')'
		os.system(convert_cmd + ' -font Arial -pointsize 36 -size 560x -gravity Center caption:"' + toplabel_text + '" "' + temp_toplabel_fname + '"') #create top label
		os.system(convert_cmd + ' "' + temp_toplabel_fname + '" "' + green_gel_ann_cap + '" -append "' + green_gel_ann_cap_top + '"') #add top label to image		
		
		#copy to final folder
		shutil.copy(red_gel_ann_cap_top, labels_filename_final_r)
		shutil.copy(green_gel_ann_cap_top, labels_filename_final_g)
		
	#create zip file containing labeled gels
	my_zip = zipfile.ZipFile(out_dir + '/labeled_gels.zip', 'w')
	flist = glob.glob(out_dir + '/*.png')
	for f in flist:
		#open and save again with skimage since image magick png file is not readable by windows photoshop
		img = io.imread(f)
		io.imsave(f, img)
		my_zip.write(f)
	my_zip.close()
		
	#delete temp directory
	if(not devel_info): shutil.rmtree(temp_dir)
	
	return out_dir

