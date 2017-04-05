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

import pandas as pd
import numpy as np
import tifffile as tf
import os
import json
import math
from skimage import io

border_width = 3

def map_pixel(pixel, min_, max_):
    #apply log mapping with (?) cutoff
    if(pixel > max_): return 255
    if(pixel < min_): return 0
    b = max_-(min_-1)
    b = b**(1/255.)
    out_pixel = math.log(pixel-(min_-1), b)
    return int(out_pixel)

def get_signal(df_image, rect_x1, rect_x2, rect_y1, rect_y2):
    
    #make sure we don't go beyond image pixels in background calculation
    x_max = len(df_image)-1
    y_max = max(df_image)
    
    if(rect_x1 < 0): rect_x1 = 0
    if(rect_x2 < 0): rect_x2 = 0
    if(rect_y1 < 0): rect_y1 = 0
    if(rect_y2 < 0): rect_y1 = 0
    
    if(rect_x1 > x_max): rect_x1 = x_max
    if(rect_x2 > x_max): rect_x2 = x_max
    if(rect_y1 > y_max): rect_y1 = y_max
    if(rect_y2 > y_max): rect_y2 = y_max
    
    if(rect_x1-border_width < 0): border_x1 = 0
    else: border_x1 = rect_x1-border_width
    if(rect_x2+border_width+1 > x_max): border_x2 = x_max
    else: border_x2 = rect_x2+border_width+1
    
    if(rect_y1-border_width < 0): border_y1 = 0
    else: border_y1 = rect_y1-border_width
    if(rect_y2+border_width+1 > y_max): border_y2 = y_max
    else: border_y2 = rect_y2+border_width+1
    
    #calculate background as median of all pixels surrounding rect, border width = 3
    background_pixels = []
    for x in range(border_x1,border_x2):
        for y in range(border_y1,border_y2):
            if(not ( (x >= rect_x1 and x <= rect_x2) and (y >= rect_y1 and y <= rect_y2) )):
                background_pixels.append(float((df_image[y][x]).rstrip('%'))/100)
    background = np.median(background_pixels)
    
    total_signal = 0.
    for x in range(rect_x1,rect_x2+1):
        for y in range(rect_y1,rect_y2+1):
            diff = float((df_image[y][x]).rstrip('%'))/100 - background
            if(diff > 0): total_signal += diff
        
    return total_signal

##################################################################################################################
#read in hdri tiff file
def load_image(image_file):
    #red channel
    tif = tf.TiffFile(image_file)
    image = tif[0].asarray()
    tif.close()
    return image

#crop as directed and save the file
#also create the json array and save 
def crop_image_json(new_width, new_height, x_offset, y_offset, new_file, image):
    
    if((x_offset + new_width) > len(image[0])): new_width = len(image[0])-x_offset
    if((y_offset + new_height) > len(image)): new_height = len(image)-y_offset
    
    cropped_image = image[y_offset:y_offset+new_height,x_offset:x_offset+new_width]
                       
    pixels = cropped_image.flatten()
    if(max(pixels) == float('inf')): #if inf is in the data, change it to 2nd highest value
        pixels_ = pixels.copy()
        pixels_[pixels_ == float('inf')] = 0
        new_max = max(pixels_)
        pixels[pixels == float('inf')] = new_max
    pixels = pixels.tolist()
    json_data = [min(pixels), max(pixels), new_width, new_height, pixels]
    #save as json file
    f = open(new_file, 'w')
    json.dump(json_data, f)
    f.close()
    
def map_pixel(pixel, min_, max_):
    if(pixel > max_): return 255
    if(pixel < min_): return 0
    b = max_-(min_-1)
    b = b**(1/255.)
    out_pixel = math.log(pixel-(min_-1), b)
    return int(out_pixel)

def open_and_convert(red_hdri_tiff_file, green_hdri_tiff_file, new_tiff_file_name):
    #loads hdri pixels from red and green
    #apply log mapping with (?) cutoff
    #place in R and G channels of RGB image
    #same image to file name given
    pass
    
def load_and_filter(json_file, min_pixel, max_pixel):
    #loads image pixels from json file
    #applies log mapping with min/max pixel cutoff
    #returns mapped pixels
    
    f = open(json_file, 'r')
    json_data = json.load(f)
    f.close()
    
    if(min_pixel == '-1'): min_pixel = json_data[0]
    if(max_pixel == '-1'): max_pixel = json_data[1]
    
    width = json_data[2]
    height = json_data[3]
    
    min_pixel = float(min_pixel)
    max_pixel = float(max_pixel)
    
    image_pixels = json_data[4]
    mapped_image_pixels = []
    for pixel in image_pixels:
        mapped_image_pixels.append(255-map_pixel(pixel, min_pixel, max_pixel))
    
    mapped_image_pixels = np.array(mapped_image_pixels)
    mapped_image_pixels = mapped_image_pixels.reshape(json_data[3],json_data[2])
    
    #mapped_image_pixels = np.expand_dims(mapped_image_pixels, 2) #add in 3rd dimension for [R,G,B]
    #mapped_image_pixels = np.repeat(mapped_image_pixels, 3, 2) #repeat the value - now its same for R,G,B
    #mapped_image_pixels = np.copy(mapped_image_pixels * np.array([0,1,0], dtype='uint8')) #zero out the R,B component for green
                        
    return (width, height, mapped_image_pixels)
    
def hdri_to_tiff_and_combine(gr_hdri, red_hdri, new_tiff, new_tiff_std):
    #combine hdri's and output a red/green hdri tiff
    #also, produce a red/green jpg for browser display
    
    tif = tf.TiffFile(gr_hdri)
    image_flat_g = tif[0].asarray().flatten()
    
    width = tif.pages[0].image_width
    height = tif.pages[0].image_length
    cutoff_len_min = int(height*width*.2)
    cutoff_len_max = int(height*width*.05)
    
    sorted_flat = sorted(image_flat_g)
    #min_pixel_g = min(image_flat_g)
    #max_pixel_g = max(image_flat_g)
    min_pixel_g = sorted_flat[cutoff_len_min]
    max_pixel_g = sorted_flat[(height*width)-cutoff_len_max-1]
    
    tif = tf.TiffFile(red_hdri)
    image_flat_r = tif[0].asarray().flatten()
    
    sorted_flat = sorted(image_flat_r)
    #min_pixel_r = min(image_flat_r)
    #max_pixel_r = max(image_flat_r)
    min_pixel_r = sorted_flat[cutoff_len_min]
    max_pixel_r = sorted_flat[(height*width)-cutoff_len_max-1]
    
    image_flat_jpg = [] #saving as tiff instead of jpg since slice doesn't have plug in to save jpg loaded for skimage
                        #may change back later
    image_flat_tiff = []
    for i,pixel in enumerate(image_flat_g):
        image_flat_jpg.append([map_pixel(image_flat_r[i], min_pixel_r, max_pixel_r),map_pixel(pixel, min_pixel_g, max_pixel_g),0])
        image_flat_tiff.append([image_flat_r[i],pixel,0])
        
    image_flat_tiff = np.array(image_flat_tiff)
    image_flat_tiff = image_flat_tiff.reshape(height,width,3)
    
    io.imsave(new_tiff, image_flat_tiff, plugin='tifffile')
    
    image_flat_jpg = np.array(image_flat_jpg)
    image_flat_jpg = image_flat_jpg.reshape(height,width,3)
    
    io.imsave(new_tiff_std, image_flat_jpg)
    
    return (height, width)
    
