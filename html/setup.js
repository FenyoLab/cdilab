var server = "http://localhost"; //"http://openslice.fenyolab.org"; //"http://localhost"; //"http://openslice.fenyolab.org";  // //"http://localhost"; //"http://openslice.fenyolab.org"; 
var density_image_resize = 1.5; //the display image is scaled for easier band selection
var collage_image_resize = .5;
var r_image_data;
var r_image_width;
var r_image_length;
var r_image_min;
var r_image_max;
var r_image_cutoff_min = 0;
var r_image_cutoff_max = 0;

var g_image_data;
var g_image_width;
var g_image_length;
var g_image_min;
var g_image_max;
var g_image_cutoff_min = 0;
var g_image_cutoff_max = 0;

$(document).ready(function()
{
        $.ajaxSetup({ cache: false });
        
        $( "#dialog" ).dialog( {autoOpen: false, modal:true, closeOnEscape:false, beforeClose: function() { return false; }, title: "Please wait...", draggable:false, resizable:false } );
        $( "#dialog_delete_dirs" ).dialog( {autoOpen: false, modal:true, closeOnEscape:false, beforeClose: function() { return false; }, title: "Please wait...", draggable:false, resizable:false } );
        $( "#dialog_clip_and_mark" ).dialog( {autoOpen: false, modal:true, closeOnEscape:false, beforeClose: function() { return false; }, title: "Please wait...", draggable:false, resizable:false } ); 
        $( "#dialog_mark" ).dialog( {autoOpen: false, modal:true, closeOnEscape:false, title: "Please wait...", draggable:false, resizable:false } ); 
        $( "#form_dialog_newdir" ).dialog( {autoOpen: false, modal:true, closeOnEscape:false, Cancel: function() { $( this ).dialog( "close" ); }, title: "New Directory", draggable:false, resizable:false } );
        $( "#form_dialog_collupload" ).dialog( {autoOpen: false, modal:true, closeOnEscape:false, Cancel: function() { $( this ).dialog( "close" ); }, title: "Upload New Gel Collage", draggable:false, resizable:false, width:800 } );
        $( "#form_dialog_label" ).dialog( {autoOpen: false, modal:true, closeOnEscape:false, Cancel: function() { $( this ).dialog( "close" ); }, title: "Label Gels", draggable:false, resizable:false, width:800 } );
        
        $('#coll_upload_form').submit(function( event )
        {
                var name = $("#coll_name").val();
                if (name == "")
                {
                        alert( "Please select name for this analysis." );
                        event.preventDefault();
                }
                else
                {
                        var fileName1 = $("#hdri_coll_file_r").val();
                        var fileName2 = $("#hdri_coll_file_g").val();
                        if (fileName1 == "" || fileName2 == "")
                        {
                                alert( "Please select the ImageStudio HDRI TIFF files to upload (both red and green channel)." );
                                event.preventDefault();
                        }
                        else
                        {
                                var fileName = $("#labels_file").val();
                                if (fileName == "")
                                {
                                        alert( "Please select a gel data file to upload." );
                                        event.preventDefault();
                                }
                                else { $('#dialog').dialog("open"); }
                        }
                }
        });
        
        $('#delete_dirs_form').submit(function( event )
        {
                //get list of dirs that are checked
                var checkedValues = $('input:checkbox:checked').map(function()
                {
                        return this.value;
                }).get();
                checkedValues = checkedValues.join(', ');
                var r = confirm( "Are you sure you want to delete the following directories:  " + checkedValues + "?" );
                if(r==true)
                {
                        //alert("OK");
                        $('#dialog_delete_dirs').dialog("open");
                }
                else
                {
                        //alert("Cancel");
                        event.preventDefault();
                }
                
        });
        
        $('#save_exposure_button').hide();
        $('#save_exposure_button').button().click
        (function(e)
        {
                origUrl = $('#file_url_hidden').val();
                
                //send the exposure settings
                var getObj =
                {
                        action: "save_exposure",
                        file: origUrl,
                        red_min: r_image_cutoff_min,
                        red_max: r_image_cutoff_max,
                        gr_min: g_image_cutoff_min,
                        gr_max: g_image_cutoff_max
                };
                
                //and the positions of the marker images 
                var parent_pos = $("#marker-container").offset();
                $("#marker-container").children().each(function( index )
                {
                        var pos = $( this ).position();
                        pos = pos.top+6;
                        if (pos < 0 || pos > r_image_length)
                        {
                                pos = -1;
                        }
                        getObj[this.id] = pos;
                });
                
                //submit ajax request to save exposure settings and marker postitions, and then reload the values into the readout
                $.post( "/cdi-cgi/cdi_webmain.py", getObj ).done(function( data )
                {
                        $('#exposure_readout').html("<br><table border='0'><tr><td><b>Saved Settings</b></td><td> Red: Min Pixel = " + r_image_cutoff_min + ", Max Pixel = " + r_image_cutoff_max + "</td></tr><tr><td>&nbsp;</td><td>Green: Min Pixel = " + g_image_cutoff_min + ", Max Pixel = " + g_image_cutoff_max + "</td></tr></table><br>");     
                
                });
                
                
        });
        
        $('#collage_markings_input').hide();
        $('#collage_markings_button').button().click
        (function(e)
        {
                srcUrl = $("#file_url_hidden").val();
                var getObj =
                {
                        action: 'save_markings',
                        file: srcUrl,
                };
                var parent_pos = $("#collage").offset();
                $("#collage").children().each(function( index )
                {
                        var pos = $( this ).position();
                        var gel_id = this.id;
                        getObj[gel_id + '_top'] = Math.round((pos.top-parent_pos.top) / collage_image_resize);
                        getObj[gel_id + '_left'] = Math.round((pos.left-parent_pos.left) / collage_image_resize);
                        getObj[gel_id + '_width'] = Math.round($( this ).width() / collage_image_resize);
                        getObj[gel_id + '_height'] = Math.round($( this ).height() / collage_image_resize);
                });
                
                //send this data to cdi_webmain.py and wait for request to finish
                $('#dialog_mark').dialog("open");
                $.post( "/cdi-cgi/cdi_webmain.py", getObj ).done(function( data )
                {
                        $('#dialog_mark').dialog("close");
                        //alert("Markings saved.");
                });
        });
        
        $('#collage_markings_clip_button').button().click
        (function(e)
        {
                srcUrl = $("#file_url_hidden").val();
                var getObj =
                {
                        action: 'save_markings_clip_gels',
                        file: srcUrl,
                };
                var parent_pos = $("#collage").offset();
                var all_gels = "";
                var gel_i = 0;
                $("#collage").children().each(function( index )
                {
                        var pos = $( this ).position();
                        var gel_id = this.id;
                        getObj[gel_id + '_top'] = Math.round((pos.top-parent_pos.top) / collage_image_resize);
                        getObj[gel_id + '_left'] = Math.round((pos.left-parent_pos.left) / collage_image_resize);
                        getObj[gel_id + '_width'] = Math.round($( this ).width() / collage_image_resize);
                        getObj[gel_id + '_height'] = Math.round($( this ).height() / collage_image_resize);
                        if(gel_i == 0) { all_gels = gel_i.toString(); }
                        else { all_gels = all_gels + ',' + gel_i.toString(); }
                        gel_i++;
                });
                
                if($('#collage_markings_clip_all').is(':checked'))
                { getObj['collage_markings_clip_choice'] = all_gels; }
                else
                {
                        var selected = $( '#collage_markings_clip_choice').val();
                        getObj['collage_markings_clip_choice'] = selected.join();
                }
                
                //send this data to cdi_webmain.py and wait for request to finish 
                $('#dialog_clip_and_mark').dialog("open");
                $.post( "/cdi-cgi/cdi_webmain.py", getObj ).done(function( data )
                {
                        //refresh the entire page.
                        //alert("Finished");
                        //$('#dialog_clip_and_mark').dialog("close");
                        //window.location.href = server + "/cdi-cgi/cdi_webmain.py";

                        var url = window.location;
                        window.location.href = url; //server + "/cdi-cgi/cdi_webmain.py";
                });
        });

        $('#density_analysis_button').hide();
        $('#density_analysis_button').button().click
        (function(e)
        {
                //show loading... message
                //$('#dialog_reload_density').dialog("open");
                
                //get image name to process
                srcUrl = $("#file_url_hidden").val();
                var getObj =
                {
                        action: 'density_reload',
                        file: srcUrl,
                };
                var i = 2;
                while(i <= 8)
                {
                        //get checkbox values
                        var checked = $("#"+"lane"+i).prop('checked');
                        getObj['lane' + i + '_checked'] = checked;
                        
                        if (checked && ($("#"+"rect"+i).length != 0))
                        {
                                //get pixel coords of each rectangle
                                var parent_pos = $("#density").offset();
                                var pos = $("#"+"rect"+i).position();
                                getObj['lane' + i + '_top'] = Math.round((pos.top-parent_pos.top) / density_image_resize);
                                getObj['lane' + i + '_left'] = Math.round((pos.left-parent_pos.left) / density_image_resize);
                                getObj['lane' + i + '_width'] = Math.round($("#"+"rect"+i).width() / density_image_resize);
                                getObj['lane' + i + '_height'] = Math.round($("#"+"rect"+i).height() / density_image_resize);
                        }
                        
                        i++;
                }
                //send this data to cdi_webmain.py and wait for request to finish - new JSON doc will be created
                $.post( "/cdi-cgi/cdi_webmain.py", getObj ).done(function( data )
                {
                        //load density analysis from JSON onto screen
                        //to do: change this to use the json sent back in 'data' instead of loading from the file
                        //same thing but won't have to do file read
                        clearDensityData();
                        loadDensityData(srcUrl);
                        
                        //hide loading... message
                        //$('#dialog_reload_density').dialog("close");
                });
        });
        
        //$('#new_gel_format').click (function ()
        //{
        //        if ($('#new_gel_format').prop('checked'))
        //        {
        //                $('#num_rows').val(7);
        //                $('#num_cols').val(6);
        //                $('#num_gels').val(42);
        //        }
        //        else
        //        {
        //                $('#num_rows').val(3);
        //                $('#num_cols').val(5);
        //                $('#num_gels').val(12);
        //        }
        //});


});

function get_step(val)
{
  return 0.1;
}

function get_sigdig(val)
{
        return val.toFixed(1);
}
  
function calculate_pixel(pixel, min, max)
{
  if (pixel > max)
  {
    return 255;
  }
  if (pixel < min)
  {
    return 0;
  }
  
  //Function is: y = log x, with base b
  // where x == [pixel - (min-1)] --> so that y == 0  when pixel == min 
  // and where b == [max - (min-1)] ^ (1/255), which is obtained by
  // solving for the base b, the formula:
  // y = log x where x is as above and p is set to max, y is set to 255
  
  var b = max - (min-1);
  b = Math.pow(b, (1/255));
  var out_pixel = Math.log(pixel-(min-1)) / Math.log(b);
  return Math.round(out_pixel);
}
  
function write_to_canvas(canvas_id, image_width, image_length, image_cutoff_min, image_cutoff_max, image_data)
{
  var canvas = document.getElementById(canvas_id);
  var context = canvas.getContext('2d');
  var imgData = context.getImageData(0,0,image_width,image_length);
  for (var i=0,j=0;i<imgData.data.length;i+=4,j++)
  {
    var p = calculate_pixel(image_data[j], image_cutoff_min, image_cutoff_max);
    imgData.data[i+0]=255-p;
    imgData.data[i+1]=255-p;
    imgData.data[i+2]=255-p;
    imgData.data[i+3]=255;
  }
  context.putImageData(imgData,0,0);
  
}
  
function validateNumber(evt)
{
        var e = evt || window.event;
        var key = e.keyCode || e.which;
    
        if (!e.shiftKey && !e.altKey && !e.ctrlKey &&
        // numbers   
        key >= 48 && key <= 57 ||
        // Numeric keypad
        key >= 96 && key <= 105 ||
        // Backspace and Tab and Enter
        key == 8 || key == 9 || key == 13 ||
        // Home and End
        key == 35 || key == 36 ||
        // left and right arrows
        key == 37 || key == 39 ||
        // Del and Ins
        key == 46 || key == 45 ||
        // period and . on keypad
        key == 190 || key == 110)
        {
            // input is VALID
        }
        else
        {
            // input is INVALID
            e.returnValue = false;
            if (e.preventDefault) e.preventDefault();
        }
}

function ec(tId, clickIcon)
{
        dstyle = document.getElementById(tId).style.display;
        if (dstyle == "none")
        {
                document.getElementById(tId).style.display = "";
                document.getElementById(clickIcon).src = "/cdi-html/minus.gif";
                document.getElementById(clickIcon).alt = "-";
        }
        else
        {
                document.getElementById(tId).style.display = "none";
                document.getElementById(clickIcon).src = "/cdi-html/plus.gif";
                document.getElementById(clickIcon).alt = "+";
        }
}

function loadImageContent_(sourceUrl)
{
        $('#density').remove();
        
        origUrl = sourceUrl;
        
        //save orig url for future exposure changes
        $('#file_url_hidden').val(origUrl);
        
        document.getElementById('canvasContainer-r').innerHTML = "<div id='marker-container'></div><canvas id=\"canvas-r\"></canvas>";
        document.getElementById('canvasContainer-g').innerHTML = "<canvas id=\"canvas-g\"></canvas>";
        
        document.getElementById("spinner-r-min").style.display = "";
        document.getElementById("spinner-r-min-val").style.display = "";
        
        document.getElementById("spinner-g-min").style.display = "";
        document.getElementById("spinner-g-min-val").style.display = "";
        
        document.getElementById("spinner-r-max").style.display = "";
        document.getElementById("spinner-r-max-val").style.display = "";
        
        document.getElementById("spinner-g-max").style.display = "";
        document.getElementById("spinner-g-max-val").style.display = "";
            
        //take off '.jpg' and make it '-r.json' and '-g.json', and put a _ in front of file name
        sourceUrl = sourceUrl.replace(/[^\\\/]+\.tif$/, '_$&');
        var sourceUrl_r = sourceUrl.replace('.tif', '-r.json');
        var sourceUrl_g = sourceUrl.replace('.tif', '-g.json');
        
        var sourceUrl_markers = sourceUrl.replace('.tif', '-markers.json');
        
        //show currently saved exposure settings
        $.post( "/cdi-cgi/cdi_webmain.py", { action: "exposure", file: origUrl } ).done(function( post_data )
        {
                var default_readout = 1;
                //alert(data);
                
                //set exposure to correct values in spinner
                var result = /Red: Min Pixel = (-?[\d\.]+)/.exec(post_data);
                var r_min = Math.ceil(parseFloat(result[1])*100)/100;
                if (r_min != -1)
                {
                        //$( "#spinner-r-min" ).spinner( "value", r_min );
                        r_image_cutoff_min = r_min;
                        default_readout = 0;
                }
                
                result = /, Max Pixel = (-?[\d\.]+)<\/td><\/tr><tr>/.exec(post_data);
                var r_max = Math.ceil(parseFloat(result[1])*100)/100; //parseInt(result[1]);
                if (r_max != -1)
                {
                        //$( "#spinner-r-max" ).spinner( "value", r_max );
                        r_image_cutoff_max = r_max;
                        default_readout = 0;
                }
                
                result = /Green: Min Pixel = (-?[\d\.]+)/.exec(post_data);
                var g_min = Math.ceil(parseFloat(result[1])*100)/100;
                if (g_min != -1)
                {
                        //$( "#spinner-g-min" ).spinner( "value", g_min );
                        g_image_cutoff_min = g_min;
                        default_readout = 0;
                }
                
                result = /, Max Pixel = (-?[\d\.]+)<\/td><\/tr><\/table>/.exec(post_data);
                var g_max = Math.ceil(parseFloat(result[1])*100)/100; //parseInt(result[1]);
                if (g_max != -1)
                {
                        //$( "#spinner-g-max" ).spinner( "value", g_max );
                        g_image_cutoff_max = g_max;
                        default_readout = 0;
                }
                
                //show save button to save the exposure settings
                $('#save_exposure_button').show();
        
                //get red image in json format and place on the canvas
                $.getJSON( sourceUrl_r, function( data )
                {
                        //filter image array
                        r_image_min = data[0];
                        r_image_max = data[1];
                        r_image_width = data[2];
                        r_image_length = data[3];
                        r_image_data = data[4];
                        
                        var r_image_abs_min  = Math.ceil(r_image_min*100)/100;
                        var r_image_abs_max  = Math.floor(r_image_max*100)/100;
                        if (default_readout)
                        {
                                r_image_cutoff_min = r_image_abs_min;
                                r_image_cutoff_max = r_image_abs_max;
                        }
                        
                        //var s = get_step(r_image_cutoff_min);
                        
                        //min red spinner
                        $("#spinner-r-min-val").text('min pixel: ' + r_image_cutoff_min.toString());
                        
                        //$( "#spinner-r-min" ).spinner({ min: r_image_abs_min, max: r_image_abs_max, step: .01 });
                        $( "#spinner-r-min" ).spinner({ min: 0, step: .01 });
                        
                        //$( "#spinner-r-min" ).spinner({ icons: { down: "ui-icon-triangle-1-s", up: "ui-icon-triangle-1-n" } });
                        $( "#spinner-r-min" ).spinner( "value", r_image_cutoff_min );
                        $( "#spinner-r-min" ).spinner({
                                change: function( event, ui )
                                {
                                        //change image min cutoff and re-display image
                                        var new_min = parseFloat(event.target.value);
                                        if (new_min >= r_image_cutoff_max)
                                        {//don't allow adjustment of min above max
                                                
                                        }
                                        else
                                        {
                                          r_image_cutoff_min = new_min;
                                          write_to_canvas('canvas-r', r_image_width, r_image_length, r_image_cutoff_min, r_image_cutoff_max, r_image_data);  
                                          
                                        }
                                        
                                },
                                spin: function( event, ui )
                                {
                                        //change image min cutoff and re-display image
                                        var new_min = ui.value;
                                        if (new_min >= r_image_cutoff_max)
                                        {//don't allow adjustment of min above max
                                          
                                        }
                                        else
                                        {
                                          r_image_cutoff_min = new_min;
                                          write_to_canvas('canvas-r', r_image_width, r_image_length, r_image_cutoff_min, r_image_cutoff_max, r_image_data);  
                                          
                                        }
                                        
                                }  
                        });
                        
                        //max red spinner
                        $("#spinner-r-max-val").text('max pixel: ' + r_image_cutoff_max.toString());
                        
                        $( "#spinner-r-max" ).spinner({ min: 0, step: .01 });
                        
                        $( "#spinner-r-max" ).spinner( "value", r_image_cutoff_max );
                        $( "#spinner-r-max" ).spinner({
                                change: function( event, ui )
                                {
                                        //change image min cutoff and re-display image
                                        var new_max = parseFloat(event.target.value);
                                        if (new_max <= r_image_cutoff_min)
                                        {//don't allow adjustment of max below min
                                          
                                        }
                                        else
                                        {
                                          r_image_cutoff_max = new_max;
                                          write_to_canvas('canvas-r', r_image_width, r_image_length, r_image_cutoff_min, r_image_cutoff_max, r_image_data);    
                                          
                                        }
                                        
                                },
                                spin: function( event, ui )
                                {
                                        //change image min cutoff and re-display image
                                        var new_max = ui.value;
                                        if (new_max <= r_image_cutoff_min)
                                        {//don't allow adjustment of max below min
                                          
                                        }
                                        else
                                        {
                                          r_image_cutoff_max = new_max;
                                          write_to_canvas('canvas-r', r_image_width, r_image_length, r_image_cutoff_min, r_image_cutoff_max, r_image_data);    
                                          
                                        }
                                        
                                }
                        });
                        
                        var canvas = document.getElementById('canvas-r');
                        canvas.setAttribute('width', r_image_width);
                        canvas.setAttribute('height', r_image_length);
                        
                        write_to_canvas('canvas-r', r_image_width, r_image_length, r_image_cutoff_min, r_image_cutoff_max, r_image_data);
                        
                        //place the arrows at the positions marking the bands for the ladder lane, next to red image
                        //these can be adjusted by user on this page
                        //create div with constant widht and height = height of red image, put it to the left of red image
                        //overlay the images of the arrows at the positions indicated by json file, make the images draggable
                        //"<div id='marker-container' style='display:inline-block; position:relative; vertical-align:top; height:210px; width:50px;'>
                        //<img src='/cdi-html/250.png' class='marker-image' style='top:6px; left:0px; height:12px; width:50px; position:absolute;'><img src='/cdi-html/150.png' class='marker-image' style='top:31px; left:0px; height:12px; width:50px; position:absolute;'><img src='/cdi-html/100.png' class='marker-image' style='top:64px; left:0px; height:12px; width:50px; position:absolute;'></div><canvas id=\"canvas-r\"></canvas>";
                        //$('.marker-image').draggable({ containment: '#marker-container' });
                        
                        $('#marker-container').css({"display":"inline-block", "position":"relative", "vertical-align":"top", "height":r_image_length+"px", "width":"50px"});
                        $.getJSON( sourceUrl_markers, function( data )
                        {
                                $.each( data, function( key, val )
                                {
                                        val = parseInt(val)-6;
                                        $("#marker-container").append(
                                        $('<img/>')
                                                .attr({id:"marker-" + key, src:"/cdi-html/" + key + ".png"})
                                                .addClass("marker-image") //50
                                                .css({"width":"800px", "height":"12px", "top":val.toString()+"px", "left":"0px", "position":"absolute"})
                                        ).show();
                                        
                                        //$('.marker-image').draggable({ containment: '#marker-container' });
                                        $('.marker-image').draggable();
                                        
                                });
                        });
                        
                        //get green image in json format and place on the canvas
                        $.getJSON( sourceUrl_g, function( data )
                        {
                                //filter image array
                                g_image_min = data[0];
                                g_image_max = data[1];
                                g_image_width = data[2];
                                g_image_length = data[3];
                                g_image_data = data[4];
                                
                                var g_image_abs_min  = Math.ceil(g_image_min*100)/100;
                                var g_image_abs_max  = Math.floor(g_image_max*100)/100;
                                if (default_readout)
                                {
                                        g_image_cutoff_min = g_image_abs_min;
                                        g_image_cutoff_max = g_image_abs_max;
                                        var html = '<br><table border="0"><tr><td><b>Saved Settings</b></td><td> Red: Min Pixel = ' + r_image_cutoff_min.toString() + ', Max Pixel = ' + r_image_cutoff_max.toString() + '</td></tr><tr><td>&nbsp;</td><td>Green: Min Pixel = ' + g_image_cutoff_min.toString() + ', Max Pixel = ' + g_image_cutoff_max.toString() + '</td></tr></table><br>';
                                        $('#exposure_readout').html(html); 
                                }
                                else { $('#exposure_readout').html(post_data); }
                                
                                //min green spinner
                                $("#spinner-g-min-val").text('min pixel: ' + g_image_cutoff_min.toString());
                                
                                $( "#spinner-g-min" ).spinner({ min: 0, step: .01 });
                                
                                $( "#spinner-g-min" ).spinner( "value", g_image_cutoff_min );
                                $( "#spinner-g-min" ).spinner({
                                        change: function( event, ui )
                                        {
                                                //change image min cutoff and re-display image
                                                var new_min = parseFloat(event.target.value);
                                                if (new_min >= g_image_cutoff_max)
                                                {//don't allow adjustment of min above max
                                                  
                                                }
                                                else
                                                {
                                                  g_image_cutoff_min = new_min;
                                                  write_to_canvas('canvas-g', g_image_width, g_image_length, g_image_cutoff_min, g_image_cutoff_max, g_image_data);  
                                                }
                                                
                                                
                                        },
                                        spin: function( event, ui )
                                        {
                                                //change image min cutoff and re-display image
                                                var new_min = ui.value;
                                                if (new_min >= g_image_cutoff_max)
                                                {//don't allow adjustment of min above max
                                                   
                                                }
                                                else
                                                {
                                                  g_image_cutoff_min = new_min;
                                                  write_to_canvas('canvas-g', g_image_width, g_image_length, g_image_cutoff_min, g_image_cutoff_max, g_image_data);    
                                                }
                                               
                                        }
                                });
                                
                                //max green spinner
                                $("#spinner-g-max-val").text('max pixel: ' + g_image_cutoff_max.toString());
                                
                                //if (g_image_cutoff_max > 10) { $( "#spinner-g-max" ).spinner({ min: 0, step: 1 }); }
                                //else { $( "#spinner-g-max" ).spinner({ min: 0, step: .01 }); }
                                $( "#spinner-g-max" ).spinner({ min: 0, step: .01 });
                                
                                $( "#spinner-g-max" ).spinner( "value", g_image_cutoff_max );
                                
                                $( "#spinner-g-max" ).spinner({
                                        change: function( event, ui )
                                        {
                                                //change image min cutoff and re-display image
                                                var new_max = parseFloat(event.target.value);
                                                if (new_max <= g_image_cutoff_min)
                                                {//don't allow adjustment of max below min
                                                        
                                                }
                                                else
                                                {
                                                  g_image_cutoff_max = new_max;
                                                  
                                                  //if (g_image_cutoff_max > 10) { $( "#spinner-g-max" ).spinner({ min: 0, step: 1 }); }
                                                  //else { $( "#spinner-g-max" ).spinner({ min: 0, step: .01 }); }
                                                  
                                                  write_to_canvas('canvas-g', g_image_width, g_image_length, g_image_cutoff_min, g_image_cutoff_max, g_image_data);    
                                                  
                                                }
                                                
                                        },
                                        spin: function( event, ui )
                                        {
                                                //change image min cutoff and re-display image
                                                var new_max = ui.value;
                                                if (new_max <= g_image_cutoff_min)
                                                {//don't allow adjustment of max below min
                                                  
                                                }
                                                else
                                                {
                                                  g_image_cutoff_max = new_max;
                                                  
                                                  //if (g_image_cutoff_max > 10) { $( "#spinner-g-max" ).spinner({ min: 0, step: 1 }); }
                                                  //else { $( "#spinner-g-max" ).spinner({ min: 0, step: .01 }); }
                                                  
                                                  write_to_canvas('canvas-g', g_image_width, g_image_length, g_image_cutoff_min, g_image_cutoff_max, g_image_data);    
                                                  
                                                }
                                                
                                        },
                                });
                                
                                var canvas = document.getElementById('canvas-g');
                                canvas.setAttribute('width', g_image_width);
                                canvas.setAttribute('height', g_image_length);
                                
                                write_to_canvas('canvas-g', g_image_width, g_image_length, g_image_cutoff_min, g_image_cutoff_max, g_image_data);
                        });
                });
        });
}

function remove_jpg_display()
{
        document.getElementById('canvasContainer-r').innerHTML = "<canvas id=\"canvas-r\"></canvas>";
        document.getElementById('canvasContainer-g').innerHTML = "<canvas id=\"canvas-g\"></canvas>";
        
        document.getElementById("spinner-r-min").style.display = "none";
        document.getElementById("spinner-r-min-val").style.display = "none";
        
        document.getElementById("spinner-g-min").style.display = "none";
        document.getElementById("spinner-g-min-val").style.display = "none";
        
        document.getElementById("spinner-r-max").style.display = "none";
        document.getElementById("spinner-r-max-val").style.display = "none";
        
        document.getElementById("spinner-g-max").style.display = "none";
        document.getElementById("spinner-g-max-val").style.display = "none";
        
        $('#save_exposure_button').hide();
        $('#exposure_readout').html('');
}

function loadDensityData(sourceUrl_bands)
{
        //use AJAX to get file that contains info for drawing the rectangles on the gel image:
        $("#content").append($('<div/>').attr("id", "density_data"))
        $.getJSON( sourceUrl_bands, function( data )
        {
                $.each( data, function( key, val )
                {
                        var pos = $("#density").position();
                        var left = Math.round((density_image_resize*parseFloat(val[0])) + parseFloat(pos.left));
                        var width = Math.round((parseFloat(val[1])-parseFloat(val[0])+1)*density_image_resize);
                        var height = Math.round((parseFloat(val[5])-parseFloat(val[4])+1)*density_image_resize);
                        var top = Math.round((density_image_resize*parseFloat(val[4])) + parseFloat(pos.top));
                        if (val[7] == "1") 
                        {       
                                $("<input type='checkbox' id='lane" + key + "' checked>")
                                        .css({"left":parseInt((left+.25*width))+"px", "position":"absolute"})
                                        .appendTo("#density_data");
                                
                                $("#density").append(
                                $('<div/>')
                                        .attr("id", "rect" + key)
                                        .addClass("ui-widget-content rect") 
                                        .css({"width":width+"px", "height":height+"px", "top":top+"px", "left":left+"px", "position":"absolute"})
                                ).show();
                                
                                
                        }
                        else
                        { 
                                if (key != "1")
                                {
                                        $("<input type='checkbox' id='lane" + key + "'>")
                                                .css({"left":parseInt((left+.25*width))+"px", "position":"absolute"})
                                                .appendTo("#density_data");
                                        $("#density").append(
                                        $('<div/>')
                                                .attr("id", "rect" + key)
                                                .addClass("ui-widget-content rect") 
                                                .css({"width":width+"px", "height":height+"px", "top":top+"px", "left":left+"px", "position":"absolute", "border-style": "dotted"})
                                        ).show();
                                }
                                
                        }
                        $( ".rect" ).draggable({ containment: '#density' });
                        $( ".rect" ).resizable({ handles: "n, w, e, s", alsoResize: ".rect", minHeight: 1, containment: '#density' });
                        //$( ".rect" ).resizable({ handles: "n, e, s, w" });
                        //$( ".rect" ).resizable({ minHeight: 1 });
                });
                
                //data is an object, change to get an array in key-order, so we get lanes in order for the table
                var data_array = [];
                $.each( data, function( key, val )
                {
                        key = parseInt(key);
                        data_array[key] = val;
                });
                var items = [];
                $.each( data_array, function( key, val )
                {
                        if (key > 0)
                        {
                                if (val[7] == "1")
                                {
                                        var sum = parseFloat(val[6]);
                                        items.push("<tr><td style=\"border-bottom: solid 1px black;\">Lane " + (parseInt(key)-1) + "</td><td style=\"border-bottom: solid 1px black; border-left: solid 1px black;\">" + sum.toFixed(2) + "</tr>");
                                        //items.push( "<li id='lane" + key + "_text'>Lane " + key + ": " + sum.toFixed(2) + "</li>" );
                                }
                                else if (parseInt(key) >= 2) 
                                {//still put it in table but leave blank
                                        items.push("<tr><td style=\"border-bottom: solid 1px black;\">Lane " + (parseInt(key)-1) + "</td><td style=\"border-bottom: solid 1px black; border-left: solid 1px black;\">&nbsp;</td></tr>");
                                }
                        }
                });
                
                //% FLAG
                if (data["7"][7] == "1" && data["8"][7] == "1")
                {
                        var ratio = parseFloat(data["7"][6])/parseFloat(data["8"][6]) * 100;
                        items.push("<tr><td style=\"border-bottom: solid 1px black;\">% Flag</td><td style=\"border-bottom: solid 1px black; border-left: solid 1px black;\">" + ratio.toFixed(2) + "</tr>");
                }
                else
                {//still put it in table but leave blank
                        items.push("<tr><td style=\"border-bottom: solid 1px black;\">% Flag</td><td style=\"border-bottom: solid 1px black; border-left: solid 1px black;\">&nbsp;</td></tr>");  
                }             
                
                //% Tot.lysate-1
                if (data["6"][7] == "1" && data["3"][7] == "1")
                {
                        var ratio = parseFloat(data["6"][6])/parseFloat(data["3"][6]) * 16 * 100;
                        items.push("<tr><td style=\"border-bottom: solid 1px black;\">% Tot.lysate-1</td><td style=\"border-bottom: solid 1px black; border-left: solid 1px black;\">" + ratio.toFixed(2) + "</tr>");
                }
                else
                {//still put it in table but leave blank
                        items.push("<tr><td style=\"border-bottom: solid 1px black;\">% Tot.lysate-1</td><td style=\"border-bottom: solid 1px black; border-left: solid 1px black;\">&nbsp;</td></tr>");  
                }
                
                //% Tot.lysate-2
                if (data["7"][7] == "1" && data["4"][7] == "1")
                {
                        var ratio = parseFloat(data["7"][6])/parseFloat(data["4"][6]) * 16 * 100;
                        items.push("<tr><td >% Tot.lysate-2</td><td style=\"border-left: solid 1px black;\">" + ratio.toFixed(2) + "</tr>");
                }
                else
                {//still put it in table but leave blank
                        items.push("<tr><td >% Tot.lysate-2</td><td style=\"border-left: solid 1px black;\">&nbsp;</td></tr>");  
                }
                               
                $("<br><br>").appendTo("#density_data");
                $("<table/>", //style="width:300px; font-family: monospace;" 
                {
                        html: items.join("") + "</table>"
                })
                        .css({"width":"300px", "font-family":"monospace"})
                        .appendTo( "#density_data" );
                $("<br>").appendTo("#density_data");
                    
        });
}

function loadContentSplitDisplay(sourceUrl, displayName, displayName2, link_id) 
{
        //remove all highlights for gel files
        $('.gel_file_links').css('color','blue'); 
        
        //highlight current file using the display name
        $('#' + link_id).css('color','red'); 
        
        var fname = sourceUrl.replace(/^.*[\\\/]/, '');
        $('#view_name').html('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;' + displayName + '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;' + displayName2);
        document.getElementById("content").innerHTML = '';
        
        $('#density_analysis_button').hide();
        $('#collage_markings_input').hide();
        
        loadImageContent_(sourceUrl); 
}

function clearDensityData()
{
        //leave image, clear everything else:
        
        //clear rectangles
        document.getElementById("density").innerHTML = '';
        
        //clear table and <br>
        $("#density_data").remove();
        
}

function loadContentBandAnalysis(sourceUrl, displayName) //, width, height)
{
        remove_jpg_display();
        $('#collage_markings_input').hide();
        
        var fname = sourceUrl.replace(/^.*[\\\/]/, '');
        $('#view_name').html(displayName);
        document.getElementById("content").innerHTML = '';
   
        //take off '.jpg' and make it '-r-d.jpg' and '-g-d.jpg', and put a _ in front of file name
        sourceUrl = sourceUrl.replace(/[^\\\/]+\.tif$/, '_$&');
        var sourceUrl_r = sourceUrl.replace(/.tif$/, '-r-d.jpg');
        var sourceUrl_bands = sourceUrl.replace(/.tif$/,'_hdr_r.band_info.json');
        
        sourceUrl_r_ = encodeURI(sourceUrl_r);
        sourceUrl_r_ = sourceUrl_r_.replace('(', '%28')
        sourceUrl_r_ = sourceUrl_r_.replace(')', '%29')
        
        sourceUrl_r_ = sourceUrl_r_ + '?' + Math.random();
        
        var imgURL = sourceUrl_r_
        var img = $('<img src="'+imgURL+'"/>').load(function()
        {
                height = Math.floor(this.height * density_image_resize);
                width = Math.floor(this.width * density_image_resize);
                var url = 'background-image: url("' + sourceUrl_r_ + '"); height: ' + height + 'px; width: ' + width + 'px; background-size: 100% 100%;'; 
                $("#content").append(
                        $('<div/>')
                        .attr("id", "density")
                        .attr("style", url)
                ).show();
                
                loadDensityData(sourceUrl_bands);
        
                $('#density_analysis_button').show();
        
                //save band url
                $('#file_url_hidden').val(sourceUrl_bands);     
                
        });   
}

function loadContent(sourceUrl)
{
        var fname = sourceUrl.replace(/^.*[\\\/]/, '');
        fname = "<a href=\"" + sourceUrl + "\">" + fname + "</a>"
        $('#view_name').html(fname);
        
        document.getElementById("content").innerHTML = '';
        
        $('#density_analysis_button').hide();
        $('#collage_markings_input').hide();
        remove_jpg_display();
        
        if(sourceUrl.search(/\.txt$/) >= 0)
        {
                var httpRequest = new XMLHttpRequest();
                httpRequest.open("GET", sourceUrl, true);
                httpRequest.send(null);
                httpRequest.onreadystatechange = function()
                {
                        if(this.readyState == 4 && this.status == 200)
                        {
                                document.getElementById("content").innerHTML = '<pre>' + this.responseText + '</pre>';
                        }
                }
        }
        else if (sourceUrl.search(/\.tiff?$/) >= 0)
        {//load image into oppposite pane (the div)
                
                $(new Image()).attr('src', '' + sourceUrl).appendTo($('#content')).show();
        }
        else if (sourceUrl.search(/\.jpe?g$/) >= 0 || sourceUrl.search(/\.png$/) >= 0)
        {
                $(new Image()).attr('src', '' + sourceUrl).appendTo($('#content')).show();
        }
}

function loadCollageMarkings(sourceJSON)
{
        //read json file for demarcation lines of gels
        //draw rectangles on gels according to json dimensions
        
        $.getJSON( sourceJSON, function( data )
        {
                var gel_names = [];
                $.each( data, function( key, val )
                {
                        if (key != 'gel-format')
                        {
                                var pos = $("#collage").position();
                                var left = Math.round((collage_image_resize*parseFloat(val[0])) + parseFloat(pos.left));
                                var top = Math.round((collage_image_resize*parseFloat(val[2])) + parseFloat(pos.top));
                                var width = Math.round(collage_image_resize*parseFloat(val[1]));
                                var height = Math.round(collage_image_resize*parseFloat(val[3]));
                                
                                //fix key for display
                                var gel_num = parseInt(key.replace('gel-', ''));
                                gel_num = gel_num+1;
                                var gel_title = 'Gel ' + gel_num.toString();
                                gel_num = gel_num-1;
                                
                                gel_names[gel_num] = gel_title;
                                
                                $("#collage").append(
                                $('<div/>')
                                        .attr("id", "rect-" + key)
                                        .addClass("ui-widget-content rect") 
                                        .css({"width":width+"px", "height":height+"px", "top":top+"px", "left":left+"px", "position":"absolute"})
                                        .html('<h3 style="font-size: 8pt; text-align: center; margin: 0; color: red;">' + gel_title + '</h3>')
                                ).show();
                                $( ".rect" ).draggable({ containment: '#collage' });
                                $( ".rect" ).resizable({ handles: "n, w, e, s", minHeight: 1, containment: '#collage' });
                        }
                });
                $.each(gel_names, function( index, value ) {
                        $("#collage_markings_clip_choice").append($("<option/>", {
                                value: index,
                                text: value
                        }));
                });
        });
        
        
}

function loadContentMarkedCollage(sourceUrl)
{
        $('#density_analysis_button').hide();
        remove_jpg_display();
        
        $('#view_name').html("Gell Collage - marked");
        document.getElementById("content").innerHTML = '';
        
        sourceUrl_ = encodeURI(sourceUrl);
        sourceUrl_ = sourceUrl_.replace('(', '%28')
        sourceUrl_ = sourceUrl_.replace(')', '%29')
        
        //load gel collage image to the rhs display
        var imgURL = sourceUrl_;
        var img = $('<img src="'+imgURL+'"/>').load(function()
        {
                height = Math.floor(this.height * collage_image_resize);
                width = Math.floor(this.width * collage_image_resize);
                var url = 'background-image: url("' + sourceUrl_ + '"); height: ' + height + 'px; width: ' + width + 'px; background-size: 100% 100%;'; 
                $("#content").append(
                        $('<div/>')
                        .attr("id", "collage")
                        .attr("style", url)
                ).show();
                
                sourceJSON = sourceUrl.replace('sectioned_collage.jpg', '_gel_marker_lines.json');
                $('#collage_markings_clip_choice').empty();
                gel_names = loadCollageMarkings(sourceJSON);
                
                $('#collage_markings_input').show();
                
                //save json url
                $('#file_url_hidden').val(sourceJSON);     
        });
}








