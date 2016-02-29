#!/local/apps/python/2.7.7/bin/python

import os
import sys
import re
import pandas as pd
import random

#loads the directory tree of a given root and returns html for display in a web page
#javascript to expand/collapse should be added to the web page that uses this module
#the +/- images should also be present - adjust the values below as needed
#
#also provides option to only load the first level under the given root

img_source_plus = '/cdi-html/plus.gif';
img_source_minus = '/cdi-html/minus.gif';
img_source_star = '/cdi-html/greyplus.gif';
data_alias = '/cdi-data/'

def load_tree(startpath):
    
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print('{}{}'.format(subindent, f))
            
def load_html_tree(startpath, show_dir_checks=True):
    #does not display files/directories beginning with '_'
    #if given js function name, will set it to execute when link is clicked, sending in url of current file as the only argument
    #otherwise clicked link will just link to the url of the file
    #if show_dir_checks is True, will display a check box next to directories, (name=directory, value=<dir-name>)
    random.seed()
    
    prev_level = -1
    div_id = 0
    first = True
    ret_str = ''
    for root, dirs, files in os.walk(startpath):
        
        if(os.sep + '_' in root): continue
        
        level = root.replace(startpath, '').count(os.sep)
        while(level <= prev_level):
            ret_str += '</div>'
            prev_level -= 1
        indent = 4 * (level)
        for i in range(0,indent): ret_str += '&nbsp;'
        
        #check if dir only contains 'invisible' files/dirs then show it as empty
        num_count = 0
        for f in files:
            if(f.startswith('_')): num_count += 1
        for d in dirs:
            if(d.startswith('_')): num_count += 1
            
        if( (dirs or files) and (num_count < (len(files) + len(dirs))) ):
            if(first or (level == 1 and os.path.basename(root) == 'Data')): ret_str += '<img src="' + img_source_minus + '" onclick="ec(\'text_' + str(div_id) + '\', \'img_' + str(div_id) + '\')" id="img_' + str(div_id) + '" style="cursor:hand;" alt="-" />'
            else:
                ret_str += '<img src="' + img_source_plus + '" onclick="ec(\'text_' + str(div_id) + '\', \'img_' + str(div_id) + '\')" id="img_' + str(div_id) + '" style="cursor:hand;" alt="+" />'
                root_val = root.replace(startpath, '').replace('\\', '/')
                if(show_dir_checks): ret_str += '<input type="checkbox" name="directory" value="' + root_val + '">'
        else:
            ret_str += '<img src="' + img_source_star + '" alt="*" />'
            root_val = root.replace(startpath, '').replace('\\', '/')
            if(show_dir_checks and not (level == 1 and os.path.basename(root) == 'Data')): ret_str += '<input type="checkbox" name="directory" value="' + root_val + '">'
        
        if(level == 1 and os.path.basename(root) == 'Data'): ret_str += ' <img title="Create new Data folder" src="/cdi-html/add_item.png" onclick="$(\'#form_dialog_newdir\').dialog(\'open\')" style="cursor:hand;" />'
        if(level == 2): ret_str += ' <img title="Upload Gel Collage" src="/cdi-html/upload1.png" onclick="$(\'.parent_dir\').val(\'' + os.path.basename(root) + '\'); $(\'#view_parent_dir\').attr(\'size\', ' + str(len(os.path.basename(root))+10) + '); $(\'#form_dialog_collupload\').dialog(\'open\')" style="cursor:hand;" />'
        if(level == 3):
            location = root.replace('\\', '/')
            location = location.replace(startpath + '/', '')
            ret_str += (' <img title="Label Gels" src="/cdi-html/exec1.png" onclick="$(\'.gels_to_label\').val(\'' +
                        location + '\'); $(\'#view_gels_to_label\').attr(\'size\', ' +
                        str(len(location)+10) + '); $(\'#form_dialog_label\').dialog(\'open\')" style="cursor:hand;" />')
            #ret_str += (' <a href="/cdi-cgi/cdi_webmain.py?action=label&gels_to_label=' +
            #            location +
            #            '"><img title="Label Gels" src="/cdi-html/exec1.png" style="cursor:hand;" /></a>')
            ret_str += (' <a href="/cdi-cgi/cdi_webmain.py?action=save_density&gels_to_label=' +
                        location +
                        '"><img title="Save Densitometric Data" src="/cdi-html/append.jpg" style="cursor:hand;" /></a>')
        
        ret_str += ' ' + os.path.basename(root)
        
        if(first or (level == 1 and os.path.basename(root) == 'Data')):
            ret_str += '<br/><div id="text_' + str(div_id) + '" >'
            first = False
        else: ret_str += '<br/><div id="text_' + str(div_id) + '" style="display:none">'
        
        subindent = 4 * (level + 1)
        files = sorted(files)
        
        if(level == 3):
            labels_filename = root + '/_labels.txt';
            #labels = pd.read_table(labels_filename)
            try:
                labels = pd.read_table(labels_filename)
                labels['CDI#']
                labels['Filter_IP']
                labels['Filter_WB']
            except(IOError,KeyError):
                labels = pd.DataFrame()
        
        #get random id for this folder - used for id's of the gel file links
        rand_num = random.randint(1,1000000)
        for f in files:
            if(f.startswith('_')): continue
            for i in range(0,subindent): ret_str += '&nbsp;'
            source = data_alias + root.replace(startpath, '').replace('\\','/') + '/' + f;
            f_d = '_' + f
            f_d = f_d.replace('.tif', '-r-d.jpg');
            mo = re.match('gel-(\d\d).tif',f)
            show_bold = False
            if(level == 3 and mo): # source.startswith('gel-') and source.endswith('.jpg')):
                #show name from metadata file in stead of gel-00, gel-01, etc.
                if(not labels.empty):
                    try:
                        gel_index = int(mo.group(1)) #display_name = labels['CDI#'][gel_index] + '_' + labels['Filter_IP'][gel_index]
                        display_name = labels['CDI#'][gel_index] + '_' + labels['Filter_IP'][gel_index]
                        display_name2 = labels['CDI#'][gel_index] + '_' + labels['Filter_WB'][gel_index]
                        if(labels['Filter_IP'][gel_index].startswith('PASS') or labels['Filter_WB'][gel_index].startswith('PASS')):
                            show_bold = True
                    except(IOError,KeyError):
                        display_name = f
                else:
                    display_name = f
                if(os.path.isfile(root + '/' + f_d)):
                    (head, tail) = os.path.split(source)
                    (tail, ext) = os.path.splitext(tail) # tail
                    tail = tail + '-' + str(rand_num)
                    ret_str += '<a class="gel_file_links" id="' + tail + '" href="javascript:loadContentSplitDisplay(\'' + source + '\',\'' + display_name + '\',\'' + display_name2 + '\',\'' + tail + '\');">'
                    if(show_bold):
                        ret_str += '<b>'
                    ret_str += display_name
                    if(show_bold):
                        ret_str += '</b>'
                    ret_str += '</a> <img title="Densitometric Analysis" src="/cdi-html/band.png" onclick="loadContentBandAnalysis(\'' + source + '\',\'' + display_name + '\');" style="cursor:hand;" /><br/>'
                else:
                    ret_str += '<a href="javascript:loadContentSplitDisplay(\'' + source + '\',\'\');">' + display_name + '</a> <br/>'
            elif(source.endswith('.zip')):
                ret_str += '<a href="' + source + '">' + f + '</a>' + '<br/>'
            elif(source.endswith('sectioned_collage.jpg')):
                ret_str += '<a href="javascript:loadContentMarkedCollage(\'' + source + '\');">Gel Collage - marked</a> <br/>'
                pass #call function in js file that will load json markers and display them on the jpg collage file
            else:
                ret_str += '<a href="javascript:loadContent(\'' + source + '\');">' + f + '</a><br/>'
            #ret_str += '<a href="' + source + '">' + f + '</a>' + '<br/>'
        
        #ret_str += '<br/>'
        
        prev_level = level
        div_id += 1
    level = 1
    while(level <= prev_level):
        ret_str += '</div>'
        prev_level -= 1
        
    return ret_str
    
def load_level(startpath):
    #load the first level under startpath - files and directories
    #create the html 'tree'
    
    pass

###########################################################################################################

#if(len(sys.argv) > 1): startpath = sys.argv[1]
#else: startpath = '.'
#
#print load_html_tree(startpath)

