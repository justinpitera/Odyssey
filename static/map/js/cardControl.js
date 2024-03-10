// Initialize variables to keep track of mouse positions
let offsetX, offsetY;

// Function to handle mouse down event on the draggable handle
function dragMouseDown(event) {
    event.preventDefault();
    // Get the current mouse position
    offsetX = event.clientX;
    offsetY = event.clientY;
    // Register mousemove and mouseup event listeners
    document.addEventListener('mousemove', elementDrag);
    document.addEventListener('mouseup', closeDragElement);
}

// Function to handle mouse move event while dragging
function elementDrag(event) {
    event.preventDefault();
    // Calculate the new position of the airport card
    const airportCard = document.getElementById('airport-card');
    airportCard.style.left = (airportCard.offsetLeft - offsetX + event.clientX) + 'px';
    airportCard.style.top = (airportCard.offsetTop - offsetY + event.clientY) + 'px';
    // Update the mouse positions
    offsetX = event.clientX;
    offsetY = event.clientY;
}

// Function to handle mouse up event and remove event listeners
function closeDragElement() {
    document.removeEventListener('mousemove', elementDrag);
    document.removeEventListener('mouseup', closeDragElement);
}

// Add event listener to the draggable handle for mouse down event
document.querySelector('#airport-card .draggable-handle').addEventListener('mousedown', dragMouseDown);



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