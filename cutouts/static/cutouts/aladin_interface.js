function aladin_window() {
    var raH = document.getElementById('raH').value;
    var raM = document.getElementById('raM').value;
    var raS = document.getElementById('raS').value;
    var decD = document.getElementById('decD').value;
    var decM = document.getElementById('decM').value;
    var decS = document.getElementById('decS').value;
    var aladin = A.aladin('#aladin-lite-div', {
        survey: "P/DSS2/color",
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