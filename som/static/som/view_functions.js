function collapse(id, container_id) {
    button = document.getElementById(id);
    container = document.getElementById(container_id);
    button.classList.toggle('active');
    display_style = container.style.display
    if(display_style === 'grid') {
        container.style.display = 'none';
    } else {
        container.style.display = 'grid';
    }
}

function activate_tab(tabName) {
    var i;
    var tabs = document.getElementsByClassName("tab");
    var tabButtons = document.getElementsByClassName("tab-button");
    for (i = 0; i < tabs.length; i++) {
     tabs[i].style.display = "none";
     tabButtons[i].classList.remove('active');
    }
    document.getElementById(tabName).style.display = "block";
    document.getElementById(tabName+"-tab").classList.add("active")
}