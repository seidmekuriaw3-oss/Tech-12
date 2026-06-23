// ==================== ETHIOSADAT - MAIN JAVASCRIPT ====================
// Professional Main JavaScript for ኢትዮሳዳት ፈርኒቸር ወድ ሰሚራ
// Part 1 of 2: Core Functions, UI Components, Form Validation, Loading States

// ==================== App Initialization ====================
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Ethiosadat App Loaded');
    
    // Initialize all components
    initFlashMessages();
    initMobileMenu();
    initBackToTop();
    initLazyLoading();
    initFormValidation();
    initNetworkDetection();
    initDarkModeDetection();
    initKeyboardShortcuts();
    initSmoothScroll();
    initScrollSpy();
    initDropdowns();
    initTabs();
    initAccordions();
    
    // Defer non-critical initialization
    if ('requestIdleCallback' in window) {
        requestIdleCallback(() => {
            initAnalytics();
            initPreloadNextPage();
        });
    } else {
        setTimeout(() => {
            initAnalytics();
            initPreloadNextPage();
        }, 100);
    }
});

// ==================== Flash Messages ====================
function initFlashMessages() {
    const flashes = document.querySelectorAll('.flash, .alert, .flash-message');
    
    flashes.forEach(flash => {
        // Add close button if not exists
        if (!flash.querySelector('.flash-close, .alert-close')) {
            const closeBtn = document.createElement('button');
            closeBtn.innerHTML = '&times;';
            closeBtn.className = 'flash-close';
            closeBtn.setAttribute('aria-label', 'Dismiss');
            closeBtn.style.cssText = `
                background: none;
                border: none;
                color: inherit;
                font-size: 20px;
                cursor: pointer;
                margin-left: auto;
                opacity: 0.7;
                padding: 0 8px;
            `;
            closeBtn.addEventListener('click', () => dismissFlash(flash));
            flash.appendChild(closeBtn);
        }
        
        // Auto dismiss after 5 seconds
        const dismissTimeout = setTimeout(() => dismissFlash(flash), 5000);
        flash.dataset.dismissTimeout = dismissTimeout;
        
        // Pause auto-dismiss on hover
        flash.addEventListener('mouseenter', () => {
            if (flash.dataset.dismissTimeout) {
                clearTimeout(parseInt(flash.dataset.dismissTimeout));
            }
        });
        flash.addEventListener('mouseleave', () => {
            const newTimeout = setTimeout(() => dismissFlash(flash), 3000);
            flash.dataset.dismissTimeout = newTimeout;
        });
    });
}

function dismissFlash(flash) {
    if (!flash || !flash.parentNode) return;
    
    flash.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    flash.style.opacity = '0';
    flash.style.transform = 'translateX(100%)';
    
    setTimeout(() => {
        if (flash && flash.parentNode) {
            flash.remove();
        }
    }, 300);
}

// ==================== Mobile Menu & Sidebar ====================
function initMobileMenu() {
    const menuToggle = document.querySelector('.menu-toggle, .mobile-menu-toggle');
    const sidebar = document.querySelector('.admin-sidebar, .mobile-sidebar, .sidebar');
    const closeBtn = document.querySelector('.sidebar-close, .menu-close');
    
    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', (e) => {
            e.preventDefault();
            sidebar.classList.toggle('open');
            toggleOverlay(sidebar.classList.contains('open'));
        });
    }
    
    // Close button
    if (closeBtn && sidebar) {
        closeBtn.addEventListener('click', () => {
            sidebar.classList.remove('open');
            toggleOverlay(false);
        });
    }
    
    // Close sidebar when clicking overlay
    const sidebarOverlay = document.querySelector('.sidebar-overlay');
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', () => {
            if (sidebar) sidebar.classList.remove('open');
            toggleOverlay(false);
        });
    }
    
    // Close on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && sidebar && sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
            toggleOverlay(false);
        }
    });
    
    // Handle window resize - close sidebar on desktop
    window.addEventListener('resize', () => {
        if (window.innerWidth > 768 && sidebar && sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
            toggleOverlay(false);
        }
    });
}

function toggleOverlay(show) {
    let overlay = document.querySelector('.sidebar-overlay');
    
    if (show) {
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'sidebar-overlay';
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                backdrop-filter: blur(2px);
                z-index: 998;
            `;
            document.body.appendChild(overlay);
        }
        document.body.style.overflow = 'hidden';
    } else {
        if (overlay && overlay.parentNode) {
            overlay.remove();
        }
        document.body.style.overflow = '';
    }
}

// ==================== Back to Top Button ====================
function initBackToTop() {
    let backToTopBtn = document.querySelector('.back-to-top');
    
    if (!backToTopBtn) {
        backToTopBtn = document.createElement('button');
        backToTopBtn.innerHTML = '↑';
        backToTopBtn.className = 'back-to-top';
        backToTopBtn.setAttribute('aria-label', 'Back to top');
        backToTopBtn.style.cssText = `
            position: fixed;
            bottom: 80px;
            right: 20px;
            width: 45px;
            height: 45px;
            border-radius: 50%;
            background: #1a73e8;
            color: white;
            border: none;
            cursor: pointer;
            display: none;
            z-index: 999;
            font-size: 24px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
            align-items: center;
            justify-content: center;
        `;
        document.body.appendChild(backToTopBtn);
    }
    
    // Hover effects
    backToTopBtn.addEventListener('mouseenter', () => {
        backToTopBtn.style.transform = 'scale(1.1)';
        backToTopBtn.style.background = '#0d47a1';
    });
    backToTopBtn.addEventListener('mouseleave', () => {
        backToTopBtn.style.transform = 'scale(1)';
        backToTopBtn.style.background = '#1a73e8';
    });
    
    // Scroll handler
    let ticking = false;
    window.addEventListener('scroll', () => {
        if (!ticking) {
            requestAnimationFrame(() => {
                if (window.scrollY > 300) {
                    backToTopBtn.style.display = 'flex';
                    backToTopBtn.style.opacity = '1';
                } else {
                    backToTopBtn.style.opacity = '0';
                    setTimeout(() => {
                        if (window.scrollY <= 300) {
                            backToTopBtn.style.display = 'none';
                        }
                    }, 300);
                }
                ticking = false;
            });
            ticking = true;
        }
    });
    
    backToTopBtn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

// ==================== Lazy Loading Images ====================
function initLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    const src = img.dataset.src;
                    const srcset = img.dataset.srcset;
                    
                    if (src) {
                        img.src = src;
                        img.removeAttribute('data-src');
                    }
                    if (srcset) {
                        img.srcset = srcset;
                        img.removeAttribute('data-srcset');
                    }
                    
                    img.classList.add('loaded');
                    observer.unobserve(img);
                }
            });
        }, {
            rootMargin: '50px 0px',
            threshold: 0.01
        });
        
        const images = document.querySelectorAll('img[data-src], img[data-lazy], img[data-srcset]');
        images.forEach(img => imageObserver.observe(img));
    } else {
        // Fallback for older browsers
        const images = document.querySelectorAll('img[data-src]');
        images.forEach(img => {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
        });
    }
    
    // Lazy load background images
    const bgElements = document.querySelectorAll('[data-bg], [data-background]');
    bgElements.forEach(el => {
        const bg = el.dataset.bg || el.dataset.background;
        if (bg) {
            el.style.backgroundImage = `url(${bg})`;
            el.removeAttribute('data-bg');
            el.removeAttribute('data-background');
        }
    });
    
    // Lazy load iframes
    const iframes = document.querySelectorAll('iframe[data-src]');
    iframes.forEach(iframe => {
        iframe.src = iframe.dataset.src;
        iframe.removeAttribute('data-src');
    });
}

// ==================== Form Validation ====================
function initFormValidation() {
    const forms = document.querySelectorAll('form[data-validate], form.validate, form.needs-validation');
    
    forms.forEach(form => {
        // Real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', () => validateField(input));
            input.addEventListener('input', () => {
                if (input.classList.contains('error')) {
                    validateField(input);
                }
            });
        });
        
        form.addEventListener('submit', (e) => {
            let isValid = true;
            const requiredFields = form.querySelectorAll('[required]');
            
            requiredFields.forEach(field => {
                if (!validateField(field)) {
                    isValid = false;
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                if (window.showToast) {
                    window.showToast('Please fill in all required fields correctly', 'error');
                }
                
                // Scroll to first error
                const firstError = form.querySelector('.error');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstError.focus();
                }
            }
        });
    });
}

function validateField(field) {
    const value = field.value ? field.value.trim() : '';
    let isValid = true;
    let errorMessage = '';
    
    // Required validation
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        errorMessage = 'This field is required';
    }
    
    // Email validation
    if (field.type === 'email' && value && !isValidEmail(value)) {
        isValid = false;
        errorMessage = 'Please enter a valid email address';
    }
    
    // Phone validation
    if (field.type === 'tel' && value && !isValidPhone(value)) {
        isValid = false;
        errorMessage = 'Please enter a valid phone number';
    }
    
    // Number validation
    if (field.type === 'number' && value && isNaN(parseFloat(value))) {
        isValid = false;
        errorMessage = 'Please enter a valid number';
    }
    
    // Min length validation
    const minLength = field.getAttribute('minlength');
    if (minLength && value && value.length < parseInt(minLength, 10)) {
        isValid = false;
        errorMessage = `Minimum ${minLength} characters required`;
    }
    
    // Max length validation
    const maxLength = field.getAttribute('maxlength');
    if (maxLength && value && value.length > parseInt(maxLength, 10)) {
        isValid = false;
        errorMessage = `Maximum ${maxLength} characters allowed`;
    }
    
    // Pattern validation
    const pattern = field.getAttribute('pattern');
    if (pattern && value && !new RegExp(pattern).test(value)) {
        isValid = false;
        errorMessage = field.getAttribute('title') || 'Invalid format';
    }
    
    // Update UI
    if (!isValid) {
        field.classList.add('error');
        showFieldError(field, errorMessage);
    } else {
        field.classList.remove('error');
        clearFieldError(field);
    }
    
    return isValid;
}

function isValidEmail(email) {
    const re = /^[^\s@]+@([^\s@.,]+\.)+[^\s@.,]{2,}$/;
    return re.test(email);
}

function isValidPhone(phone) {
    // Ethiopian phone number format
    const cleaned = phone.replace(/[\s\-\(\)\+]/g, '');
    const re = /^(09|07|2519)[0-9]{8}$/;
    return re.test(cleaned);
}

function showFieldError(field, message) {
    let error = field.parentNode.querySelector('.field-error, .form-error');
    if (!error) {
        error = document.createElement('small');
        error.className = 'field-error form-error';
        error.style.cssText = `
            display: block;
            color: #f44336;
            font-size: 12px;
            margin-top: 4px;
        `;
        field.parentNode.appendChild(error);
    }
    error.textContent = message;
}

function clearFieldError(field) {
    const error = field.parentNode.querySelector('.field-error, .form-error');
    if (error) error.remove();
}

// ==================== Toast Notification ====================
function showToast(message, type = 'success', duration = 3000) {
    // Remove existing toasts if too many
    const existingToasts = document.querySelectorAll('.toast-notification');
    if (existingToasts.length > 5) {
        existingToasts[0].remove();
    }
    
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.setAttribute('role', 'alert');
    
    const icons = {
        success: '✓',
        error: '✗',
        warning: '⚠',
        info: 'ℹ'
    };
    
    toast.innerHTML = `
        <span class="toast-icon" style="font-size: 18px;">${icons[type] || icons.info}</span>
        <span class="toast-message" style="flex: 1;">${escapeHtml(message)}</span>
        <button class="toast-close" aria-label="Close">&times;</button>
    `;
    
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        min-width: 280px;
        max-width: 400px;
        padding: 12px 16px;
        background: ${type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : type === 'warning' ? '#ff9800' : '#2196f3'};
        color: white;
        border-radius: 8px;
        z-index: 10000;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        animation: slideInRight 0.3s ease;
        font-size: 14px;
        cursor: pointer;
    `;
    
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.style.cssText = `
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        font-size: 18px;
        margin-left: auto;
        opacity: 0.8;
        padding: 0 4px;
    `;
    closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dismissToast(toast);
    });
    
    // Click anywhere to dismiss
    toast.addEventListener('click', () => dismissToast(toast));
    
    document.body.appendChild(toast);
    
    const timeout = setTimeout(() => dismissToast(toast), duration);
    toast.dataset.timeout = timeout;
}

function dismissToast(toast) {
    if (toast.dataset.timeout) {
        clearTimeout(parseInt(toast.dataset.timeout));
    }
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => {
        if (toast && toast.parentNode) {
            toast.remove();
        }
    }, 300);
}

// ==================== Loading States ====================
let loadingOverlay = null;
let loadingTimeout = null;

function showLoading(message = 'Loading...') {
    if (loadingOverlay) {
        hideLoading();
    }
    
    // Clear any pending auto-hide
    if (loadingTimeout) {
        clearTimeout(loadingTimeout);
    }
    
    loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'loading-overlay';
    loadingOverlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(2px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10001;
        flex-direction: column;
        gap: 16px;
    `;
    
    loadingOverlay.innerHTML = `
        <div class="loading-spinner"></div>
        <div class="loading-message" style="color: white; font-size: 14px;">${escapeHtml(message)}</div>
    `;
    
    document.body.appendChild(loadingOverlay);
    
    // Add spinner style if not exists
    if (!document.querySelector('#loading-spinner-style')) {
        const style = document.createElement('style');
        style.id = 'loading-spinner-style';
        style.textContent = `
            .loading-spinner {
                width: 48px;
                height: 48px;
                border: 4px solid rgba(255, 255, 255, 0.3);
                border-top-color: white;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            @media (prefers-reduced-motion: reduce) {
                .loading-spinner {
                    animation: none;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

function hideLoading() {
    if (loadingOverlay) {
        loadingOverlay.style.opacity = '0';
        setTimeout(() => {
            if (loadingOverlay && loadingOverlay.parentNode) {
                loadingOverlay.remove();
                loadingOverlay = null;
            }
        }, 300);
    }
}

// Auto-hide loading after 30 seconds (safety)
function showLoadingWithTimeout(message = 'Loading...', timeoutMs = 30000) {
    showLoading(message);
    if (loadingTimeout) clearTimeout(loadingTimeout);
    loadingTimeout = setTimeout(() => {
        if (loadingOverlay) {
            hideLoading();
            if (window.showToast) {
                window.showToast('Loading timed out. Please try again.', 'warning');
            }
        }
    }, timeoutMs);
}

// ==================== Modal Dialog ====================
function showModal(title, content, onConfirm = null, options = {}) {
    const modal = document.createElement('div');
    modal.className = 'custom-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(2px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10002;
    `;
    
    const showCancel = options.showCancel !== false;
    const confirmText = options.confirmText || 'Confirm';
    const cancelText = options.cancelText || 'Cancel';
    const isDestructive = options.isDestructive || false;
    
    modal.innerHTML = `
        <div class="modal-content" style="
            background: var(--modal-bg, white);
            border-radius: 16px;
            max-width: 500px;
            width: 90%;
            padding: 24px;
            animation: fadeInUp 0.3s ease;
            box-shadow: 0 20px 35px rgba(0, 0, 0, 0.2);
        ">
            <h3 style="margin: 0 0 12px 0; color: var(--modal-text, #333);">${escapeHtml(title)}</h3>
            <div class="modal-body" style="margin-bottom: 24px; line-height: 1.5;">${content}</div>
            <div style="display: flex; gap: 12px; justify-content: flex-end;">
                ${showCancel ? `<button class="btn btn-outline modal-cancel" style="padding: 8px 20px;">${escapeHtml(cancelText)}</button>` : ''}
                <button class="btn ${isDestructive ? 'btn-danger' : 'btn-primary'} modal-confirm" style="padding: 8px 20px;">${escapeHtml(confirmText)}</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Apply dark mode
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        const modalContent = modal.querySelector('.modal-content');
        if (modalContent) {
            modalContent.style.setProperty('--modal-bg', '#1a1a2e');
            modalContent.style.setProperty('--modal-text', '#eeeeee');
        }
    }
    
    const cancelBtn = modal.querySelector('.modal-cancel');
    const confirmBtn = modal.querySelector('.modal-confirm');
    
    const closeModal = () => {
        modal.style.opacity = '0';
        setTimeout(() => {
            if (modal && modal.parentNode) modal.remove();
        }, 300);
        document.removeEventListener('keydown', handleEscape);
    };
    
    if (cancelBtn) {
        cancelBtn.addEventListener('click', closeModal);
    }
    
    confirmBtn.addEventListener('click', () => {
        if (onConfirm) onConfirm();
        closeModal();
    });
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
    
    const handleEscape = (e) => {
        if (e.key === 'Escape') {
            closeModal();
        }
    };
    document.addEventListener('keydown', handleEscape);
    
    // Focus confirm button
    confirmBtn.focus();
    
    return modal;
}

// ==================== Network Detection ====================
function initNetworkDetection() {
    let wasOffline = false;
    
    function updateNetworkStatus() {
        const isOnline = navigator.onLine;
        
        if (!isOnline && !wasOffline) {
            if (window.showToast) {
                window.showToast('You are offline. Please check your internet connection.', 'warning', 5000);
            }
            document.body.classList.add('offline');
            wasOffline = true;
        } else if (isOnline && wasOffline) {
            document.body.classList.remove('offline');
            if (window.showToast) {
                window.showToast('Back online!', 'success');
            }
            wasOffline = false;
        }
    }
    
    window.addEventListener('online', updateNetworkStatus);
    window.addEventListener('offline', updateNetworkStatus);
    
    updateNetworkStatus();
}

// ==================== Dark Mode Detection ====================
function initDarkModeDetection() {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
    
    function updateDarkMode(e) {
        if (e.matches) {
            document.body.classList.add('dark-mode');
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.body.classList.remove('dark-mode');
            document.documentElement.setAttribute('data-theme', 'light');
        }
    }
    
    prefersDark.addEventListener('change', updateDarkMode);
    updateDarkMode(prefersDark);
}

// ==================== Keyboard Shortcuts ====================
function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + / for search focus
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            const searchInput = document.querySelector('.search-box input, #search-input, [type="search"]');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
        
        // ESC to close modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.custom-modal, .modal, .fullscreen-modal.active');
            modals.forEach(modal => {
                if (modal.remove) modal.remove();
            });
            const overlays = document.querySelectorAll('.sidebar-overlay');
            overlays.forEach(overlay => {
                if (overlay.remove) overlay.remove();
            });
        }
        
        // Ctrl/Cmd + K for admin search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const adminSearch = document.querySelector('#admin-search, .admin-search-input');
            if (adminSearch) {
                adminSearch.focus();
                adminSearch.select();
            }
        }
        
        // Ctrl/Cmd + S for save
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            const saveBtn = document.querySelector('.btn-save, button[type="submit"], .save-btn');
            if (saveBtn) saveBtn.click();
        }
    });
}

// ==================== Smooth Scroll ====================
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]:not([href="#"]), .smooth-scroll').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId && targetId !== '#' && targetId !== '#0') {
                const target = document.querySelector(targetId);
                if (target) {
                    e.preventDefault();
                    const offset = this.dataset.offset ? parseInt(this.dataset.offset, 10) : 0;
                    const targetPosition = target.getBoundingClientRect().top + window.scrollY - offset;
                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });
                }
            }
        });
    });
}

// ==================== Scroll Spy ====================
function initScrollSpy() {
    const sections = document.querySelectorAll('section[id], div[id]');
    const navLinks = document.querySelectorAll('.scroll-spy-link, .nav-link-scroll');
    
    if (sections.length === 0 || navLinks.length === 0) return;
    
    const observerOptions = {
        threshold: 0.3,
        rootMargin: '0px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const id = entry.target.getAttribute('id');
                navLinks.forEach(link => {
                    link.classList.remove('active');
                    const href = link.getAttribute('href');
                    if (href === `#${id}`) {
                        link.classList.add('active');
                    }
                });
            }
        });
    }, observerOptions);
    
    sections.forEach(section => observer.observe(section));
}

// ==================== Dropdowns ====================
function initDropdowns() {
    const dropdowns = document.querySelectorAll('.dropdown, .dropdown-container');
    
    dropdowns.forEach(dropdown => {
        const trigger = dropdown.querySelector('.dropdown-trigger, .dropdown-toggle');
        const menu = dropdown.querySelector('.dropdown-menu, .dropdown-content');
        
        if (trigger && menu) {
            trigger.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                // Close other dropdowns
                dropdowns.forEach(d => {
                    if (d !== dropdown) {
                        const m = d.querySelector('.dropdown-menu, .dropdown-content');
                        if (m) m.classList.remove('show');
                    }
                });
                
                menu.classList.toggle('show');
            });
        }
    });
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', () => {
        const allMenus = document.querySelectorAll('.dropdown-menu.show, .dropdown-content.show');
        allMenus.forEach(menu => menu.classList.remove('show'));
    });
}

// ==================== Tabs ====================
function initTabs() {
    const tabContainers = document.querySelectorAll('.tabs-container, [data-tabs]');
    
    tabContainers.forEach(container => {
        const tabs = container.querySelectorAll('.tab, [data-tab]');
        const panes = container.querySelectorAll('.tab-pane, [data-tab-content]');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const targetId = tab.dataset.tab || tab.getAttribute('href')?.substring(1);
                
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                panes.forEach(pane => {
                    if (pane.id === targetId || pane.dataset.tabContent === targetId) {
                        pane.classList.add('active');
                        pane.style.display = 'block';
                    } else {
                        pane.classList.remove('active');
                        pane.style.display = 'none';
                    }
                });
            });
        });
        
        // Show first tab by default
        if (tabs.length > 0 && !container.querySelector('.tab.active')) {
            tabs[0].click();
        }
    });
}

// ==================== Accordions ====================
function initAccordions() {
    const accordions = document.querySelectorAll('.accordion, [data-accordion]');
    
    accordions.forEach(accordion => {
        const headers = accordion.querySelectorAll('.accordion-header, [data-accordion-header]');
        
        headers.forEach(header => {
            header.addEventListener('click', () => {
                const content = header.nextElementSibling;
                const isOpen = content && content.classList.contains('open');
                
                // Close others if accordion is exclusive
                if (accordion.dataset.exclusive !== 'false') {
                    accordion.querySelectorAll('.accordion-content').forEach(c => {
                        c.classList.remove('open');
                        c.style.maxHeight = null;
                    });
                }
                
                if (content) {
                    if (!isOpen) {
                        content.classList.add('open');
                        content.style.maxHeight = content.scrollHeight + 'px';
                    } else {
                        content.classList.remove('open');
                        content.style.maxHeight = null;
                    }
                }
            });
        });
    });
}

// ==================== Helper Functions ====================
function formatPrice(price) {
    if (price === undefined || price === null) return '0 ETB';
    const num = parseFloat(price);
    if (isNaN(num)) return '0 ETB';
    return num.toLocaleString('en-US') + ' ETB';
}

function formatDate(dateString, format = 'short') {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'Invalid date';
    
    if (format === 'short') {
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function timeAgo(dateString) {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'Invalid date';
    
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 10) return 'Just now';
    if (seconds < 60) return `${seconds} seconds ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days} day${days > 1 ? 's' : ''} ago`;
    const weeks = Math.floor(days / 7);
    if (weeks < 4) return `${weeks} week${weeks > 1 ? 's' : ''} ago`;
    const months = Math.floor(days / 30);
    if (months < 12) return `${months} month${months > 1 ? 's' : ''} ago`;
    const years = Math.floor(days / 365);
    return `${years} year${years > 1 ? 's' : ''} ago`;
}

function copyToClipboard(text) {
    if (!text) return;
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            if (window.showToast) window.showToast('Copied to clipboard!', 'success');
        }).catch(() => {
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

function fallbackCopyToClipboard(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    if (window.showToast) window.showToast('Copied to clipboard!', 'success');
}

function debounce(func, wait) {
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

function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

function setUrlParameter(name, value, replaceState = true) {
    const url = new URL(window.location.href);
    if (value !== null && value !== undefined && value !== '') {
        url.searchParams.set(name, value);
    } else {
        url.searchParams.delete(name);
    }
    
    if (replaceState) {
        window.history.replaceState({}, '', url);
    } else {
        window.history.pushState({}, '', url);
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==================== ETHIOSADAT - MAIN JAVASCRIPT ====================
// Professional Main JavaScript for ኢትዮሳዳት ፈርኒቸር ወድ ሰሚራ
// Part 2 of 2: Analytics, Preload, PWA, CSS Animations, Service Worker, Final Exports

// ==================== Analytics (Basic) ====================
function initAnalytics() {
    // Track page view
    if (typeof gtag !== 'undefined') {
        gtag('config', 'GA_MEASUREMENT_ID', {
            page_path: window.location.pathname,
            send_page_view: true
        });
    }
    
    // Track outbound links
    const outboundLinks = document.querySelectorAll('a[href^="http"]');
    outboundLinks.forEach(link => {
        if (!link.href.includes(window.location.hostname)) {
            link.addEventListener('click', (e) => {
                const href = link.getAttribute('href');
                console.log('Outbound link clicked:', href);
                
                // You can send to analytics here
                if (typeof gtag !== 'undefined') {
                    gtag('event', 'click', {
                        event_category: 'outbound',
                        event_label: href,
                        transport_type: 'beacon'
                    });
                }
                
                // Track in localStorage for offline analytics
                trackOfflineEvent('outbound_click', { url: href });
            });
        }
    });
    
    // Track button clicks
    const trackedButtons = document.querySelectorAll('[data-track]');
    trackedButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const eventName = btn.dataset.track;
            const eventValue = btn.dataset.trackValue || '';
            
            if (typeof gtag !== 'undefined') {
                gtag('event', eventName, {
                    event_category: 'button_click',
                    event_label: eventValue
                });
            }
            
            trackOfflineEvent(eventName, { label: eventValue });
        });
    });
    
    // Track product views
    const productCards = document.querySelectorAll('.product-card');
    productCards.forEach(card => {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const productId = card.dataset.id;
                    const productName = card.querySelector('.product-title')?.textContent;
                    
                    if (typeof gtag !== 'undefined') {
                        gtag('event', 'view_item', {
                            items: [{ id: productId, name: productName }]
                        });
                    }
                    
                    observer.unobserve(card);
                }
            });
        }, { threshold: 0.5 });
        observer.observe(card);
    });
}

// Offline analytics storage
let offlineEvents = [];

function trackOfflineEvent(eventName, data = {}) {
    if (!navigator.onLine) {
        offlineEvents.push({
            event: eventName,
            data: data,
            timestamp: Date.now()
        });
        
        // Store in localStorage for persistence
        try {
            localStorage.setItem('offline_analytics', JSON.stringify(offlineEvents));
        } catch (e) {
            console.error('Failed to store offline analytics:', e);
        }
    } else if (offlineEvents.length > 0) {
        // Sync offline events when back online
        syncOfflineEvents();
    }
}

function syncOfflineEvents() {
    if (offlineEvents.length === 0) return;
    
    const events = [...offlineEvents];
    offlineEvents = [];
    
    events.forEach(event => {
        if (typeof gtag !== 'undefined') {
            gtag('event', event.event, {
                event_category: 'offline',
                event_label: JSON.stringify(event.data),
                timestamp: event.timestamp
            });
        }
    });
    
    // Clear localStorage
    try {
        localStorage.removeItem('offline_analytics');
    } catch (e) {
        console.error('Failed to clear offline analytics:', e);
    }
}

// Listen for online event to sync
window.addEventListener('online', syncOfflineEvents);

// ==================== Preload Next Page ====================
function initPreloadNextPage() {
    // Prefetch common links on hover (desktop only)
    if (window.matchMedia('(hover: hover)').matches) {
        const links = document.querySelectorAll('a[href^="/"]:not([href*="logout"]):not([href*="delete"])');
        
        let hoverTimeout = null;
        
        links.forEach(link => {
            link.addEventListener('mouseenter', () => {
                const href = link.getAttribute('href');
                if (href && !href.startsWith('http') && href !== window.location.pathname && href !== '/') {
                    // Delay prefetch to avoid unnecessary requests on fast hovers
                    hoverTimeout = setTimeout(() => {
                        const preloadLink = document.createElement('link');
                        preloadLink.rel = 'prefetch';
                        preloadLink.href = href;
                        preloadLink.as = 'document';
                        document.head.appendChild(preloadLink);
                        
                        // Remove after 10 seconds
                        setTimeout(() => {
                            if (preloadLink && preloadLink.parentNode) {
                                preloadLink.remove();
                            }
                        }, 10000);
                    }, 100);
                }
            });
            
            link.addEventListener('mouseleave', () => {
                if (hoverTimeout) {
                    clearTimeout(hoverTimeout);
                    hoverTimeout = null;
                }
            });
        });
    }
    
    // Prefetch critical pages on page load
    const criticalPages = ['/products', '/about', '/branches'];
    criticalPages.forEach(page => {
        if (page !== window.location.pathname) {
            const preloadLink = document.createElement('link');
            preloadLink.rel = 'prefetch';
            preloadLink.href = page;
            preloadLink.as = 'document';
            document.head.appendChild(preloadLink);
        }
    });
    
    // Preload WebP images if supported
    if (supportsWebP()) {
        const images = document.querySelectorAll('img[data-webp]');
        images.forEach(img => {
            const webpSrc = img.dataset.webp;
            if (webpSrc) {
                const preloadLink = document.createElement('link');
                preloadLink.rel = 'preload';
                preloadLink.as = 'image';
                preloadLink.href = webpSrc;
                document.head.appendChild(preloadLink);
            }
        });
    }
}

function supportsWebP() {
    const canvas = document.createElement('canvas');
    if (canvas.getContext && canvas.getContext('2d')) {
        return canvas.toDataURL('image/webp').indexOf('image/webp') === 5;
    }
    return false;
}

// ==================== Service Worker Cleanup ====================
function initServiceWorker() {
    // Service worker disabled — unregister any existing registrations
    // to prevent old SWs from intercepting fetch requests.
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistrations().then(regs => {
            regs.forEach(r => r.unregister());
        });
    }
}

// Request notification permission
function requestNotificationPermission() {
    if ('Notification' in window) {
        if (Notification.permission === 'default') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    console.log('Notification permission granted');
                    // Register for push notifications
                    registerPushNotifications();
                }
            });
        }
    }
}

function registerPushNotifications() {
    if ('serviceWorker' in navigator && 'PushManager' in window) {
        navigator.serviceWorker.ready.then(registration => {
            registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: urlBase64ToUint8Array('YOUR_VAPID_PUBLIC_KEY')
            }).then(subscription => {
                console.log('Push subscription successful:', subscription);
                // Send subscription to server
                fetch('/api/notifications/subscribe', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(subscription)
                });
            }).catch(error => {
                console.error('Push subscription failed:', error);
            });
        });
    }
}

function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

// ==================== Performance Monitoring ====================
function initPerformanceMonitoring() {
    if ('performance' in window && 'getEntriesByType' in performance) {
        // Monitor page load time
        const paintEntries = performance.getEntriesByType('paint');
        paintEntries.forEach(entry => {
            if (entry.name === 'first-contentful-paint') {
                console.log('FCP:', entry.startTime, 'ms');
                // Send to analytics
                if (typeof gtag !== 'undefined') {
                    gtag('event', 'timing_complete', {
                        name: 'first_contentful_paint',
                        value: Math.round(entry.startTime)
                    });
                }
            }
        });
        
        // Monitor LCP (Largest Contentful Paint)
        const lcpObserver = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const lastEntry = entries[entries.length - 1];
            console.log('LCP:', lastEntry.startTime, 'ms');
            if (typeof gtag !== 'undefined') {
                gtag('event', 'timing_complete', {
                    name: 'largest_contentful_paint',
                    value: Math.round(lastEntry.startTime)
                });
            }
        });
        lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });
    }
}

// ==================== CSS Animations ====================
(function addAnimationStyles() {
    if (document.querySelector('#main-animation-styles')) return;
    
    const animationStyles = document.createElement('style');
    animationStyles.id = 'main-animation-styles';
    animationStyles.textContent = `
        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(100%);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes slideOutRight {
            from {
                opacity: 1;
                transform: translateX(0);
            }
            to {
                opacity: 0;
                transform: translateX(100%);
            }
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
            }
            to {
                opacity: 1;
            }
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        @keyframes shimmer {
            0% {
                background-position: -200% 0;
            }
            100% {
                background-position: 200% 0;
            }
        }
        
        /* Skeleton loading */
        .skeleton {
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
        }
        
        /* Dark mode skeleton */
        @media (prefers-color-scheme: dark) {
            .skeleton {
                background: linear-gradient(90deg, #2a2a3e 25%, #1a1a2e 50%, #2a2a3e 75%);
            }
        }
        
        /* Reduced Motion Preference */
        @media (prefers-reduced-motion: reduce) {
            *,
            *::before,
            *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
                scroll-behavior: auto !important;
            }
            
            .skeleton {
                animation: none;
            }
        }
        
        /* Toast animations */
        .toast-notification {
            animation: slideInRight 0.3s ease forwards;
        }
        
        /* Modal animations */
        .custom-modal {
            animation: fadeIn 0.2s ease;
        }
        
        /* Back to top button hover */
        .back-to-top {
            transition: transform 0.2s ease, background 0.2s ease;
        }
        
        /* Offline indicator */
        body.offline::before {
            content: '⚠️ You are offline. Some features may be unavailable.';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: #ff9800;
            color: #fff;
            text-align: center;
            padding: 8px;
            font-size: 12px;
            z-index: 10000;
            font-weight: 500;
        }
        
        body.offline {
            padding-top: 40px;
        }
        
        /* Smooth transitions */
        .fade-transition {
            transition: opacity 0.3s ease;
        }
        
        .slide-transition {
            transition: transform 0.3s ease;
        }
    `;
    document.head.appendChild(animationStyles);
})();

// ==================== Online/Offline Indicator ====================
function initOfflineIndicator() {
    const isOnline = navigator.onLine;
    if (!isOnline) {
        const indicator = document.createElement('div');
        indicator.className = 'offline-indicator';
        indicator.textContent = '📡 You are offline. Please check your connection.';
        indicator.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: #f44336;
            color: white;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 12px;
            z-index: 9999;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            animation: fadeInUp 0.3s ease;
        `;
        document.body.appendChild(indicator);
        
        setTimeout(() => {
            if (indicator && indicator.parentNode) {
                indicator.style.opacity = '0';
                setTimeout(() => indicator.remove(), 300);
            }
        }, 5000);
    }
}

// ==================== Register Custom Events ====================
function initCustomEvents() {
    // Cart updated event
    window.addEventListener('cartUpdated', () => {
        updateCartBadges();
    });
    
    // Products filtered event
    document.addEventListener('filtersApplied', (e) => {
        console.log(`Products filtered: ${e.detail.count} items shown`);
    });
    
    // Page loaded event
    window.dispatchEvent(new CustomEvent('appLoaded', { 
        detail: { timestamp: Date.now() }
    }));
}

function updateCartBadges() {
    const badges = document.querySelectorAll('.cart-count, .cart-badge');
    badges.forEach(badge => {
        // Trigger animation
        badge.classList.add('cart-updated');
        setTimeout(() => badge.classList.remove('cart-updated'), 300);
    });
}

// ==================== User Activity Tracking ====================
let userInactive = false;
let inactivityTimer = null;

function initUserActivityTracking() {
    function resetInactivityTimer() {
        if (inactivityTimer) clearTimeout(inactivityTimer);
        
        if (userInactive) {
            userInactive = false;
            document.body.classList.remove('user-inactive');
        }
        
        inactivityTimer = setTimeout(() => {
            userInactive = true;
            document.body.classList.add('user-inactive');
        }, 5 * 60 * 1000); // 5 minutes
    }
    
    window.addEventListener('mousemove', resetInactivityTimer);
    window.addEventListener('keypress', resetInactivityTimer);
    window.addEventListener('click', resetInactivityTimer);
    window.addEventListener('scroll', resetInactivityTimer);
    
    resetInactivityTimer();
}

// ==================== Focus Trap for Modals ====================
function trapFocus(element) {
    const focusableElements = element.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    if (focusableElements.length === 0) return;
    
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];
    
    element.addEventListener('keydown', (e) => {
        if (e.key !== 'Tab') return;
        
        if (e.shiftKey) {
            if (document.activeElement === firstFocusable) {
                lastFocusable.focus();
                e.preventDefault();
            }
        } else {
            if (document.activeElement === lastFocusable) {
                firstFocusable.focus();
                e.preventDefault();
            }
        }
    });
    
    firstFocusable.focus();
}

// ==================== Scroll to Element ====================
function scrollToElement(elementId, offset = 0) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const elementPosition = element.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.scrollY - offset;
    
    window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
    });
}

// ==================== Detect Device Type ====================
function getDeviceType() {
    const ua = navigator.userAgent;
    if (/(tablet|ipad|playbook|silk)|(android(?!.*mobi))/i.test(ua)) {
        return 'tablet';
    }
    if (/Mobile|iP(hone|od)|Android|BlackBerry|IEMobile|Kindle|Silk-Accelerated|(hpw|web)OS|Opera M(obi|ini)/.test(ua)) {
        return 'mobile';
    }
    return 'desktop';
}

function initDeviceDetection() {
    const deviceType = getDeviceType();
    document.body.classList.add(`device-${deviceType}`);
    console.log(`Device detected: ${deviceType}`);
}

// ==================== Cookie Consent ====================
function initCookieConsent() {
    const hasConsent = localStorage.getItem('cookie_consent');
    
    if (!hasConsent) {
        const consentBanner = document.createElement('div');
        consentBanner.className = 'cookie-consent';
        consentBanner.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 20px;
            right: 20px;
            max-width: 400px;
            background: var(--bg-white, white);
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            z-index: 10003;
            font-size: 13px;
            line-height: 1.5;
            border: 1px solid var(--border-color, #eee);
        `;
        
        consentBanner.innerHTML = `
            <p style="margin: 0 0 12px 0;">🍪 We use cookies to enhance your experience. By continuing to visit this site you agree to our use of cookies.</p>
            <div style="display: flex; gap: 10px; justify-content: flex-end;">
                <button class="btn btn-outline btn-sm cookie-decline">Decline</button>
                <button class="btn btn-primary btn-sm cookie-accept">Accept</button>
            </div>
        `;
        
        document.body.appendChild(consentBanner);
        
        const acceptBtn = consentBanner.querySelector('.cookie-accept');
        const declineBtn = consentBanner.querySelector('.cookie-decline');
        
        acceptBtn.addEventListener('click', () => {
            localStorage.setItem('cookie_consent', 'accepted');
            consentBanner.remove();
            if (window.showToast) window.showToast('Cookie preferences saved', 'success');
        });
        
        declineBtn.addEventListener('click', () => {
            localStorage.setItem('cookie_consent', 'declined');
            consentBanner.remove();
        });
    }
}

// ==================== Final Initialization ====================
document.addEventListener('DOMContentLoaded', function() {
    // Initialize remaining components
    initServiceWorker();
    initPerformanceMonitoring();
    initOfflineIndicator();
    initCustomEvents();
    initUserActivityTracking();
    initDeviceDetection();
    initCookieConsent();
    
    // Request notification permission after user interaction
    const requestPermissionBtn = document.querySelector('.request-notification-btn');
    if (requestPermissionBtn) {
        requestPermissionBtn.addEventListener('click', requestNotificationPermission);
    }
});

// ==================== Export All Functions ====================
// Make all functions globally available
window.initServiceWorker = initServiceWorker;
window.requestNotificationPermission = requestNotificationPermission;
window.scrollToElement = scrollToElement;
window.getDeviceType = getDeviceType;
window.trapFocus = trapFocus;
window.syncOfflineEvents = syncOfflineEvents;
window.trackOfflineEvent = trackOfflineEvent;

// Performance marks
if (window.performance && window.performance.mark) {
    performance.mark('app_loaded');
}

// Console greeting
console.log(`
╔═══════════════════════════════════════════╗
║   👗 SEMIRA FASHION v1.0.0                ║
║   Professional E-commerce Platform        ║
║   Made with ❤️ for Ethiopian Fashion     ║
╚═══════════════════════════════════════════╝
`);
// ==================== Exports (Part 1) ====================
if (!window.showToast) window.showToast = showToast;
if (!window.showModal) window.showModal = showModal;
window.showLoading = showLoading;
window.showLoadingWithTimeout = showLoadingWithTimeout;
window.hideLoading = hideLoading;
window.formatPrice = formatPrice;
window.formatDate = formatDate;
window.timeAgo = timeAgo;
window.copyToClipboard = copyToClipboard;
window.debounce = debounce;
window.throttle = throttle;
window.getUrlParameter = getUrlParameter;
window.setUrlParameter = setUrlParameter;
window.escapeHtml = escapeHtml;