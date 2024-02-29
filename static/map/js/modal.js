document.getElementById('filters-btn').addEventListener('click', function() {
    const modal = document.getElementById('modal');
    modal.classList.remove('hidden', 'modal-exit'); // Remove hidden and any exit animation class
    modal.classList.add('modal-enter'); // Trigger the pop-in animation
});

document.getElementById('close-modal').addEventListener('click', function() {
    const modal = document.getElementById('modal');
    modal.classList.add('modal-exit'); // Start the pop-out animation
    
    setTimeout(() => {
        modal.classList.add('hidden'); // Hide the modal after the animation
        modal.classList.remove('modal-enter', 'modal-exit'); // Clean up animation classes
    }, 500); // Match the duration of your popOut animation
});