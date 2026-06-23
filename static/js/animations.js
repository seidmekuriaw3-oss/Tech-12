// ==================== ANIMATIONS.JS ====================
// Professional Animations and Effects for SEMIRA FASHION
// Includes: Scroll animations, hover effects, loading animations, cart animations, etc.

// ==================== DOM Ready ====================
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all animations
    initScrollReveal();
    initHoverEffects();
    initLoadingAnimations();
    initCartAnimations();
    initFormAnimations();
    initPageTransitions();
    initCounterAnimations();
    initPulseEffects();
});

// ==================== SCROLL REVEAL ANIMATIONS ====================
function initScrollReveal() {
    const revealElements = document.querySelectorAll('.scroll-reveal, .fade-in-up, .fade-in, .slide-in-left, .slide-in-right');
    
    if (revealElements.length === 0) return;
    
    // Create observer
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
                // Unobserve after animation
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    // Observe each element
    revealElements.forEach(element => {
        observer.observe(element);
    });
}

// ==================== HOVER EFFECTS ====================
function initHoverEffects() {
    // Product card hover effect
    const productCards = document.querySelectorAll('.product-card');
    productCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.classList.add('hover-grow');
        });
        card.addEventListener('mouseleave', function() {
            this.classList.remove('hover-grow');
        });
    });
    
    // Button ripple effect
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', createRippleEffect);
    });
    
    // Image zoom on hover
    const imageContainers = document.querySelectorAll('.product-image, .branch-image, .hero-image');
    imageContainers.forEach(container => {
        const img = container.querySelector('img');
        if (img) {
            container.addEventListener('mouseenter', () => {
                img.style.transform = 'scale(1.05)';
                img.style.transition = 'transform 0.5s ease';
            });
            container.addEventListener('mouseleave', () => {
                img.style.transform = 'scale(1)';
            });
        }
    });
}

function createRippleEffect(event) {
    const button = event.currentTarget;
    const ripple = document.createElement('span');
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;
    
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${x}px`;
    ripple.style.top = `${y}px`;
    ripple.className = 'ripple-effect';
    
    // Remove existing ripples
    const existingRipple = button.querySelector('.ripple-effect');
    if (existingRipple) existingRipple.remove();
    
    button.appendChild(ripple);
    
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

// ==================== LOADING ANIMATIONS ====================
function initLoadingAnimations() {
    // Skeleton loading effect
    const skeletonElements = document.querySelectorAll('.skeleton');
    skeletonElements.forEach(skeleton => {
        skeleton.classList.add('shimmer');
    });
    
    // Page loading spinner
    const pageLoader = document.getElementById('page-loader');
    if (pageLoader) {
        window.addEventListener('load', () => {
            setTimeout(() => {
                pageLoader.style.opacity = '0';
                setTimeout(() => {
                    pageLoader.style.display = 'none';
                }, 300);
            }, 500);
        });
    }
}

function showPageLoader() {
    let loader = document.getElementById('page-loader');
    if (!loader) {
        loader = document.createElement('div');
        loader.id = 'page-loader';
        loader.innerHTML = `
            <div class="loader-container">
                <div class="loader-spinner"></div>
                <p>Loading...</p>
            </div>
        `;
        loader.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255,255,255,0.95);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 99999;
            transition: opacity 0.3s ease;
        `;
        document.body.appendChild(loader);
    }
    loader.style.display = 'flex';
    loader.style.opacity = '1';
}

function hidePageLoader() {
    const loader = document.getElementById('page-loader');
    if (loader) {
        loader.style.opacity = '0';
        setTimeout(() => {
            loader.style.display = 'none';
        }, 300);
    }
}

// ==================== CART ANIMATIONS ====================
function initCartAnimations() {
    // Add to cart animation
    const addToCartButtons = document.querySelectorAll('.add-to-cart-btn, .btn-add-cart');
    addToCartButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Create flying element animation
            const cartIcon = document.querySelector('.cart-icon, .cart-count-parent');
            if (cartIcon) {
                const clone = this.cloneNode(true);
                clone.style.position = 'fixed';
                clone.style.width = `${this.offsetWidth}px`;
                clone.style.height = `${this.offsetHeight}px`;
                clone.style.left = `${this.getBoundingClientRect().left}px`;
                clone.style.top = `${this.getBoundingClientRect().top}px`;
                clone.style.opacity = '0.8';
                clone.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
                clone.style.pointerEvents = 'none';
                clone.style.zIndex = '99999';
                document.body.appendChild(clone);
                
                const targetRect = cartIcon.getBoundingClientRect();
                setTimeout(() => {
                    clone.style.left = `${targetRect.left}px`;
                    clone.style.top = `${targetRect.top}px`;
                    clone.style.opacity = '0';
                    clone.style.transform = 'scale(0.5)';
                }, 10);
                
                setTimeout(() => {
                    clone.remove();
                    // Bounce cart icon
                    cartIcon.classList.add('cart-bump');
                    setTimeout(() => {
                        cartIcon.classList.remove('cart-bump');
                    }, 500);
                }, 800);
            }
            
            // Button loading state
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="spinner-sm"></span> Adding...';
            this.disabled = true;
            
            setTimeout(() => {
                this.innerHTML = originalText;
                this.disabled = false;
            }, 1000);
        });
    });
    
    // Cart item remove animation
    const removeButtons = document.querySelectorAll('.cart-item-remove, .remove-from-cart');
    removeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const cartItem = this.closest('.cart-item, .cart-row');
            if (cartItem) {
                cartItem.style.transition = 'all 0.3s ease';
                cartItem.style.opacity = '0';
                cartItem.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    cartItem.remove();
                }, 300);
            }
        });
    });
}

// ==================== FORM ANIMATIONS ====================
function initFormAnimations() {
    // Input focus effects
    const formInputs = document.querySelectorAll('.form-control, input, textarea, select');
    formInputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement?.classList.add('input-focused');
            this.style.borderColor = '#1a73e8';
            this.style.boxShadow = '0 0 0 3px rgba(26, 115, 232, 0.2)';
        });
        
        input.addEventListener('blur', function() {
            this.parentElement?.classList.remove('input-focused');
            this.style.borderColor = '';
            this.style.boxShadow = '';
        });
    });
    
    // Form submit loading state
    const forms = document.querySelectorAll('form[data-loading="true"]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="spinner-sm"></span> Processing...';
                submitBtn.disabled = true;
                
                // Restore after 5 seconds maximum (will be overwritten by actual response)
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 5000);
            }
        });
    });
    
    // Floating labels
    const floatingLabels = document.querySelectorAll('.floating-label');
    floatingLabels.forEach(label => {
        const input = label.querySelector('input, textarea');
        if (input && input.value) {
            label.classList.add('label-floating');
        }
        
        input?.addEventListener('focus', () => {
            label.classList.add('label-floating');
        });
        
        input?.addEventListener('blur', () => {
            if (!input.value) {
                label.classList.remove('label-floating');
            }
        });
    });
}

// ==================== PAGE TRANSITIONS ====================
function initPageTransitions() {
    // Smooth page transitions for internal links
    const internalLinks = document.querySelectorAll('a[href^="/"]:not([target="_blank"]):not([data-no-transition])');
    
    internalLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href === '#' || href === '' || href.startsWith('#') || href.startsWith('javascript:')) return;
            
            e.preventDefault();
            
            // Add page transition class
            document.body.classList.add('page-transition-out');
            
            setTimeout(() => {
                window.location.href = href;
            }, 300);
        });
    });
    
    // Remove transition class on page load
    document.body.classList.remove('page-transition-out');
    document.body.classList.add('page-transition-in');
    
    setTimeout(() => {
        document.body.classList.remove('page-transition-in');
    }, 500);
}

// ==================== COUNTER ANIMATIONS ====================
function initCounterAnimations() {
    const counters = document.querySelectorAll('.counter, .stat-number');
    
    if (counters.length === 0) return;
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counter = entry.target;
                const target = parseInt(counter.getAttribute('data-target') || counter.innerText);
                animateCounter(counter, target);
                observer.unobserve(counter);
            }
        });
    }, { threshold: 0.5 });
    
    counters.forEach(counter => {
        observer.observe(counter);
    });
}

function animateCounter(element, target) {
    let current = 0;
    const increment = target / 50;
    const duration = 1000;
    const stepTime = duration / 50;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.innerText = target;
            clearInterval(timer);
        } else {
            element.innerText = Math.floor(current);
        }
    }, stepTime);
}

// ==================== PULSE EFFECTS ====================
function initPulseEffects() {
    // Pulse animation for notifications
    const notificationBadge = document.querySelector('.cart-count, .notification-badge');
    if (notificationBadge && parseInt(notificationBadge.innerText) > 0) {
        notificationBadge.classList.add('pulse');
        setTimeout(() => {
            notificationBadge.classList.remove('pulse');
        }, 1000);
    }
    
    // Pulse on new content
    const newContent = document.querySelectorAll('.new-item, .just-added');
    newContent.forEach(item => {
        item.classList.add('pulse-once');
        setTimeout(() => {
            item.classList.remove('pulse-once');
        }, 1000);
    });
}

// ==================== TOAST ANIMATIONS (for backward compatibility) ====================
function showAnimatedToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `animated-toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-icon">${type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ'}</div>
        <div class="toast-message">${message}</div>
    `;
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: ${type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : '#2196f3'};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        gap: 12px;
        z-index: 10001;
        animation: slideInRight 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ==================== SCROLL TO TOP BUTTON ====================
function initScrollToTop() {
    let scrollBtn = document.getElementById('scroll-to-top');
    
    if (!scrollBtn) {
        scrollBtn = document.createElement('button');
        scrollBtn.id = 'scroll-to-top';
        scrollBtn.innerHTML = '↑';
        scrollBtn.style.cssText = `
            position: fixed;
            bottom: 80px;
            right: 20px;
            width: 45px;
            height: 45px;
            background: #1a73e8;
            color: white;
            border: none;
            border-radius: 50%;
            cursor: pointer;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
            z-index: 999;
            font-size: 24px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        document.body.appendChild(scrollBtn);
    }
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            scrollBtn.style.opacity = '1';
            scrollBtn.style.visibility = 'visible';
        } else {
            scrollBtn.style.opacity = '0';
            scrollBtn.style.visibility = 'hidden';
        }
    });
    
    scrollBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// ==================== STAGGERED CHILDREN ANIMATION ====================
function initStaggeredChildren() {
    const containers = document.querySelectorAll('.stagger-children');
    
    containers.forEach(container => {
        const children = container.children;
        Array.from(children).forEach((child, index) => {
            child.style.animationDelay = `${index * 0.05}s`;
        });
    });
}

// ==================== FULLSCREEN MODAL ANIMATIONS ====================
function openFullscreenModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    modal.style.display = 'block';
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    // Animate content
    const content = modal.querySelector('.fullscreen-modal-content');
    if (content) {
        content.style.animation = 'slideInRight 0.3s ease';
    }
}

function closeFullscreenModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    const content = modal.querySelector('.fullscreen-modal-content');
    if (content) {
        content.style.animation = 'slideOutRight 0.3s ease';
    }
    
    setTimeout(() => {
        modal.classList.remove('active');
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }, 300);
}

// ==================== ADD DYNAMIC CSS FOR ANIMATIONS ====================
const animationStyles = document.createElement('style');
animationStyles.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .page-transition-out {
        opacity: 0;
        transform: translateY(20px);
        transition: opacity 0.3s ease, transform 0.3s ease;
    }
    
    .page-transition-in {
        animation: fadeInUp 0.5s ease;
    }
    
    .ripple-effect {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.5);
        transform: scale(0);
        animation: ripple-animation 0.6s linear;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .pulse-once {
        animation: pulse 0.5s ease-in-out;
    }
    
    .cart-bump {
        animation: cartBump 0.3s ease-in-out;
    }
    
    @keyframes cartBump {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.2); }
    }
    
    .hover-grow {
        transform: scale(1.02);
        transition: transform 0.3s ease;
    }
    
    .spinner-sm {
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2px solid rgba(255,255,255,0.3);
        border-top-color: white;
        border-radius: 50%;
        animation: spin 0.6s linear infinite;
        vertical-align: middle;
        margin-right: 8px;
    }
    
    .loader-spinner {
        width: 50px;
        height: 50px;
        border: 4px solid #f0f0f0;
        border-top-color: #1a73e8;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        margin: 0 auto;
    }
    
    .loader-container {
        text-align: center;
    }
    
    .loader-container p {
        margin-top: 15px;
        color: #666;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    /* Reduced motion */
    @media (prefers-reduced-motion: reduce) {
        *,
        *::before,
        *::after {
            animation-duration: 0.01ms !important;
            transition-duration: 0.01ms !important;
        }
        
        .page-transition-out,
        .page-transition-in {
            transition: none;
            animation: none;
        }
    }
`;

document.head.appendChild(animationStyles);

// ==================== INITIALIZE ON LOAD ====================
window.addEventListener('load', function() {
    initScrollToTop();
    initStaggeredChildren();
});

// ==================== EXPORTS ====================
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        showPageLoader,
        hidePageLoader,
        showAnimatedToast,
        openFullscreenModal,
        closeFullscreenModal,
        animateCounter
    };
}

// Make functions globally available
window.showPageLoader = showPageLoader;
window.hidePageLoader = hidePageLoader;
window.showAnimatedToast = showAnimatedToast;
window.openFullscreenModal = openFullscreenModal;
window.closeFullscreenModal = closeFullscreenModal;