document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll('[data-modal-toggle]').forEach(trigger => {
        trigger.addEventListener('click', function(event) {
            event.preventDefault();
            const modalId = this.getAttribute('data-modal-toggle');
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.remove('hidden'); // Make sure the modal is visible before animating
                modal.classList.add('modal-show'); // Apply the opening animation
            }
        });
    });

    // Close modal with animation
    document.querySelectorAll('[data-modal-hide]').forEach(trigger => {
        trigger.addEventListener('click', function(event) {
            event.preventDefault();
            const modalId = this.getAttribute('data-modal-hide');
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.add('modal-hide'); // Start the closing animation
                
                // Wait for the animation to finish before hiding the modal
                modal.addEventListener('animationend', () => {
                    modal.classList.add('hidden'); // Finally hide the modal
                    modal.classList.remove('modal-show', 'modal-hide'); // Clean up animation classes
                }, {once: true}); // Ensure the event is only handled once
            }
        });
    });
});