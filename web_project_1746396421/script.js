document.addEventListener('DOMContentLoaded', function() {
    const actionButton = document.getElementById('action-button');
    const circle = document.querySelector('.circle');
    const mainTitle = document.querySelector('.main-title');
    
    // Array of fun colors for the title
    const colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6'];
    let colorIndex = 0;
    
    // Button click event
    actionButton.addEventListener('click', function() {
        // Toggle the active class on the circle
        circle.classList.toggle('active');
        
        // Change the title color
        colorIndex = (colorIndex + 1) % colors.length;
        mainTitle.style.color = colors[colorIndex];
        
        // Add a small animation to the title
        mainTitle.style.transform = 'scale(1.1)';
        setTimeout(() => {
            mainTitle.style.transform = 'scale(1)';
        }, 300);
        
        // Change button text based on circle state
        if (circle.classList.contains('active')) {
            actionButton.textContent = 'Reset';
        } else {
            actionButton.textContent = 'Click Me!';
        }
    });
    
    // Add hover effect to the circle
    circle.addEventListener('mouseover', function() {
        if (!circle.classList.contains('active')) {
            circle.style.transform = 'scale(1.2)';
        }
    });
    
    circle.addEventListener('mouseout', function() {
        if (!circle.classList.contains('active')) {
            circle.style.transform = 'scale(1)';
        }
    });
});
