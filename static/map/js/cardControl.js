

// Function to handle mouse down event on the draggable handle
function dragMouseDown(event, elementId) {
    event.preventDefault();
    let element = document.getElementById(elementId);
    
    // Initialize variables to keep track of mouse positions within the closure
    let offsetX = event.clientX;
    let offsetY = event.clientY;

    // Function to handle mouse move event while dragging
    function elementDrag(event) {
        event.preventDefault();
        // Calculate the new cursor position:
        let dx = offsetX - event.clientX;
        let dy = offsetY - event.clientY;
        offsetX = event.clientX;
        offsetY = event.clientY;

        // Set the element's new position:
        element.style.top = (element.offsetTop - dy) + "px";
        element.style.left = (element.offsetLeft - dx) + "px";
    }

    // Function to handle mouse up event and remove event listeners
    function closeDragElement() {
        // Stop moving when mouse button is released:
        document.removeEventListener('mousemove', elementDrag);
        document.removeEventListener('mouseup', closeDragElement);
    }

    // Register mousemove and mouseup event listeners
    document.addEventListener('mousemove', elementDrag);
    document.addEventListener('mouseup', closeDragElement);
}

// Attach the mousedown event listener to the draggable handle of both the airport and plan flight cards
document.querySelector('#airport-card .draggable-handle')?.addEventListener('mousedown', function(event) {
    dragMouseDown(event, 'airport-card');
});

document.querySelector('#plan-flight-card .draggable-handle')?.addEventListener('mousedown', function(event) {
    dragMouseDown(event, 'plan-flight-card');
});

function changeTab(tabId) {
    document.querySelectorAll('#tabContents > div').forEach(function(div) {
        div.style.display = 'none';
    });
    document.getElementById(tabId).style.display = 'block';

    // Update tabs to show active state
    document.querySelectorAll('#tabs a').forEach(function(a) {
        a.classList.remove('text-blue-600', 'border-blue-600');
        a.classList.add('text-gray-500', 'border-transparent');
    });
    document.querySelector(`#tabs a[onclick="changeTab('${tabId}')"]`).classList.add('text-blue-600', 'border-blue-600');
}

// Initialize the first tab as active
changeTab('details');

// Close airport card when clicking close button
document
  .getElementById("close-airport-card-btn")
  .addEventListener("click", function () {
    document.getElementById("airport-card").style.display = "none";
  });

  // Close airport card when clicking close button
  document
  .getElementById("close-flightplan-card-btn")
  .addEventListener("click", function () {
    document.getElementById("plan-flight-card").style.display = "none";
  });



