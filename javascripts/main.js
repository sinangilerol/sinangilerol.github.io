copyright_year = document.getElementById('copyright-year');
updateYear(copyright_year);

function updateYear(element) {
    current_year = new Date().getFullYear();
    element.innerHTML = current_year;
}