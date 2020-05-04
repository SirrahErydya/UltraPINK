/**
 * Basic manipulation for PINK-generated SOMs
 */

var tool_selected = 'tool-selected';
var som_img_size = 100;
var csrf_token_name = "csrfmiddlewaretoken";
var selected_prototypes = [];
var selected_cutouts = [];
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

function click_image(html_id, db_id, is_proto) {
    var selected_class = is_proto ? 'proto-selected' : 'cutout-selected';
    var el_id = is_proto ? html_id : "cutout"+html_id;
    var img = document.getElementById(el_id);
    var tool = document.getElementsByClassName(tool_selected)[0];
    if(tool.id == 'pointer') {
        select_single(img, db_id, selected_class);
    } else if(tool.id == 'selection') {
        select_multiple(img, db_id, selected_class)
    }
}

function select_single(img, db_id, selected_class) {
    var already_active = img.classList.contains(selected_class);
    var selected_imgs = document.getElementsByClassName(selected_class);
    var proto_container = document.getElementById('prototype-enlargement');
    proto_container.innerHTML = '';
    for(var i=0; i<selected_imgs.length; i++) {
        selected_imgs[i].classList.remove(selected_class);
        if(selected_class == 'proto-selected') {
            selection_info = document.getElementById('proto-info');
            selection_info.innerHTML = '';
            selected_prototypes = [];
        } else if(selected_class == 'cutout-selected') {
            selected_cutouts = []
        }
    }
    if(!already_active) {
        proto_container.appendChild(img.cloneNode(true));
        img.classList.add(selected_class);
        if(selected_class == 'proto-selected') {
            request_prototypes([img.id]);
            show_selection_info(selected_prototypes[0], 'proto-info')
        } else if(selected_class == 'cutout-selected') {
            //selected_cutouts.push(img)
        }
    }
}

function show_selection_info(selected, element_id) {
     selection_info = document.getElementById(element_id);
     selection_info.innerHTML = '<h3>Selected: Prototype ('+ selected.x + ',' +  selected.y +')</h3>';
     label = selected.label.name.trim() !== '' ? selected.label.name : "Unlabeled";
     selection_info.innerHTML += '<p><b>Label: </b>'+ label + '</p>';
 }


function select_multiple(img, db_id, selected_class) {
    if(img.classList.contains(selected_class)) {
        img.classList.remove(selected_class);
        if(selected_class == 'cutout-selected') {
            selected_cutouts.filter(i => i !== img)
        }
    } else {
        img.classList.add(selected_class);
        if(selected_class == 'cutout-selected') {
            selected_cutouts.push(img)
        }
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

function show_best_fits(som_id) {
    var input_field = document.getElementById('input-cutouts');
    selection = Array.from(document.getElementsByClassName('proto-selected'));
    if(selection.length <= 0){
        alert("No prototypes are selected. Use one of the tools to select one or many prototypes.");
        return;
    }
    var data = JSON.stringify({ 'protos': selection.map(s => s.id)});
    request_cutouts( '/som/get_best_fits/'+som_id+'/'+input_field.value, data);
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
    cutout_view()
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

function cutout_view() {
    var som_container = document.getElementById('som-container');
    var modal = document.getElementById('modal-window');
    var som_info = document.getElementById('som-info');
    som_container.style.width = '40vh';
    som_container.style.height = '40vh';
    modal.style.display = 'block';
    som_info.style.display = 'none';
}

function create_cutout_images(best_fits, protos, outlier_case) {
    var img_container = document.getElementById('cutouts');
    var modal_header = document.getElementById('modal-header');
    var proto_label_button1 = document.getElementById("label-cutouts-proto");
    var proto_label_button2 = document.getElementById("label-all-cutouts-proto");
    var export_outliers_button = document.getElementById("export-outliers");
    if(outlier_case) {
        modal_header.innerHTML = "<h1>These are the "+ best_fits.length +" images that fit the least to any of the prototypes.</h1>";
        proto_label_button1.style.display = 'none';
        proto_label_button2.style.display = 'none';
        export_outliers_button.style.display = 'inline';
    } else {
        modal_header.innerHTML = "<h1>These are the "+ best_fits.length +" best matching images to your choice.</h1>";
        proto_label_button1.style.display = 'inline';
        proto_label_button2.style.display = 'inline';
        export_outliers_button.style.display = 'none';

        for(var i=0; i<protos.length; i++) {
            show_selection_info(protos[i], "prototype-preview")
        }
    }
    for(var i=0; i<best_fits.length; i++) {
        url = best_fits[i].url;
        ra = best_fits[i].ra;
        dec = best_fits[i].dec;
        id = best_fits[i].db_id;
        img_container.innerHTML +=
            "<div class='cutout-img' id='cutout"+id+"' onclick='click_image("+id+",  false)'>"+
            "<img src='" + url + "' alt='cutout" + i + "'>" +
            "</div>";
    }
}

function close_cutout_modal() {
    var som_container = document.getElementById('som-container');
    var modal = document.getElementById('modal-window');
    var som_info = document.getElementById('som-info');
    var img_container = document.getElementById('cutouts');
    var proto_preview = document.getElementById('prototype-preview');
    img_container.innerHTML = '';
    proto_preview.innerHTML = '';
    modal.style.display = "none";
    som_container.style.width = '80vh';
    som_container.style.height = '80vh';
    som_info.style.display = 'block';
    selected_cutouts = []
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
    selection = Array.from(document.getElementsByClassName('proto-selected'));
    var data = { 'protos': selection.map(s => s.id)};
    apply_label(data, label)
}

function label_all_cutouts(proto_label) {
    var img_container = document.getElementById('cutouts');
    cutouts = Array.from(img_container.childNodes);

    label_cutouts(cutouts, proto_label)
}

function label_selected_cutouts(proto_label) {
    label_cutouts(selected_cutouts, proto_label)
}

function label_cutouts(cutouts, proto_label) {
    if(proto_label) {
        label = selected_prototypes[0].label;
    } else {
        label = document.getElementById('cutout-label').value;
    }
    var data = { 'cutouts': cutouts.filter(c => c.id).map(c => c.id.match(/\d/g).join(""))};
    apply_label(data, label)
}

function change_view(button) {
    active_buttons = document.getElementsByClassName('view-selected');
    for(i=0; i<active_buttons.length; i++) {
        if(active_buttons[i].id !== 'hist-button') {
            active_buttons[i].classList.remove('view-selected');
        }
    }
    container = document.getElementById('som-container');
    legend_container = document.getElementById('label-legend');
    var som_info = document.getElementById('info-table');
    if(button.id !== 'heatmap_button') {
        container.classList.remove('heatmap-view')
    }
    if(button.id === 'labels_button') {
        som_info.style.display = 'none';
        legend_container.style.display = 'block';
    } else {
        som_info.style.display = 'table';
        legend_container.style.display = 'none';
    }
    button.classList.add("view-selected");
}

 function proto_view(button) {
    change_view(button);
    container.style.backgroundImage = '';
    elements = container.getElementsByClassName('prototype');
 }

 function heatmap_view(img, button) {
    change_view(button);
    container = document.getElementById('som-container');
    container.style.backgroundImage = 'url('+img+')';
    container.classList.add('heatmap-view');
    elements = container.getElementsByClassName('prototype');
 }

function export_outliers() {
    var img_container = document.getElementById('cutouts');
    outliers = Array.from(img_container.childNodes);
    var data = { 'outlier_ids': outliers.filter(c => c.id).map(c => c.id.match(/\d/g).join(""))};
    export_catalog('outliers', data)
}

function toggle_histogram(button) {
    var hist_container = document.getElementById('histogram');
    var legend_container = document.getElementById('label-legend');
    var som_info = document.getElementById('info-table');
    if(button.classList.contains('view-selected')) {
        hist_container.style.display = 'none';
        button.classList.remove('view-selected');
        active_view = document.getElementsByClassName('view-selected')[0];
        if(active_view.id === 'labels_button') {
            legend_container.style.display = 'block';
        } else {
            som_info.style.display = 'block';
        }
    } else {
        button.classList.add('view-selected');
        hist_container.style.display = 'block';
        legend_container.style.display = 'none';
        som_info.style.display = 'none';
    }

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

