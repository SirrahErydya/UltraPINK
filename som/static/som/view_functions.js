function collapse(id, container_id) {
    button = document.getElementById(id);
    container = document.getElementById(container_id);
    button.classList.toggle('active');
    if(container.style.display === 'block') {
        container.style.display = 'none';
    } else {
        container.style.display = 'block';
    }
}