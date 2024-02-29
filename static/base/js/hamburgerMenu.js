// Wait for the DOM to be fully loaded
document.addEventListener("DOMContentLoaded", function() {
    // Target the button using its 'data-collapse-toggle' attribute
    var toggleButton = document.querySelector('[data-collapse-toggle="navbar-default"]');

    // Function to toggle the menu
    function toggleMenu() {
        var menu = document.getElementById('navbar-default');
        if (menu.classList.contains('hidden')) {
        menu.classList.remove('hidden');
        } else {
        menu.classList.add('hidden');
        }
    }

    // Listen for click events on the toggle button
    toggleButton.addEventListener('click', toggleMenu);
    });