// ==================== MODAL COMPONENT ====================
// Professional Modal Dialog for SEMIRA FASHION

class Modal {
    constructor(options = {}) {
        this.options = {
            title: '',
            content: '',
            size: 'medium', // small, medium, large, fullscreen
            showClose: true,
            showCancel: true,
            closeOnOverlay: true,
            closeOnEsc: true,
            onConfirm: null,
            onCancel: null,
            onClose: null,
            confirmText: 'Confirm',
            cancelText: 'Cancel',
            confirmButtonClass: 'btn-primary',
            cancelButtonClass: 'btn-outline',
            isDestructive: false,
            isLoading: false,
            ...options
        };
        
        this.modal = null;
        this.previouslyFocused = null;
        this.focusableElements = [];
        this.isOpen = false;
        this.escKeyHandler = this.handleEscKey.bind(this);
        this.tabKeyHandler = this.handleTabKey.bind(this);
        this.create();
    }
    
    create() {
        // Store previously focused element
        this.previouslyFocused = document.activeElement;
        
        // Create modal element
        this.modal = document.createElement('div');
        this.modal.className = 'modal-component';
        this.modal.setAttribute('role', 'dialog');
        this.modal.setAttribute('aria-modal', 'true');
        this.modal.setAttribute('aria-labelledby', 'modal-title');
        
        // Modal styles
        this.modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(4px);
            -webkit-backdrop-filter: blur(4px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.3s ease, visibility 0.3s ease;
        `;
        
        // Modal container styles based on size
        const sizeClass = this.getSizeClass();
        const maxWidth = this.getMaxWidth();
        const destructiveClass = this.options.isDestructive ? 'modal-destructive' : '';
        
        // Build modal HTML
        this.modal.innerHTML = `
            <div class="modal-container ${sizeClass} ${destructiveClass}" 
                 style="
                    background: var(--modal-bg, #ffffff);
                    border-radius: 20px;
                    max-width: ${maxWidth};
                    width: 90%;
                    max-height: 85vh;
                    overflow: hidden;
                    transform: scale(0.95);
                    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
                 ">
                <div class="modal-header" style="
                    padding: 20px 24px;
                    border-bottom: 1px solid var(--modal-border, #e9ecef);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                 ">
                    <h3 id="modal-title" style="margin: 0; font-size: 1.25rem; font-weight: 600; color: var(--modal-text, #333);">
                        ${this.escapeHtml(String(this.options.title || ''))}
                    </h3>
                    ${this.options.showClose ? `
                        <button class="modal-close" 
                                aria-label="Close modal"
                                style="
                                    background: none;
                                    border: none;
                                    font-size: 28px;
                                    cursor: pointer;
                                    color: var(--modal-text, #666);
                                    padding: 0;
                                    width: 32px;
                                    height: 32px;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    border-radius: 50%;
                                    transition: all 0.2s;
                                    line-height: 1;
                                ">
                            &times;
                        </button>
                    ` : ''}
                </div>
                <div class="modal-body" style="
                    padding: 24px;
                    overflow-y: auto;
                    max-height: calc(85vh - 130px);
                    color: var(--modal-text, #333);
                 ">
                    ${this.getContentHtml()}
                </div>
                <div class="modal-footer" style="
                    padding: 16px 24px;
                    border-top: 1px solid var(--modal-border, #e9ecef);
                    display: flex;
                    justify-content: flex-end;
                    gap: 12px;
                 ">
                    ${this.options.showCancel ? `
                        <button class="modal-cancel btn ${this.options.cancelButtonClass}" 
                                style="padding: 10px 20px;">
                            ${this.escapeHtml(String(this.options.cancelText))}
                        </button>
                    ` : ''}
                    <button class="modal-confirm btn ${this.options.confirmButtonClass}" 
                            style="padding: 10px 20px;">
                        ${this.options.isLoading ? '<span class="modal-spinner"></span> ' : ''}
                        ${this.escapeHtml(String(this.options.confirmText))}
                    </button>
                </div>
            </div>
        `;
        
        // Add to DOM
        document.body.appendChild(this.modal);
        
        // Apply dark mode if needed
        this.applyTheme();
        
        // Trigger entrance animation
        requestAnimationFrame(() => {
            if (this.modal) {
                this.modal.style.opacity = '1';
                this.modal.style.visibility = 'visible';
                const container = this.modal.querySelector('.modal-container');
                if (container) container.style.transform = 'scale(1)';
            }
        });
        
        // Bind events
        this.bindEvents();
        this.trapFocus();
        this.isOpen = true;
        
        // Prevent body scroll
        document.body.style.overflow = 'hidden';
    }
    
    getContentHtml() {
        const content = this.options.content;
        if (typeof content === 'string') {
            return content;
        } else if (content && content.nodeType) {
            // If content is a DOM element, wrap it
            const wrapper = document.createElement('div');
            wrapper.appendChild(content.cloneNode(true));
            return wrapper.innerHTML;
        }
        return '';
    }
    
    applyTheme() {
        // Check for dark mode preference
        const isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        if (isDarkMode && this.modal) {
            const container = this.modal.querySelector('.modal-container');
            if (container) {
                container.style.setProperty('--modal-bg', '#1a1a2e');
                container.style.setProperty('--modal-border', '#2a2a3e');
                container.style.setProperty('--modal-text', '#eeeeee');
            }
        }
    }
    
    getSizeClass() {
        const sizes = {
            small: 'modal-small',
            medium: 'modal-medium',
            large: 'modal-large',
            fullscreen: 'modal-fullscreen'
        };
        return sizes[this.options.size] || 'modal-medium';
    }
    
    getMaxWidth() {
        const widths = {
            small: '400px',
            medium: '550px',
            large: '800px',
            fullscreen: '95%'
        };
        return widths[this.options.size] || '550px';
    }
    
    bindEvents() {
        if (!this.modal) return;
        
        const closeBtn = this.modal.querySelector('.modal-close');
        const cancelBtn = this.modal.querySelector('.modal-cancel');
        const confirmBtn = this.modal.querySelector('.modal-confirm');
        const overlay = this.modal;
        
        // Close button
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close(false));
            closeBtn.addEventListener('mouseenter', (e) => {
                e.target.style.background = 'rgba(0, 0, 0, 0.05)';
            });
            closeBtn.addEventListener('mouseleave', (e) => {
                e.target.style.background = 'transparent';
            });
        }
        
        // Cancel button
        if (cancelBtn && this.options.showCancel) {
            cancelBtn.addEventListener('click', () => this.close(false));
        }
        
        // Confirm button
        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => {
                if (this.options.isLoading) return;
                this.close(true);
            });
        }
        
        // Overlay click
        if (this.options.closeOnOverlay) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) this.close(false);
            });
        }
        
        // ESC key
        if (this.options.closeOnEsc) {
            document.addEventListener('keydown', this.escKeyHandler);
        }
    }
    
    handleEscKey(e) {
        if (e.key === 'Escape' && this.modal && this.isOpen) {
            this.close(false);
        }
    }
    
    trapFocus() {
        if (!this.modal) return;
        
        // Get all focusable elements
        const focusableSelectors = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
        this.focusableElements = Array.from(this.modal.querySelectorAll(focusableSelectors));
        
        if (this.focusableElements.length > 0) {
            this.focusableElements[0].focus();
        }
        
        // Add focus trap listener
        this.modal.addEventListener('keydown', this.tabKeyHandler);
    }
    
    handleTabKey(e) {
        if (e.key !== 'Tab') return;
        if (this.focusableElements.length === 0) return;
        
        const firstElement = this.focusableElements[0];
        const lastElement = this.focusableElements[this.focusableElements.length - 1];
        
        if (e.shiftKey) {
            if (document.activeElement === firstElement) {
                lastElement.focus();
                e.preventDefault();
            }
        } else {
            if (document.activeElement === lastElement) {
                firstElement.focus();
                e.preventDefault();
            }
        }
    }
    
    setLoading(loading) {
        if (!this.modal) return;
        
        const confirmBtn = this.modal.querySelector('.modal-confirm');
        if (confirmBtn) {
            if (loading) {
                confirmBtn.disabled = true;
                confirmBtn.style.opacity = '0.7';
                confirmBtn.innerHTML = '<span class="modal-spinner"></span> Loading...';
                this.options.isLoading = true;
            } else {
                confirmBtn.disabled = false;
                confirmBtn.style.opacity = '1';
                confirmBtn.innerHTML = this.escapeHtml(String(this.options.confirmText));
                this.options.isLoading = false;
            }
        }
    }
    
    setContent(content) {
        if (!this.modal) return;
        
        const body = this.modal.querySelector('.modal-body');
        if (body) {
            if (typeof content === 'string') {
                body.innerHTML = content;
            } else if (content && content.nodeType) {
                body.innerHTML = '';
                body.appendChild(content.cloneNode(true));
            }
        }
    }
    
    setTitle(title) {
        if (!this.modal) return;
        
        const titleEl = this.modal.querySelector('#modal-title');
        if (titleEl) {
            titleEl.innerHTML = this.escapeHtml(String(title));
        }
    }
    
    close(confirmed = false) {
        if (!this.modal) return;
        
        // Remove event listeners
        if (this.options.closeOnEsc) {
            document.removeEventListener('keydown', this.escKeyHandler);
        }
        if (this.modal) {
            this.modal.removeEventListener('keydown', this.tabKeyHandler);
        }
        
        // Exit animation
        this.modal.style.opacity = '0';
        const container = this.modal.querySelector('.modal-container');
        if (container) container.style.transform = 'scale(0.95)';
        
        setTimeout(() => {
            if (this.modal && this.modal.parentNode) {
                this.modal.remove();
            }
            
            // Restore body scroll
            document.body.style.overflow = '';
            
            // Restore focus
            if (this.previouslyFocused && this.previouslyFocused.focus) {
                try {
                    this.previouslyFocused.focus();
                } catch (e) {
                    // Ignore if element no longer exists
                }
            }
            
            this.isOpen = false;
            this.modal = null;
            
            // Callback handlers
            if (confirmed && this.options.onConfirm) {
                this.options.onConfirm();
            } else if (!confirmed && this.options.onCancel) {
                this.options.onCancel();
            }
            
            if (this.options.onClose) {
                this.options.onClose();
            }
        }, 300);
    }
    
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// ==================== GLOBAL MODAL FUNCTIONS ====================

/**
 * Show a modal dialog
 * @param {string} title - Modal title
 * @param {string|HTMLElement} content - Modal content
 * @param {Function} onConfirm - Callback when confirmed
 * @param {Object} options - Additional options
 * @returns {Modal} Modal instance
 */
function showModal(title, content, onConfirm = null, options = {}) {
    return new Modal({
        title: title,
        content: content,
        onConfirm: onConfirm,
        ...options
    });
}

/**
 * Show a confirmation dialog
 * @param {string} title - Modal title
 * @param {string} message - Confirmation message
 * @param {Function} onConfirm - Callback when confirmed
 * @param {Function} onCancel - Callback when cancelled
 * @returns {Modal} Modal instance
 */
function showConfirm(title, message, onConfirm, onCancel = null) {
    return new Modal({
        title: title,
        content: message,
        onConfirm: onConfirm,
        onCancel: onCancel,
        confirmText: 'Yes',
        cancelText: 'No'
    });
}

/**
 * Show an alert dialog
 * @param {string} title - Alert title
 * @param {string} content - Alert message
 * @param {string} type - Alert type (info, success, error, warning)
 * @returns {Modal} Modal instance
 */
function showAlert(title, content, type = 'info') {
    const buttonClass = type === 'error' ? 'btn-danger' : 'btn-primary';
    const iconMap = {
        info: 'ℹ️',
        success: '✅',
        error: '❌',
        warning: '⚠️'
    };
    const icon = iconMap[type] || 'ℹ️';
    
    return new Modal({
        title: `${icon} ${title}`,
        content: content,
        showCancel: false,
        confirmText: 'OK',
        confirmButtonClass: buttonClass
    });
}

/**
 * Show a loading modal
 * @param {string} message - Loading message
 * @returns {Modal} Modal instance
 */
function showLoadingModal(message = 'Loading...') {
    return new Modal({
        title: 'Please wait',
        content: `
            <div style="text-align: center; padding: 20px;">
                <div class="modal-spinner-large"></div>
                <p style="margin-top: 15px;">${message}</p>
            </div>
        `,
        showCancel: false,
        showClose: false,
        closeOnOverlay: false,
        closeOnEsc: false,
        confirmText: 'Close',
        showConfirm: false
    });
}

/**
 * Close all modals (if any are open)
 */
function closeAllModals() {
    const modals = document.querySelectorAll('.modal-component');
    modals.forEach(modal => {
        if (modal.remove) modal.remove();
    });
    document.body.style.overflow = '';
}

/**
 * Show a toast notification (inline with modal)
 * @param {string} message - Toast message
 * @param {string} type - Toast type (info, success, error, warning)
 */
function showToast(message, type = 'info') {
    // Remove existing toast
    const existingToast = document.querySelector('.modal-toast');
    if (existingToast) existingToast.remove();
    
    const toast = document.createElement('div');
    toast.className = `modal-toast modal-toast-${type}`;
    toast.textContent = message;
    
    const bgColor = {
        error: '#f44336',
        success: '#4caf50',
        warning: '#ff9800',
        info: '#2196f3'
    }[type] || '#333';
    
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: ${bgColor};
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        z-index: 10001;
        font-size: 14px;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: fadeInUp 0.3s ease;
        cursor: pointer;
    `;
    
    document.body.appendChild(toast);
    
    // Auto hide after 3 seconds
    const timeout = setTimeout(() => {
        if (toast && toast.parentNode) {
            toast.style.opacity = '0';
            setTimeout(() => {
                if (toast && toast.parentNode) toast.remove();
            }, 300);
        }
    }, 3000);
    
    // Allow clicking to dismiss
    toast.addEventListener('click', () => {
        clearTimeout(timeout);
        toast.style.opacity = '0';
        setTimeout(() => {
            if (toast && toast.parentNode) toast.remove();
        }, 300);
    });
    
    return toast;
}

// Add CSS animations
(function addModalStyles() {
    if (document.getElementById('modal-styles')) return;
    
    const modalStyles = document.createElement('style');
    modalStyles.id = 'modal-styles';
    modalStyles.textContent = `
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateX(-50%) translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }
        }
        
        .modal-spinner {
            display: inline-block;
            width: 14px;
            height: 14px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: modalSpin 0.6s linear infinite;
            margin-right: 6px;
            vertical-align: middle;
        }
        
        .modal-spinner-large {
            width: 40px;
            height: 40px;
            border: 3px solid #f0f0f0;
            border-top-color: #1a73e8;
            border-radius: 50%;
            animation: modalSpin 0.8s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes modalSpin {
            to { transform: rotate(360deg); }
        }
        
        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
            .modal-spinner-large {
                border-color: #2a2a3e;
                border-top-color: #4285f4;
            }
        }
        
        /* Reduced motion preference */
        @media (prefers-reduced-motion: reduce) {
            .modal-spinner,
            .modal-spinner-large {
                animation: none;
            }
        }
        
        /* Responsive modal */
        @media (max-width: 576px) {
            .modal-container {
                width: 95% !important;
                border-radius: 16px !important;
            }
            
            .modal-header {
                padding: 15px 20px !important;
            }
            
            .modal-body {
                padding: 20px !important;
            }
            
            .modal-footer {
                padding: 12px 20px !important;
                flex-direction: column;
            }
            
            .modal-footer button {
                width: 100%;
                justify-content: center;
            }
        }
    `;
    document.head.appendChild(modalStyles);
})();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { 
        Modal, 
        showModal, 
        showConfirm, 
        showAlert, 
        showLoadingModal,
        closeAllModals,
        showToast
    };
}

// Make globally available for browser
if (typeof window !== 'undefined') {
    window.Modal = Modal;
    window.showModal = showModal;
    window.showConfirm = showConfirm;
    window.showAlert = showAlert;
    window.showLoadingModal = showLoadingModal;
    window.closeAllModals = closeAllModals;
    window.showToast = showToast;
}