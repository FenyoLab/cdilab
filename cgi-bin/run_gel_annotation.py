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

import sys
import tifffile as tf
import gel_annotation as ga
import os
import subprocess
import pandas as pd
import re
import json
import image_tools as it
import numpy as np
import glob
import shutil
from datetime import datetime

num_lanes_per_gel = '8'

def make_density_file(head, gel_name, gel_root):
    #load the labels file for the predicted mol weight of the bands used for density analysis
    #read labels file and get the MW's where the bands of interest are located
    labels = pd.read_table(head + '/_labels.txt')
    
    #load the json markers file for the ladder information
    f = open(head + '/_' + gel_name + '-markers.json', 'r')
    gel_marker_info = json.load(f)
    f.close()
    
    cur_ladder = []
    ladder_peaks = []
    gel_markers = {}
    for marker in gel_marker_info:
        gel_markers[int(float(marker))] = int(float(gel_marker_info[marker]))
        
    for marker in sorted(gel_markers.keys(), reverse=True): 
        cur_ladder.append(marker)
        ladder_peaks.append(int(gel_markers[marker]))
        
    #locate pixel position of the pred mol weight on the gel based on ladder info
    #locate density rectangle on the image, using peaks found and ladder
    gel_i = int(gel_name.replace('gel-', ''))
    pred_mw = float(labels['Predicted Molecular weight'][gel_i])
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
                    
    #create the initial density analysis json file
    #open gel hdr file for finding signal for each band
    df = pd.read_table(head + "/" + gel_root, header=None, skiprows=1, comment='#', sep='[,:()]')
    df=df.drop([2,4,5,6], axis=1)
    df.columns=['x','y','signal']
    df_image = df.pivot(index='x', columns='y', values='signal')
    image_width = len(df_image)
    
    #create a file (_gel-xx_hdr.bands.txt) for each gel with: lane number, x_lane_start, x_lane_end, pred_mw, actual_mw, y_band_start, y_band_end, signal, is_checked
    band_info = {}
    for j in range(1,int(num_lanes_per_gel)+1):
        band_info[j] = ['-1','-1',str(pred_mw),'-1','-1','-1','-1','0']
    
    #set band st/end y-values
    band_height = 6
    for j in range(2,int(num_lanes_per_gel)+1):
        band_info[j][3] = '0'
        band_info[j][4] = str(int(this-.5*band_height))
        band_info[j][5] = str(int(this+.5*band_height))
        
        #calculating sum separately using hdr gel image
        #use a background subtraction technique to match ImageStudio 'background'
        band_info[j][7] = '1' 
    
    #set band st/end x-values, using the lane start and end, but correcting for slanted lanes
    lanes_file = open(head + '/' + gel_root.replace('.txt','.log.txt'), 'r')
    for line in lanes_file:
        mo = re.search(r"Lane (\d) start: (\d+),(\d+) (\d+),(\d+) \(x = (\d+), i = (-?\d)\)", line)
        index = 0
        if(not mo):
            mo = re.search(r"Lane (\d) end  : (\d+),(\d+) (\d+),(\d+) \(x = (\d+), i = (-?\d)\)", line)
            index = 1
            if(not mo): continue
        lane_n = int(mo.group(1))
        i_value = int(mo.group(7))
        if(band_info[lane_n][4] != '-1'):
            band_pos_mult = float(band_info[lane_n][4])/float(mo.group(5)) # band-st-pos/gel-height
            add_to_band = abs(int(mo.group(2)) - int(mo.group(4))) #diff between st/end of lane start line or end line
            if(i_value < 0): #slanted forward
                band_info[lane_n][index] = str(int(mo.group(4)) + int( add_to_band * (1-band_pos_mult) ))
            elif(i_value > 0): #slanted backward
                band_info[lane_n][index] = str(int(mo.group(2)) + int( add_to_band * band_pos_mult ))
            else:
                band_info[lane_n][index] = mo.group(2)
        else: band_info[lane_n][index] = mo.group(2)
        
    #we want all lane width to be the same so take the average that's found above and use the start values as above, forcing atleast 1 pixel in between lanes
    ave_width = 0
    for j in range(2,int(num_lanes_per_gel)+1):
        ave_width += int(band_info[j][1])-int(band_info[j][0]);
    ave_width = int(ave_width/int(num_lanes_per_gel))
    
    #now we have all band rect info, get signal for each band
    for j in range(2,int(num_lanes_per_gel)+1):
        band_info[j][6] = str(it.get_signal(df_image, int(band_info[j][0]), int(band_info[j][1]), int(band_info[j][4]), int(band_info[j][5])))
        
        #fix lane widths to all be the same
        end_band_pixel = int(band_info[j][0])+ave_width
        band_info[j][1] = str(end_band_pixel)
    
    #save information to json file
    f = open(head + '/' + gel_root.replace('.txt', '.band_info.json'), 'w')
    json.dump(band_info, f)
    f.close()

#########################################################################################################################################
logfile = False
#x = 5/0
try:

    if(len(sys.argv) == 1): function = 'test'
    else: function = sys.argv[1]
    
    
    if(function == 'mark_collage'):
        
        #split up hdri tiff from ImageStudio into it's 5 tiff files, saving only the first one
        #red channel
        tif = tf.TiffFile(sys.argv[2])
        (head,tail) = os.path.split(sys.argv[2])
        
        try:
            logfile = open(head + '/run-log.txt', 'a')
            date=datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
            logfile.write("(" + date + ") function call == " + str(sys.argv) + "\n")
        except IOError as e:
            pass
        
        (base,ext) = os.path.splitext(tail)
        hdri_file_r = head + '/_HDRI-page-1-r.tif'
        tf.imsave(hdri_file_r, tif[0].asarray())
        tif.close()
        
        #green channel
        tif = tf.TiffFile(sys.argv[3])
        (head,tail) = os.path.split(sys.argv[3])
        (base,ext) = os.path.splitext(tail)
        hdri_file_g = head + '/_HDRI-page-1-g.tif'
        tf.imsave(hdri_file_g, tif[0].asarray())
        tif.close()
        
        if(sys.argv[8] == '1'): new_gel_format = True
        else: new_gel_format = False
        #call mark_collage to create json files that will mark the lane boundaries
        ga.mark_collage(new_gel_format, hdri_file_r, hdri_file_g, sys.argv[4], sys.argv[9], sys.argv[10], num_gels=int(sys.argv[5]),num_x=int(sys.argv[6]),num_y=int(sys.argv[7]))
        
    elif(function == 'clip_and_mark_gels'): 
        (head, tail) = os.path.split(sys.argv[2])
        
        try:
            logfile = open(head + '/run-log.txt', 'a')
            date=datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
            logfile.write("(" + date + ") function call == " + str(sys.argv) + "\n")
        except IOError as e:
            pass
        
        #call clip_and_mark_gels, which will use the json information to clip the gels and locate
        #the marker lane and the bands.  The pixel positions of the bands for each gel will be saved to a json
        num_rows_metadata = ga.clip_and_mark_gels(sys.argv[2], sys.argv[3], head + '/_HDRI-page-1-r.tif', head + '/_HDRI-page-1-g.tif', head + '/_labels.txt', sys.argv[5], sys.argv[6])
        
        #obtain lane demarcations (find_lane_boundaries) and then use the marker lane info to position the rectangles for density analysis
        #glob to get gel files
        gel_choices = sys.argv[3]
        gel_choices = gel_choices.split(',')
        file_list = glob.glob(head + '/gel-*.tif')
        for gel_id in gel_choices:
            gel_i = int(gel_id)
            if(len(gel_id) == 1):
                    gel_id = 'gel-0' + gel_id
            else:
                    gel_id = 'gel-' + gel_id
                        
            if(gel_i >= num_rows_metadata):
                continue
            
            gel_root = '_' + gel_id + '_hdr_r.txt'
            
            subprocess.check_call(["perl", sys.argv[4] + "/find_lane_boundaries2.pl", head + "/" + gel_root, num_lanes_per_gel, sys.argv[5]]) 
            
            #set up an initial file with the sum of intensity over the default rectangles drawn on the image
            #user will adjust and re-save through the interface
            make_density_file(head, gel_id, gel_root)
            
    elif(function == 'label_gels2'):
        head = sys.argv[2]
        
        try:
            logfile = open(head + '/run-log.txt', 'a')
            date=datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
            logfile.write("(" + date + ") function call == " + str(sys.argv) + "\n")
        except IOError as e:
            pass
        
        ga.label_gels2(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])
        
    else:
        print 'test: ' + sys.version
        if(len(sys.argv) > 1): print sys.argv[1]
except ValueError as e:
    if(logfile):
        logfile.write("Key error: {0}".format(e.message) + "\n")
        logfile.close()
    raise
except KeyError as e:
    if(logfile):
        logfile.write("Key error: {0}".format(e.message) + "\n")
        logfile.close()
    raise
except IOError as e:
    if(logfile):
        logfile.write("I/O error({0}): {1}".format(e.errno, e.strerror) + "\n")
        logfile.close()
    raise
#except CalledProcessError as e:
#    if(logfile):
#        logfile.write("CalledProcessError({0}): {1}".format(e.returncode, e.cmd) + "\n")
#        logfile.close()
#    raise
except:
    if(logfile):
        logfile.write( "Unexpected error:" + str(sys.exc_info()[0]) + "\n")
        logfile.close()
    raise

if(logfile):
    logfile.close()