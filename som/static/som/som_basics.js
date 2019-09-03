/**
 * Basic manipulation for PINK-generated SOMs
 */

var proto_selected = 'proto-selected';
var tool_selected = 'tool-selected';

function select_tool(id) {
    var selected_tools = document.getElementsByClassName(tool_selected);
    var tool = document.getElementById(id);
    for(var i=0; i<selected_tools.length; i++) {
        selected_tools[i].classList.remove(tool_selected);
    }
    tool.classList.add(tool_selected)
}

function click_prototype(id) {
    var img = document.getElementById(id);
    var tool = document.getElementsByClassName(tool_selected)[0];
    if(tool.id == 'pointer') {
        select_single(img);
    } else if(tool.id == 'zoom') {

    } else if(tool.id == 'magnifier') {

    } else if(tool.id == 'select') {
        select_multiple(img);
    } else if(tool.id == 'wand') {

    }
}

function select_single(img) {
    var already_active = img.classList.contains(proto_selected);
    var selected_imgs = document.getElementsByClassName(proto_selected);
    for(var i=0; i<selected_imgs.length; i++) {
        selected_imgs[i].classList.remove(proto_selected);
    }
    if(!already_active) {
        img.classList.add(proto_selected);
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
    input_field = document.getElementById('input-cutouts');
    selection = document.getElementsByClassName(proto_selected);
    if(selection.length > 1) {
        var data = '{ "protos": [ "' + selection[0].id;
        for(var i=1; i<selection.length; i++) {
            data += '", "' + selection[i].id;
        }
        data += '" ] }';
        request_cutouts( '/som/get_best_fits/'+input_field.value, data)
    } else if (selection.length === 1){
        request_cutouts('/som/get_best_fits/'+selection[0].id+'/'+input_field.value, "");
    } else {
        alert("No prototypes are selected. Use one of the tools to select one or many prototypes.");
    }
}

function show_outliers() {
    input_field = document.getElementById('input-outliers');
    request_cutouts('/som/get_outliers/'+input_field.value, '');
}



// Open a popup with the best fits for a prototype
function request_cutouts(url, data) {
    var modal = document.getElementById('modal');
    modal.style.display = 'block';
    var img_container = document.getElementById('cutouts');
    $.ajax({
        url: url,
        data: data,
        dataType: 'json',
        success: function (data) {
            if (data.success) {
                var best_fits = data.best_fits;
                img_container.innerHTML = '';
                for(var i=0; i<best_fits.length; i++) {
                    url = best_fits[i].url;
                    ra = best_fits[i].ra;
                    dec = best_fits[i].dec;
                    img_container.innerHTML +=
                        "<div id=cutout"+i+">"+
                        "<img src='" + url + "' alt='cutout" + i + "' onclick='show_in_aladin("+ra+","+dec+", cutout"+i+")'></div>";
                }
            }
        }
      });
}

window.onclick = function(event) {
    var modals = document.getElementsByClassName('modal');
    Array.from(modals).forEach(function(modal) {
        if (event.target === modal) {
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
