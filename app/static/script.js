// Sample data for cards
const cardsData = [
    {
        id: 1,
        title: "Product 1",
        description: "This is an amazing product you'll love!",
        image: "https://via.placeholder.com/400x500/667eea/ffffff?text=Product+1"
    },
    {
        id: 2,
        title: "Product 2",
        description: "High quality and great value for money.",
        image: "https://via.placeholder.com/400x500/764ba2/ffffff?text=Product+2"
    },
    {
        id: 3,
        title: "Product 3",
        description: "Perfect for your daily needs.",
        image: "https://via.placeholder.com/400x500/f093fb/ffffff?text=Product+3"
    },
    {
        id: 4,
        title: "Product 4",
        description: "Limited time offer - don't miss out!",
        image: "https://via.placeholder.com/400x500/4facfe/ffffff?text=Product+4"
    },
    {
        id: 5,
        title: "Product 5",
        description: "Customer favorite with 5-star ratings.",
        image: "https://via.placeholder.com/400x500/00f2fe/ffffff?text=Product+5"
    }
];

class SwipeApp {
    constructor() {
        this.cards = [...cardsData];
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
        
        this.init();
    }
    
    init() {
        this.renderCards();
        this.attachEventListeners();
    }
    
    renderCards() {
        this.cardsContainer.innerHTML = '';
        
        // Render cards in reverse order so the first card is on top
        for (let i = Math.min(this.currentIndex + 2, this.cards.length - 1); i >= this.currentIndex; i--) {
            if (i < this.cards.length) {
                const card = this.createCard(this.cards[i], i);
                this.cardsContainer.appendChild(card);
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
        }
        
        card.innerHTML = `
            <div class="swipe-indicator pass">NOPE</div>
            <div class="swipe-indicator like">LIKE</div>
            <img src="${data.image}" alt="${data.title}" class="card-image" loading="eager">
            <div class="card-content">
                <h2 class="card-title">${data.title}</h2>
                <p class="card-description">${data.description}</p>
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
        // Touch events
        this.cardsContainer.addEventListener('mousedown', this.onDragStart.bind(this), { passive: true });
        this.cardsContainer.addEventListener('touchstart', this.onDragStart.bind(this), { passive: true });
        
        document.addEventListener('mousemove', this.onDragMove.bind(this), { passive: false });
        document.addEventListener('touchmove', this.onDragMove.bind(this), { passive: false });
        
        document.addEventListener('mouseup', this.onDragEnd.bind(this));
        document.addEventListener('touchend', this.onDragEnd.bind(this));
        
        // Button events
        this.passBtn.addEventListener('click', () => this.swipe('left'));
        this.likeBtn.addEventListener('click', () => this.swipe('right'));
    }
    
    onDragStart(e) {
        const target = e.target.closest('.card');
        if (!target || parseInt(target.dataset.index) !== this.currentIndex) return;
        
        this.isDragging = true;
        this.currentCard = target;
        this.currentCard.classList.add('swiping');
        
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
        
        // Swipe threshold
        const swipeThreshold = 100;
        
        if (Math.abs(deltaX) > swipeThreshold) {
            const direction = deltaX > 0 ? 'right' : 'left';
            this.completeSwipe(direction);
        } else {
            // Reset card position
            this.currentCard.classList.remove('swiping');
            this.currentCard.style.transform = '';
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
        
        this.currentCard.classList.remove('swiping');
        this.currentCard.classList.add(direction === 'right' ? 'swiped-right' : 'swiped-left');
        
        // Log the action (you can replace this with actual API calls)
        const cardData = this.cards[this.currentIndex];
        console.log(`${direction === 'right' ? 'Liked' : 'Passed'}:`, cardData);
        
        // Move to next card
        setTimeout(() => {
            this.currentIndex++;
            this.renderCards();
        }, 300);
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