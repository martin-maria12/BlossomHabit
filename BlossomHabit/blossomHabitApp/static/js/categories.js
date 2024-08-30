document.addEventListener('DOMContentLoaded', function() {
    var postIts = document.querySelectorAll('.post-it');
    // pentru fiecare cateogorie gasita retinem numele ei pentru a putea redirectiona catre pagina dedicata ei utilizatorul
    postIts.forEach(function(postIt) {
        postIt.addEventListener('click', function() {
            var categoryName = postIt.getAttribute('data-category-name');
            window.location.href = '/category?category=' + encodeURIComponent(categoryName);
        });
    });
});
