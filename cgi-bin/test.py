#!C:\WinPython-64bit-2.7.5.3\python-2.7.5.amd64\python

import sys
import os
import numpy as np
import gel_annotation as ga
import subprocess
import gel_signal as gs
import pandas as pd
import image_tools as it
from skimage import io
import tifffile as tf
import math

gr_hdri = "C:\CDI Labs\Data\New Gels\8-5-14-1-red_green-2-retry (2015-02-06-16.05.54)\\_HDRI-page-1-g.tif"
red_hdri = "C:\CDI Labs\Data\New Gels\8-5-14-1-red_green-2-retry (2015-02-06-16.05.54)\\_HDRI-page-1-r.tif"

#use the above 2 files to create a red-green tiff image
#loads hdri pixels from red and green
#apply log mapping with (?) cutoff
#place in R and G channels of RGB image
#same image to file name given
    
def map_pixel(pixel, min_, max_):
    if(pixel > max_): return 255
    if(pixel < min_): return 0
    b = max_-(min_-1)
    b = b**(1/255.)
    out_pixel = math.log(pixel-(min_-1), b)
    return int(out_pixel)

#green#
tif = tf.TiffFile(gr_hdri)

width = tif.pages[0].image_width
height = tif.pages[0].image_length
image_flat = tif[0].asarray().flatten()
min_pixel = min(image_flat)
max_pixel = max(image_flat)

gr_mapped_image_pixels = []
for pixel in image_flat:
    gr_mapped_image_pixels.append(map_pixel(pixel, min_pixel, max_pixel))
gr_mapped_image_pixels = np.array(gr_mapped_image_pixels)
gr_mapped_image_pixels = gr_mapped_image_pixels.reshape(height,width)

#red#
tif = tf.TiffFile(red_hdri)

width = tif.pages[0].image_width
height = tif.pages[0].image_length
image_flat = tif[0].asarray().flatten()
min_pixel = min(image_flat)
max_pixel = max(image_flat)

red_mapped_image_pixels = []
for pixel in image_flat:
    red_mapped_image_pixels.append(map_pixel(pixel, min_pixel, max_pixel))
red_mapped_image_pixels = np.array(red_mapped_image_pixels)
red_mapped_image_pixels = red_mapped_image_pixels.reshape(height,width)

#final#
red_mapped_image_pixels = np.expand_dims(red_mapped_image_pixels, 2) #add in 3rd dimension for [R,G,B]
red_mapped_image_pixels = np.repeat(red_mapped_image_pixels, 3, 2) #repeast the value - now its same for R,G,B
red_mapped_image_pixels = np.copy(red_mapped_image_pixels * np.array([1,0,0], dtype='uint8')) #zero out the G,B component for red
io.imsave("C:/temp/collage-r.tif", red_mapped_image_pixels)

gr_mapped_image_pixels = np.expand_dims(gr_mapped_image_pixels, 2) #add in 3rd dimension for [R,G,B]
gr_mapped_image_pixels = np.repeat(gr_mapped_image_pixels, 3, 2) #repeast the value - now its same for R,G,B
gr_mapped_image_pixels = np.copy(gr_mapped_image_pixels * np.array([0,1,0], dtype='uint8')) #zero out the R,B component for green
io.imsave("C:/temp/collage-g.tif", gr_mapped_image_pixels)

final_image = red_mapped_image_pixels + gr_mapped_image_pixels
io.imsave("C:/temp/collage.tif", final_image)


#gel_file = "C:\\CDI Labs\\Data\\Test-Folder\\NewTest-Green2 (2014-07-29-10.56.00)\\_gel-00_hdr_r.txt"
#df = pd.read_table(gel_file,header=None,skiprows=1,comment='#',sep='[,:()]')
#df=df.drop([2,4,5,6], axis=1)
#df.columns=['x','y','signal']
#df_image = df.pivot(index='x', columns='y', values='signal')
#
#s = gs.get_signal(df_image, 61, 89, 82, 86)
#print s
#
##from PIL import Image
##im = Image.open('C:\\CDI Labs\\Data\\Test-Folder\\Test_HDRI_Collage4 (2014-07-17-10.58.02)\\_gel-00-r-d.jpg')
##width, height = im.size
#
###'split_collage' 'C:/CDI Labs/Data/Test-Folder/NewTest-Signal1 (2014-07-30-10.32.49)/Image_0000416_01-RG1.tif' 'C:/CDI Labs/Data/Test-Folder/NewTest-Signal1 (2014-07-30-10.32.49)/0000416_01_700.TIF' 'C:/CDI Labs/Data/Test-Folder/NewTest-Signal1 (2014-07-30-10.32.49)/0000416_01_800.TIF' 'C:/CDI Labs/Data/Test-Folder/NewTest-Signal1 (2014-07-30-10.32.49)/_labels.txt' '12' '5' '3' 'C:/Projects/Boeke'
#
#new_dir = 'C:/CDI Labs/Data/Test-Folder/Test_HDRI_Collage4 (2014-07-17-10.58.02)'
#coll_filename = 'Image_0000416_01-RG1.tif'
#hdri_filename = '0000416_01_700.TIF'
#metadata_filename = 'labels.txt'
#num_gels = '12'
#num_cols = '5'
#num_rows = '3'
#
#band_file = 'C:/CDI Labs/Data/Test-Folder/Test_HDRI_Collage4 (2014-07-17-10.58.02)/_gel-00_hdr.band_info.json'
#f = open(band_file, 'r')
#band_info = json.load(f)
#f.close()
#
#subprocess.call(["python", "run_gel_annotation.py", "split_collage",
#                                                new_dir + '/' + coll_filename,
#                                                new_dir + '/' + hdri_filename,
#                                                new_dir + '/' + metadata_filename,
#                                                num_gels,
#                                                num_cols,
#                                                num_rows])
#subprocess.call(["perl", "find_lane_boundaries2.pl", "C:\\CDI Labs\\Data\\Test-Folder\\Test_HDRI_Collage4 (2014-07-16-15.22.28)\\_gel-00_hdr.txt", '8'])
#subprocess.call(["python", "run_gel_annotation1.py"])
#
#ret = os.system('run_gel_annotation.py split_collage "C:/CDI Labs/Data/Test-Folder/Test_HDRI_Collage4 (2014-07-16-14.46.19)/Image_0000416_01-RG1.tif" "C:/CDI Labs/Data/Test-Folder/Test_HDRI_Collage4 (2014-07-16-14.46.19)/0000416_01_700.TIF" 12 5 3')
#print ret  
    #'run_gel_annotation.py split_collage "C:/CDI Labs/Data/Test-Folder/Test_HDRI_Collage2 (2014-07-16-14.28.32)/Image_0000416_01-RG1.tif" "C:/CDI Labs/Data/Test-Folder/Test_HDRI_Collage2 (2014-07-16-14.28.32)/0000416_01_700.TIF" 12 5 3')
#ga.split_collage('C:\\CDI Labs\\Data\\Test-Folder\\NewTest2\\red-green1.tif', 'C:\\CDI Labs\\Data\\Test-Folder\\NewTest2\\hdri-red.tif', 12, 5, 3) 

#ga.label_gels2('C:\\CDI Labs\\Data\\Tests\\Coll1 (2014-06-16-12.19.45)',
#               'C:\\CDI Labs\\Labels\\labels2.txt',
#               'C:\\CDI Labs\\Labels\\annotation2.png',
#               'C:\\CDI Labs\\Data\\Test-Folder\\Tests\\Coll1 (2014-06-16-12.19.45)\\_exposure.txt')


