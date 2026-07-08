document.addEventListener('DOMContentLoaded', () => {
    // 1. Initial Fade In Animations
    setTimeout(() => {
        const elements = document.querySelectorAll('.fade-up');
        elements.forEach(el => el.classList.add('visible'));
    }, 100);

    // 2. Terminal Typing Animation
    const terminalLines = document.querySelectorAll('.delay-load');
    let delay = 1000;
    
    terminalLines.forEach((line, index) => {
        setTimeout(() => {
            line.style.opacity = '1';
            line.style.transition = 'opacity 0.2s';
        }, delay);
        
        // Slightly faster for the output lines, pause before success
        if (index === 3) {
            delay += 800; // Fake compilation time
        } else {
            delay += 400;
        }
    });

    // 3. Copy Install Command
    const copyBtn = document.getElementById('copy-install');
    copyBtn.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText('git clone https://github.com/vaibhav-space/vindex.git');
            const originalHTML = copyBtn.innerHTML;
            copyBtn.innerHTML = '<code>Copied!</code> <svg class="copy-icon" viewBox="0 0 24 24" fill="none" stroke="#4ade80" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>';
            copyBtn.style.borderColor = '#4ade80';
            
            setTimeout(() => {
                copyBtn.innerHTML = originalHTML;
                copyBtn.style.borderColor = 'rgba(255, 255, 255, 0.1)';
            }, 2000);
        } catch (err) {
            console.error('Failed to copy text: ', err);
        }
    });

    // 4. Subtle Particle Canvas Background
    const canvas = document.getElementById('particle-canvas');
    const ctx = canvas.getContext('2d');
    
    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;
    
    const particles = [];
    const particleCount = Math.floor(window.innerWidth / 15);
    
    window.addEventListener('resize', () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });

    class Particle {
        constructor() {
            this.x = Math.random() * width;
            this.y = Math.random() * height;
            this.size = Math.random() * 2 + 0.5;
            this.speedX = Math.random() * 1 - 0.5;
            this.speedY = Math.random() * 1 - 0.5;
            this.opacity = Math.random() * 0.5 + 0.1;
        }
        
        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            
            if (this.x > width) this.x = 0;
            if (this.x < 0) this.x = width;
            if (this.y > height) this.y = 0;
            if (this.y < 0) this.y = height;
        }
        
        draw() {
            ctx.fillStyle = `rgba(139, 92, 246, ${this.opacity})`;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }
    
    for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
    }
    
    function animate() {
        ctx.clearRect(0, 0, width, height);
        for (let i = 0; i < particles.length; i++) {
            particles[i].update();
            particles[i].draw();
        }
        requestAnimationFrame(animate);
    }
    
    animate();
});
