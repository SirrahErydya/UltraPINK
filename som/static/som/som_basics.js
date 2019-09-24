/**
 * Basic manipulation for PINK-generated SOMs
 */

var proto_selected = 'proto-selected';
var tool_selected = 'tool-selected';
var som_img_size = 100;
var csrf_token_name = "csrfmiddlewaretoken";
var selected_prototypes = [];
var label_colors = {};


function select_tool(id) {
    var som_container = document.getElementById('som-container');
    var selected_tools = document.getElementsByClassName(tool_selected);
    var tool = document.getElementById(id);
    for(var i=0; i<selected_tools.length; i++) {
        if(selected_tools[i].id == 'magnifier') {
            som_container.removeEventListener("mousedown", magnify);
            som_container.removeEventListener("mouseup", remove_magnifier);
        } else if(selected_tools[i].id == 'zoom') {
            som_container.removeEventListener('wheel', zoom_som);
            som_container.style.backgroundSize = '100%';
            som_img_size = 100
        }
        selected_tools[i].classList.remove(tool_selected);
    }
    if(id == "magnifier") {
        som_container.addEventListener("mousedown", magnify);
        som_container.addEventListener("mouseup", remove_magnifier);
    } else if(id == "zoom") {
        som_container.addEventListener('wheel', zoom_som);
    }
    tool.classList.add(tool_selected)
}

function click_prototype(id) {
    var img = document.getElementById(id);
    var tool = document.getElementsByClassName(tool_selected)[0];
    if(tool.id == 'pointer') {
        select_single(img);
    } else if(tool.id == 'zoom') {

    } else if(tool.id == 'selection') {
        select_multiple(img)
    } else if(tool.id == 'wand') {

    }
}

function select_single(img) {
    var already_active = img.classList.contains(proto_selected);
    var selected_imgs = document.getElementsByClassName(proto_selected);
    for(var i=0; i<selected_imgs.length; i++) {
        selected_imgs[i].classList.remove(proto_selected);
        selection_info = document.getElementById('prototype-info');
        selection_info.innerHTML = '';
        selected_prototypes = [];
    }
    if(!already_active) {
        img.classList.add(proto_selected);
        request_prototypes([img.id]);
        show_selection_info(selected_prototypes[0])
    }
}

function select_multiple(img) {
    if(img.classList.contains(proto_selected)) {
        img.classList.remove(proto_selected)
    } else {
        img.classList.add(proto_selected);
    }
}


// Set Aladin Lite snippet coordinates
function go_to_aladin(i) {
    // Open loc.txt, parse RA and Dec and goto these coordinates
    // Each prototype has its own directory and each directory contains
    // a file loc.txt that contains the coordinates to the first few best
    // matching sources to this prototype.
    $.get('website/prototype' + proto_x + '_' + proto_y + '_0/loc.txt', function(data) {
        var line = data.split("\n")[i];
        var ra = line.split(';')[0];
        var dec = line.split(';')[1];
        console.log(ra, dec); // Uncomment to write coordinates to console
        aladin.gotoRaDec(ra,dec);
        aladin.setFov(12/60);
                   }, 'text');
}

function show_best_fits() {
    var input_field = document.getElementById('input-cutouts');
    selection = Array.from(document.getElementsByClassName(proto_selected));
    if(selection.length <= 0){
        alert("No prototypes are selected. Use one of the tools to select one or many prototypes.");
        return;
    }
    var data = JSON.stringify({ 'protos': selection.map(s => s.id)});
    request_cutouts( '/som/get_best_fits/'+input_field.value, data);
}

function show_outliers(som_id) {
    input_field = document.getElementById('input-outliers');
    request_cutouts('/som/get_outliers/'+som_id+'/'+input_field.value, '');
}

function request_prototypes(proto_ids) {
    var data = JSON.stringify({ 'protos': proto_ids});
    var csrf_token = $('input[name="'+csrf_token_name+'"]').attr('value');
    $.ajaxSetup({
        beforeSend: function(xhr) {
            xhr.setRequestHeader("X-CSRFToken", csrf_token);
        }
    });
    $.ajax({
        url: '/som/get_protos',
        data: data,
        dataType: 'json',
        method: 'POST',
        success: function (data) {
            if (data.success) {
                selected_prototypes = data.protos;
            }
        },
        async: false
      });
    console.log(selected_prototypes);
}

// Open a popup with the best fits for a prototype
function request_cutouts(url, data) {
    var modal = document.getElementById('modal');
    modal.style.display = 'block';
    var csrf_token = $('input[name="'+csrf_token_name+'"]').attr('value');
    outlier_case = data.trim() === '';
    $.ajaxSetup({
        beforeSend: function(xhr) {
            xhr.setRequestHeader("X-CSRFToken", csrf_token);
        }
    });
    $.ajax({
        url: url,
        data: data,
        dataType: 'json',
        method: 'POST',
        success: function (data) {
            if (data.success) {
                create_cutout_images(data.best_fits, selected_prototypes, outlier_case);
            }
        }
      });
}

function create_cutout_images(best_fits, protos, outlier_case) {
    var img_container = document.getElementById('cutouts');
    var modal_header = document.getElementById('modal-header');
    var proto_label_button = document.getElementById("label-cutouts-proto");
    if(outlier_case) {
        modal_header.innerHTML = "<h1>These are the "+ best_fits.length +" images that fit the least to any of the prototypes.</h1>";
        proto_label_button.style.display = 'none'
    } else {
        modal_header.innerHTML = "<h1>These are the "+ best_fits.length +" best matching images to your choice.</h1>";
        modal_header.innerHTML += "<p><b>Chosen prototypes:</b>";
        proto_label_button.style.display = 'inline'

        for(var i=0; i<protos.length; i++) {
            id = "" + protos[i].x + protos[i].y;
            label = protos[i].label.trim() !== '' ? protos[i].label : "Unlabeled";
            modal_header.innerHTML += id + " (Label: " + label +")";
            if(i < best_fits.length-1) {
                modal_header.innerHTML += ", ";
            }
            modal_header.innerHTML += "</p>";
        }
    }
    for(var i=0; i<best_fits.length; i++) {
        url = best_fits[i].url;
        ra = best_fits[i].ra;
        dec = best_fits[i].dec;
        id = best_fits[i].db_id;
        img_container.innerHTML +=
            "<div id="+id+">"+
            "<img src='" + url + "' alt='cutout" + i + "'>" +
            "</div>";
    }
}

window.onclick = function(event) {
    var modals = document.getElementsByClassName('modal');
    var img_container = document.getElementById('cutouts');
    Array.from(modals).forEach(function(modal) {
        if (event.target === modal) {
            img_container.innerHTML = '';
            modal.style.display = "none";
        }});
}

function open_aladin(path, idx) {
    $.get(path+'loc.txt', function(data) {
        var line = data.split("\n")[idx];
        var ra = line.split(';')[0];
        var dec = line.split(';')[1];
        console.log(ra, dec); // Uncomment to write coordinates to console
        aladin.gotoRaDec(ra,dec);
        aladin.setFov(12/60);
                   }, 'text');
}

function show_in_aladin(ra, dec, div_id) {
    var aladin = A.aladin(div_id,
            {showFullscreenControl: false, // Hide fullscreen controls
            showGotoControl: false, // Hide go-to controls
            showFrame: false, //Hide frame 'J2000' enzo
            showLayersControl : false,});
    aladin.gotoRaDec(ra,dec);
    aladin.setFov(12/60);
}

function magnify(event) {
    zoom = 10;
    var glass, w, h, bw;

    container = document.getElementById('som-container');

    /* Create magnifier glass: */
    glass = document.getElementById('magnify-window');
    pos = getCursorPos(event);
    glass.style.display = 'block';
    glass.style.backgroundImage = container.style.backgroundImage;
    glass.style.backgroundRepeat = "no-repeat";
    glass.style.backgroundSize = 100 * zoom + '%';

    /* Set background properties for the magnifier glass: */
    w = glass.offsetWidth / 2;
    h = glass.offsetHeight / 2;

    /* Execute a function when someone moves the magnifier glass over the image: */
    glass.addEventListener("mousemove", moveMagnifier);
    container.addEventListener("mousemove", moveMagnifier);

    /*and also for touch screens:*/
    glass.addEventListener("touchmove", moveMagnifier);
    container.addEventListener("touchmove", moveMagnifier);

    function moveMagnifier(e) {
        var pos, x, y;
        /* Prevent any other actions that may occur when moving over the image */
        e.preventDefault();
        /* Get the cursor's x and y positions: */
        pos = getCursorPos(e);
        x = pos.x;
        y = pos.y;
        glass_left = (x-5);
        glass_top = (y-5);
        glass.style.left = glass_left + "px";
        glass.style.top =  glass_top + "px";
        /* Display what the magnifier glass "sees": */
        container_bb = container.getBoundingClientRect();
        bg_x = container_bb.left - x;
        bg_y = container_bb.top - y;
        glass.style.backgroundPosition = (bg_x * (zoom/4)) + "px " +  (bg_y * (zoom/4)) + "px";
    }

    function getCursorPos(e) {
        x = e.clientX;
        y = e.clientY;
        return {x, y};
    }

    
}

function remove_magnifier(event) {
    glass = document.getElementById('magnify-window');
    glass.style.display = 'none';
}

function zoom_som(event) {
    container = document.getElementById('som-container');

    var e_delta = (event.deltaY || -event.wheelDelta || event.detail);
    var delta =  e_delta && ((e_delta >> 10) || 1) || 0;
    console.log(delta);
    var scale = 1;
    if(delta < 0) {
        scale += 0.1
    } else {
        scale -= 0.1
    }
    som_img_size = som_img_size * scale;
    container.style.backgroundSize = som_img_size * scale + '%';
}

function apply_label(data, label) {
    var csrf_token = $('input[name="'+csrf_token_name+'"]').attr('value');
    $.ajaxSetup({
    beforeSend: function(xhr) {
        xhr.setRequestHeader("X-CSRFToken", csrf_token);
    }
    });
    $.post({
    url: '/som/label/'+label,
    data: JSON.stringify(data),
    contentType: 'json',
    dataType: 'json',
    success: function (data) {
        if (data.success) {
            alert("The label was applied successfully to the selected images.")
        } else {
            alert("The label could not have been applied.")
        }
    }
    });
 }

function label_protos() {
    label = document.getElementById('label').value;
    selection = Array.from(document.getElementsByClassName(proto_selected));
    var data = { 'protos': selection.map(s => s.id)};
    apply_label(data, label)
}

function label_cutouts(proto_label) {
    if(proto_label) {
        label = selected_prototypes[0].label;
    } else {
        label = document.getElementById('cutout-label').value;
    }
    var img_container = document.getElementById('cutouts');
    cutouts = Array.from(img_container.childNodes);
    var data = { 'cutouts': cutouts.filter(c => c.id).map(c => c.id)};
    apply_label(data, label)
}

function change_view(img, button) {
    active_buttons = document.getElementsByClassName('active-action-button')
    for(i=0; i<active_buttons.length; i++) {
        active_buttons[i].classList.remove('active-action-button')
    }
    container = document.getElementById('som-container');
    if(button.id === 'prototype_button' || button.id === 'heatmap_button') {
        elements = Array.from(container.childNodes).filter(el => parseInt(el.id) == el.id);
        for(var i=0; i<elements.length; i++) {
            elements[i].style.backgroundColor = 'rgba(0, 0, 0, 0)';
            legend_container = document.getElementById('label-legend');
            legend_container.innerHTML = "";
            legend_container.style.backgroundColor = 'white';
        }
    }
    container.style.backgroundImage = 'url('+img+')';
    button.classList.add("active-action-button")
 }

 function color_map(img, button) {
    container = document.getElementById('som-container');
    elements = Array.from(container.childNodes).filter(el => parseInt(el.id) == el.id);
    var prototypes = [];
    var data = JSON.stringify({ 'protos': elements.map(el => el.id)});
    var csrf_token = $('input[name="'+csrf_token_name+'"]').attr('value');
    $.ajaxSetup({
        beforeSend: function(xhr) {
            xhr.setRequestHeader("X-CSRFToken", csrf_token);
        }
    });
    $.ajax({
        url: '/som/get_protos',
        data: data,
        dataType: 'json',
        method: 'POST',
        success: function (data) {
            if (data.success) {
                prototypes = data.protos
            }
        },
        async: false
    });

    for(var i=0; i < prototypes.length; i++) {
        label = prototypes[i].label;
        if(label !== '') {
            if(!(label in label_colors)) {
                color = getRandomColor();
                label_colors[label] = color
            }
            var r = label_colors[label][0];
            var g = label_colors[label][1];
            var b = label_colors[label][2];
            document.getElementById(prototypes[i].proto_id).style.backgroundColor = "rgba("+r+","+g+","+b+",0.7)";
        }
     }
    display_label_legend()
    change_view(img, button)
 }

 function getRandomColor() {
  var r = Math.floor(Math.random() * 255);
  var g = Math.floor(Math.random() * 255);
  var b = Math.floor(Math.random() * 255);
  return [r, g, b];
}

function display_label_legend() {
    legend_container = document.getElementById('label-legend');
    legend_container.style.backgroundColor = 'lavenderblush';
    legend_container.innerHTML = '<h3>Label legend</h3>';
    for(var label in label_colors) {
        var r = label_colors[label][0];
        var g = label_colors[label][1];
        var b = label_colors[label][2];
        legend_container.innerHTML += '<p style="color: rgb('+r+','+g+','+b+')">'+label+'</p>'
    }
}

 function show_selection_info(selected) {
     selection_info = document.getElementById('prototype-info');
     selection_info.innerHTML = '<h3>Selected: Prototype ('+ selected.x + ',' +  selected.y +')</h3>';
     label = selected.label.trim() !== '' ? selected.label : "Unlabeled";
     selection_info.innerHTML += '<p><b>Label: </b>'+ label + '</p>';
     selection_info.innerHTML += "<img src='" + selected.url + "'/>";
 }

function export_catalog(filename, data) {
    filename = filename.replace(/\s+/g, '');
    var csrf_token = $('input[name="'+csrf_token_name+'"]').attr('value');
    $.ajaxSetup({
    beforeSend: function(xhr) {
        xhr.setRequestHeader("X-CSRFToken", csrf_token);
    }
    });
    $.post({
    url: '/som/export/'+filename,
    data: JSON.stringify(data),
    contentType: 'json',
    dataType: 'json',
    success: function (data) {
        if (data.success) {
            alert("The catalog was exported and saved under the name " + filename + ".csv")
        } else {
            alert("The export was not possible")
        }
    }
    });
 }

