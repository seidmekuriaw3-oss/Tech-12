// ==================== TOAST NOTIFICATION COMPONENT ====================
// Professional Toast Notifications for SEMIRA FASHION

class Toast {
    constructor(options = {}) {
        this.options = {
            position: 'bottom-right', // top-right, top-left, bottom-right, bottom-left, top-center, bottom-center
            duration: 3000,
            animation: 'slide',
            showProgress: true,
            dismissible: true,
            maxToasts: 5,
            ...options
        };
        
        this.container = null;
        this.toasts = [];
        this.createContainer();
    }
    
    createContainer() {
        // Remove existing container if any
        if (this.container && this.container.parentNode) {
            this.container.parentNode.removeChild(this.container);
        }
        
        // Create new container
        this.container = document.createElement('div');
        this.container.className = `toast-container toast-container-${this.options.position}`;
        
        // Position styles
        const positionStyles = {
            'top-right': `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 12px;
            `,
            'top-left': `
                position: fixed;
                top: 20px;
                left: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 12px;
            `,
            'bottom-right': `
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 12px;
            `,
            'bottom-left': `
                position: fixed;
                bottom: 20px;
                left: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 12px;
            `,
            'top-center': `
                position: fixed;
                top: 20px;
                left: 50%;
                transform: translateX(-50%);
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 12px;
                align-items: center;
            `,
            'bottom-center': `
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 12px;
                align-items: center;
            `
        };
        
        this.container.style.cssText = positionStyles[this.options.position] || positionStyles['bottom-right'];
        document.body.appendChild(this.container);
    }
    
    show(message, type = 'success', duration = null, options = {}) {
        const toastDuration = duration || this.options.duration;
        
        // Check max toasts limit
        if (this.toasts.length >= this.options.maxToasts) {
            this.removeOldestToast();
        }
        
        const toast = this.createToastElement(message, type, toastDuration, options);
        this.container.appendChild(toast);
        this.toasts.push(toast);
        
        // Trigger entrance animation
        requestAnimationFrame(() => {
            toast.classList.add('toast-enter');
        });
        
        // Start progress bar
        let progressInterval = null;
        let startTime = Date.now();
        
        if (this.options.showProgress && !options.noProgress) {
            const progressBar = toast.querySelector('.toast-progress');
            if (progressBar) {
                progressInterval = setInterval(() => {
                    // Check if toast still exists
                    if (!toast || !toast.parentNode) {
                        if (progressInterval) clearInterval(progressInterval);
                        return;
                    }
                    
                    const elapsed = Date.now() - startTime;
                    const percentage = Math.min((elapsed / toastDuration) * 100, 100);
                    progressBar.style.width = `${percentage}%`;
                    
                    if (percentage >= 100) {
                        if (progressInterval) clearInterval(progressInterval);
                    }
                }, 16);
            }
        }
        
        // Auto dismiss
        const timeoutId = setTimeout(() => {
            this.dismiss(toast);
            if (progressInterval) clearInterval(progressInterval);
        }, toastDuration);
        
        toast.dataset.timeoutId = timeoutId;
        toast.dataset.progressInterval = progressInterval;
        
        return toast;
    }
    
    createToastElement(message, type, duration, options = {}) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        // Base styles
        const backgroundColor = this.getBackgroundColor(type);
        const icon = this.getIcon(type);
        
        toast.style.cssText = `
            background: ${backgroundColor};
            color: white;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 14px;
            min-width: 280px;
            max-width: 400px;
            opacity: 0;
            transform: ${this.getInitialTransform()};
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        `;
        
        // Apply dark mode if needed
        this.applyDarkMode(toast);
        
        // Toast content
        toast.innerHTML = `
            <div class="toast-icon" style="
                padding-left: 16px;
                font-size: 20px;
            ">${icon}</div>
            <div class="toast-content" style="
                flex: 1;
                padding: 14px 0;
                font-weight: 500;
                line-height: 1.4;
                word-break: break-word;
            ">${this.escapeHtml(String(message))}</div>
            ${this.options.dismissible && !options.noDismiss ? `
                <button class="toast-dismiss" style="
                    background: none;
                    border: none;
                    color: rgba(255,255,255,0.7);
                    cursor: pointer;
                    font-size: 18px;
                    padding: 14px 16px;
                    transition: all 0.2s;
                    line-height: 1;
                ">&times;</button>
            ` : ''}
            ${this.options.showProgress && !options.noProgress ? `
                <div class="toast-progress" style="
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    height: 3px;
                    background: rgba(255,255,255,0.5);
                    width: 0%;
                    transition: width 0.05s linear;
                "></div>
            ` : ''}
        `;
        
        // Dismiss button handler
        const dismissBtn = toast.querySelector('.toast-dismiss');
        if (dismissBtn) {
            dismissBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.dismiss(toast);
                const timeoutId = parseInt(toast.dataset.timeoutId);
                if (timeoutId) clearTimeout(timeoutId);
                const progressInterval = toast.dataset.progressInterval;
                if (progressInterval) clearInterval(parseInt(progressInterval));
            });
            
            // Hover effect
            dismissBtn.addEventListener('mouseenter', () => {
                dismissBtn.style.color = 'white';
                dismissBtn.style.transform = 'scale(1.1)';
            });
            dismissBtn.addEventListener('mouseleave', () => {
                dismissBtn.style.color = 'rgba(255,255,255,0.7)';
                dismissBtn.style.transform = 'scale(1)';
            });
        }
        
        // Click to dismiss
        if (options.clickToDismiss) {
            toast.style.cursor = 'pointer';
            toast.addEventListener('click', (e) => {
                // Don't dismiss if clicking on dismiss button
                if (e.target.classList && e.target.classList.contains('toast-dismiss')) return;
                this.dismiss(toast);
                const timeoutId = parseInt(toast.dataset.timeoutId);
                if (timeoutId) clearTimeout(timeoutId);
                const progressInterval = toast.dataset.progressInterval;
                if (progressInterval) clearInterval(parseInt(progressInterval));
            });
        }
        
        // Hover pause
        toast.addEventListener('mouseenter', () => {
            const timeoutId = parseInt(toast.dataset.timeoutId);
            if (timeoutId) clearTimeout(timeoutId);
            
            const progressInterval = toast.dataset.progressInterval;
            if (progressInterval) clearInterval(parseInt(progressInterval));
        });
        
        toast.addEventListener('mouseleave', () => {
            const newTimeoutId = setTimeout(() => {
                this.dismiss(toast);
            }, duration || this.options.duration);
            toast.dataset.timeoutId = newTimeoutId;
            
            // Restart progress bar from current width
            const progressBar = toast.querySelector('.toast-progress');
            if (progressBar) {
                const currentWidth = parseFloat(progressBar.style.width) || 0;
                const remainingDuration = (duration || this.options.duration) * (1 - currentWidth / 100);
                const newStartTime = Date.now();
                
                const newProgressInterval = setInterval(() => {
                    if (!toast || !toast.parentNode) {
                        if (newProgressInterval) clearInterval(newProgressInterval);
                        return;
                    }
                    const elapsed = Date.now() - newStartTime;
                    const newPercentage = currentWidth + (elapsed / (duration || this.options.duration)) * 100;
                    progressBar.style.width = `${Math.min(100, newPercentage)}%`;
                    
                    if (newPercentage >= 100) {
                        if (newProgressInterval) clearInterval(newProgressInterval);
                    }
                }, 16);
                toast.dataset.progressInterval = newProgressInterval;
            }
        });
        
        return toast;
    }
    
    getInitialTransform() {
        const position = this.options.position;
        if (position.includes('top')) {
            return 'translateY(-100%)';
        }
        if (position.includes('bottom')) {
            return 'translateY(100%)';
        }
        return 'scale(0.9)';
    }
    
    dismiss(toast) {
        if (!toast || !toast.parentNode) return;
        
        // Clear intervals
        const progressInterval = toast.dataset.progressInterval;
        if (progressInterval) clearInterval(parseInt(progressInterval));
        
        toast.classList.remove('toast-enter');
        toast.classList.add('toast-exit');
        
        // Trigger exit animation
        toast.style.opacity = '0';
        toast.style.transform = this.getInitialTransform();
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
            this.toasts = this.toasts.filter(t => t !== toast);
        }, 300);
    }
    
    removeOldestToast() {
        const oldest = this.toasts[0];
        if (oldest) {
            this.dismiss(oldest);
        }
    }
    
    getBackgroundColor(type) {
        const colors = {
            success: 'linear-gradient(135deg, #4caf50, #45a049)',
            error: 'linear-gradient(135deg, #f44336, #e53935)',
            warning: 'linear-gradient(135deg, #ff9800, #fb8c00)',
            info: 'linear-gradient(135deg, #2196f3, #1e88e5)'
        };
        return colors[type] || colors.info;
    }
    
    getIcon(type) {
        const icons = {
            success: '✓',
            error: '✗',
            warning: '⚠',
            info: 'ℹ'
        };
        return icons[type] || icons.info;
    }
    
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    applyDarkMode(element) {
        const isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (isDarkMode) {
            element.style.backdropFilter = 'blur(10px)';
            element.style.background = 'rgba(30, 30, 46, 0.95)';
            element.style.webkitBackdropFilter = 'blur(10px)';
        }
    }
    
    // Convenience methods
    success(message, duration = null, options = {}) {
        return this.show(message, 'success', duration, options);
    }
    
    error(message, duration = null, options = {}) {
        return this.show(message, 'error', duration, options);
    }
    
    warning(message, duration = null, options = {}) {
        return this.show(message, 'warning', duration, options);
    }
    
    info(message, duration = null, options = {}) {
        return this.show(message, 'info', duration, options);
    }
    
    // Clear all toasts
    clearAll() {
        this.toasts.forEach(toast => {
            if (toast && toast.parentNode) {
                const progressInterval = toast.dataset.progressInterval;
                if (progressInterval) clearInterval(parseInt(progressInterval));
                toast.parentNode.removeChild(toast);
            }
        });
        this.toasts = [];
    }
    
    // Change position dynamically
    setPosition(position) {
        const validPositions = ['top-right', 'top-left', 'bottom-right', 'bottom-left', 'top-center', 'bottom-center'];
        if (!validPositions.includes(position)) {
            console.warn(`Invalid position: ${position}. Using default.`);
            return;
        }
        
        this.options.position = position;
        this.createContainer();
        
        // Re-add existing toasts to new container
        const existingToasts = [...this.toasts];
        this.toasts = [];
        existingToasts.forEach(toast => {
            if (toast && toast.parentNode) {
                const clone = toast.cloneNode(true);
                this.container.appendChild(clone);
                this.toasts.push(clone);
            }
        });
    }
    
    // Check if any toasts are active
    hasActiveToasts() {
        return this.toasts.length > 0;
    }
}

// ==================== GLOBAL TOAST INSTANCE ====================
let globalToast = null;

function getToastInstance() {
    if (!globalToast) {
        globalToast = new Toast();
    }
    return globalToast;
}

// ==================== GLOBAL FUNCTIONS (Backward Compatibility) ====================
function showToast(message, type = 'success', duration = null) {
    return getToastInstance().show(message, type, duration);
}

function showSuccess(message, duration = null) {
    return getToastInstance().success(message, duration);
}

function showError(message, duration = null) {
    return getToastInstance().error(message, duration);
}

function showWarning(message, duration = null) {
    return getToastInstance().warning(message, duration);
}

function showInfo(message, duration = null) {
    return getToastInstance().info(message, duration);
}

function clearAllToasts() {
    if (globalToast) {
        globalToast.clearAll();
    }
}

// ==================== ADD CSS STYLES ====================
(function addToastStyles() {
    if (document.getElementById('toast-styles')) return;
    
    const toastStyles = document.createElement('style');
    toastStyles.id = 'toast-styles';
    toastStyles.textContent = `
        @keyframes toastSlideInRight {
            from {
                opacity: 0;
                transform: translateX(100%);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes toastSlideInLeft {
            from {
                opacity: 0;
                transform: translateX(-100%);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes toastSlideInTop {
            from {
                opacity: 0;
                transform: translateY(-100%);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes toastSlideInBottom {
            from {
                opacity: 0;
                transform: translateY(100%);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .toast-enter {
            opacity: 1 !important;
            transform: translateX(0) translateY(0) scale(1) !important;
        }
        
        .toast-exit {
            opacity: 0 !important;
        }
        
        /* Progress bar animation */
        .toast-progress {
            pointer-events: none;
        }
        
        /* Mobile responsive */
        @media (max-width: 576px) {
            .toast-container {
                left: 10px !important;
                right: 10px !important;
                transform: none !important;
            }
            
            .toast {
                min-width: auto !important;
                width: calc(100% - 20px) !important;
                max-width: none !important;
            }
            
            .toast-icon {
                padding-left: 12px !important;
                font-size: 18px !important;
            }
            
            .toast-content {
                padding: 12px 0 !important;
                font-size: 13px !important;
            }
            
            .toast-dismiss {
                padding: 12px 16px !important;
            }
        }
        
        /* Reduced motion preference */
        @media (prefers-reduced-motion: reduce) {
            .toast,
            .toast-progress,
            .toast-dismiss {
                transition: none !important;
                animation: none !important;
            }
            
            .toast-progress {
                display: none !important;
            }
        }
        
        /* Dark mode additional styles */
        @media (prefers-color-scheme: dark) {
            .toast {
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
            }
        }
    `;
    document.head.appendChild(toastStyles);
})();

// ==================== EXPORT FOR MODULE USAGE ====================
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { 
        Toast, 
        toast: getToastInstance(),
        showToast, 
        showSuccess, 
        showError, 
        showWarning, 
        showInfo,
        clearAllToasts
    };
}

// Make globally available for browser
if (typeof window !== 'undefined') {
    window.Toast = Toast;
    window.toast = getToastInstance();
    window.showToast = showToast;
    window.showSuccess = showSuccess;
    window.showError = showError;
    window.showWarning = showWarning;
    window.showInfo = showInfo;
    window.clearAllToasts = clearAllToasts;
}