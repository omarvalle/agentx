document.addEventListener('DOMContentLoaded', () => {
    // Add a subtle background animation
    const container = document.querySelector('.container');
    
    // Add some random particles in the background
    for (let i = 0; i < 20; i++) {
        createParticle();
    }
    
    // Make the text interactive on hover
    const message = document.querySelector('.message');
    message.addEventListener('mouseover', () => {
        message.style.color = '#e74c3c';
    });
    
    message.addEventListener('mouseout', () => {
        message.style.color = '#ecf0f1';
    });
});

function createParticle() {
    const body = document.querySelector('body');
    const particle = document.createElement('div');
    
    // Style the particle
    particle.style.position = 'absolute';
    particle.style.width = Math.random() * 5 + 'px';
    particle.style.height = particle.style.width;
    particle.style.background = 'rgba(255, 255, 255, 0.5)';
    particle.style.borderRadius = '50%';
    
    // Position the particle randomly
    particle.style.left = Math.random() * 100 + 'vw';
    particle.style.top = Math.random() * 100 + 'vh';
    
    // Add animation
    particle.style.animation = `float ${Math.random() * 10 + 5}s linear infinite`;
    
    // Add to DOM
    body.appendChild(particle);
    
    // Create keyframes for floating animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes float {
            0% {
                transform: translate(0, 0);
                opacity: 0;
            }
            10% {
                opacity: 1;
            }
            90% {
                opacity: 1;
            }
            100% {
                transform: translate(${Math.random() * 100 - 50}px, ${Math.random() * -100 - 50}px);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}
