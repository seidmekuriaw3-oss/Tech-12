// ==================== CUSTOM CAROUSEL/SLIDER ====================
// Native JavaScript Carousel - No external dependencies

class ProductCarousel {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            slidesPerView: 1,
            spaceBetween: 20,
            loop: true,
            autoplay: true,
            autoplayDelay: 5000,
            pauseOnHover: true,
            navigation: true,
            pagination: true,
            breakpoints: {
                640: { slidesPerView: 2 },
                768: { slidesPerView: 3 },
                1024: { slidesPerView: 4 }
            },
            ...options
        };
        
        this.currentIndex = 0;
        this.currentTranslate = 0;
        this.slides = [];
        this.slideWidth = 0;
        this.slidesPerView = 1;
        this.autoplayInterval = null;
        this.isAnimating = false;
        this.track = null;
        this.prevBtn = null;
        this.nextBtn = null;
        this.dots = null;
        this.resizeHandler = null;
        this.touchStartX = 0;
        this.touchEndX = 0;
        
        this.init();
    }
    
    init() {
        // Get slides
        this.slides = Array.from(this.container.querySelectorAll('.swiper-slide, .product-slide, .carousel-slide'));
        if (this.slides.length === 0) return;
        
        // Get or create track
        this.track = this.container.querySelector('.swiper-wrapper, .carousel-track');
        if (!this.track) {
            this.createTrack();
        }
        
        // Make container relative for absolute positioning of buttons
        this.container.style.position = 'relative';
        
        // Calculate slides per view based on screen width
        this.updateSlidesPerView();
        
        // Create navigation buttons
        if (this.options.navigation) {
            this.createNavigation();
        }
        
        // Create pagination dots
        if (this.options.pagination) {
            this.createPagination();
        }
        
        // Clone slides for infinite loop if needed
        if (this.options.loop && this.slides.length > this.slidesPerView) {
            this.cloneSlides();
        }
        
        // Re-get slides after cloning
        this.slides = Array.from(this.track.children);
        
        // Set slide widths
        this.setSlideWidths();
        
        // Add resize listener
        this.resizeHandler = this.handleResize.bind(this);
        window.addEventListener('resize', this.resizeHandler);
        
        // Add touch events for mobile
        this.addTouchEvents();
        
        // Add hover pause
        if (this.options.autoplay && this.options.pauseOnHover) {
            this.container.addEventListener('mouseenter', () => this.stopAutoplay());
            this.container.addEventListener('mouseleave', () => this.startAutoplay());
        }
        
        // Go to first slide (or appropriate starting position for loop)
        if (this.options.loop && this.slides.length > this.slidesPerView) {
            const startIndex = this.slidesPerView;
            this.goToSlide(startIndex, true);
        } else {
            this.goToSlide(0, true);
        }
        
        // Start autoplay
        if (this.options.autoplay) {
            this.startAutoplay();
        }
    }
    
    createTrack() {
        // Wrap slides in a track div if not already wrapped
        const track = document.createElement('div');
        track.className = 'carousel-track';
        track.style.cssText = `
            display: flex;
            transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            will-change: transform;
            height: 100%;
        `;
        
        const children = Array.from(this.container.children);
        children.forEach(child => {
            track.appendChild(child);
        });
        
        this.container.appendChild(track);
        this.track = track;
    }
    
    updateSlidesPerView() {
        const width = window.innerWidth;
        let slidesPerView = this.options.slidesPerView;
        
        // Check breakpoints (sorted ascending)
        const breakpoints = Object.keys(this.options.breakpoints)
            .map(Number)
            .sort((a, b) => a - b);
        
        for (let bp of breakpoints) {
            if (width >= bp) {
                slidesPerView = this.options.breakpoints[bp].slidesPerView;
            }
        }
        
        this.slidesPerView = slidesPerView;
        return slidesPerView;
    }
    
    setSlideWidths() {
        const containerWidth = this.container.clientWidth;
        const gap = this.options.spaceBetween;
        const slideWidth = (containerWidth - (gap * (this.slidesPerView - 1))) / this.slidesPerView;
        
        this.slideWidth = slideWidth;
        
        this.slides.forEach(slide => {
            slide.style.cssText = `
                flex: 0 0 ${slideWidth}px;
                margin-right: ${gap}px;
                transition: transform 0.3s ease;
                box-sizing: border-box;
            `;
        });
        
        // Set track width
        const totalWidth = this.slides.length * (slideWidth + gap);
        this.track.style.width = `${totalWidth}px`;
    }
    
    createNavigation() {
        // Previous button
        const prevBtn = document.createElement('button');
        prevBtn.className = 'carousel-prev';
        prevBtn.innerHTML = '❮';
        prevBtn.setAttribute('aria-label', 'Previous slide');
        prevBtn.style.cssText = `
            position: absolute;
            top: 50%;
            left: 10px;
            transform: translateY(-50%);
            background: rgba(0,0,0,0.5);
            color: white;
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 20px;
            z-index: 10;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        prevBtn.addEventListener('click', () => this.prev());
        prevBtn.addEventListener('mouseenter', () => {
            prevBtn.style.background = 'rgba(0,0,0,0.8)';
            prevBtn.style.transform = 'translateY(-50%) scale(1.1)';
        });
        prevBtn.addEventListener('mouseleave', () => {
            prevBtn.style.background = 'rgba(0,0,0,0.5)';
            prevBtn.style.transform = 'translateY(-50%) scale(1)';
        });
        
        // Next button
        const nextBtn = document.createElement('button');
        nextBtn.className = 'carousel-next';
        nextBtn.innerHTML = '❯';
        nextBtn.setAttribute('aria-label', 'Next slide');
        nextBtn.style.cssText = `
            position: absolute;
            top: 50%;
            right: 10px;
            transform: translateY(-50%);
            background: rgba(0,0,0,0.5);
            color: white;
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 20px;
            z-index: 10;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        nextBtn.addEventListener('click', () => this.next());
        nextBtn.addEventListener('mouseenter', () => {
            nextBtn.style.background = 'rgba(0,0,0,0.8)';
            nextBtn.style.transform = 'translateY(-50%) scale(1.1)';
        });
        nextBtn.addEventListener('mouseleave', () => {
            nextBtn.style.background = 'rgba(0,0,0,0.5)';
            nextBtn.style.transform = 'translateY(-50%) scale(1)';
        });
        
        this.container.appendChild(prevBtn);
        this.container.appendChild(nextBtn);
        
        this.prevBtn = prevBtn;
        this.nextBtn = nextBtn;
        
        // Hide buttons on mobile if only one slide visible
        this.updateNavigationVisibility();
    }
    
    updateNavigationVisibility() {
        if (this.slides.length <= this.slidesPerView) {
            if (this.prevBtn) this.prevBtn.style.display = 'none';
            if (this.nextBtn) this.nextBtn.style.display = 'none';
        } else {
            if (this.prevBtn) this.prevBtn.style.display = 'flex';
            if (this.nextBtn) this.nextBtn.style.display = 'flex';
        }
    }
    
    createPagination() {
        const dotsContainer = document.createElement('div');
        dotsContainer.className = 'carousel-dots';
        dotsContainer.style.cssText = `
            position: absolute;
            bottom: 15px;
            left: 0;
            right: 0;
            display: flex;
            justify-content: center;
            gap: 8px;
            z-index: 10;
            flex-wrap: wrap;
            padding: 5px;
        `;
        
        const totalDots = this.options.loop ? this.slides.length - (this.slidesPerView * 2) : this.slides.length;
        for (let i = 0; i < totalDots; i++) {
            const dot = document.createElement('button');
            dot.className = 'carousel-dot';
            dot.setAttribute('aria-label', `Go to slide ${i + 1}`);
            dot.style.cssText = `
                width: 8px;
                height: 8px;
                background: rgba(255,255,255,0.5);
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
    
    updatePagination() {
        if (!this.dots) return;
        
        const visibleIndex = this.getVisibleSlideIndex();
        this.dots.forEach((dot, i) => {
            if (i === visibleIndex) {
                dot.style.background = 'white';
                dot.style.transform = 'scale(1.2)';
                dot.style.width = '20px';
                dot.style.borderRadius = '10px';
            } else {
                dot.style.background = 'rgba(255,255,255,0.5)';
                dot.style.transform = 'scale(1)';
                dot.style.width = '8px';
                dot.style.borderRadius = '50%';
            }
        });
    }
    
    getVisibleSlideIndex() {
        const slideTotal = this.slideWidth + this.options.spaceBetween;
        const offset = -this.currentTranslate;
        let index = Math.round(offset / slideTotal);
        
        if (this.options.loop) {
            const actualStart = this.slidesPerView;
            const actualEnd = this.slides.length - this.slidesPerView;
            index = Math.max(actualStart, Math.min(index, actualEnd - 1));
            index = index - actualStart;
        }
        
        return Math.min(Math.max(0, index), this.dots ? this.dots.length - 1 : 0);
    }
    
    goToSlide(index, skipAnimation = false) {
        if (this.isAnimating) return;
        
        let targetIndex = index;
        const slideTotal = this.slideWidth + this.options.spaceBetween;
        const maxIndex = this.slides.length - this.slidesPerView;
        
        if (this.options.loop) {
            const actualStart = this.slidesPerView;
            const actualEnd = this.slides.length - this.slidesPerView;
            
            if (targetIndex < 0) {
                targetIndex = actualEnd - 1;
            } else if (targetIndex >= actualEnd) {
                targetIndex = actualStart;
            } else {
                targetIndex = Math.min(Math.max(actualStart, targetIndex), actualEnd - 1);
            }
        } else {
            targetIndex = Math.min(Math.max(0, targetIndex), maxIndex);
        }
        
        this.currentIndex = targetIndex;
        const translateX = -(targetIndex * slideTotal);
        
        if (skipAnimation) {
            this.track.style.transition = 'none';
            this.track.style.transform = `translateX(${translateX}px)`;
            // Force reflow
            this.track.offsetHeight;
            this.track.style.transition = '';
        } else {
            this.isAnimating = true;
            this.track.style.transform = `translateX(${translateX}px)`;
            
            setTimeout(() => {
                this.isAnimating = false;
            }, 400);
        }
        
        this.currentTranslate = translateX;
        this.updatePagination();
        this.updateNavigationVisibility();
        
        // Handle loop edge cases
        if (this.options.loop) {
            this.handleLoopEdge(targetIndex, slideTotal);
        }
    }
    
    handleLoopEdge(currentIndex, slideTotal) {
        const actualStart = this.slidesPerView;
        const actualEnd = this.slides.length - this.slidesPerView;
        
        if (currentIndex <= actualStart) {
            // At start, jump to the actual end without animation
            setTimeout(() => {
                this.track.style.transition = 'none';
                const jumpIndex = actualEnd - 1;
                this.currentIndex = jumpIndex;
                this.currentTranslate = -(jumpIndex * slideTotal);
                this.track.style.transform = `translateX(${this.currentTranslate}px)`;
                this.track.offsetHeight;
                this.track.style.transition = '';
            }, 400);
        } else if (currentIndex >= actualEnd - 1) {
            // At end, jump to actual start
            setTimeout(() => {
                this.track.style.transition = 'none';
                const jumpIndex = actualStart;
                this.currentIndex = jumpIndex;
                this.currentTranslate = -(jumpIndex * slideTotal);
                this.track.style.transform = `translateX(${this.currentTranslate}px)`;
                this.track.offsetHeight;
                this.track.style.transition = '';
            }, 400);
        }
    }
    
    next() {
        let nextIndex = this.currentIndex + 1;
        if (!this.options.loop && nextIndex > this.slides.length - this.slidesPerView) {
            nextIndex = 0;
        }
        this.goToSlide(nextIndex);
        this.resetAutoplay();
    }
    
    prev() {
        let prevIndex = this.currentIndex - 1;
        if (!this.options.loop && prevIndex < 0) {
            prevIndex = this.slides.length - this.slidesPerView;
        }
        this.goToSlide(prevIndex);
        this.resetAutoplay();
    }
    
    startAutoplay() {
        if (this.autoplayInterval) clearInterval(this.autoplayInterval);
        this.autoplayInterval = setInterval(() => {
            this.next();
        }, this.options.autoplayDelay);
    }
    
    stopAutoplay() {
        if (this.autoplayInterval) {
            clearInterval(this.autoplayInterval);
            this.autoplayInterval = null;
        }
    }
    
    resetAutoplay() {
        if (this.options.autoplay) {
            this.stopAutoplay();
            this.startAutoplay();
        }
    }
    
    cloneSlides() {
        const clones = [];
        const slidesToClone = this.slidesPerView;
        
        // Clone first few slides and append to end
        for (let i = 0; i < slidesToClone; i++) {
            const clone = this.slides[i].cloneNode(true);
            clone.classList.add('clone');
            clone.setAttribute('aria-hidden', 'true');
            this.track.appendChild(clone);
            clones.push(clone);
        }
        
        // Clone last few slides and prepend to beginning
        const startIndex = this.slides.length - slidesToClone;
        for (let i = startIndex; i < this.slides.length; i++) {
            const clone = this.slides[i].cloneNode(true);
            clone.classList.add('clone');
            clone.setAttribute('aria-hidden', 'true');
            this.track.insertBefore(clone, this.track.firstChild);
            clones.unshift(clone);
        }
    }
    
    addTouchEvents() {
        this.container.addEventListener('touchstart', (e) => {
            this.touchStartX = e.changedTouches[0].screenX;
            this.stopAutoplay();
        }, { passive: true });
        
        this.container.addEventListener('touchend', (e) => {
            this.touchEndX = e.changedTouches[0].screenX;
            const diff = this.touchEndX - this.touchStartX;
            
            if (Math.abs(diff) > 50) {
                if (diff > 0) {
                    this.prev();
                } else {
                    this.next();
                }
            }
            
            this.startAutoplay();
        });
    }
    
    handleResize() {
        this.updateSlidesPerView();
        this.setSlideWidths();
        
        // Re-clone if needed
        if (this.options.loop) {
            // Remove existing clones
            const clones = this.track.querySelectorAll('.clone');
            clones.forEach(clone => clone.remove());
            this.slides = Array.from(this.track.children);
            this.cloneSlides();
            this.slides = Array.from(this.track.children);
            this.setSlideWidths();
        }
        
        const startIndex = this.options.loop ? this.slidesPerView : 0;
        this.goToSlide(startIndex, true);
        this.updateNavigationVisibility();
    }
    
    destroy() {
        this.stopAutoplay();
        if (this.resizeHandler) {
            window.removeEventListener('resize', this.resizeHandler);
        }
        if (this.prevBtn) this.prevBtn.remove();
        if (this.nextBtn) this.nextBtn.remove();
        if (this.dots) {
            this.dots.forEach(dot => {
                if (dot.parentNode) dot.parentNode.remove();
            });
        }
        
        // Restore original slides
        const children = Array.from(this.track.children);
        children.forEach(child => {
            if (child.classList && child.classList.contains('clone')) {
                child.remove();
            } else {
                child.style.cssText = '';
            }
        });
        
        // Unwrap track
        const parent = this.container;
        const trackChildren = Array.from(this.track.children);
        trackChildren.forEach(child => {
            parent.appendChild(child);
        });
        this.track.remove();
    }
}

// ==================== PRODUCT CAROUSEL INIT ====================
function initProductCarousel() {
    const swiperEl = document.querySelector('.product-swiper, .products-carousel, .featured-carousel');
    if (!swiperEl) {
        console.log('Product carousel container not found');
        return null;
    }
    
    try {
        return new ProductCarousel(swiperEl, {
            slidesPerView: 1,
            spaceBetween: 20,
            loop: true,
            autoplay: true,
            autoplayDelay: 5000,
            navigation: true,
            pagination: true,
            breakpoints: {
                640: { slidesPerView: 2 },
                768: { slidesPerView: 3 },
                1024: { slidesPerView: 4 }
            }
        });
    } catch (error) {
        console.error('Error initializing product carousel:', error);
        return null;
    }
}

// ==================== HERO SLIDER INIT ====================
function initHeroSlider() {
    const heroSwiper = document.querySelector('.hero-swiper, .hero-slider, .main-slider');
    if (!heroSwiper) {
        console.log('Hero slider container not found');
        return null;
    }
    
    try {
        return new ProductCarousel(heroSwiper, {
            slidesPerView: 1,
            spaceBetween: 0,
            loop: true,
            autoplay: true,
            autoplayDelay: 4000,
            navigation: true,
            pagination: true,
            breakpoints: {}
        });
    } catch (error) {
        console.error('Error initializing hero slider:', error);
        return null;
    }
}

// ==================== SIMPLE FADE SLIDER (Alternative) ====================
class FadeSlider {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            autoplay: true,
            interval: 4000,
            navigation: true,
            pagination: true,
            ...options
        };
        this.currentIndex = 0;
        this.slides = [];
        this.autoplayInterval = null;
        this.dots = null;
        this.prevBtn = null;
        this.nextBtn = null;
        this.init();
    }
    
    init() {
        this.slides = Array.from(this.container.querySelectorAll('.fade-slide, .hero-slide, .slider-slide'));
        if (this.slides.length === 0) return;
        
        // Set container position
        this.container.style.position = 'relative';
        this.container.style.overflow = 'hidden';
        
        // Style slides
        this.slides.forEach((slide, i) => {
            slide.style.transition = 'opacity 0.5s ease';
            slide.style.position = 'absolute';
            slide.style.top = '0';
            slide.style.left = '0';
            slide.style.right = '0';
            slide.style.bottom = '0';
            slide.style.opacity = i === 0 ? '1' : '0';
        });
        
        // Set container height to match tallest slide
        this.updateContainerHeight();
        window.addEventListener('resize', () => this.updateContainerHeight());
        
        // Create navigation
        if (this.options.navigation) {
            this.createNavigation();
        }
        
        // Create pagination dots
        if (this.options.pagination) {
            this.createDots();
        }
        
        // Start autoplay
        if (this.options.autoplay) {
            this.startAutoplay();
        }
        
        // Pause on hover
        this.container.addEventListener('mouseenter', () => this.stopAutoplay());
        this.container.addEventListener('mouseleave', () => this.startAutoplay());
    }
    
    updateContainerHeight() {
        const activeSlide = this.slides[this.currentIndex];
        if (activeSlide) {
            const height = activeSlide.offsetHeight;
            this.container.style.height = `${height}px`;
        }
    }
    
    createNavigation() {
        // Previous button
        this.prevBtn = document.createElement('button');
        this.prevBtn.className = 'fade-prev';
        this.prevBtn.innerHTML = '❮';
        this.prevBtn.setAttribute('aria-label', 'Previous slide');
        this.prevBtn.style.cssText = `
            position: absolute;
            top: 50%;
            left: 10px;
            transform: translateY(-50%);
            background: rgba(0,0,0,0.5);
            color: white;
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 20px;
            z-index: 10;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        this.prevBtn.addEventListener('click', () => this.prev());
        this.container.appendChild(this.prevBtn);
        
        // Next button
        this.nextBtn = document.createElement('button');
        this.nextBtn.className = 'fade-next';
        this.nextBtn.innerHTML = '❯';
        this.nextBtn.setAttribute('aria-label', 'Next slide');
        this.nextBtn.style.cssText = `
            position: absolute;
            top: 50%;
            right: 10px;
            transform: translateY(-50%);
            background: rgba(0,0,0,0.5);
            color: white;
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 20px;
            z-index: 10;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        this.nextBtn.addEventListener('click', () => this.next());
        this.container.appendChild(this.nextBtn);
    }
    
    createDots() {
        const dotsContainer = document.createElement('div');
        dotsContainer.className = 'fade-dots';
        dotsContainer.style.cssText = `
            position: absolute;
            bottom: 20px;
            left: 0;
            right: 0;
            display: flex;
            justify-content: center;
            gap: 10px;
            z-index: 10;
        `;
        
        this.slides.forEach((_, i) => {
            const dot = document.createElement('button');
            dot.className = 'fade-dot';
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
        });
        
        this.container.appendChild(dotsContainer);
        this.dots = Array.from(dotsContainer.children);
    }
    
    updateDots() {
        if (!this.dots) return;
        this.dots.forEach((dot, i) => {
            dot.style.background = i === this.currentIndex ? 'white' : 'rgba(255,255,255,0.5)';
        });
    }
    
    goToSlide(index) {
        if (index === this.currentIndex) return;
        if (index < 0) index = this.slides.length - 1;
        if (index >= this.slides.length) index = 0;
        
        // Fade out current, fade in new
        this.slides[this.currentIndex].style.opacity = '0';
        this.slides[index].style.opacity = '1';
        
        this.currentIndex = index;
        this.updateContainerHeight();
        this.updateDots();
        this.resetAutoplay();
    }
    
    next() {
        this.goToSlide(this.currentIndex + 1);
    }
    
    prev() {
        this.goToSlide(this.currentIndex - 1);
    }
    
    startAutoplay() {
        if (this.autoplayInterval) clearInterval(this.autoplayInterval);
        this.autoplayInterval = setInterval(() => this.next(), this.options.interval);
    }
    
    stopAutoplay() {
        if (this.autoplayInterval) {
            clearInterval(this.autoplayInterval);
            this.autoplayInterval = null;
        }
    }
    
    resetAutoplay() {
        if (this.options.autoplay) {
            this.stopAutoplay();
            this.startAutoplay();
        }
    }
    
    destroy() {
        this.stopAutoplay();
        if (this.prevBtn) this.prevBtn.remove();
        if (this.nextBtn) this.nextBtn.remove();
        if (this.dots) {
            if (this.dots[0] && this.dots[0].parentNode) {
                this.dots[0].parentNode.remove();
            }
        }
        window.removeEventListener('resize', () => this.updateContainerHeight());
    }
}

// ==================== INITIALIZE ON DOM READY ====================
document.addEventListener('DOMContentLoaded', () => {
    // Initialize product carousel
    initProductCarousel();
    
    // Initialize hero slider
    initHeroSlider();
    
    // Alternative: Use fade slider for hero if container exists
    const heroContainer = document.querySelector('.hero-slider-container, .fade-slider-container');
    if (heroContainer && heroContainer.querySelectorAll('.hero-slide, .fade-slide').length > 0) {
        new FadeSlider(heroContainer, {
            autoplay: true,
            interval: 4000,
            navigation: true,
            pagination: true
        });
        console.log('Fade slider initialized');
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ProductCarousel, FadeSlider, initProductCarousel, initHeroSlider };
}

// Make globally available
if (typeof window !== 'undefined') {
    window.ProductCarousel = ProductCarousel;
    window.FadeSlider = FadeSlider;
    window.initProductCarousel = initProductCarousel;
    window.initHeroSlider = initHeroSlider;
}