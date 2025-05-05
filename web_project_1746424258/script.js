document.addEventListener('DOMContentLoaded', function() {
    createConfetti();
});

function createConfetti() {
    const container = document.getElementById('confetti-container');
    const colors = ['#f44336', '#e91e63', '#9c27b0', '#673ab7', '#3f51b5', 
                   '#2196f3', '#03a9f4', '#00bcd4', '#009688', '#4CAF50', 
                   '#8BC34A', '#CDDC39', '#FFEB3B', '#FFC107', '#FF9800', '#FF5722'];
    
    const confettiCount = 100;
    
    for (let i = 0; i < confettiCount; i++) {
        setTimeout(() => {
            const confetti = document.createElement('div');
            confetti.classList.add('confetti');
            
            // Random position
            const startPositionX = Math.random() * window.innerWidth;
            
            // Random color
            const color = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.backgroundColor = color;
            
            // Random rotation
            const rotation = Math.random() * 360;
            confetti.style.transform = `rotate(${rotation}deg)`;
            
            // Set initial position
            confetti.style.left = `${startPositionX}px`;
            confetti.style.top = '-10px';
            
            container.appendChild(confetti);
            
            // Animate falling
            animateConfetti(confetti);
        }, i * 50);
    }
}

function animateConfetti(confetti) {
    const animationDuration = 3000 + Math.random() * 2000;
    const finalPositionY = window.innerHeight + 10;
    const finalPositionX = parseInt(confetti.style.left) + (Math.random() * 200 - 100);
    
    confetti.animate([
        { transform: `translate(0, 0) rotate(0deg)`, opacity: 1 },
        { transform: `translate(${Math.random() * 100 - 50}px, ${finalPositionY / 2}px) rotate(${Math.random() * 360}deg)`, opacity: 0.8 },
        { transform: `translate(${finalPositionX - parseInt(confetti.style.left)}px, ${finalPositionY}px) rotate(${Math.random() * 720}deg)`, opacity: 0 }
    ], {
        duration: animationDuration,
        easing: 'cubic-bezier(0.215, 0.61, 0.355, 1)'
    }).onfinish = function() {
        confetti.remove();
        // Create new confetti for continuous effect
        const newConfetti = document.createElement('div');
        newConfetti.classList.add('confetti');
        newConfetti.style.backgroundColor = confetti.style.backgroundColor;
        newConfetti.style.left = `${Math.random() * window.innerWidth}px`;
        newConfetti.style.top = '-10px';
        document.getElementById('confetti-container').appendChild(newConfetti);
        animateConfetti(newConfetti);
    };
}
