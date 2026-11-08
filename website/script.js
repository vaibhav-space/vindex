document.addEventListener('DOMContentLoaded', () => {
    // 1. Copy Install Command
    const copyBtn = document.getElementById('copy-install');
    if (copyBtn) {
        copyBtn.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText('git clone https://github.com/vaibhav-space/vindex.git');
                const originalHTML = copyBtn.innerHTML;
                copyBtn.innerHTML = '<code>Copied!</code> <svg class="copy-icon" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>';
                copyBtn.style.borderColor = '#059669';
                
                setTimeout(() => {
                    copyBtn.innerHTML = originalHTML;
                    copyBtn.style.borderColor = 'var(--border-subtle)';
                }, 2000);
            } catch (err) {
                console.error('Failed to copy: ', err);
            }
        });
    }

    // 2. Video Player & Scene Synchronization
    const demoVideo = document.getElementById('demoVideo');
    const playerTime = document.getElementById('playerTime');
    const sceneCards = document.querySelectorAll('.demo-scene-card');

    if (demoVideo) {
        demoVideo.addEventListener('timeupdate', () => {
            const cur = demoVideo.currentTime;
            const dur = demoVideo.duration || 10.03;
            
            // Format time display
            const curMins = Math.floor(cur / 60);
            const curSecs = (cur % 60).toFixed(2);
            const durMins = Math.floor(dur / 60);
            const durSecs = (dur % 60).toFixed(2);
            if (playerTime) {
                playerTime.innerText = `${curMins < 10 ? '0' : ''}${curMins}:${curSecs < 10 ? '0' : ''}${curSecs} / ${durMins < 10 ? '0' : ''}${durMins}:${durSecs}`;
            }

            // Sync active scene card
            sceneCards.forEach((card, idx) => {
                let isActive = false;
                if (idx === 0 && cur < 3.2) isActive = true;
                else if (idx === 1 && cur >= 3.2 && cur < 7.5) isActive = true;
                else if (idx === 2 && cur >= 7.5) isActive = true;

                if (isActive) {
                    card.classList.add('active');
                } else {
                    card.classList.remove('active');
                }
            });
        });
    }

    // Global seek function called by scene card onclick
    window.seekLandingVideo = function(seconds) {
        if (demoVideo) {
            demoVideo.currentTime = seconds;
            demoVideo.play().catch(() => {});
        }
    };

    // 3. Tab Switching: Artifact Explorer
    const artTabs = document.querySelectorAll('.art-tab');
    const artPanes = document.querySelectorAll('.art-content');
    artTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            artTabs.forEach(t => t.classList.remove('active'));
            artPanes.forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            const target = document.getElementById(tab.dataset.target);
            if (target) target.classList.add('active');
        });
    });

    // 4. Tab Switching: Developer Interfaces
    const ifTabs = document.querySelectorAll('.if-tab');
    const ifPanes = document.querySelectorAll('.if-pane');
    ifTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            ifTabs.forEach(t => t.classList.remove('active'));
            ifPanes.forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            const target = document.getElementById(tab.dataset.target);
            if (target) target.classList.add('active');
        });
    });
});
