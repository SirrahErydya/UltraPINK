/**
 * Basic manipulation for PINK-generated SOMs
 */

var proto_selected = 'proto-selected';
var tool_selected = 'tool-selected';


function select_tool(id) {
    var som_container = document.getElementById('som-container');
    var selected_tools = document.getElementsByClassName(tool_selected);
    var tool = document.getElementById(id);
    for(var i=0; i<selected_tools.length; i++) {
        if(selected_tools[i].id == 'magnifier') {
            deactivate_magnifier();
            som_container.removeEventListener("mousemove", magnify);
        }
        selected_tools[i].classList.remove(tool_selected);
    }
    if(id == "magnifier") {
        som_container.addEventListener("mousemove", magnify);
    }
    tool.classList.add(tool_selected)
}

function click_prototype(id) {
    var img = document.getElementById(id);
    var tool = document.getElementsByClassName(tool_selected)[0];
    if(tool.id == 'pointer') {
        select_single(img);
    } else if(tool.id == 'zoom') {

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

function magnify(event) {
    zoom = 20;
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
    bw = 3;
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
        glass.style.left = (x-w-container.style.left) + "px";
        glass.style.top = (y-h-container.style.top) + "px";
        if(x < container.style.left || x > container.style.left + container.style.width ||
            y < container.style.top || y > container.style.top + container.style.height) {
            glass.style.display = 'none';
        } else {
            glass.style.display = 'block';
        }
        /* Display what the magnifier glass "sees": */
        glass.style.backgroundPosition = "-" + ((x * zoom) - w + bw) + "px -" + ((y * zoom) - h + bw) + "px";
    }

    function getCursorPos(e) {
        x = e.clientX;
        y = e.clientY;
        return {x, y};
    }

    
}