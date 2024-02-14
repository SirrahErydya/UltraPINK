function aladin_window() {
    var raH = document.getElementById('raH').value;
    var raM = document.getElementById('raM').value;
    var raS = document.getElementById('raS').value;
    var decD = document.getElementById('decD').value;
    var decM = document.getElementById('decM').value;
    var decS = document.getElementById('decS').value;
    var survey = document.getElementById('survey').value;
    var aladin = A.aladin('#aladin-lite-div', {
        survey: survey,
        fov:0.05,
        target: raH + ' ' + raM + ' ' + raS + ' ' + decD + ' ' + decM + ' ' + decS});
    return false; // To prevent the page reload
}

function reset_position(raH, raM, raS, decD, decM, decS) {
    document.getElementById('raH').value = raH;
    document.getElementById('raM').value = raM;
    document.getElementById('raS').value = raS;
    document.getElementById('decD').value = decD;
    document.getElementById('decM').value = decM;
    document.getElementById('decS').value = decS;
    aladin_window()
}

function request_spatial_cutouts(cutout_id) {
    var csrf_token_name = "csrfmiddlewaretoken";
    var csrf_token = $('input[name="'+csrf_token_name+'"]').attr('value');
    var n = document.getElementById('number_cutouts').value;
    var url = '/cutouts/get_cutouts/' + cutout_id + '/' + n;
    $.ajaxSetup({
        beforeSend: function(xhr) {
            xhr.setRequestHeader("X-CSRFToken", csrf_token);
        }
    });
    $.ajax({
        url: url,
        data: '',
        dataType: 'json',
        method: 'POST',
        success: function (data) {
            if (data.success) {
                display_cutouts(data.closest_cuts);
            } else {
                alert("Error during cutout request")
            }
        }
      });
    return false;
}

function display_cutouts(cutouts) {
    container = document.getElementById('cutout-container');
    container.innerHTML = '';
    for(var i=0; i<cutouts.length; i++) {
        container.innerHTML +=
            '<div class="row">' +
                '<div class="col s2">' +
                    '<a href="/cutouts/cutout-view/' + project_id + '/' + som_id + '/' + cutouts[i].db_obj.db_id + '">' +
                    '<img src="' + cutouts[i].db_obj.url + '"/></a>' +
                '</div>' +
                '<div class="col s10">' +
                    '<p><b>Cutout #' + cutouts[i].db_obj.index + ' (' + cutouts[i].identifier + ')</b></p>' +
                    '<div class="row">' +
                        '<div class="col s3">' +
                            '<b>Position:</b>' +
                        '</div>' +
                        '<div class="col s4">'+
                            '<p>RAJ200 = ' + cutouts[i].location.ra + '</p>' +
                        '</div>' +
                        '<div class="col s4">' +
                            '<p>DECJ200 =' + cutouts[i].location.dec + '</p>' +
                        '</div>' +
                    '</div>' +
                    '<div class="row">' +
                        '<div class="col s3">' +
                            '<b>Closest Prototype:</b>' +
                        '</div>' +
                        '<div class="col s8">' +
                            '<p>' +
                                '(' + cutouts[i].db_obj.closest_proto.x +',' + cutouts[i].db_obj.closest_proto.y + ')' +
                            '</p>' +
                        '</div>' +
                    '</div>' +
                    '<div class="row">' +
                        '<div class="col s3">' +
                            '<b>Distance:</b>' +
                        '</div>' +
                        '<div class="col s8">' +
                            '<p>' +
                                cutouts[i].distance +  " deg" +
                            '</p>' +
                        '</div>' +
                    '</div>' +
                '</div>';
    }
}