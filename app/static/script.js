// Generate a stable device fingerprint
function generateDeviceId() {
    // Check if we already have a device ID stored
    let deviceId = localStorage.getItem('deviceId');
    if (deviceId) {
        return deviceId;
    }
    
    // Generate fingerprint from stable browser properties
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('Device Fingerprint', 2, 2);
    const canvasFingerprint = canvas.toDataURL();
    
    const fingerprint = [
        navigator.userAgent,
        navigator.language,
        screen.width + 'x' + screen.height,
        screen.colorDepth,
        new Date().getTimezoneOffset(),
        !!window.sessionStorage,
        !!window.localStorage,
        canvasFingerprint
    ].join('|||');
    
    // Create hash from fingerprint
    deviceId = simpleHash(fingerprint);
    
    // Store in localStorage for consistency
    localStorage.setItem('deviceId', deviceId);
    return deviceId;
}

// Simple hash function
function simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(36);
}

// Generate a stable device fingerprint
function generateDeviceId() {
    // Check if we already have a device ID stored
    let deviceId = localStorage.getItem('deviceId');
    if (deviceId) {
        return deviceId;
    }
    
    // Generate fingerprint from stable browser properties
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('Device Fingerprint', 2, 2);
    const canvasFingerprint = canvas.toDataURL();
    
    const fingerprint = [
        navigator.userAgent,
        navigator.language,
        screen.width + 'x' + screen.height,
        screen.colorDepth,
        new Date().getTimezoneOffset(),
        !!window.sessionStorage,
        !!window.localStorage,
        canvasFingerprint
    ].join('|||');
    
    // Create hash from fingerprint
    deviceId = simpleHash(fingerprint);
    
    // Store in localStorage for consistency
    localStorage.setItem('deviceId', deviceId);
    return deviceId;
}

// Simple hash function
function simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(36);
}

// Pull-to-refresh functionality
let pullStartY = 0;
let pullMoveY = 0;
let isPulling = false;

function initPullToRefresh() {
    const appContainer = document.querySelector('.app-container');
    
    appContainer.addEventListener('touchstart', (e) => {
        if (window.scrollY === 0) {
            pullStartY = e.touches[0].clientY;
            isPulling = true;
        }
    }, { passive: true });
    
    appContainer.addEventListener('touchmove', (e) => {
        if (!isPulling) return;
        
        pullMoveY = e.touches[0].clientY - pullStartY;
        
        // Only trigger if pulling down (positive value) and at top of page
        if (pullMoveY > 0 && window.scrollY === 0) {
            // Add visual feedback
            if (pullMoveY > 80) {
                appContainer.style.transform = `translateY(${Math.min(pullMoveY / 3, 40)}px)`;
            }
        }
    }, { passive: true });
    
    appContainer.addEventListener('touchend', () => {
        if (isPulling && pullMoveY > 80) {
            // Reload the page
            location.reload();
        }
        
        // Reset
        appContainer.style.transform = '';
        appContainer.style.transition = 'transform 0.3s ease';
        setTimeout(() => {
            appContainer.style.transition = '';
        }, 300);
        isPulling = false;
        pullStartY = 0;
        pullMoveY = 0;
    }, { passive: true });
}

class SwipeApp {
    constructor() {
        this.cards = [];
        this.currentIndex = 0;
        this.cardsContainer = document.getElementById('cardsContainer');
        this.noCardsMessage = document.getElementById('noCards');
        this.passBtn = document.getElementById('passBtn');
        this.superLikeBtn = document.getElementById('superLikeBtn');
        this.likeBtn = document.getElementById('likeBtn');
        
        this.isDragging = false;
        this.startX = 0;
        this.startY = 0;
        this.currentX = 0;
        this.currentY = 0;
        this.currentCard = null;
        this.likeIndicator = null;
        this.passIndicator = null;
        this.isAnimating = false;
        
        this.init();
    }
    
    async init() {
        await this.loadProducts();
        this.renderCards();
        this.attachEventListeners();
    }
    
    async loadProducts() {
        try {
            const response = await fetch('/api/products');
            if (!response.ok) {
                throw new Error('Failed to load products');
            }
            this.cards = await response.json();
            console.log(`Loaded ${this.cards.length} products`);
        } catch (error) {
            console.error('Error loading products:', error);
            this.showNoCards();
        }
    }
    
    renderCards() {
        // Remove only old cards that are no longer needed
        const existingCards = this.cardsContainer.querySelectorAll('.card');
        existingCards.forEach(card => {
            const cardIndex = parseInt(card.dataset.index);
            if (cardIndex < this.currentIndex - 1 || cardIndex > this.currentIndex + 2) {
                card.remove();
            }
        });
        
        // Add new cards if needed - render in reverse order for proper z-index
        for (let i = Math.min(this.currentIndex + 2, this.cards.length - 1); i >= this.currentIndex; i--) {
            const existingCard = this.cardsContainer.querySelector(`[data-index="${i}"]`);
            if (!existingCard && i < this.cards.length) {
                const card = this.createCard(this.cards[i], i);
                // Insert at the beginning to maintain z-index order
                this.cardsContainer.insertBefore(card, this.cardsContainer.firstChild);
            }
        }
        
        if (this.currentIndex >= this.cards.length) {
            this.showNoCards();
        }
    }
    
    createCard(data, index) {
        const card = document.createElement('div');
        card.className = 'card';
        card.dataset.index = index;
        
        // Add z-index so current card is on top
        const zIndex = this.cards.length - index;
        card.style.zIndex = zIndex;
        
        // Scale down cards below - use transform for better performance
        if (index > this.currentIndex) {
            const scale = 1 - (index - this.currentIndex) * 0.05;
            card.style.transform = `scale(${scale})`;
            card.style.transition = 'transform 0.3s ease';
        }
        
        card.innerHTML = `
            <div class="swipe-indicator pass">NOPE</div>
            <div class="swipe-indicator like">LIKE</div>
            <img src="${data.image}" alt="${data.title}" class="card-image" loading="eager" decoding="async">
            <div class="card-content">
                ${data.brand || data.category ? `<div class="card-meta">
                    ${data.brand ? `<span class="card-brand">${data.brand}</span>` : ''}
                    ${data.brand && data.category ? `<span class="card-separator">•</span>` : ''}
                    ${data.category ? `<span class="card-category">${data.category}</span>` : ''}
                </div>` : ''}
                <h2 class="card-title">${data.title}</h2>
                <p class="card-description">${data.description}</p>
                ${data.price ? `<p class="card-price">${data.price} kr</p>` : ''}
            </div>
        `;
        
        // Handle image loading to ensure gradient background shows
        const img = card.querySelector('.card-image');
        img.onload = () => {
            img.classList.add('loaded');
        };
        img.onerror = () => {
            // Keep gradient background if image fails to load
            console.warn('Failed to load image:', data.image);
        };
        
        return card;
    }
    
    attachEventListeners() {
        // Touch events - bind methods once to avoid multiple bindings
        this.boundDragStart = this.onDragStart.bind(this);
        this.boundDragMove = this.onDragMove.bind(this);
        this.boundDragEnd = this.onDragEnd.bind(this);
        
        this.cardsContainer.addEventListener('mousedown', this.boundDragStart);
        this.cardsContainer.addEventListener('touchstart', this.boundDragStart, { passive: true });
        
        document.addEventListener('mousemove', this.boundDragMove);
        document.addEventListener('touchmove', this.boundDragMove, { passive: false });
        
        document.addEventListener('mouseup', this.boundDragEnd);
        document.addEventListener('touchend', this.boundDragEnd);
        
        // Button events with explicit press/release class handling to avoid stuck active states on mobile
        const addPress = (el) => {
            // Cancel any pending clears and restart the animation by forcing reflow
            if (el._pressTimer) {
                clearTimeout(el._pressTimer);
            }
            el.classList.remove('active-press');
            void el.offsetWidth; // force reflow so the next add retriggers transition
            el.classList.add('active-press');
            el._pressTimer = setTimeout(() => el.classList.remove('active-press'), 140);
        };
        const clearPress = (el) => {
            if (el._pressTimer) {
                clearTimeout(el._pressTimer);
                el._pressTimer = null;
            }
            el.classList.remove('active-press');
        };
        const clearPressWithDelay = (el, delay = 80) => {
            clearPress(el);
            setTimeout(() => clearPress(el), delay);
        };
        const bindPressHandlers = (el, handler) => {
            const onDown = (e) => {
                if (e.pointerType === 'mouse' && e.buttons !== 1) return;
                addPress(el);
            };
            const onUp = () => clearPressWithDelay(el);
            const onCancel = () => clearPress(el);

            el.addEventListener('pointerdown', onDown);
            el.addEventListener('pointerup', onUp);
            el.addEventListener('pointerleave', onCancel);
            el.addEventListener('pointercancel', onCancel);
            el.addEventListener('click', (e) => {
                clearPress(el);
                handler(e);
            });
        };

        bindPressHandlers(this.passBtn, () => this.swipe('left'));
        bindPressHandlers(this.superLikeBtn, () => this.swipe('up'));
        bindPressHandlers(this.likeBtn, () => this.swipe('right'));
    }
    
    onDragStart(e) {
        const target = e.target.closest('.card');
        if (!target || parseInt(target.dataset.index) !== this.currentIndex) return;
        
        // Allow starting a new drag even if previous animation isn't complete
        
        // Prevent default drag behavior for mouse events
        if (e.type === 'mousedown') {
            e.preventDefault();
        }
        
        this.isDragging = true;
        this.currentCard = target;
        this.currentCard.classList.add('swiping');
        this.currentCard.style.cursor = 'grabbing';
        
        // Cache indicator elements
        this.likeIndicator = this.currentCard.querySelector('.swipe-indicator.like');
        this.passIndicator = this.currentCard.querySelector('.swipe-indicator.pass');
        
        const clientX = e.type === 'mousedown' ? e.clientX : e.touches[0].clientX;
        const clientY = e.type === 'mousedown' ? e.clientY : e.touches[0].clientY;
        this.startX = clientX;
        this.startY = clientY;
        this.currentX = clientX;
        this.currentY = clientY;
    }
    
    onDragMove(e) {
        if (!this.isDragging || !this.currentCard) return;
        
        const clientX = e.type === 'mousemove' ? e.clientX : e.touches[0].clientX;
        const clientY = e.type === 'mousemove' ? e.clientY : e.touches[0].clientY;
        
        const deltaX = clientX - this.startX;
        const deltaY = clientY - this.startY;
        
        // Only prevent default if moving horizontally more than vertically
        if (Math.abs(deltaX) > Math.abs(deltaY)) {
            e.preventDefault();
        }
        
        this.currentX = clientX;
        this.currentY = clientY;
        
        const rotation = deltaX * 0.1;
        
        // Use requestAnimationFrame for smoother animations
        requestAnimationFrame(() => {
            if (!this.currentCard) return;
            this.currentCard.style.transform = `translateX(${deltaX}px) rotate(${rotation}deg)`;
            
            // Show swipe indicators
            const opacity = Math.min(Math.abs(deltaX) / 100, 1);
            
            if (deltaX > 0) {
                this.likeIndicator.style.opacity = opacity;
                this.passIndicator.style.opacity = 0;
            } else {
                this.passIndicator.style.opacity = opacity;
                this.likeIndicator.style.opacity = 0;
            }
        });
    }
    
    onDragEnd(e) {
        if (!this.isDragging || !this.currentCard) return;
        
        this.isDragging = false;
        const deltaX = this.currentX - this.startX;
        const cardToAnimate = this.currentCard;
        
        // Always swipe the card in the direction it was dragged if moved more than 10px
        if (Math.abs(deltaX) > 10) {
            const direction = deltaX > 0 ? 'right' : 'left';
            
            // Shorter, faster animation
            const targetX = direction === 'right' ? window.innerWidth * 1.5 : -window.innerWidth * 1.5;
            const targetRotation = direction === 'right' ? 30 : -30;
            
            // Remove swiping class to enable transitions
            cardToAnimate.classList.remove('swiping');
            
            // Scale up the next card smoothly and immediately
            const nextCard = this.cardsContainer.querySelector(`[data-index="${this.currentIndex + 1}"]`);
            if (nextCard) {
                nextCard.style.transform = 'scale(1)';
                nextCard.style.transition = 'transform 0.35s ease';
            }
            
            // Apply faster transition and animate current card out
            cardToAnimate.style.transition = `transform 0.35s ease-out`;
            cardToAnimate.style.transform = `translateX(${targetX}px) rotate(${targetRotation}deg)`;
            
            // Log the action and save to database
            const cardData = this.cards[this.currentIndex];
            console.log(`${direction === 'right' ? 'Liked' : 'Passed'}:`, cardData);
            
            // Save to database
            const action = direction === 'right' ? 'like' : 'pass';
            this.saveSwipe(cardData.id, cardData.date_title, action);
            
            // Increment immediately and render new cards faster
            this.currentIndex++;
            
            // Remove the old card and add new one after shorter delay
            setTimeout(() => {
                cardToAnimate.remove();
                this.renderCards();
            }, 200);
        } else {
            // Reset card position if barely moved
            cardToAnimate.classList.remove('swiping');
            cardToAnimate.style.transition = 'transform 0.3s ease';
            cardToAnimate.style.transform = '';
            cardToAnimate.style.cursor = 'grab';
            this.resetIndicators();
        }
        
        this.currentCard = null;
        this.likeIndicator = null;
        this.passIndicator = null;
    }
    
    swipe(direction) {
        const card = this.cardsContainer.querySelector(`[data-index="${this.currentIndex}"]`);
        if (!card) return;
        
        this.currentCard = card;
        this.completeSwipe(direction);
    }
    
    completeSwipe(direction) {
        if (!this.currentCard) return;
        
        const cardToAnimate = this.currentCard;
        let targetX, targetY, targetRotation;
        
        if (direction === 'up') {
            // Super like - fly upward
            targetX = 0;
            targetY = -window.innerHeight * 1.5;
            targetRotation = 0;
        } else {
            targetX = direction === 'right' ? window.innerWidth * 1.5 : -window.innerWidth * 1.5;
            targetY = 0;
            targetRotation = direction === 'right' ? 30 : -30;
        }
        
        // Scale up the next card smoothly
        const nextCard = this.cardsContainer.querySelector(`[data-index="${this.currentIndex + 1}"]`);
        if (nextCard) {
            nextCard.style.transform = 'scale(1)';
            nextCard.style.transition = 'transform 0.35s ease';
        }
        
        // Animate card out
        cardToAnimate.classList.remove('swiping');
        cardToAnimate.style.transition = 'transform 0.35s ease-out';
        cardToAnimate.style.transform = `translate(${targetX}px, ${targetY}px) rotate(${targetRotation}deg)`;
        
        // Log the action and save to database
        const cardData = this.cards[this.currentIndex];
        const actionName = direction === 'right' ? 'Liked' : direction === 'up' ? 'Super Liked' : 'Passed';
        console.log(`${actionName}:`, cardData);
        
        // Save to database
        const action = direction === 'right' ? 'like' : direction === 'up' ? 'superlike' : 'pass';
        this.saveSwipe(cardData.id, cardData.date_title, action);
        
        // Increment immediately and clean up
        this.currentIndex++;
        
        setTimeout(() => {
            cardToAnimate.remove();
            this.renderCards();
        }, 200);
        
        this.currentCard = null;
    }
    
    resetIndicators() {
        if (!this.currentCard) return;
        const indicators = this.currentCard.querySelectorAll('.swipe-indicator');
        indicators.forEach(ind => ind.style.opacity = 0);
    }
    
    showNoCards() {
        this.cardsContainer.style.display = 'none';
        this.noCardsMessage.style.display = 'block';
    }
    
    saveSwipe(dataId, dateTitle, action) {
        // Get product name and price from current card data
        const cardData = this.cards.find(c => c.id === dataId);
        const productName = cardData ? cardData.title : '';
        const price = cardData ? cardData.price : 0;
        const deviceId = generateDeviceId();
        
        // Save swipe to database via API
        fetch('/api/swipe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                data_id: dataId,
                date_title: dateTitle,
                product_name: productName,
                price: price,
                device_id: deviceId,
                action: action
            })
        }).catch(error => {
            console.error('Error saving swipe:', error);
        });
    }
}

// Fullscreen toggle
function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => {
            console.log('Error attempting to enable fullscreen:', err);
        });
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const app = new SwipeApp();
    
    // Initialize pull-to-refresh
    initPullToRefresh();
    
    // Fullscreen button
    const fullscreenBtn = document.getElementById('fullscreenBtn');
    if (fullscreenBtn) {
        fullscreenBtn.addEventListener('click', toggleFullscreen);
    }
    
    // Settings modal functionality
    const settingsBtn = document.getElementById('settingsBtn');
    const settingsModal = document.getElementById('settingsModal');
    const closeModal = document.getElementById('closeModal');
    const modalBody = document.getElementById('modalBody');
    
    settingsBtn.addEventListener('click', async () => {
        settingsModal.classList.add('active');
        await loadHistory();
    });
    
    closeModal.addEventListener('click', () => {
        settingsModal.classList.remove('active');
    });
    
    settingsModal.addEventListener('click', (e) => {
        if (e.target === settingsModal) {
            settingsModal.classList.remove('active');
        }
    });
    
    async function loadHistory() {
        modalBody.innerHTML = '<p class="loading">Loading...</p>';
        
        try {
            const deviceId = generateDeviceId();
            const response = await fetch(`/api/history?device_id=${deviceId}`);
            const history = await response.json();
            
            if (history.length === 0) {
                modalBody.innerHTML = '<p class="loading">No swipe history yet</p>';
                return;
            }
            
            modalBody.innerHTML = history.map(item => {
                const status = item.is_superliked ? 'superliked' : item.is_liked ? 'liked' : 'passed';
                const statusText = item.is_superliked ? 'Super Liked' : item.is_liked ? 'Liked' : 'Passed';
                const productInfo = item.product_name ? `${item.product_name} - ${item.price} kr` : `Product ID: ${item.data_id}`;
                
                return `
                    <div class="history-item">
                        <div class="history-info">
                            <div class="history-name">${productInfo}</div>
                            <div class="history-date">${item.date_title} • ${new Date(item.created_at).toLocaleString()}</div>
                        </div>
                        <div class="history-actions">
                            <select class="status-badge status-${status}" onchange="updateEntry(${item.id}, this.value); this.blur();">
                                <option value="like" ${item.is_liked ? 'selected' : ''}>Liked</option>
                                <option value="superlike" ${item.is_superliked ? 'selected' : ''}>Super Liked</option>
                                <option value="pass" ${item.is_passed ? 'selected' : ''}>Passed</option>
                            </select>
                        </div>
                    </div>
                `;
            }).join('');
        } catch (error) {
            console.error('Error loading history:', error);
            modalBody.innerHTML = '<p class="loading">Error loading history</p>';
        }
    }
    
    window.updateEntry = async (id, action) => {
        if (!action) return;
        
        try {
            const response = await fetch(`/api/history/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ action })
            });
            
            if (response.ok) {
                await loadHistory();
            }
        } catch (error) {
            console.error('Error updating entry:', error);
        }
    };
});