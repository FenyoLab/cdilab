#!C:\WinPython-32bit-2.7.6.3\python-2.7.6\python
#!/local/apps/python/2.7.7/bin/python

local_version = True

from datetime import datetime
import sys
import os
import cgi
import cgitb
import re
import subprocess
import glob
import shutil
import json
import image_tools as it
from skimage import io
cgitb.enable()
from subprocess import Popen, PIPE

try: # Windows needs stdio set for binary mode.
    import msvcrt
    msvcrt.setmode (0, os.O_BINARY) # stdin  = 0
    msvcrt.setmode (1, os.O_BINARY) # stdout = 1
except ImportError:
    pass

data_folder = 'Data'
ANNOTATION_FILE_NAME = 'annotation2.png'

if(local_version):
    #for cgi debugging
    sys.path.append('C:\\Komodo-PythonRemoteDebugging-8.5.3-83298-win32-x86\\pythonlib') 
    from dbgp.client import brk
    #brk(host="localhost", port=49475) #sets hard breakpoint (port number should match value for Port from 'Debug->Listener Status' in Komodo)

SETTINGS_TABLE = {'LOCAL_HOME':'', 'LOCAL_DATA':''}
settings_file = './settings.txt'
if(local_version):
    image_magick_dir = 'C:/ImageMagick-6.8.9-16bit-HDRI/VisualMagick/bin' #'C:/Program Files (x86)/ImageMagick-6.7.8-Q16'
else:
    image_magick_dir = '/local/apps/ImageMagick/6.8.9-4/bin'

def read_settings():
    try:
        f = open(settings_file, 'r')
    except(IOError):
        return 'Could not open ' + '"' + settings_file + '" for reading.\n'
    
    for line in f:
        line = line.strip()
        if(line and line[0] != '#'): #ignore lines beginning with # as comments
            m = re.match(r'([A-Z_]+)\s*=\s*(.+)', line)
            if(m):
                if(m.group(1) in SETTINGS_TABLE):
                    SETTINGS_TABLE[m.group(1)] = (m.group(2)).replace('\\','/') #always use forward slash
                    
    #check we got all settings required
    missing = ''
    for key in SETTINGS_TABLE.keys():
        if not SETTINGS_TABLE[key]: missing += (key + ', ')
    if(missing):
        return 'Settings file (' + settings_file + ') was missing the following keys: ' + missing[0:-2] + '.\n'
    
    return ''

def print_header(msg=''):
    print "Content-Type: text/html"
    print
    print '<!DOCTYPE html>'
    print '<html><head><title>CDI Laboratories - Gel Image Processing and Analysis </title>'
    print '<link rel="stylesheet" href="//code.jquery.com/ui/1.11.0/themes/smoothness/jquery-ui.css">'
    #print '<script src="//code.jquery.com/jquery-1.10.2.js"></script>'
    #print '<script src="//code.jquery.com/ui/1.11.0/jquery-ui.js"></script>'
    #print '<script src="/cdi-html/external/jquery/jquery.js"></script>'
    #print '<link rel="stylesheet" href="/cdi-html/jquery-ui.min.css">'
    print '<script src="/cdi-html/jquery-1.10.2.min.js"></script>'
    print '<script src="/cdi-html/jquery-ui.js"></script>'
    #print '<script type="text/javascript" src="/cdi-html/caman.full.min.js"></script>'
    print '<script src="/cdi-html/setup.js" type="text/javascript"></script>'
    print '<link rel="stylesheet" type="text/css" href="/cdi-html/main1.css" />'
    #print '<style>.rect { background: rgba(255, 255, 255, 0); border:1px solid red; } .ui-widget-content .ui-icon { background-image: url("");}</style>'
    print '</head><body>'
    
    print '<div id="dialog" class="popup_dialog"><p><img src="/cdi-html/spinner.gif"/> Uploading gel collage files...  </p></div>'
    #print '<div id="dialog_expload" class="popup_dialog"><p><img src="/cdi-html/spinner.gif"/> Loading exposure settings...  </p></div>'
    #print '<div id="dialog_label" class="popup_dialog"><p><img src="/cdi-html/spinner.gif"/> Labeling and annotating gels...  </p></div>'
    print '<div id="dialog_delete_dirs" class="popup_dialog"><p><img src="/cdi-html/spinner.gif"/> Deleting...  </p></div>'
    print '<div id="dialog_clip_and_mark" class="popup_dialog"><p><img src="/cdi-html/spinner.gif"/> Clipping gels...  </p></div>'
    #print '<div id="dialog_reload_density" class="popup_dialog"><p><img src="/cdi-html/spinner.gif"/> Saving and reloading table...  </p></div>'
    
    print '<div id="form_dialog_newdir" class="popup_dialog">'
    print '<form action="/cdi-cgi/cdi_webmain.py">'
    print 'Directory Name: <input type="text" name="new_dir"><br/><br/>'
    print '<input type="submit" value="Submit"><input type="hidden" name="action" value="new_dir">'
    print '</form></div>'
    
    #print '<div id="form_dialog_label" class="popup_dialog">'
    #print '<form method="post" action="/cdi-cgi/cdi_webmain.py" id="label_form" enctype="multipart/form-data">'
    #print 'Label gels in: '
    #print '<input type="text" name="view_gels_to_label" id="view_gels_to_label" class="gels_to_label" value="(none)" disabled>'
    #print '<input type="hidden" name="gels_to_label" class="gels_to_label" value="(none)">'
    #print '<br/><br/>'
    ##print 'Select gel data file:'
    ##print '<input name="labels_file" id="labels_file" type="file">'
    ##print '<br/><br/>'
    #print '<input name="submit" type="submit" value="Label" id="label_button">'
    #print '<input type="hidden" name="action" value="label">'
    #print '</form></div>'
    
    print '<div id="form_dialog_collupload" class="popup_dialog">'
    print '<form method="post" action="/cdi-cgi/cdi_webmain.py" id="coll_upload_form" enctype="multipart/form-data">'
    print 'Parent Directory: '
    print '<input type="text" name="view_parent_dir" id="view_parent_dir" class="parent_dir" value="(none)" disabled>'
    print '<input type="hidden" name="parent_dir" class="parent_dir" value="(none)">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
    print '<input type="checkbox" name="new_gel_format" id="new_gel_format">&nbsp;New Gel Format'
    print '<br/><br/>'
    print 'Name: '
    print '<input type="text" name="coll_name", size="30", maxlength="40">'
    print '<br/><br/>'
    print 'No. Rows: <input type="text" id="num_rows" name="num_rows" onblur="if(parseInt($(this).val()) <= 0) { $(this).val(1); }" onkeydown="validateNumber(event);" size="2" maxlength="2" value="3">&nbsp;&nbsp;&nbsp;'
    print 'No. Columns: <input type="text" id="num_cols" name="num_cols" onblur="if(parseInt($(this).val()) <= 0) { $(this).val(1); }" onkeydown="validateNumber(event);" size="2" maxlength="2" value="5">&nbsp;&nbsp;&nbsp;'
    print 'No. Gels: <input type="text" id="num_gels" name="num_gels" onblur="if(parseInt($(this).val()) <= 0) { $(this).val(1); }" onkeydown="validateNumber(event);" size="2" maxlength="2" value="12">'
    print '<br/><br/>'
    print 'Select standard TIFF file:'
    print '<input name="coll_file" id="coll_file" type="file">'
    print '<br/><br/>'
    print 'Select ImageStudio HDRI TIFF file (RED channel):'
    print '<input name="hdri_coll_file_r" id="hdri_coll_file" type="file">'
    print '<br/><br/>'
    print 'Select ImageStudio HDRI TIFF file (GREEN channel):'
    print '<input name="hdri_coll_file_g" id="hdri_coll_file" type="file">'
    print '<br/><br/>'
    print 'Select gel data file (tab-delimited text file):'
    print '<input name="labels_file" id="labels_file" type="file">'
    print '<br/><br/>'
    print '<input name="submit" type="submit" value="Upload" id="coll_upload_button">'
    print '<input name="action" type="hidden" value="coll_upload">'
    print '</form></div>'
    
    print '<table class="maintable"><tr class="banner" ><td colspan="2"><h1>Gel Image Processing and Analysis</h1></td></tr>'
    if(msg): print '<tr class="status_msg" ><td colspan="2"><p><i>' + msg + '</i></p></td></tr>'

def print_footer():
    print "</table></body></html>"
    
def print_files_list():
    
    print '<tr ><td class="files_list">'
    print '<form action="/cdi-cgi/cdi_webmain.py" id="delete_dirs_form">'
    print '<h3><u>Data Folders</u> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
    print '<input name="sumbit" type="submit" value="Delete Checked Folders" id="delete_dirs_button"><br/></h3>'
    print '<div id="list" style="overflow-y:scroll; height:600px" >'
    to_print = dir_to_html.load_html_tree(SETTINGS_TABLE['LOCAL_DATA'])
    print to_print
    print '<br/><br/>'
    print '<input type="hidden" name="action" value="delete_dirs">'
    print '</form>'
    print '</div>'
    print '</td>'
    
    
def print_functions_list():
    print '<td class="functions_list">'
    print '<h3><u>Viewing Pane</u></h3> <span id="view_name"></span>'
    print '<div id="content" style="overflow:auto; width:775px;" ></div>'
    print '<input type="button" id="density_analysis_button" value="Save Band Selections">'
    print '<input type="button" id="collage_markings_button" value="Save Gel Selections">'
    print '<input type="hidden" id="file_url_hidden">'
    print '<table  cellspacing="20"><tr>'
    print '<td>'
    #print '<div id="markerContainer"><img src="/cdi-html/250_marker.png"></div>'
    print '<div id="canvasContainer-r"><canvas id=\"canvas-r\"></canvas></div><br>'
    
    #slider
    #print '<div class="slider" id="slider-r-min" style="display:none"></div><span id="slider-r-min-val" style="display:none">Min Pixel: 0</span>'
    #print '<br><div class="slider" id="slider-r-max" style="display:none"></div><span id="slider-r-max-val" style="display:none">Max Pixel: 0</span></td>'
    #print '<td><div id="canvasContainer-g"><canvas id=\"canvas-g\"></canvas></div><br>'
    #print '<div class="slider" id="slider-g-min" style="display:none"></div><span id="slider-g-min-val" style="display:none">Min Pixel: 0</span>'
    #print '<br><div class="slider" id="slider-g-max" style="display:none"></div><span id="slider-g-max-val" style="display:none">Max Pixel: 0</span></td>'
    
    #spinner
    print '<input id="spinner-r-min" style="display:none"><br><span id="spinner-r-min-val" style="display:none">Min Pixel: 0</span>'
    print '<br><input id="spinner-r-max" style="display:none"><br><span id="spinner-r-max-val" style="display:none">Max Pixel: 0</span></td>'
    print '<td><div id="canvasContainer-g"><canvas id=\"canvas-g\"></canvas></div><br>'
    print '<input id="spinner-g-min" style="display:none"><br><span id="spinner-g-min-val" style="display:none">Min Pixel: 0</span>'
    print '<br><input id="spinner-g-max" style="display:none"><br><span id="spinner-g-max-val" style="display:none">Max Pixel: 0</span></td>'
    
    print '</tr><tr><td colspan="2"><span id="exposure_readout"></span><input type="button" id="save_exposure_button" value="Save Current Settings"></td></tr>'
    print '</table></tr>'
    print '</td></tr>'
    
def upload_file(fileitem, upload_dir):
    coll_filename = os.path.basename(fileitem.filename)
    fout = file (os.path.join(upload_dir, coll_filename), 'wb')
    while 1:
        chunk = fileitem.file.read(1024)
        if not chunk: break
        fout.write (chunk)
    fout.close()
    
def display_home_page(msg=''):
    print_header(msg)

    print_files_list()

    print_functions_list()

    print_footer()
        

def display_error_page(err_str):
    print_header()
    
    print '<tr><td class="files_list">'
    print '<p>' + err_str + '</p>'
    
    print '<td class="functions_list">&nbsp;'
    print '</td></tr>'
    
    print_footer()
    
def display_exposure_html(r_min, r_max, g_min, g_max):
    print "Content-Type: text/html"
    print
    print   ('<br><table border="0"><tr><td><b>Saved Settings</b></td><td> Red: Min Pixel = ' + r_min + ', Max Pixel = ' + r_max +
            '</td></tr><tr><td>&nbsp;</td><td>Green: Min Pixel = ' + g_min + ', Max Pixel = ' + g_max + '</td></tr></table><br>')
    
def check_file_type(filename, ext_pattern):
    (base, ext) = os.path.splitext(filename)
    if(re.match(ext_pattern, ext, re.I)):
        return True
    else: return False

####################################################################################################################################################################

#read settings file
err_str = read_settings()
if(err_str):
    display_error_page('Error loading settings file: ' + err_str)
    quit
    
##################################################################
#add to path for the apache user, so it can import our cdi modules 
sys.path.append(SETTINGS_TABLE['LOCAL_HOME'])

#set up home dir for the apache user (needed by matplotlib)
os.environ['HOME']=SETTINGS_TABLE['LOCAL_HOME']
#################################################################

import dir_to_html    
import pandas as pd

#if(local_version):
#    import gel_annotation as ga

import image_tools as it

#process the form:
form = cgi.FieldStorage()
if(not form):
    display_home_page()
else:
    #form data was posted: process the data
    action = form.getvalue('action')
    msg = ''
    if(action == 'new_dir'):
        #create new dir in Data folder
        new_dir_name = form.getvalue('new_dir')
        if(os.path.isdir(SETTINGS_TABLE['LOCAL_DATA'] + '/' + data_folder + '/' + new_dir_name)):
            msg = 'The directory "' + new_dir_name + '" already exists!'
        else:
            try:
                os.mkdir(SETTINGS_TABLE['LOCAL_DATA'] + '/' + data_folder + '/' + new_dir_name)
            except IOError as e:
                msg = "I/O error({0}): {1}".format(e.errno, e.strerror) + '.'
            #except WindowsError as e:
            #    msg = "Windows error({0}): {1}".format(e.errno, e.strerror) + '.'
            #exception here for bad linux file names?
        display_home_page(msg)
    elif(action == 'exposure'): #NOT USED 
        #get exposure from file
        fname = form.getvalue('file')
        fname = fname.replace('/cdi-data', SETTINGS_TABLE['LOCAL_DATA'])
        (head, tail) = os.path.split(fname)
        exp_fname = head + '/' + '_exposure.txt'
        red_min = '-1'
        gr_min = '-1'
        red_max = '-1'
        gr_max = '-1'
        try:
            f = open(exp_fname, 'r')
            for line in f:
                line = line.strip()
                vals = line.split('\t')
                if(vals and vals[0]):
                    if(vals[0] == tail):
                        red_min = vals[1]
                        red_max = vals[2]
                        gr_min = vals[3]
                        gr_max = vals[4]
        except IOError:
            pass
        
        #save hdri image with red b and c applied gel-00.jpg to _gel-00-r-d.jpg - i don't know if i want to do this
        #hdri_image = re.sub('^gel', '_gel', tail)
        #hdri_image = re.sub('.jpg$', '-r-d.jpg', hdri_image)
        #hdri_image_ = re.sub('.jpg$', '-view.jpg', hdri_image)
        #os.system(convert_cmd + ' -brightness-contrast ' + red_b + 'x' + red_c + ' "' +  head + '/' + hdri_image + '" "' +  head + '/' + hdri_image_ + '"')
        
        display_exposure_html(red_min, red_max, gr_min, gr_max)
    elif(action == 'save_exposure'):
        
        #save exposure details
        fname = form.getvalue('file')
        red_min = form.getvalue('red_min')
        red_max = form.getvalue('red_max')
        gr_min = form.getvalue('gr_min')
        gr_max = form.getvalue('gr_max')
        fname = fname.replace('/cdi-data', SETTINGS_TABLE['LOCAL_DATA'])
        (head, tail) = os.path.split(fname)
        exp_fname = head + '/' + '_exposure.txt'
        try:
            f = open(exp_fname, 'r')
            exp_dict = {}
            for line in f:
                line = line.strip()
                vals = line.split('\t')
                if(vals and vals[0]):
                    exp_dict[vals[0]] = [vals[1], vals[2], vals[3], vals[4]]
            f.close()
            exp_dict[tail] = [red_min, red_max, gr_min, gr_max]
            f = open(exp_fname, 'w')
            for k in exp_dict.keys():
                f.write(k + '\t' + exp_dict[k][0] + '\t' + exp_dict[k][1] + '\t' + exp_dict[k][2] + '\t' + exp_dict[k][3] + '\n')
            f.close()
        except IOError:
            f = open(exp_fname, 'w')
            f.write(tail + '\t' + red_min + '\t' + red_max + '\t' + gr_min + '\t' + gr_max + '\n')
        f.close()
        
        if(local_version):
            os.chdir(image_magick_dir)
            convert_cmd = 'convert'
        else:
            convert_cmd = image_magick_dir + '/convert'
        
        #apply settings to density analysis image
        density_image = re.sub('^gel', '_gel', tail)
        #density_image = re.sub('.tif$', '-r-d.jpg', density_image)
        density_image_tif = re.sub('.tif$', '-r-d.tif', density_image)
        density_image_jpg = re.sub('.tif$', '-r-d.jpg', density_image)
        
        orig_red_gel = re.sub('^gel', '_gel', tail)
        orig_red_gel = re.sub('.tif$','-r.json', orig_red_gel)
        (image_width, image_height, new_image_r) = it.load_and_filter(head + '/' + orig_red_gel, red_min, red_max)
        
        io.imsave(head + '/' + density_image_tif, new_image_r)
        os.system(convert_cmd + ' "' + head + '/' + density_image_tif + '" "' + head + '/' + density_image_jpg + '"') 
                
        #save marker positions (may have been adjusted by user)
        json_fname = head + '/_' + tail.replace('.tif', '-markers.json')
        f = open(json_fname, 'r')
        marker_info = json.load(f)
        f.close()
        
        for marker in marker_info.keys():
            #get new value set by user
            pos = form.getvalue('marker-' + marker)
            marker_info[marker] = pos
        f = open(json_fname, 'w')
        json.dump(marker_info, f)
        f.close()
        
        #re-do densitometric calculations now that user has changed the marker positions?!
        #this might not be wanted if user has already adjusted the rectangles...
            
    elif(action == 'coll_upload'):
        #gel collage is being uploaded
        coll_name = form.getvalue('coll_name')
        fileitem = form['coll_file']
        hdri_fileitem_r = form['hdri_coll_file_r']
        hdri_fileitem_g = form['hdri_coll_file_g']
        labels_fileitem = form['labels_file']
        new_gel_checked = form.getvalue('new_gel_format')
        if(new_gel_checked == 'on'): new_gel_checked = '1'
        else: new_gel_checked = '0'
            
        if(not fileitem.filename or not hdri_fileitem_r.filename or not hdri_fileitem_g.filename or not labels_fileitem.filename):
            msg = 'Please choose all files to upload.'
        else:
            coll_filename = os.path.basename(fileitem.filename)
            hdri_filename_r = os.path.basename(hdri_fileitem_r.filename)
            hdri_filename_g = os.path.basename(hdri_fileitem_g.filename)
            labels_filename = os.path.basename(labels_fileitem.filename)
            
            if(not check_file_type(coll_filename, '.tif?f')):
                msg = 'Please upload a tif image file only for the gel collage file.' 
            if(not check_file_type(hdri_filename_r, '.tif?f') or not check_file_type(hdri_filename_g, '.tif?f')):
                msg = 'Please upload a tif image file only for the HDRI gel collage files.' 
            if(not check_file_type(labels_filename, '.txt')):
                msg = 'Please upload a txt file only for the gel data file (Excel file saved as Text (Tab delimited)).' 
                
            if(not msg):
                if(not coll_name): coll_name = coll_filename
                date=datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
                coll_name += ' (' + date + ')'
                parent_dir = form.getvalue('parent_dir')
                
                num_rows = form.getvalue('num_rows')
                if(not num_rows): num_rows = '3'
                num_cols = form.getvalue('num_cols')
                if(not num_cols): num_cols = '5'
                num_gels = form.getvalue('num_gels')
                if(not num_gels): num_gels = '12'
                
                #create dir coll_name
                new_dir = SETTINGS_TABLE['LOCAL_DATA'] + '/' + data_folder + '/' + parent_dir + '/' + coll_name
                try:
                    os.mkdir(new_dir)
                except IOError as e:
                    msg = "I/O error({0}): {1}".format(e.errno, e.strerror) + '.'
                except WindowsError as e:
                    msg = "Windows error({0}): {1}".format(e.errno, e.strerror) + '.'
                else:
                    upload_file(fileitem, new_dir)
                    upload_file(hdri_fileitem_r, new_dir)
                    upload_file(hdri_fileitem_g, new_dir)
                    upload_file(labels_fileitem, new_dir)
                    shutil.copy(new_dir + '/' + labels_filename, new_dir + '/_labels.txt')
                    
                    #(2) *NEW* run script to find separation lines for the gels in the collage
                    #saving the line position to a json file for display to user and manual adjustment
                    if(local_version):
                        subprocess.check_call(["python", "run_gel_annotation.py", "mark_collage",
                                                new_dir + '/' + coll_filename,
                                                new_dir + '/' + hdri_filename_r,
                                                new_dir + '/' + hdri_filename_g,
                                                new_dir + '/_labels.txt',
                                                num_gels,
                                                num_cols,
                                                num_rows,
                                                new_gel_checked])
                    else:
                        pid = Popen(["./run_gel_annotation.py", "mark_collage",
                                        new_dir + '/' + coll_filename,
                                        new_dir + '/' + hdri_filename_r,
                                        new_dir + '/' + hdri_filename_g,
                                        new_dir + '/' + '/_labels.txt',
                                        num_gels,
                                        num_cols,
                                        num_rows,
                                        new_gel_checked], stdout=PIPE, stderr=PIPE, stdin=PIPE).pid
                        
                    ##(2) run script to separate collage and create gel images
                    #if(local_version):
                    #    subprocess.check_call(["python", "run_gel_annotation.py", "split_collage",
                    #                            new_dir + '/' + coll_filename,
                    #                            new_dir + '/' + hdri_filename_r,
                    #                            new_dir + '/' + hdri_filename_g,
                    #                            new_dir + '/_labels.txt',
                    #                            num_gels,
                    #                            num_cols,
                    #                            num_rows,
                    #                            SETTINGS_TABLE['LOCAL_HOME']])
                    #else:
                    #    pid = Popen(["./run_gel_annotation.py", "split_collage",
                    #                            new_dir + '/' + coll_filename,
                    #                            new_dir + '/' + hdri_filename_r,
                    #                            new_dir + '/' + hdri_filename_g,
                    #                            new_dir + '/' + '/_labels.txt',
                    #                            num_gels,
                    #                            num_cols,
                    #                            num_rows,
                    #                            SETTINGS_TABLE['LOCAL_HOME']], stdout=PIPE, stderr=PIPE, stdin=PIPE).pid
                    
        display_home_page(msg)
    elif(action == 'label'):
        gel_dir = form.getvalue('gels_to_label') 
        ann_file = SETTINGS_TABLE['LOCAL_HOME'] + '/' + ANNOTATION_FILE_NAME
        
        if(local_version):
            subprocess.check_call(["python", "run_gel_annotation.py", "label_gels2",
                                    SETTINGS_TABLE['LOCAL_DATA'] + '/' + gel_dir,
                                    SETTINGS_TABLE['LOCAL_DATA'] + '/' + gel_dir + '/' + '/_labels.txt',
                                    ann_file,
                                    SETTINGS_TABLE['LOCAL_DATA'] + '/' + gel_dir + '/' + '_exposure.txt'])
        else:
            pid = Popen(["./run_gel_annotation.py", "label_gels2",
                        SETTINGS_TABLE['LOCAL_DATA'] + '/' + gel_dir,
                        SETTINGS_TABLE['LOCAL_DATA'] + '/' + gel_dir + '/' + '/_labels.txt',
                        ann_file,
                        SETTINGS_TABLE['LOCAL_DATA'] + '/' + gel_dir + '/' + '_exposure.txt'], stdout=PIPE, stderr=PIPE, stdin=PIPE).pid
        display_home_page(msg)
    elif(action == 'save_density'):
        #should I put this in a separate process??
        gel_dir = form.getvalue('gels_to_label')
        
        #retrieve labels file (_labels.txt) and append the densitometric data
        labels_filename = SETTINGS_TABLE['LOCAL_DATA'] + '/' + gel_dir + '/_labels.txt'
        labels = pd.read_table(labels_filename, index_col=False)
        if('Ladder' in labels.columns):
            labels = labels.drop('Ladder',1)
        labels = labels.dropna()
        labels = labels.drop([labels.columns[0]], axis=1)
        
        
        labels['%Flag1'] = 0. #initialize
        labels['%Flag2'] = 0.
        labels['%Tot.lysate-1'] = 0.
        labels['%Tot.lysate-2'] = 0. 
        
        #data taken from json files for each gel (_gel-xx_hdr_r.band_info.json)
        file_list = glob.glob(SETTINGS_TABLE['LOCAL_DATA'] + '/' + gel_dir + '/*.json')
        for band_file in file_list:
            (head, tail) = os.path.split(band_file)
            (root, ext) = os.path.splitext(tail)
            mo = re.search('_gel-(\d\d)_hdr_r.band_info.json', tail)
            if(mo): i = int(mo.group(1))
            else: continue #something wrong
            
            pass_red = labels['Filter_IP'][i]
            if(pass_red.upper().startswith('FAIL')): continue #green depends on red 
            
            pass_green = labels['Filter_WB'][i]
            if(pass_green.upper().startswith('FAIL')): pass_green = False
            else: pass_green = True
            
            #load green channel hdri image for this gel
            if(pass_green):
                gel_file = re.sub('_r\.band_info\.json$', '_g.txt', band_file)
                df = pd.read_table(gel_file,header=None,skiprows=1,comment='#',sep='[,:()]')
                df=df.drop([2,4,5,6], axis=1)
                df.columns=['x','y','signal']
                df_image = df.pivot(index='x', columns='y', values='signal')
            
            #load band info
            f = open(band_file, 'r')
            band_info = json.load(f)
            f.close()
            
            #calculate signal for green channel
            signal = {}
            bands = [int(j) for j in band_info.keys()]
            bands.sort()
            for key in bands:
                if(key != 1): #skip marker lane
                    if(not ('Signal-RL'+str(key-1) in labels.keys())):
                            labels['Signal-RL'+str(key-1)] = 0. #initialize
                            
                    if(band_info[str(key)][7] == '1'):
                        labels['Signal-RL'+str(key-1)][i] = float(band_info[str(key)][6])
                        if(pass_green):
                            rect_x1 = int(band_info[str(key)][0])
                            rect_x2 = int(band_info[str(key)][1])
                            rect_y1 = int(band_info[str(key)][4])
                            rect_y2 = int(band_info[str(key)][5])
                            signal[key] = it.get_signal(df_image, rect_x1, rect_x2, rect_y1, rect_y2)
                        else: signal[key] = 0.
                    else:
                        signal[key] = 0.
                        
            for key in bands:
                if(key != 1): #skip marker lane
                    if(not ('Signal-GL'+str(key-1) in labels.keys())):
                        labels['Signal-GL'+str(key-1)] = 0. #initialize
                    labels['Signal-GL'+str(key-1)][i] = signal[key]
            
            if(labels["Signal-RL7"][i] == 0):
                labels['%Flag1'][i] = 0.
            else:
                labels['%Flag1'][i] = (labels["Signal-RL6"][i]/labels["Signal-RL7"][i]) * 100
                
            if(labels["Signal-RL7"][i] == 0):
                labels['%Flag2'][i] = 0.
            else:
                labels['%Flag2'][i] = (labels["Signal-RL5"][i]/labels["Signal-RL7"][i]) * 100
                
            if(labels["Signal-RL2"][i] == 0):
                labels['%Tot.lysate-1'][i] = 0.
            else:
                labels['%Tot.lysate-1'][i] = (labels["Signal-RL5"][i]/(labels["Signal-RL2"][i]*16)) * 100
                
            if(labels["Signal-RL3"][i] == 0):
                labels['%Tot.lysate-2'][i] = 0.
            else:
                labels['%Tot.lysate-2'][i] = (labels["Signal-RL6"][i]/(labels["Signal-RL3"][i]*16)) * 100
            
        #then copy it as densitometry (<date>).txt (tab delimited format)
        date=datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
        labels.to_csv(SETTINGS_TABLE['LOCAL_DATA'] + '/' + gel_dir + '/' + 'densitometry (' + date + ').txt', sep='\t', index=True)
        
        display_home_page(msg)
        
    elif(action == 'delete_dirs'):
        to_delete = form.getvalue('directory')
        if(not isinstance(to_delete,list)): to_delete = [to_delete]
        for dir_name in to_delete:
            try:
                shutil.rmtree(SETTINGS_TABLE['LOCAL_DATA'] + '/' + dir_name)
            except IOError as e:
                msg = "I/O error({0}): {1}".format(e.errno, e.strerror) + '.'
        display_home_page(msg)
        
    elif(action == 'density_reload'):
        
        band_file = form.getvalue('file')
        band_file = re.sub('[\\\/]cdi-data[\\\/]', SETTINGS_TABLE['LOCAL_DATA'] + '/', band_file)
        gel_file = re.sub('\.band_info\.json$', '.txt', band_file)
        f = open(band_file, 'r')
        #f = open('C:\\CDI Labs\\Data\\Test-Folder\\3-29-1 (2014-09-24-23.21.36)\\_gel-10_hdr_r.band_info.json', 'r')
        band_info = json.load(f)
        f.close()
        
        df = pd.read_table(gel_file,header=None,skiprows=1,comment='#',sep='[,:()]')
        df=df.drop([2,4,5,6], axis=1)
        df.columns=['x','y','signal']
        df_image = df.pivot(index='x', columns='y', values='signal')
        saved_y_width = -1
        saved_x_width = -1
        for i in range(2,9):
            #get checked value for each band
            checked = form.getvalue('lane' + str(i) + '_checked')
            if(checked == 'true'):
                if(band_info[str(i)][7] == '1'):

                    #get rectangle position/size for each band
                    rect_y1 = int(form.getvalue('lane' + str(i) + '_top'))
                    rect_y2 = int(form.getvalue('lane' + str(i) + '_height')) + rect_y1 - 1
                    saved_y_width = rect_y2 - rect_y1 + 1
                    rect_x1 = int(form.getvalue('lane' + str(i) + '_left'))
                    rect_x2 = int(form.getvalue('lane' + str(i) + '_width')) + rect_x1 - 1
                    saved_x_width = rect_x2 - rect_x1 + 1
                    
                    total_signal = it.get_signal(df_image, rect_x1, rect_x2, rect_y1, rect_y2)
            
                    band_info[str(i)][0] = str(rect_x1)
                    band_info[str(i)][1] = str(rect_x2)
                    band_info[str(i)][4] = str(rect_y1)
                    band_info[str(i)][5] = str(rect_y2)
                    band_info[str(i)][6] = str(total_signal)  
            else:
                #lane not checked, will not be considered in density analysis - 
                band_info[str(i)][7] = '0'
        
        for i in range(2,9):
            #get checked value for each band
            checked = form.getvalue('lane' + str(i) + '_checked')
            if(checked == 'true'):
                if(band_info[str(i)][7] == '0'):
                    band_info[str(i)][7] = '1'
                    
                    #get rectangle position/size for each band - get y position from another checked band
                    #to make sure this rectangle maches height with the others
                    if(saved_y_width > 0):
                        
                        rect_y1 = int(band_info[str(i)][4])
                        rect_y2 = rect_y1 + saved_y_width - 1
                        rect_x1 = int(band_info[str(i)][0])
                        rect_x2 = rect_x1 + saved_x_width - 1
                        
                        
                        
                        total_signal = it.get_signal(df_image, rect_x1, rect_x2, rect_y1, rect_y2)
                        
                        band_info[str(i)][0] = str(rect_x1)
                        band_info[str(i)][1] = str(rect_x2)
                        band_info[str(i)][4] = str(rect_y1)
                        band_info[str(i)][5] = str(rect_y2)
                        band_info[str(i)][6] = str(total_signal)  
                
        
        #save json object to file
        f = open(band_file, 'w')
        json.dump(band_info, f)
        f.close()
        
        print "Content-Type: text/json"
        print
        print json.dumps(band_info)
        
    elif(action == 'save_markings_clip_gels'):
        #load rectangle dimensions for each gel and save to json file
        
        gel_marker_file = form.getvalue('file')
        gel_marker_file = re.sub('[\\\/]cdi-data[\\\/]', SETTINGS_TABLE['LOCAL_DATA'] + '/', gel_marker_file)
        f = open(gel_marker_file, 'r')
        gel_marker_info = json.load(f)
        f.close()
        
        #loop through gels, updating the rect values with the get object
        for gel_id in gel_marker_info:
            if(gel_id == 'gel-format'): continue
            gel_id_ = 'rect-' + gel_id
            gel_marker_info[gel_id] = [int(form.getvalue(gel_id_ + '_left')),int(form.getvalue(gel_id_ + '_width')),
                                       int(form.getvalue(gel_id_ + '_top')),int(form.getvalue(gel_id_ + '_height'))]
        #save json object to file
        f = open(gel_marker_file, 'w')
        json.dump(gel_marker_info, f)
        f.close()
        
        #clip and mark gels
        if(local_version):
            subprocess.check_call(["python", "run_gel_annotation.py", "clip_and_mark_gels",
                                    gel_marker_file, SETTINGS_TABLE['LOCAL_HOME']])
        else:
            pid = Popen(["./run_gel_annotation.py", "clip_and_mark_gels",
                                    gel_marker_file, SETTINGS_TABLE['LOCAL_HOME']], stdout=PIPE, stderr=PIPE, stdin=PIPE).pid
        display_home_page(msg)
    
    
    
    
    
    
    
    
    
    