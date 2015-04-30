#!/local/apps/python/2.7.7/bin/python

#'mark_collage' 'C:/CDI Labs/Data/New Test-Folder/Test-MARK (2014-12-29-09.34.05)/red-green-4.tif.tiff' 'C:/CDI Labs/Data/New Test-Folder/Test-MARK (2014-12-29-09.34.05)/0000437_01_700.TIF' 'C:/CDI Labs/Data/New Test-Folder/Test-MARK (2014-12-29-09.34.05)/0000437_01_800.TIF' 'C:/CDI Labs/Data/New Test-Folder/Test-MARK (2014-12-29-09.34.05)/_labels.txt' '12' '5' '3' 'C:/Projects/Boeke/cgi-bin'
#'mark_collage' 'C:/CDI Labs/Data/New Test-Folder/Test-MARK-2 (2015-01-02-11.25.03)/red-green-5.tif.tif' 'C:/CDI Labs/Data/New Test-Folder/Test-MARK-2 (2015-01-02-11.25.03)/0000436_01_700.TIF' 'C:/CDI Labs/Data/New Test-Folder/Test-MARK-2 (2015-01-02-11.25.03)/0000436_01_800.TIF' 'C:/CDI Labs/Data/New Test-Folder/Test-MARK-2 (2015-01-02-11.25.03)/_labels.txt' '12' '5' '3'
#'clip_and_mark_gels' 'C:/CDI Labs//Data/New Test-Folder/Test-Mark-4 (2015-01-05-09.37.55)/_gel_marker_lines.json' 'C:/Projects/Boeke/cgi-bin'
#'label_gels2' 'C:/CDI Labs/Data/New Test-Folder/Test-Mark-4 (2015-01-05-09.37.55)' 'C:/CDI Labs/Data/New Test-Folder/Test-Mark-4 (2015-01-05-09.37.55)//_labels.txt' 'C:/Projects/Boeke/cgi-bin/annotation2.png' 'C:/CDI Labs/Data/New Test-Folder/Test-Mark-4 (2015-01-05-09.37.55)/_exposure.txt'
#'mark_collage' 'C:/CDI Labs/Data/Test-Version-2/3-29-2-NoLadderMetadataColumn (2015-01-23-11.59.30)/red-green-4.tif.tiff' 'C:/CDI Labs/Data/Test-Version-2/3-29-2-NoLadderMetadataColumn (2015-01-23-11.59.30)/0000437_01_700.TIF' 'C:/CDI Labs/Data/Test-Version-2/3-29-2-NoLadderMetadataColumn (2015-01-23-11.59.30)/0000437_01_800.TIF' 'C:/CDI Labs/Data/Test-Version-2/3-29-2-NoLadderMetadataColumn (2015-01-23-11.59.30)/_labels.txt' '12' '5' '3'
#'mark_collage' 'C:/CDI Labs/Data/New Gels/8-5-14-1_red-green-2 (2015-02-04-10.46.55)/red-green-2.tif' 'C:/CDI Labs/Data/New Gels/8-5-14-1_red-green-2 (2015-02-04-10.46.55)/0000579_02_700.TIF' 'C:/CDI Labs/Data/New Gels/8-5-14-1_red-green-2 (2015-02-04-10.46.55)/0000579_02_800.TIF' 'C:/CDI Labs/Data/New Gels/8-5-14-1_red-green-2 (2015-02-04-10.46.55)/_labels.txt' '42' '6' '7'
#'clip_and_mark_gels' 'C:/CDI Labs/Data/New Gels/Test-from site - NEW (2015-02-17-09.41.59)/_gel_marker_lines.json' 'C:/Projects/Boeke/cgi-bin'
#'label_gels2' 'C:\CDI Labs\Data\New Gels\8-5-14-1-red_green-2-retry (2015-02-06-16.05.54)' 'C:\CDI Labs\Data\New Gels\8-5-14-1-red_green-2-retry (2015-02-06-16.05.54)/_labels.txt' 'C:/Projects/Boeke/cgi-bin/annotation2.png' 'C:\CDI Labs\Data\New Gels\8-5-14-1-red_green-2-retry (2015-02-06-16.05.54)/_exposure.txt'
#'mark_collage' 'C:/CDI Labs/Data/New Gels/Test from site - 3 (2015-02-17-12.42.38)/red-green.tif' 'C:/CDI Labs/Data/New Gels/Test from site - 3 (2015-02-17-12.42.38)/0000704_01_700.TIF' 'C:/CDI Labs/Data/New Gels/Test from site - 3 (2015-02-17-12.42.38)/0000704_01_800.TIF' 'C:/CDI Labs/Data/New Gels/Test from site - 3 (2015-02-17-12.42.38)/_labels.txt' '24' '6' '4' '1'
#'mark_collage' 'C:/CDI Labs/Data/New Gels/Test from site - 4 (2015-02-17-13.47.00)/red-green1.tif' 'C:/CDI Labs/Data/New Gels/Test from site - 4 (2015-02-17-13.47.00)/0000707_02_700.TIF' 'C:/CDI Labs/Data/New Gels/Test from site - 4 (2015-02-17-13.47.00)/0000707_02_800.TIF' 'C:/CDI Labs/Data/New Gels/Test from site - 4 (2015-02-17-13.47.00)/_labels.txt' '24' '6' '4' '1'
#'mark_collage' 'C:/CDI Labs/Data/New Gels/2-17-2015-RETRY-2 (2015-04-27-10.02.52)/red-green-3.tif.tif' 'C:/CDI Labs/Data/New Gels/2-17-2015-RETRY-2 (2015-04-27-10.02.52)/0000773_01_700.TIF' 'C:/CDI Labs/Data/New Gels/2-17-2015-RETRY-2 (2015-04-27-10.02.52)/0000773_01_800.TIF' 'C:/CDI Labs/Data/New Gels/2-17-2015-RETRY-2 (2015-04-27-10.02.52)/_labels.txt' '23' '6' '4' '1'
 
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

num_lanes_per_gel = '8'
#exit(1)

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
        gel_markers[int(marker)] = int(gel_marker_info[marker])
        
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

if(len(sys.argv) == 1): function = 'test'
else: function = sys.argv[1]

if(function == 'mark_collage'):
    
    #rename collage file
    coll_filename = sys.argv[2]
    (head, tail) = os.path.split(coll_filename)
    shutil.copy(coll_filename, head + '/Gel_Collage.tif')
    #os.rename(coll_filename, head + '/Gel_Collage.tif')
    coll_filename = head + '/Gel_Collage.tif'
    
    #split up hdri tiff from ImageStudio into it's 5 tiff files, saving only the first one
    #red channel
    tif = tf.TiffFile(sys.argv[3])
    (head,tail) = os.path.split(sys.argv[3])
    (base,ext) = os.path.splitext(tail)
    hdri_file_r = head + '/_HDRI-page-1-r.tif'
    tf.imsave(hdri_file_r, tif[0].asarray())
    tif.close()
    
    #green channel
    tif = tf.TiffFile(sys.argv[4])
    (head,tail) = os.path.split(sys.argv[4])
    (base,ext) = os.path.splitext(tail)
    hdri_file_g = head + '/_HDRI-page-1-g.tif'
    tf.imsave(hdri_file_g, tif[0].asarray())
    tif.close()
    
    if(sys.argv[9] == '1'): new_gel_format = True
    else: new_gel_format = False
    #call mark_collage to create json files that will mark the lane boundaries
    ga.mark_collage(new_gel_format, coll_filename, sys.argv[5],num_gels=int(sys.argv[6]),num_x=int(sys.argv[7]),num_y=int(sys.argv[8]))
    
elif(function == 'clip_and_mark_gels'): 
    
    (head, tail) = os.path.split(sys.argv[2])
    
    #call clip_and_mark_gels, which will use the json information to clip the gels and locate
    #the marker lane and the bands.  The pixel positions of the bands for each gel will be saved to a json
    ga.clip_and_mark_gels(sys.argv[2], head + '/Gel_Collage.tif', head + '/_HDRI-page-1-r.tif',
                          head + '/_HDRI-page-1-g.tif', head + '/_labels.txt')
    
    #obtain lane demarcations (find_lane_boundaries) and then use the marker lane info to position the rectangles for density analysis
    #glob to get gel files
    file_list = glob.glob(head + '/gel-*.tif')
    for gel_file in file_list:
        (head, tail) = os.path.split(gel_file)
        (gel_name, ext) = os.path.splitext(tail)
        gel_root = '_' + gel_name + '_hdr_r.txt'
        
        subprocess.check_call(["perl", sys.argv[3] + "/find_lane_boundaries2.pl", head + "/" + gel_root, num_lanes_per_gel]) 
        
        #set up an initial file with the sum of intensity over the default rectangles drawn on the image
        #user will adjust and re-save through the interface
        make_density_file(head, gel_name, gel_root)
#THIS FUNCTION NO LONGER USED IN VERSION 2        
elif(function == 'split_collage'):
    #first, split up hdri tiff from ImageStudio into it's 5 tiff files, saving only the first one
    
    #red channel
    tif = tf.TiffFile(sys.argv[3])
    (head,tail) = os.path.split(sys.argv[3])
    (base,ext) = os.path.splitext(tail)
    hdri_file_r = head + '/_' + base + '-page-1-r' + ext
    tf.imsave(hdri_file_r, tif[0].asarray())
    tif.close()
    
    #green channel
    tif = tf.TiffFile(sys.argv[4])
    (head,tail) = os.path.split(sys.argv[4])
    (base,ext) = os.path.splitext(tail)
    hdri_file_g = head + '/_' + base + '-page-1-g' + ext
    tf.imsave(hdri_file_g, tif[0].asarray())
    tif.close()
    
    #read labels file and get the MW's where the bands of interest are located
    labels = pd.read_table(sys.argv[5])
    
    #then, call split_collage to split up the gels
    ga.split_collage(sys.argv[2],hdri_file_r, hdri_file_g,sys.argv[5],num_gels=int(sys.argv[6]),num_x=int(sys.argv[7]),num_y=int(sys.argv[8]))
    
    #then call to find_lane_boundaries and find_lane_masses fore each gel file
    num_gels = int(sys.argv[6])
    for i in range(num_gels):
        if(i < 10): gel_name = '_gel-0' + str(i)
        else: gel_name = '_gel-' + str(i)
        gel_root = gel_name + '_hdr_r.txt'
        if(not os.path.isfile(head + '/' + gel_name + '.txt')): continue
        
        subprocess.check_call(["perl", sys.argv[9] + "/find_lane_boundaries2.pl", head + "/" + gel_root, num_lanes_per_gel])
        
        #this version does not call find_lane_masses, but just draws the rectangles across the image at the predicted molecular weight position
        #read in some saved info from the gel separation that we need for the rectangles
        info_file = open(head + '/' + gel_name + '.txt', 'r')
        peaks_x_sorted___ = info_file.readline().strip().rstrip(',').split(',')
        for j, p in enumerate(peaks_x_sorted___): peaks_x_sorted___[j] = int(p)
        #ladder_type = int(info_file.readline().strip())
        start_peak = int(info_file.readline().strip())
        top = float(info_file.readline().strip())
        bottom = float(info_file.readline().strip())
                
        #read the current ladder configuration from the labels file, set cur_ladder
        full_ladder = (250,150,100,75,50,37,25,20,15,10) #(250,150,100,75,50,37)
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
            
        
            
        ladder = []
        for mass in full_ladder:
                remove = False
                for rem_mass in labels_ladder:
                        if(int(float(rem_mass)) == mass):
                                remove = True
                                break
                if(not remove):ladder.append(mass)
                        
        pred_mw = float(labels['Predicted Molecular weight'][i])
        found_arrow = 0
        this = 0
        if ladder[0]+(ladder[0]-ladder[1]) > pred_mw:
                pos1=peaks_x_sorted___[start_peak]
                pos2=peaks_x_sorted___[start_peak+1]
                        
                if ladder[0] <= pred_mw:
                        this=(np.log(pred_mw)-np.log(ladder[0]))/(np.log(ladder[0])-np.log(ladder[1]))*(pos1-pos2)+pos1
                else:
                        if ladder[1] <= pred_mw:
                                this=(np.log(pred_mw)-np.log(ladder[1]))/(np.log(ladder[0])-np.log(ladder[1]))*(pos1-pos2)+pos2
                        else:
                                for k in range(0,len(ladder)):
                                        if (found_arrow==0) and (ladder[start_peak+k]<=pred_mw):
                                                found_arrow=1
                                                pos1=peaks_x_sorted___[start_peak+k-1]
                                                pos2=peaks_x_sorted___[start_peak+k]
                                                this=(np.log(pred_mw)-np.log(ladder[k]))/(np.log(ladder[k-1])-np.log(ladder[k]))*(pos1-pos2)+pos2
        if(this > 0):
            this = this-top; 
            
        #open gel hdr file for finding signal for each band
        df = pd.read_table(head + "/" + gel_root,header=None,skiprows=1,comment='#',sep='[,:()]')
        df=df.drop([2,4,5,6], axis=1)
        df.columns=['x','y','signal']
        df_image = df.pivot(index='x', columns='y', values='signal')
        image_width = len(df_image)
        
        #XXXmatch up MW's with the mass from '_gel-xx_hdr.lane-details.y', and
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
            
            #Not using sum from find_lane_masses.pl, instead calculating it separately using hdr gel image
            #Reason - I want to use a different background subtraction technique - to match ImageStudio 'background'
            #band_info[j][6] = str(bands['sum'][min_k])
            band_info[j][7] = '1' #checked == 1
        
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
            #band_info[lane_n][index] = str(min(int(mo.group(2)), int(mo.group(4))))
            
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
            #don't do this!  it will just change the lane width of the bands, which we don't want.  allow overlap and image overrun
            #it will be ignored in the signal calculation
            #if(j == int(num_lanes_per_gel)):
            #    if(end_band_pixel >= image_width):
            #        end_band_pixel = image_width-1
            #else:
            #    if(int(band_info[j+1][0]) <= end_band_pixel):
            #        end_band_pixel = int(band_info[j+1][0])-1
            band_info[j][1] = str(end_band_pixel)
        
        #save information to json file
        f = open(head + '/' + gel_root.replace('.txt', '.band_info.json'), 'w')
        json.dump(band_info, f)
        f.close()
   
elif(function == 'label_gels2'):
    
    ga.label_gels2(sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])
else:
    print 'test: ' + sys.version
    if(len(sys.argv) > 1): print sys.argv[1]