// ==================== MODERN SLIDER/CAROUSEL ====================
// Professional Slider with Touch Support and Accessibility

class ModernSlider {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            autoPlay: true,
            interval: 5000,
            speed: 500,
            pauseOnHover: true,
            pauseOnVisibilityChange: true,
            keyboardNavigation: true,
            swipeEnabled: true,
            loop: true,
            showDots: true,
            showProgress: true,
            ...options
        };
        
        this.currentIndex = 0;
        this.slides = [];
        this.totalSlides = 0;
        this.autoPlayInterval = null;
        this.isAnimating = false;
        this.isPaused = false;
        this.touchStartX = 0;
        this.touchEndX = 0;
        this.track = null;
        this.dots = null;
        this.progressBar = null;
        this.announcement = null;
        this.prevHandler = null;
        this.nextHandler = null;
        this.keydownHandler = null;
        this.resizeHandler = null;
        
        this.init();
    }
    
    init() {
        // Get slider elements
        this.track = this.container.querySelector('.slider-track, .swiper-wrapper, .carousel-track');
        this.slides = Array.from(this.container.querySelectorAll('.slider-slide, .slide, .swiper-slide, .carousel-slide'));
        this.totalSlides = this.slides.length;
        
        if (this.totalSlides === 0) {
            console.warn('No slides found in slider container');
            return;
        }
        
        if (this.totalSlides <= 1) {
            // Hide navigation if only one slide
            this.hideNavigation();
            return;
        }
        
        // Create track if not exists
        if (!this.track) {
            this.createTrack();
        }
        
        // Set up slider structure
        this.setupSlider();
        
        // Create UI elements
        if (this.options.showDots) this.createDots();
        if (this.options.showProgress) this.createProgressBar();
        
        // Set up event listeners
        this.bindEvents();
        
        // Set initial slide position
        this.update();
        
        // Start autoplay if enabled
        if (this.options.autoPlay) {
            this.startAutoPlay();
        }
        
        // Set ARIA attributes
        this.setAccessibilityAttributes();
        
        // Handle visibility change (pause when tab is inactive)
        if (this.options.pauseOnVisibilityChange) {
            this.initVisibilityAPI();
        }
    }
    
    createTrack() {
        // Wrap slides in a track div
        this.track = document.createElement('div');
        this.track.className = 'slider-track';
        
        const children = Array.from(this.container.children);
        children.forEach(child => {
            if (!child.classList || (!child.classList.contains('slider-prev') && 
                !child.classList.contains('slider-next') && 
                !child.classList.contains('slider-dots'))) {
                this.track.appendChild(child);
            }
        });
        
        this.container.appendChild(this.track);
    }
    
    setupSlider() {
        // Ensure slides have proper styling
        this.slides.forEach((slide, index) => {
            slide.style.flex = '0 0 100%';
            slide.style.position = 'relative';
            slide.style.width = '100%';
            slide.setAttribute('aria-label', `Slide ${index + 1} of ${this.totalSlides}`);
            slide.setAttribute('role', 'group');
        });
        
        // Ensure track has proper styling
        if (this.track) {
            this.track.style.display = 'flex';
            this.track.style.transition = `transform ${this.options.speed}ms cubic-bezier(0.4, 0, 0.2, 1)`;
            this.track.style.willChange = 'transform';
            this.track.style.width = '100%';
            this.track.style.height = '100%';
        }
        
        // Set container position
        this.container.style.position = 'relative';
        this.container.style.overflow = 'hidden';
        this.container.setAttribute('role', 'region');
        this.container.setAttribute('aria-roledescription', 'carousel');
    }
    
    createDots() {
        // Remove existing dots container if any
        const existingDots = this.container.querySelector('.slider-dots');
        if (existingDots) existingDots.remove();
        
        const dotsContainer = document.createElement('div');
        dotsContainer.className = 'slider-dots';
        dotsContainer.setAttribute('aria-label', 'Slide navigation');
        dotsContainer.style.cssText = `
            position: absolute;
            bottom: 15px;
            left: 0;
            right: 0;
            display: flex;
            justify-content: center;
            gap: 10px;
            z-index: 10;
        `;
        
        for (let i = 0; i < this.totalSlides; i++) {
            const dot = document.createElement('button');
            dot.className = 'slider-dot';
            dot.dataset.index = i;
            dot.setAttribute('aria-label', `Go to slide ${i + 1}`);
            dot.style.cssText = `
                width: 10px;
                height: 10px;
                background: ${i === this.currentIndex ? 'white' : 'rgba(255,255,255,0.5)'};
                border: none;
                border-radius: 50%;
                cursor: pointer;
                transition: all 0.3s ease;
                padding: 0;
            `;
            dot.addEventListener('click', () => this.goToSlide(i));
            dotsContainer.appendChild(dot);
        }
        
        this.container.appendChild(dotsContainer);
        this.dots = Array.from(dotsContainer.children);
    }
    
    createProgressBar() {
        // Remove existing progress bar
        const existingProgress = this.container.querySelector('.slider-progress');
        if (existingProgress) existingProgress.remove();
        
        const progress = document.createElement('div');
        progress.className = 'slider-progress';
        progress.style.cssText = `
            position: absolute;
            bottom: 0;
            left: 0;
            height: 3px;
            background: rgba(255, 255, 255, 0.5);
            width: 0%;
            pointer-events: none;
            z-index: 10;
        `;
        this.container.appendChild(progress);
        this.progressBar = progress;
    }
    
    bindEvents() {
        // Navigation buttons
        const prevBtn = this.container.querySelector('.slider-prev, .carousel-prev');
        const nextBtn = this.container.querySelector('.slider-next, .carousel-next');
        
        if (prevBtn) {
            prevBtn.removeEventListener('click', this.prevHandler);
            this.prevHandler = () => this.prev();
            prevBtn.addEventListener('click', this.prevHandler);
            prevBtn.setAttribute('aria-label', 'Previous slide');
        }
        
        if (nextBtn) {
            nextBtn.removeEventListener('click', this.nextHandler);
            this.nextHandler = () => this.next();
            nextBtn.addEventListener('click', this.nextHandler);
            nextBtn.setAttribute('aria-label', 'Next slide');
        }
        
        // Pause on hover
        if (this.options.pauseOnHover) {
            this.container.addEventListener('mouseenter', () => this.pauseAutoPlay());
            this.container.addEventListener('mouseleave', () => this.resumeAutoPlay());
        }
        
        // Keyboard navigation
        if (this.options.keyboardNavigation) {
            this.keydownHandler = this.handleKeydown.bind(this);
            document.addEventListener('keydown', this.keydownHandler);
        }
        
        // Touch events for mobile
        if (this.options.swipeEnabled) {
            this.initTouchEvents();
        }
        
        // Window resize - recalculate positions
        this.resizeHandler = this.debounce(() => {
            this.update();
        }, 150);
        window.addEventListener('resize', this.resizeHandler);
    }
    
    initTouchEvents() {
        this.container.addEventListener('touchstart', (e) => {
            this.touchStartX = e.changedTouches[0].screenX;
            this.pauseAutoPlay();
        }, { passive: true });
        
        this.container.addEventListener('touchend', (e) => {
            this.touchEndX = e.changedTouches[0].screenX;
            this.handleSwipe();
            this.resumeAutoPlay();
        });
    }
    
    handleSwipe() {
        const swipeThreshold = 50;
        const diff = this.touchEndX - this.touchStartX;
        
        if (Math.abs(diff) > swipeThreshold) {
            if (diff > 0) {
                this.prev();
            } else {
                this.next();
            }
        }
    }
    
    handleKeydown(e) {
        // Only handle if slider is visible in viewport
        const rect = this.container.getBoundingClientRect();
        const isVisible = rect.top < window.innerHeight && rect.bottom > 0;
        
        if (!isVisible) return;
        
        if (e.key === 'ArrowLeft') {
            e.preventDefault();
            this.prev();
        } else if (e.key === 'ArrowRight') {
            e.preventDefault();
            this.next();
        }
    }
    
    goToSlide(index, skipAnimation = false) {
        if (this.isAnimating) return;
        if (index === this.currentIndex) return;
        
        // Handle loop boundaries
        if (this.options.loop) {
            if (index < 0) index = this.totalSlides - 1;
            if (index >= this.totalSlides) index = 0;
        } else {
            if (index < 0) index = 0;
            if (index >= this.totalSlides) index = this.totalSlides - 1;
        }
        
        if (index === this.currentIndex) return;
        
        this.isAnimating = true;
        this.currentIndex = index;
        
        // Update track position
        const offset = -this.currentIndex * 100;
        
        if (this.track) {
            if (skipAnimation) {
                this.track.style.transition = 'none';
                this.track.style.transform = `translateX(${offset}%)`;
                // Force reflow
                void this.track.offsetHeight;
                this.track.style.transition = `transform ${this.options.speed}ms cubic-bezier(0.4, 0, 0.2, 1)`;
            } else {
                this.track.style.transform = `translateX(${offset}%)`;
            }
        }
        
        // Update dots
        this.updateDots();
        
        // Trigger slide change event
        this.dispatchEvent();
        
        // Reset animation flag
        setTimeout(() => {
            this.isAnimating = false;
        }, this.options.speed);
        
        // Reset autoplay
        this.resetAutoPlay();
    }
    
    update() {
        const offset = -this.currentIndex * 100;
        if (this.track) {
            this.track.style.transform = `translateX(${offset}%)`;
        }
        this.updateDots();
    }
    
    updateDots() {
        if (!this.dots) return;
        
        this.dots.forEach((dot, i) => {
            if (i === this.currentIndex) {
                dot.classList.add('active');
                dot.style.background = 'white';
                dot.style.transform = 'scale(1.2)';
                dot.setAttribute('aria-current', 'true');
            } else {
                dot.classList.remove('active');
                dot.style.background = 'rgba(255,255,255,0.5)';
                dot.style.transform = 'scale(1)';
                dot.removeAttribute('aria-current');
            }
        });
    }
    
    next() {
        if (this.options.loop || this.currentIndex < this.totalSlides - 1) {
            this.goToSlide(this.currentIndex + 1);
        }
    }
    
    prev() {
        if (this.options.loop || this.currentIndex > 0) {
            this.goToSlide(this.currentIndex - 1);
        }
    }
    
    startAutoPlay() {
        if (this.autoPlayInterval) {
            clearInterval(this.autoPlayInterval);
            this.autoPlayInterval = null;
        }
        
        this.autoPlayInterval = setInterval(() => {
            if (!this.isPaused && !this.isAnimating) {
                this.next();
                this.resetProgressAnimation();
            }
        }, this.options.interval);
        
        this.resetProgressAnimation();
    }
    
    pauseAutoPlay() {
        this.isPaused = true;
        if (this.autoPlayInterval) {
            clearInterval(this.autoPlayInterval);
            this.autoPlayInterval = null;
        }
        this.pauseProgressAnimation();
    }
    
    resumeAutoPlay() {
        if (!this.options.autoPlay) return;
        this.isPaused = false;
        if (!this.autoPlayInterval) {
            this.startAutoPlay();
        }
        this.resumeProgressAnimation();
    }
    
    resetAutoPlay() {
        if (this.options.autoPlay && !this.isPaused) {
            if (this.autoPlayInterval) {
                clearInterval(this.autoPlayInterval);
                this.autoPlayInterval = null;
            }
            this.startAutoPlay();
        }
    }
    
    resetProgressAnimation() {
        if (!this.progressBar) return;
        
        this.progressBar.style.animation = 'none';
        this.progressBar.style.width = '0%';
        
        // Force reflow
        void this.progressBar.offsetHeight;
        
        this.progressBar.style.animation = `progress ${this.options.interval}ms linear forwards`;
        this.progressBar.style.width = '100%';
    }
    
    pauseProgressAnimation() {
        if (!this.progressBar) return;
        this.progressBar.style.animationPlayState = 'paused';
    }
    
    resumeProgressAnimation() {
        if (!this.progressBar) return;
        this.progressBar.style.animationPlayState = 'running';
    }
    
    hideNavigation() {
        const prevBtn = this.container.querySelector('.slider-prev, .carousel-prev');
        const nextBtn = this.container.querySelector('.slider-next, .carousel-next');
        const dots = this.container.querySelector('.slider-dots');
        
        if (prevBtn) prevBtn.style.display = 'none';
        if (nextBtn) nextBtn.style.display = 'none';
        if (dots) dots.style.display = 'none';
    }
    
    setAccessibilityAttributes() {
        this.container.setAttribute('aria-live', 'polite');
        this.container.setAttribute('aria-atomic', 'true');
        
        // Add slide count announcement
        if (!this.announcement) {
            this.announcement = document.createElement('div');
            this.announcement.className = 'sr-only';
            this.announcement.setAttribute('aria-live', 'polite');
            this.announcement.style.cssText = `
                position: absolute;
                width: 1px;
                height: 1px;
                padding: 0;
                margin: -1px;
                overflow: hidden;
                clip: rect(0, 0, 0, 0);
                white-space: nowrap;
                border: 0;
            `;
            this.container.appendChild(this.announcement);
        }
    }
    
    dispatchEvent() {
        // Update announcement for screen readers
        if (this.announcement) {
            this.announcement.textContent = `Slide ${this.currentIndex + 1} of ${this.totalSlides}`;
        }
        
        // Dispatch custom event
        const event = new CustomEvent('slideChange', { 
            detail: { 
                index: this.currentIndex,
                total: this.totalSlides,
                currentSlide: this.slides[this.currentIndex]
            } 
        });
        this.container.dispatchEvent(event);
    }
    
    initVisibilityAPI() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseAutoPlay();
            } else {
                this.resumeAutoPlay();
            }
        });
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Public API methods
    destroy() {
        // Clean up event listeners
        const prevBtn = this.container.querySelector('.slider-prev, .carousel-prev');
        const nextBtn = this.container.querySelector('.slider-next, .carousel-next');
        
        if (prevBtn && this.prevHandler) {
            prevBtn.removeEventListener('click', this.prevHandler);
        }
        if (nextBtn && this.nextHandler) {
            nextBtn.removeEventListener('click', this.nextHandler);
        }
        
        if (this.keydownHandler) {
            document.removeEventListener('keydown', this.keydownHandler);
        }
        
        if (this.resizeHandler) {
            window.removeEventListener('resize', this.resizeHandler);
        }
        
        // Stop autoplay
        this.pauseAutoPlay();
        
        // Remove announcement
        if (this.announcement && this.announcement.parentNode) {
            this.announcement.remove();
        }
        
        // Remove dots
        const dots = this.container.querySelector('.slider-dots');
        if (dots) dots.remove();
        
        // Remove progress bar
        if (this.progressBar && this.progressBar.parentNode) {
            this.progressBar.remove();
        }
        
        // Reset track styles
        if (this.track) {
            this.track.style.transform = '';
            this.track.style.transition = '';
        }
        
        this.container.dataset.sliderInitialized = 'false';
    }
    
    getCurrentIndex() {
        return this.currentIndex;
    }
    
    getTotalSlides() {
        return this.totalSlides;
    }
}

// ==================== Initialize Sliders ====================
function initSliders() {
    const sliderContainers = document.querySelectorAll('.slider-container, .hero-slider, .carousel-container');
    
    sliderContainers.forEach(container => {
        // Check if already initialized
        if (container.dataset.sliderInitialized === 'true') return;
        
        const autoPlay = container.dataset.autoplay !== 'false';
        const interval = parseInt(container.dataset.interval, 10) || 5000;
        const loop = container.dataset.loop !== 'false';
        const speed = parseInt(container.dataset.speed, 10) || 500;
        
        const slider = new ModernSlider(container, {
            autoPlay: autoPlay,
            interval: interval,
            speed: speed,
            loop: loop,
            pauseOnHover: true,
            keyboardNavigation: true,
            swipeEnabled: true,
            showDots: container.querySelector('.slider-dots') === null,
            showProgress: true
        });
        
        // Store instance for potential external access
        container.sliderInstance = slider;
        container.dataset.sliderInitialized = 'true';
    });
}

// ==================== CSS Styles ====================
(function addSliderStyles() {
    if (document.getElementById('slider-styles')) return;
    
    const sliderStyles = document.createElement('style');
    sliderStyles.id = 'slider-styles';
    sliderStyles.textContent = `
        @keyframes sliderProgress {
            0% { width: 0%; }
            100% { width: 100%; }
        }
        
        .slider-container,
        .hero-slider,
        .carousel-container {
            position: relative;
            overflow: hidden;
        }
        
        .slider-track {
            display: flex;
            transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            will-change: transform;
            height: 100%;
        }
        
        .slider-slide,
        .slide,
        .swiper-slide {
            flex: 0 0 100%;
            width: 100%;
        }
        
        .slider-dots {
            position: absolute;
            bottom: 15px;
            left: 0;
            right: 0;
            display: flex;
            justify-content: center;
            gap: 10px;
            z-index: 10;
        }
        
        .slider-dot {
            width: 10px;
            height: 10px;
            background: rgba(255, 255, 255, 0.5);
            border: none;
            border-radius: 50%;
            cursor: pointer;
            transition: all 0.3s ease;
            padding: 0;
        }
        
        .slider-dot.active {
            background: white;
            transform: scale(1.2);
        }
        
        .slider-progress {
            position: absolute;
            bottom: 0;
            left: 0;
            height: 3px;
            background: rgba(255, 255, 255, 0.5);
            width: 0%;
            pointer-events: none;
            z-index: 10;
        }
        
        /* Navigation buttons */
        .slider-prev,
        .slider-next,
        .carousel-prev,
        .carousel-next {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            background: rgba(0, 0, 0, 0.5);
            color: white;
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 20px;
            z-index: 10;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }
        
        .slider-prev,
        .carousel-prev {
            left: 15px;
        }
        
        .slider-next,
        .carousel-next {
            right: 15px;
        }
        
        .slider-prev:hover,
        .slider-next:hover,
        .carousel-prev:hover,
        .carousel-next:hover {
            background: rgba(0, 0, 0, 0.8);
            transform: translateY(-50%) scale(1.1);
        }
        
        /* Screen reader only */
        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .slider-prev,
            .slider-next,
            .carousel-prev,
            .carousel-next {
                width: 32px;
                height: 32px;
                font-size: 16px;
            }
            
            .slider-prev { left: 10px; }
            .slider-next { right: 10px; }
            
            .slider-dot {
                width: 8px;
                height: 8px;
            }
        }
        
        /* Reduced motion */
        @media (prefers-reduced-motion: reduce) {
            .slider-track {
                transition: none !important;
            }
            
            .slider-progress {
                animation: none !important;
            }
        }
    `;
    document.head.appendChild(sliderStyles);
})();

// ==================== Initialize on DOM Ready ====================
document.addEventListener('DOMContentLoaded', () => {
    initSliders();
});

// ==================== Handle Dynamically Added Sliders ====================
if (window.MutationObserver) {
    const sliderObserver = new MutationObserver((mutations) => {
        let shouldInit = false;
        
        mutations.forEach((mutation) => {
            if (mutation.addedNodes.length) {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1) { // Element node
                        if (node.classList && (
                            node.classList.contains('slider-container') ||
                            node.classList.contains('hero-slider') ||
                            node.classList.contains('carousel-container') ||
                            node.querySelector('.slider-container, .hero-slider, .carousel-container')
                        )) {
                            shouldInit = true;
                        }
                    }
                });
            }
        });
        
        if (shouldInit) {
            setTimeout(initSliders, 100);
        }
    });
    
    sliderObserver.observe(document.body, { childList: true, subtree: true });
}

// ==================== Exports ====================
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ModernSlider, initSliders };
}

window.ModernSlider = ModernSlider;
window.initSliders = initSliders;