function toggleMenu() {
    var menu = document.querySelector('.nav-menu');
    if (menu.style.opacity === '1') {
        menu.style.opacity = '0';
        setTimeout(function() { menu.style.display = 'none'; }, 500); // Wait for animation
    } else {
        menu.style.display = 'block';
        setTimeout(function() { menu.style.opacity = '1'; }, 10); // Small delay to start transition
    }
}
