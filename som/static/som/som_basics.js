/**
 * Basic manipulation for PINK-generated SOMs
 * Written by Rafael Mostert
 */

var survery_dir =
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


// Open a popup with the best fits for a prototype
function show_best_fits(id) {
    var modal = document.getElementById('modal'+id);
    modal.style.display = 'block';
    var img_container = document.getElementById('cutouts'+id);
    var url = "";
    if(id === '-o') {
        url = '/som/get_outliers/'+10
    } else {
        url = '/som/get_best_fits/'+id+'/'+10
    }
    if(img_container.innerHTML === null || img_container.innerHTML.trim().length === 0) {
        $.ajax({
            url: url,
            dataType: 'json',
            success: function (data) {
                if (data.success) {
                    var best_fits = data.best_fits;
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
