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