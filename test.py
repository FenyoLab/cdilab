#!/usr/bin/python

from skimage import io, exposure, img_as_float, dtype_limits
from skimage import data_dir
import numpy as np
import tifffile as tf
import matplotlib.pyplot as plt
import math
import json
pixel_saturation = 0

def SaveFigureAsImage(fileName,fig=None,**kwargs):
    ''' Save a Matplotlib figure as an image without borders or frames.
       Args:
            fileName (str): String that ends in .png etc.

            fig (Matplotlib figure instance): figure you want to save as the image
        Keyword Args:
            orig_size (tuple): width, height of the original image used to maintain 
            aspect ratio.
    '''
    fig.patch.set_alpha(0)
    if kwargs.has_key('orig_size'): # Aspect ratio scaling if required
        w,h = kwargs['orig_size']
        fig_size = fig.get_size_inches()
        w2,h2 = fig_size[0],fig_size[1]
        fig.set_size_inches([(w2/w)*w,(w2/w)*h])
        fig.set_dpi((w2/w)*fig.get_dpi())
    a=fig.gca()
    a.set_frame_on(False)
    a.set_xticks([]); a.set_yticks([])
    plt.axis('off')
    plt.xlim(0,h); plt.ylim(w,0)
    fig.savefig(fileName, transparent=True, bbox_inches='tight', \
        pad_inches=0)
    
def intensity_stretch(image):
    if(pixel_saturation == 0):
        min_in_range = image.min()
        max_in_range = image.max()
    else:
        pixels = image.flatten()
        pixels.sort()
        num_saturated = int((pixel_saturation*(len(pixels)))/2)
        index = len(pixels) - num_saturated - 1
        max_in_range = pixels[index]
        min_in_range = pixels[num_saturated]
    
    return exposure.rescale_intensity(
        image, in_range=(min_in_range,max_in_range), out_range=(0,255)) #out_range=(0,65535))

def calculate_pixel_lin(pixel, min_, max_):
    if (pixel > max_):
        return 255
    if (pixel < min_):
        return 0
    out_pixel = (255./(max_-min_))*(pixel-max_) + 255
    return int(out_pixel)

def calculate_pixel(pixel, min_, max_):
    if (pixel > max_):
        return 255
    if (pixel < min_):
        return 0
    
    b = max_ - (min_-1);
    b = math.pow(b, (1./255))
    out_pixel = math.log(pixel-(min_-1)) / math.log(b)
    return int(out_pixel)

max_ = 100.
min_ = .5
x = .6
b = max_ - (min_-1)
b = b**(1/255.)
print math.log(x-(min_-1), b)

#a = io.imread('C:\\Projects\\Boeke\\ImageStudio\\Images\\0000416_01/0000416_01_700.tif', True, plugin='tifffile')
#tif = tf.TiffFile('C:\\Projects\\Boeke\\ImageStudio\\Images\\0000416_01/0000416_01_700.tif')
##tif = tf.TiffFile('C:\\CDI Labs\\Data\\Test-Folder\\NEW-3-29-1 (2014-09-24-13.45.49)\\gel-00.tif')
##'C:/temp/700-1.tif') #'C:\\Projects\\Boeke\\ImageStudio\\0000416_01_700-1.tif') #C:\\CDI Labs\\Data\\Test-Folder\\Test-Collage (2014-06-30-22.33.52)\\1-9-14-1.tif') #'C:\\Projects\\Boeke\\ImageStudio\\0000416_01_700-1.tif') #Images\\0000416_01/0000416_01_700.tif') #Image_0000416_01-RG.tif')
#
#l = tif.pages[0].image_length
#w = tif.pages[0].image_width
#
#images = tif.asarray()
#image0 = tif[0].asarray()

f = open('C:/Projects/Boeke/html/image_pixels.json', 'r')
json_data = json.load(f)
f.close()

min_ = json_data[0]
max_ = json_data[1]
min_ = float(min_)
max_ = float(max_)
#max_ = 15
pixel_values = json_data[4]
pixel_values = sorted(pixel_values)
#pixel_values = image0.flatten()
pixel_values_lin = []
pixel_values_log = []
for v in pixel_values:
    pixel_values_lin.append(calculate_pixel_lin(v, min_, max_))
    pixel_values_log.append(calculate_pixel(v, min_, max_))
    
plt.plot(pixel_values, pixel_values_lin) 
plt.savefig('C:/Projects/Boeke/tone_mapping_lin.png') #save current figure on the plt to a file
plt.clf() #clear figure

plt.plot(pixel_values, pixel_values_log) 
plt.savefig('C:/Projects/Boeke/tone_mapping_log.png') #save current figure on the plt to a file
plt.clf() #clear figure

#tf.imsave("C:/temp/test.tif", image0)

#A = .92
#gamma = .1/8
#new_image = (image0**gamma) * A
#max_range = 1 / (A**(1/gamma))
#
#new_image = intensity_stretch(new_image)
#
#print new_image.min()
#print new_image.max()
#print new_image.dtype
#new_image = new_image.astype(np.uint8) #(np.uint16)
#print new_image.min()
#print new_image.max()
#print new_image.dtype

#print image0.min()
#print image0.max()
#
#pixels = image0.flatten()
#fig1=plt.figure()     
#plt.hist(pixels, image0.max(), log=True) 
#fig1.savefig("C:/temp/hist1.png")
#
#pixels = new_image.flatten()
#fig1=plt.figure()     
#plt.hist(pixels, new_image.max(), log=True) 
#fig1.savefig("C:/temp/hist2.png")
#
#tf.imsave('C:/temp/700-1-gamma.tif', new_image) #700-1-16.tif

#
#
#i = 0
#for page in tif:
#    for tag in page.tags.values():
#        t = tag.name, tag.value
#        print t
#    print
#    print
#    image = page.asarray()
#    if page.is_rgb: pass
#    if page.is_palette:
#        t = page.color_map
#    if page.is_stk:
#        t = page.mm_uic_tags.number_planes
#    if page.is_lsm:
#        t = page.cz_lsm_info
#    i += 1
#    
#    print image[0][0].dtype
#    print image[0][0]
#    print image.min()
#    print image.max()
#    
#    image_1 = image.astype(np.float32)
#    print image_1[0][0].dtype
#    print image_1[0][0]
#    print image_1.min()
#    print image_1.max()
#    
#    image_1 = image.astype(np.float64)
#    print image_1[0][0].dtype
#    print image_1[0][0]
#    print image_1.min()
#    print image_1.max()
    
    #x = np.array([np.float16(1.1279296875)])
    #print x[0]
    #print x.dtype
    #x = x.astype(np.float64, copy=False)
    #print x[0]
    #print x.dtype
    #
    #y = dtype_limits(x)
    #print y
#    
#    
#    
#    #fig = plt.gcf()
#    ##fig.set_size_inches(20,20)
#    #plt.imshow(image, cmap='jet')
#    #SaveFigureAsImage('C:\\Projects\\Boeke\\ImageStudio\\test' + str(i) + '.png', plt.gcf(), orig_size=(int(image.shape[0]), int(image.shape[1])))
#    #plt.clf()
#    
#    #save page as image
#    tf.imsave('C:\\Projects\\Boeke\\ImageStudio\\0000416_01_700-' + str(i) + '.tif', image)
#    #io.imsave('C:\\Projects\\Boeke\\ImageStudio\\test' + str(i) + '__.tif', image) #, plugin='freeimage')
#    
#    #autolevel image and save?
#    #image_1 = np.copy(image)
#    #x = dtype_limits(image)
#    #image_1 = intensity_stretch(image_1)
#    ##image_1 = img_as_float(image_1, force_copy=False)
#    #tf.imsave('C:\\Projects\\Boeke\\ImageStudio\\0000416_01_700-' + str(i) + '.0.1.tif', image_1)
#    #
#    #
#    #c1_display = np.copy(image_1)
#    #c1_display.dtype = 'uint8'
#    #c1_display = np.expand_dims(c1_display, 2) #add in 3rd dimension for [R,G,B]
#    #c1_display = np.repeat(c1_display, 3, 2) #repeast the value - now its same for R,G,B
#    #c1_display = np.copy(c1_display * np.array([255,0,0], dtype='uint8')) #zero out the G,B component for red
#    #
#    #tf.imsave('C:\\Projects\\Boeke\\ImageStudio\\test' + str(i) + '-is.tif', c1_display)
#    
#print i
#tif.close()
#
#
#
#
#
######################################################################################################################################
####didn't work###
##io.use_plugin('fits', kind='imread_collection')
#
####didn't work###
###img = MultiImage('C:\\Projects\\Boeke\\ImageStudio\\Images\\0000416_01')
###img = MultiImage(data_dir + '/multipage.tif')
##img = io.MultiImage('C:\\Projects\\Boeke\\ImageStudio\\Images\\0000416_01' + '/0000416_01_700.tif')
##
##print len(img)
##
##for frame in img:
##    print(frame.shape)
#    
####didn't work###
##coll = io.ImageCollection('C:\\Projects\\Boeke\\ImageStudio\\Images\\0000416_01' + '/0000416_01_700.tif')
##print len(coll)
##
##print coll[0].shape
#
#
###a = io.imread('C:\\Projects\\Boeke\\ImageStudio\\Image_0000416_01-RG.tif', plugin='freeimage')
##a = io.imread('C:\\Projects\\Boeke\\ImageStudio\\Images\\0000416_01/0000416_01_700.tif', True, plugin='freeimage')
###a = io.imread_collection('C:\\Projects\\Boeke\\ImageStudio\\Images\\0000416_01' + '/0000416_01_700.tif')
##print a.shape
##
###gr_mult = np.array([0,1,0], dtype='uint8')
###c2_display_image = np.copy(a * gr_mult) #save a copy of the green image 
###c2_image = a[:,:,1] #convert to greyscale - take green position (1) of the RBG part only
###io.imsave('C:\\Projects\\Boeke\\ImageStudio\\test-green.tif', c2_display_image, plugin='freeimage')
###
###r_mult = np.array([1,0,0], dtype='uint8')
###c1_display_image = np.copy(a * r_mult) #save a copy of the green image 
###c1_image = a[:,:,0] #convert to greyscale - take green position (1) of the RBG part only
###io.imsave('C:\\Projects\\Boeke\\ImageStudio\\test-red.tif', c1_display_image, plugin='freeimage')
##
###p = io.plugins()
###print p
###print
###
###p = io.plugins(True)
###print p
##
##
