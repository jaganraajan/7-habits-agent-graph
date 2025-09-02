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
        this.initHabit1();
        this.initHabits4567();
        this.bindEvents();
        this.bindHabits4567Events();
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
        this.githubSummary = document.getElementById('githubSummary');
        this.summaryContent = document.getElementById('summaryContent');
        this.summaryLoading = document.getElementById('summaryLoading');
        this.currentGithubData = null; // Store current GitHub data for summarization
    }

    initHabit1() {
        this.habit1Header = document.getElementById('habit1Header');
        this.habit1Content = document.getElementById('habit1Content');
        this.habit1ToggleIcon = document.getElementById('habit1ToggleIcon');
        this.habit1Loading = document.getElementById('habit1Loading');
        this.habit1Error = document.getElementById('habit1Error');
        this.habit1Markdown = document.getElementById('habit1Markdown');
        this.habit1Expanded = false;
        this.habit1Loaded = false;
        
        // Ensure content starts collapsed
        this.habit1Content.classList.remove('expanded');
        this.habit1Header.classList.remove('expanded');
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
        
        // GitHub summarize
        const summarizeGitHubBtn = document.getElementById('summarizeGitHubBtn');
        if (summarizeGitHubBtn) {
            summarizeGitHubBtn.addEventListener('click', () => this.summarizeGitHubActivity());
        }

        // Habit 1 toggle
        this.habit1Header.addEventListener('click', () => this.toggleHabit1());

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
        console.log('Loading GitHub activity');
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
        this.currentGithubData = data; // Store data for summarization
        
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

    async summarizeGitHubActivity() {
        if (!this.currentGithubData) {
            alert('Please load GitHub activity first by clicking Refresh.');
            return;
        }

        try {
            // Show loading state
            this.summaryLoading.style.display = 'block';
            this.githubSummary.style.display = 'block';
            this.summaryContent.innerHTML = '';

            const response = await fetch('/api/github-summary', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    github_data: this.currentGithubData
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.summaryContent.innerHTML = this.escapeHtml(data.summary);
            } else {
                this.summaryContent.innerHTML = 'Error generating summary: ' + (data.error || 'Unknown error');
            }
        } catch (error) {
            console.error('Error summarizing GitHub activity:', error);
            this.summaryContent.innerHTML = 'Failed to generate summary. Please try again.';
        } finally {
            this.summaryLoading.style.display = 'none';
        }
    }

    // Habit 1 - Be Proactive methods
    toggleHabit1() {
        this.habit1Expanded = !this.habit1Expanded;
        
        if (this.habit1Expanded) {
            this.habit1Content.classList.add('expanded');
            this.habit1Header.classList.add('expanded');
            
            // Load content on first expand
            if (!this.habit1Loaded) {
                this.loadHabit1Summary();
                this.habit1Loaded = true;
            }
        } else {
            this.habit1Content.classList.remove('expanded');
            this.habit1Header.classList.remove('expanded');
        }
    }

    async loadHabit1Summary() {
        this.habit1Loading.style.display = 'block';
        this.habit1Error.style.display = 'none';
        this.habit1Markdown.innerHTML = '';

        try {
            const response = await fetch('/api/habit1-summary');
            
            if (response.ok) {
                const data = await response.json();
                if (data.exists) {
                    this.habit1Markdown.innerHTML = this.parseMarkdown(data.content);
                } else {
                    this.showHabit1Placeholder();
                }
            } else {
                throw new Error('Failed to load summary');
            }
        } catch (error) {
            console.error('Error loading Habit 1 summary:', error);
            this.habit1Error.style.display = 'block';
        } finally {
            this.habit1Loading.style.display = 'none';
        }
    }

    showHabit1Placeholder() {
        this.habit1Markdown.innerHTML = `
            <div class="habit1-placeholder">
                <i class="bi bi-lightning-fill"></i>
                <h4>Ready to Be Proactive?</h4>
                <p>The weekly GitHub research summary hasn't been generated yet.</p>
                <p>Run the <code>habit1-proactive</code> workflow to discover:</p>
                <ul style="text-align: left; display: inline-block;">
                    <li>Top agentic/MCP repositories for contribution</li>
                    <li>Beginner-friendly issues and opportunities</li>
                    <li>Learning resources and documentation</li>
                    <li>Recent patterns and examples</li>
                </ul>
                <p><small>Execute via CLI: <code>python main.py</code> and select 'habit1-proactive'</small></p>
            </div>
        `;
    }

    parseMarkdown(content) {
        // Simple markdown parsing for basic formatting
        let html = content
            // Headers
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            // Bold
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Italic
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Code inline
            .replace(/`(.*?)`/g, '<code>$1</code>')
            // Links
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
            // Line breaks
            .replace(/\n/g, '<br>');

        // Convert lists
        html = html.replace(/^- (.*$)/gim, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
        
        // Convert numbered lists
        html = html.replace(/^\d+\. (.*$)/gim, '<li>$1</li>');
        
        return html;
    }

    // Habits 4-7 methods
    initHabits4567() {
        // Initialize variables for each habit
        for (let i = 4; i <= 7; i++) {
            this[`habit${i}Header`] = document.getElementById(`habit${i}Header`);
            this[`habit${i}Content`] = document.getElementById(`habit${i}Content`);
            this[`habit${i}ToggleIcon`] = document.getElementById(`habit${i}ToggleIcon`);
            this[`habit${i}Loading`] = document.getElementById(`habit${i}Loading`);
            this[`habit${i}Error`] = document.getElementById(`habit${i}Error`);
            this[`habit${i}Markdown`] = document.getElementById(`habit${i}Markdown`);
            this[`habit${i}Expanded`] = false;
            this[`habit${i}Loaded`] = false;
            
            // Ensure content starts collapsed
            this[`habit${i}Content`].classList.remove('expanded');
            this[`habit${i}Header`].classList.remove('expanded');
        }
    }

    bindHabits4567Events() {
        // Bind click events for each habit header
        for (let i = 4; i <= 7; i++) {
            this[`habit${i}Header`].addEventListener('click', () => this.toggleHabit(i));
        }
    }

    toggleHabit(habitNumber) {
        const expanded = this[`habit${habitNumber}Expanded`] = !this[`habit${habitNumber}Expanded`];
        
        if (expanded) {
            this[`habit${habitNumber}Content`].classList.add('expanded');
            this[`habit${habitNumber}Header`].classList.add('expanded');
            
            // Load content on first expand
            if (!this[`habit${habitNumber}Loaded`]) {
                this.loadHabits4567Summary();
                // Mark all as loaded since they share the same summary
                for (let i = 4; i <= 7; i++) {
                    this[`habit${i}Loaded`] = true;
                }
            }
        } else {
            this[`habit${habitNumber}Content`].classList.remove('expanded');
            this[`habit${habitNumber}Header`].classList.remove('expanded');
        }
    }

    async loadHabits4567Summary() {
        // Show loading for all habits
        for (let i = 4; i <= 7; i++) {
            this[`habit${i}Loading`].style.display = 'block';
            this[`habit${i}Error`].style.display = 'none';
            this[`habit${i}Markdown`].innerHTML = '';
        }

        try {
            const response = await fetch('/api/habit4567-summary');
            
            if (response.ok) {
                const data = await response.json();
                if (data.exists) {
                    this.parseAndDistributeHabits4567Content(data.content);
                } else {
                    this.showHabits4567Placeholder();
                }
            } else {
                throw new Error('Failed to load summary');
            }
        } catch (error) {
            console.error('Error loading Habits 4-7 summary:', error);
            for (let i = 4; i <= 7; i++) {
                this[`habit${i}Error`].style.display = 'block';
            }
        } finally {
            for (let i = 4; i <= 7; i++) {
                this[`habit${i}Loading`].style.display = 'none';
            }
        }
    }

    parseAndDistributeHabits4567Content(content) {
        // Parse the full content and extract sections for each habit
        const fullHtml = this.parseMarkdown(content);
        
        // Extract habit-specific sections
        const habit4Content = this.extractHabitSection(fullHtml, 'Habit 4');
        const habit5Content = this.extractHabitSection(fullHtml, 'Habit 5');
        const habit6Content = this.extractHabitSection(fullHtml, 'Habit 6');  
        const habit7Content = this.extractHabitSection(fullHtml, 'Habit 7');
        
        // Display content for each habit
        this.habit4Markdown.innerHTML = habit4Content || this.getHabitPlaceholder(4);
        this.habit5Markdown.innerHTML = habit5Content || this.getHabitPlaceholder(5);
        this.habit6Markdown.innerHTML = habit6Content || this.getHabitPlaceholder(6);
        this.habit7Markdown.innerHTML = habit7Content || this.getHabitPlaceholder(7);
    }

    extractHabitSection(html, habitTitle) {
        // Extract content between habit headers
        const regex = new RegExp(`<h2[^>]*>.*?${habitTitle}.*?</h2>(.*?)(?=<h2|$)`, 'is');
        const match = html.match(regex);
        return match ? `<h2>${habitTitle}</h2>${match[1]}` : null;
    }

    showHabits4567Placeholder() {
        const placeholders = {
            4: this.getHabitPlaceholder(4),
            5: this.getHabitPlaceholder(5),
            6: this.getHabitPlaceholder(6),
            7: this.getHabitPlaceholder(7)
        };
        
        for (let i = 4; i <= 7; i++) {
            this[`habit${i}Markdown`].innerHTML = placeholders[i];
        }
    }

    getHabitPlaceholder(habitNumber) {
        const habits = {
            4: {
                icon: 'bi-people-fill',
                title: 'Think Win-Win',
                description: 'Collaborative development patterns and mutual benefit approaches',
                focus: ['Collaborative issue resolution', 'Mutual benefit code reviews', 'Consensus building patterns', 'Team synergy examples']
            },
            5: {
                icon: 'bi-ear-fill', 
                title: 'Seek First to Understand',
                description: 'Review analysis and discussion understanding practices',
                focus: ['Thoughtful code review discussions', 'ADR and RFC processes', 'Understanding-first approaches', 'Learning from disagreements']
            },
            6: {
                icon: 'bi-diagram-3-fill',
                title: 'Synergize',
                description: 'Multi-tool integration and collaborative examples',
                focus: ['Tool integration patterns', 'Cross-functional collaboration', 'Synergistic workflows', 'Integration success stories']
            },
            7: {
                icon: 'bi-tools',
                title: 'Sharpen the Saw',
                description: 'Learning resources and continuous growth opportunities',
                focus: ['Learning paths and resources', 'New releases and updates', 'Skill development opportunities', 'Mentorship examples']
            }
        };
        
        const habit = habits[habitNumber];
        return `
            <div class="habit-placeholder">
                <i class="${habit.icon}"></i>
                <h4>Ready for ${habit.title}?</h4>
                <p>The collaborative growth summary hasn't been generated yet.</p>
                <p>Run the <code>habit4567-summary</code> workflow to discover:</p>
                <ul style="text-align: left; display: inline-block;">
                    ${habit.focus.map(item => `<li>${item}</li>`).join('')}
                </ul>
                <p><small>Execute via CLI: <code>python main.py</code> and select 'habit4567-summary'</small></p>
            </div>
        `;
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