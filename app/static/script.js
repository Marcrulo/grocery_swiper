class SwipeApp {
    constructor() {
        this.cards = [];
        this.currentIndex = 0;
        this.cardsContainer = document.getElementById('cardsContainer');
        this.noCardsMessage = document.getElementById('noCards');
        this.passBtn = document.getElementById('passBtn');
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
        
        // Button events
        this.passBtn.addEventListener('click', () => this.swipe('left'));
        this.likeBtn.addEventListener('click', () => this.swipe('right'));
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
            
            // Log the action
            const cardData = this.cards[this.currentIndex];
            console.log(`${direction === 'right' ? 'Liked' : 'Passed'}:`, cardData);
            
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
        const targetX = direction === 'right' ? window.innerWidth * 1.5 : -window.innerWidth * 1.5;
        const targetRotation = direction === 'right' ? 30 : -30;
        
        // Scale up the next card smoothly
        const nextCard = this.cardsContainer.querySelector(`[data-index="${this.currentIndex + 1}"]`);
        if (nextCard) {
            nextCard.style.transform = 'scale(1)';
            nextCard.style.transition = 'transform 0.35s ease';
        }
        
        // Animate card out
        cardToAnimate.classList.remove('swiping');
        cardToAnimate.style.transition = 'transform 0.35s ease-out';
        cardToAnimate.style.transform = `translateX(${targetX}px) rotate(${targetRotation}deg)`;
        
        // Log the action
        const cardData = this.cards[this.currentIndex];
        console.log(`${direction === 'right' ? 'Liked' : 'Passed'}:`, cardData);
        
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
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SwipeApp();
});