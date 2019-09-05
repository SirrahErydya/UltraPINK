
function request_page(url, args) {
    link = url;
    for(i=0; i<args.length; i++) {
        link += '/' + args[i];
    }
    window.location.href = link
}