// 7 Habits Agent Graph Web UI JavaScript

class VisionBoardApp {
    constructor() {
        this.currentSlide = 0;
        this.images = [];
        this.autoplayInterval = null;
        this.autoplayActive = false;
        this.currentSessionId = null;
        
        this.init();
    }

    init() {
        this.initSlideshow();
        this.initChat();
        this.initGitHub();
        this.bindEvents();
        this.loadImages();
        this.startNewChat();
        this.loadGitHubActivity();
    }

    initSlideshow() {
        this.slides = document.querySelectorAll('.slide');
        this.updateSlideCounter();
        
        if (this.slides.length === 0) {
            document.getElementById('prevBtn').disabled = true;
            document.getElementById('nextBtn').disabled = true;
            document.getElementById('autoplayBtn').disabled = true;
        }
    }

    initChat() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.loadingIndicator = document.getElementById('loadingIndicator');
        
        // Enable chat interface once initialized
        this.messageInput.disabled = false;
        this.sendBtn.disabled = false;
    }

    initGitHub() {
        this.githubContent = document.getElementById('githubContent');
        this.githubLoading = document.getElementById('githubLoading');
        this.githubError = document.getElementById('githubError');
        this.commitsList = document.getElementById('commitsList');
        this.prsList = document.getElementById('prsList');
    }

    bindEvents() {
        // Slideshow controls
        document.getElementById('prevBtn').addEventListener('click', () => this.previousSlide());
        document.getElementById('nextBtn').addEventListener('click', () => this.nextSlide());
        document.getElementById('autoplayBtn').addEventListener('click', () => this.toggleAutoplay());
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshImages());
        }
        
        // GitHub refresh
        const refreshGitHubBtn = document.getElementById('refreshGitHubBtn');
        if (refreshGitHubBtn) {
            refreshGitHubBtn.addEventListener('click', () => this.loadGitHubActivity());
        }

        // Chat controls
        document.getElementById('sendBtn').addEventListener('click', () => this.sendMessage());
        document.getElementById('newChatBtn').addEventListener('click', () => this.startNewChat());
        // Enter key for sending messages
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        // Auto-refresh images every 30 seconds
        setInterval(() => this.refreshImages(), 30000);
    }

    // Slideshow methods
    showSlide(n) {
        if (this.slides.length === 0) return;
        
        this.slides[this.currentSlide].classList.remove('active');
        this.currentSlide = (n + this.slides.length) % this.slides.length;
        this.slides[this.currentSlide].classList.add('active');
        this.updateSlideCounter();
    }

    nextSlide() {
        this.showSlide(this.currentSlide + 1);
    }

    previousSlide() {
        this.showSlide(this.currentSlide - 1);
    }

    toggleAutoplay() {
        const btn = document.getElementById('autoplayBtn');
        const icon = btn.querySelector('i');
        
        if (this.autoplayActive) {
            clearInterval(this.autoplayInterval);
            this.autoplayActive = false;
            icon.className = 'bi bi-play';
            btn.innerHTML = '<i class="bi bi-play"></i> Auto';
        } else {
            this.autoplayInterval = setInterval(() => this.nextSlide(), 3000);
            this.autoplayActive = true;
            icon.className = 'bi bi-pause';
            btn.innerHTML = '<i class="bi bi-pause"></i> Auto';
        }
    }

    updateSlideCounter() {
        const counter = document.getElementById('imageCounter');
        if (this.slides.length === 0) {
            counter.textContent = '0 / 0';
        } else {
            counter.textContent = `${this.currentSlide + 1} / ${this.slides.length}`;
        }
    }

    async refreshImages() {
        console.log('in refresh images')
        console.log(this.images)
        try {
            const response = await fetch('/api/images');
            const data = await response.json();
            // If the number of images changed, re-render the slideshow
            
                // Only update the src of each image element
            this.images = data.images;
            const slideshowContainer = document.getElementById('imageSlideshow');
            if (slideshowContainer) {
                const imgElements = slideshowContainer.querySelectorAll('img');
                this.images.forEach((img, idx) => {
                    if (imgElements[idx]) {
                        imgElements[idx].src = img.path;
                    }
                });
            }
        } catch (error) {
            console.error('Error refreshing images:', error);
        }
    }

    // renderSlideshow() {
    //     // Remove all slides
    //     const slideshowContainer = document.getElementById('imageSlideshow');
    //     if (!slideshowContainer) return;
    //     slideshowContainer.innerHTML = '';
    //     // Add new slides
    //     this.images.forEach((img, idx) => {
    //         console.log('rendering image', img)
    //         const slideDiv = document.createElement('div');
    //         slideDiv.className = 'slide' + (idx === 0 ? ' active' : '');
    //         const imgElem = document.createElement('img');
    //         imgElem.src = img.path;
    //         imgElem.alt = `Vision Image ${idx + 1}`;
    //         slideDiv.appendChild(imgElem);
    //         slideshowContainer.appendChild(slideDiv);
    //     });
    //     // Update slides reference and counter
    //     this.slides = document.querySelectorAll('.slide');
    //     this.currentSlide = 0;
    //     this.updateSlideCounter();
    // }

    async loadImages() {
        try {
            const response = await fetch('/api/images');
            const data = await response.json();
            this.images = data.images;
        } catch (error) {
            console.error('Error loading images:', error);
        }
    }

    // Chat methods
    async startNewChat() {
        try {
            const response = await fetch('/api/chat/new', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            this.currentSessionId = data.session_id;
            
            // Clear chat messages except welcome message
            const welcomeMessage = this.chatMessages.querySelector('.assistant-message');
            this.chatMessages.innerHTML = '';
            if (welcomeMessage) {
                this.chatMessages.appendChild(welcomeMessage);
            }
            
            this.addMessage('assistant', 'Hello! I\'m your 7 Habits AI assistant. I can help you with various tasks including creating vision board images. Try asking me to "generate a vision board image" or any other question!');
            
        } catch (error) {
            console.error('Error starting new chat:', error);
            this.addMessage('assistant', 'Sorry, I encountered an error starting a new chat session. Please try again.');
        }
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;

        // Disable input while processing
        this.setInputEnabled(false);
        this.showLoading(true);

        // Add user message to chat
        this.addMessage('user', message);
        this.messageInput.value = '';

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.currentSessionId
                })
            });

            const data = await response.json();
            
            if (response.ok) {
                this.currentSessionId = data.session_id;
                this.addMessage('assistant', data.response);
                
                // Check if message might have generated an image
                if (this.isImageGenerationMessage(message)) {
                    // Refresh images after a short delay to allow for image generation
                    setTimeout(() => this.refreshImages(), 2000);
                }
            } else {
                this.addMessage('assistant', `Error: ${data.error}`);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage('assistant', 'Sorry, I encountered an error processing your message. Please try again.');
        } finally {
            this.setInputEnabled(true);
            this.showLoading(false);
        }
    }

    isImageGenerationMessage(message) {
        const imageKeywords = [
            'add image', 'create image', 'generate image', 'vision board',
            'dall-e', 'dalle', 'picture', 'photo', 'visual'
        ];
        const lowerMessage = message.toLowerCase();
        return imageKeywords.some(keyword => lowerMessage.includes(keyword));
    }

    addMessage(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const now = new Date();
        const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.innerHTML = `
            <div class="message-content">
                ${type === 'user' ? '<strong>You:</strong>' : '<strong>AI Assistant:</strong>'} ${this.escapeHtml(content)}
            </div>
            <div class="message-time">
                <small class="text-muted">${timeStr}</small>
            </div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    setInputEnabled(enabled) {
        this.messageInput.disabled = !enabled;
        this.sendBtn.disabled = !enabled;
    }

    showLoading(show) {
        this.loadingIndicator.style.display = show ? 'block' : 'none';
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // GitHub Activity methods
    async loadGitHubActivity() {
        this.showGitHubLoading(true);
        this.hideGitHubError();
        
        try {
            const response = await fetch('/api/github-activity');
            const data = await response.json();
            
            if (response.ok) {
                this.displayGitHubActivity(data);
            } else {
                throw new Error(data.error || 'Failed to load GitHub activity');
            }
        } catch (error) {
            console.error('Error loading GitHub activity:', error);
            this.showGitHubError();
        } finally {
            this.showGitHubLoading(false);
        }
    }

    displayGitHubActivity(data) {
        this.hideGitHubError(); // Hide error when displaying data
        
        // Display commits
        this.commitsList.innerHTML = '';
        if (data.commits && data.commits.length > 0) {
            data.commits.forEach(commit => {
                const commitElement = this.createCommitElement(commit);
                this.commitsList.appendChild(commitElement);
            });
        } else {
            this.commitsList.innerHTML = '<div class="text-muted text-center p-3">No recent commits</div>';
        }

        // Display pull requests
        this.prsList.innerHTML = '';
        if (data.pull_requests && data.pull_requests.length > 0) {
            data.pull_requests.forEach(pr => {
                const prElement = this.createPRElement(pr);
                this.prsList.appendChild(prElement);
            });
        } else {
            this.prsList.innerHTML = '<div class="text-muted text-center p-3">No pull requests</div>';
        }
    }

    createCommitElement(commit) {
        const div = document.createElement('div');
        div.className = 'activity-item';
        
        const shortSha = commit.sha.substring(0, 7);
        const date = new Date(commit.date).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        div.innerHTML = `
            <div class="item-title">${this.escapeHtml(commit.message)}</div>
            <div class="item-meta">
                <span class="item-author">${this.escapeHtml(commit.author.name)}</span>
                <span class="item-sha">${shortSha}</span>
                <span class="item-date">${date}</span>
            </div>
        `;
        
        div.addEventListener('click', () => {
            if (commit.url) {
                window.open(commit.url, '_blank');
            }
        });
        
        return div;
    }

    createPRElement(pr) {
        const div = document.createElement('div');
        div.className = 'activity-item';
        
        const date = new Date(pr.created_at).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        div.innerHTML = `
            <div class="item-title">
                <span class="pr-number">#${pr.number}</span> ${this.escapeHtml(pr.title)}
            </div>
            <div class="item-meta">
                <span class="item-author">${this.escapeHtml(pr.user.login)}</span>
                <span class="pr-state ${pr.state}">${pr.state}</span>
                <span class="item-date">${date}</span>
            </div>
        `;
        
        div.addEventListener('click', () => {
            if (pr.url) {
                window.open(pr.url, '_blank');
            }
        });
        
        return div;
    }

    showGitHubLoading(show) {
        if (show) {
            this.githubLoading.style.display = 'block';
            this.githubContent.style.display = 'none';
        } else {
            this.githubLoading.style.display = 'none';
            this.githubContent.style.display = 'block';
        }
    }

    showGitHubError() {
        this.githubError.classList.remove('d-none');
        this.githubContent.style.display = 'none';
    }

    hideGitHubError() {
        this.githubError.classList.add('d-none');
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new VisionBoardApp();
});

// Handle window resize for responsive layout
window.addEventListener('resize', () => {
    // Adjust layout if needed
});

// Handle visibility change to pause/resume autoplay
document.addEventListener('visibilitychange', () => {
    const app = window.visionBoardApp;
    if (app && app.autoplayActive) {
        if (document.hidden) {
            clearInterval(app.autoplayInterval);
        } else {
            app.autoplayInterval = setInterval(() => app.nextSlide(), 3000);
        }
    }
});