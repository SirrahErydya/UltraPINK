/**
 * Basic manipulation for PINK-generated SOMs
 */

var tool_selected = 'tool-selected';
var active_class = 'tool-active';
var csrf_token_name = "csrfmiddlewaretoken";
var selected_prototypes = [];
var selected_cutouts = [];
var label_colors = {};


function select_tool(id, grid_path) {
    var som_container = document.getElementById('som-container');
    var selected_tools = document.getElementsByClassName(tool_selected);
    var tool = document.getElementById(id);
    for(var i=0; i<selected_tools.length; i++) {
        if(selected_tools[i].id == 'magnifier') {
            remove_magnifier();
        } else if(selected_tools[i].id == 'zoom') {
            remove_zoom(som_container);
            som_container.style.transform = "scale(1) translate(0px, 0px)";
            show_info_panels();
        }
        selected_tools[i].classList.remove(tool_selected);
    }
    if(id == "magnifier") {
        magnify(grid_path);
    } else if(id == "zoom") {
        zoom_som(som_container);
        hide_info_panels();
    }
    tool.classList.add(tool_selected)
}

function toggle(id) {
    element = document.getElementById(id);
    if(element.classList.contains(active_class)) {
        element.classList.remove(active_class);
    } else {
        element.classList.add(active_class);
    }
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

function show_hover_preview(hovered) {
    if(selected_prototypes.length !== 1) {
        var proto_container = document.getElementById('prototype-enlargement');
        img = document.getElementById(hovered);
        proto_container.innerHTML = '';
        proto_container.appendChild(img.cloneNode(true));
    }
}

function show_selection_info(selected, element_id) {
     selection_info = document.getElementById(element_id);
     selection_info.innerHTML = '<p class="subheadline">Selected: Prototype ('+ selected.x + ',' +  selected.y +')</p>';
     label = selected.label === '' ?  "Unlabeled" : selected.label.name;
     selection_info.innerHTML += '<p><b>Label: </b>'+ label + '</p>';
 }

function show_info_panels() {
    var info_text = document.getElementById('som-info');
    info_text.style.display = "block";
    var proto_container = document.getElementById('prototype-enlargement');
    proto_container.style.display = "block";
}

function hide_info_panels() {
    var info_text = document.getElementById('som-info');
    info_text.style.display = "none";
    var proto_container = document.getElementById('prototype-enlargement');
    proto_container.style.display = "none";
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
    cutout_view();
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
    som_container.style.display = "none";
    modal.style.display = 'block';
}

function create_cutout_images(best_fits, protos, outlier_case) {
    var img_container = document.getElementById('cutouts');
    var modal_header = document.getElementById('modal-header');
    var proto_label_button1 = document.getElementById("label-cutouts-proto");
    var proto_label_button2 = document.getElementById("label-all-cutouts-proto");
    var export_outliers_button = document.getElementById("export-outliers");
    if(outlier_case) {
        modal_header.innerHTML = "<p>These are the "+ best_fits.length +" images that fit the least to any of the prototypes.</p>";
        proto_label_button1.style.display = 'none';
        proto_label_button2.style.display = 'none';
        export_outliers_button.style.display = 'inline';
    } else {
        modal_header.innerHTML = "<p>These are the "+ best_fits.length +" best matching images to your choice.</p>";
        proto_label_button1.style.display = 'inline';
        proto_label_button2.style.display = 'inline';
        export_outliers_button.style.display = 'none';
    }
    for(var i=0; i<best_fits.length; i++) {
        url = best_fits[i].url;
        ra = best_fits[i].ra;
        dec = best_fits[i].dec;
        id = best_fits[i].db_id;
        img_container.innerHTML +=
            "<div class='cutout-img' id='cutout"+id+"' onclick='on_cutout_click("+id+")'>"+
            "<img src='" + url + "' alt='cutout" + i + "'>" +
            "</div>";
    }
}

function on_cutout_click(cutout_id) {
    var inspect = document.getElementById('inspect-cutout');
    if(inspect.classList.contains(active_class)) {
        request_page('/cutouts/cutout-view', [project_id, som_id, cutout_id]);
    } else {
        click_image(cutout_id, false);
    }
}

function close_cutout_modal() {
    var som_container = document.getElementById('som-container');
    var modal = document.getElementById('modal-window');
    var img_container = document.getElementById('cutouts');
    img_container.innerHTML = '';
    modal.style.display = "none";
    som_container.style.display = 'grid';
    selected_cutouts = []
}

function magnify(img_path) {
    zoom = 5;
    var glass, w, h, bw;

    container = document.getElementById('som-container');

    /* Create magnifier glass: */
    glass = document.getElementById('magnify-window');
    glass.style.backgroundImage = "url('" + img_path + "')";
    glass.style.display = "block";
    glass.style.backgroundRepeat = "no-repeat";
    glass.style.backgroundSize = (container.scrollWidth * zoom) + "px " + (container.scrollHeight * zoom) + "px";


    /* Set background properties for the magnifier glass: */
    w = glass.offsetWidth / 2;
    h = glass.offsetHeight / 2;
    bw = 1; // Border width

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
        /* Prevent the magnifier glass from being positioned outside the image: */
        container_bb = container.getBoundingClientRect();
        if (x > container_bb.right - (w )) {x = container_bb.right - (w );}
        if (x < container_bb.left + (w )) {x = container_bb.left + (w );}
        if (y > container_bb.bottom - (h )) {y = container_bb.bottom - (h );}
        if (y < container_bb.top + (h )) {y = container_bb.top + (h );}
        glass_left = (x-w);
        glass_top = (y-h);
        glass.style.left = glass_left + "px";
        glass.style.top =  glass_top + "px";
        /* Display what the magnifier glass "sees": */
        glass.style.backgroundPosition = "-" + (((x-container_bb.left) * zoom) - w + bw) + "px -" +
            (((y-container_bb.top) * zoom) - h + bw) + "px";

    }

    function getCursorPos(e) {
        x = e.clientX;
        y = e.clientY;
        return {x, y};
    }

    
}

function remove_magnifier() {
    glass = document.getElementById('magnify-window');
    glass.style.display = 'none';
}

function zoom_som(container) {
    var scale = 1;
    var point_x = 0;
    var point_y = 0;
    var start = { x: 0, y: 0 };
    var panning = false;

    function set_transform() {
        container.style.transform = "translate(" + point_x + "px, " + point_y + "px) scale(" + scale + ")";
    }

    container.onmousedown = function (e) {
        e.preventDefault();
        start = { x: e.clientX - point_x, y: e.clientY - point_y };
        panning = true;
    };

    container.onmouseup = function (e) {
        panning = false;
    };

    container.onmousemove = function (e) {
        e.preventDefault();
        if (!panning) {
          return;
        }
        point_x = (e.clientX - start.x);
        point_y = (e.clientY - start.y);
        set_transform();
    };


    container.onwheel = function (e) {
        e.preventDefault();
        var delta = (e.wheelDelta ? e.wheelDelta : -e.deltaY);
        (delta > 0) ? (scale *= 1.2) : (scale /= 1.2);
        set_transform();
    }


}

function remove_zoom(container) {
    container.onwheel = [];
    container.onmousedown = [];
    container.onmousemove = [];
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

function view(view, img) {
    active_buttons = document.getElementsByClassName('view-selected');
    for(i=0; i<active_buttons.length; i++) {
        if(active_buttons[i].id !== 'hist-button') {
            active_buttons[i].classList.remove('view-selected');
        }
    }
    container = document.getElementById('som-container');
    legend_container = document.getElementById('label-legend');
    var som_info = document.getElementById('info-table');
    if(view === 'proto') {
        container.classList.remove('transparent-view');
        button = document.getElementById('prototype_button');
    } else {
        container.classList.add('transparent-view');
    }
    if(view === 'heatmap') {
        container.style.backgroundImage = 'url('+img+')';
        button = document.getElementById('heatmap_button')
    } else {
        container.style.backgroundImage = '';
    }
    if(view === 'labels') {
        som_info.style.display = 'none';
        legend_container.style.display = 'block';
        button = document.getElementById('labels_button')
    } else {
        som_info.style.display = 'table';
        legend_container.style.display = 'none';
    }
    button.classList.add("view-selected");
}

function proto_color(proto_id, r, g, b, view) {
    img = document.getElementById(proto_id);
    proto = img.parentElement;
    if(view === 'proto') {
        proto.style.backgroundColor = 'rgba(255,255,255,0)';
    } else if(view === 'heatmap') {
        proto.style.backgroundColor = 'rgba(255,255,255,0)';
    } else if(view === 'labels') {
        proto.style.backgroundColor = 'rgba(' + r + ',' + g + ',' + b + ',' + 1 + ')';
    }
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

