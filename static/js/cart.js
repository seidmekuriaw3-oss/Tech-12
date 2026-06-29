// ==================== ETHIOSADAT - CART JAVASCRIPT ====================
// Professional Shopping Cart Functionality

// Helper: turn DB thumbnail path (e.g. "uploads/products/x.jpg") into a full URL
function cartThumbUrl(thumbnail) {
    if (!thumbnail) return '/static/images/placeholder.png';
    if (thumbnail.startsWith('http') || thumbnail.startsWith('/')) return thumbnail;
    return '/static/' + thumbnail;
}

// Cart API endpoints
const CART_API = {
    count: '/api/cart/count',
    add: '/api/cart/add',
    update: '/api/cart/update',
    remove: '/api/cart/remove',
    cart: '/api/cart',
    clear: '/cart/clear',
    checkout: '/cart/checkout'
};

// Cart configuration
const CART_CONFIG = {
    autoRefreshInterval: 30000,
    maxRetries: 3,
    retryDelay: 1000,
    enableLocalStorage: true,
    storageKey: 'semirafashion_cart'
};

// ==================== Cart State Management ====================
class CartManager {
    constructor() {
        this.cart = [];
        this.count = 0;
        this.subtotal = 0;
        this.discount = 0;
        this.shipping = 0;
        this.total = 0;
        this.isLoading = false;
        this.refreshTimer = null;
        this.init();
    }
    
    init() {
        // Load from localStorage if available
        if (CART_CONFIG.enableLocalStorage) {
            this.loadFromStorage();
        }
        
        // Fetch fresh data from server (silently — ignores empty/failed responses)
        this.refresh();
    }
    
    loadFromStorage() {
        try {
            const saved = localStorage.getItem(CART_CONFIG.storageKey);
            if (saved) {
                const data = JSON.parse(saved);
                this.cart = data.cart || [];
                this.count = data.count || 0;
                this.updateUI();
            }
        } catch (e) {
            console.error('Error loading cart from storage:', e);
        }
    }
    
    saveToStorage() {
        if (!CART_CONFIG.enableLocalStorage) return;
        
        try {
            localStorage.setItem(CART_CONFIG.storageKey, JSON.stringify({
                cart: this.cart,
                count: this.count,
                subtotal: this.subtotal,
                total: this.total,
                timestamp: Date.now()
            }));
        } catch (e) {
            console.error('Error saving cart to storage:', e);
        }
    }
    
    refresh() {
        return this.fetchCartData();
    }
    
    fetchCartData(retryCount = 0) {
        return fetch(CART_API.cart)
            .then(res => res.text())
            .then(text => {
                if (!text || !text.trim()) return;
                const data = JSON.parse(text);
                if (data.success) {
                    this.cart = data.items || data.cart || [];
                    this.count = data.item_count || data.count || 0;
                    this.subtotal = data.subtotal || 0;
                    this.discount = data.discount || 0;
                    this.shipping = data.shipping_cost || 0;
                    this.total = data.total || 0;
                    this.updateUI();
                    this.saveToStorage();
                }
            })
            .catch(() => {});
    }
    
    updateUI() {
        // Update cart count badges
        this.updateCartBadges();
        
        // Update cart page if visible
        if (this.isCartPage()) {
            this.updateCartPage();
        }
        
        // Update mini cart if visible
        this.updateMiniCart();
    }
    
    updateCartBadges() {
        const badges = document.querySelectorAll('#cart-count, .cart-count, .cart-badge, .cart-badge-count');
        badges.forEach(badge => {
            if (this.count > 0) {
                badge.textContent = this.count;
                badge.style.display = 'inline-flex';
                this.animateBadge(badge);
            } else {
                badge.style.display = 'none';
            }
        });
    }
    
    animateBadge(element) {
        element.classList.add('cart-badge-animate');
        setTimeout(() => element.classList.remove('cart-badge-animate'), 300);
    }
    
    isCartPage() {
        const path = window.location.pathname;
        return path === '/cart' || path === '/cart/' || path === '/checkout' || path === '/checkout/';
    }
    
    updateCartPage() {
        // Update totals
        const subtotalEl = document.getElementById('cart-subtotal');
        const discountEl = document.getElementById('cart-discount');
        const shippingEl = document.getElementById('cart-shipping');
        const totalEl = document.getElementById('cart-total');
        const freeShippingMsg = document.getElementById('free-shipping-message');
        
        if (subtotalEl) subtotalEl.textContent = this.formatPrice(this.subtotal);
        if (discountEl) discountEl.textContent = this.discount > 0 ? `- ${this.formatPrice(this.discount)}` : '';
        if (shippingEl) shippingEl.textContent = this.shipping === 0 ? 'Free' : this.formatPrice(this.shipping);
        if (totalEl) totalEl.textContent = this.formatPrice(this.total);
        
        // Free shipping progress bar
        if (freeShippingMsg && this.subtotal > 0) {
            const threshold = 5000;
            const progress = Math.min((this.subtotal / threshold) * 100, 100);
            const remaining = threshold - this.subtotal;
            
            if (this.subtotal >= threshold) {
                freeShippingMsg.innerHTML = '<span class="success">✓ Congratulations! You get free shipping!</span>';
            } else {
                freeShippingMsg.innerHTML = `<span>Add ${this.formatPrice(remaining)} more to get free shipping!</span>
                    <div class="progress-bar"><div class="progress" style="width: ${progress}%;"></div></div>`;
            }
        }
    }
    
    updateMiniCart() {
        const miniCart = document.querySelector('.mini-cart, .cart-dropdown, .mini-cart-items');
        if (!miniCart) return;
        
        if (this.cart.length === 0) {
            miniCart.innerHTML = '<div class="empty-cart text-center p-4">Your cart is empty 🛒</div>';
        } else {
            this.renderMiniCartItems(miniCart);
        }
    }
    
    renderMiniCartItems(container) {
        let html = '';
        const itemsToShow = Math.min(this.cart.length, 5);
        
        for (let i = 0; i < itemsToShow; i++) {
            const item = this.cart[i];
            html += `
                <div class="mini-cart-item d-flex align-center" style="gap: 12px; padding: 12px 0; border-bottom: 1px solid var(--border-color, #eee);">
                    <img src="${item.thumbnail || item.image || '/static/images/placeholder.png'}" alt="${item.name || item.product_name}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 8px;">
                    <div class="flex-1">
                        <div class="fw-500">${this.truncate(item.name || item.product_name, 25)}</div>
                        <div class="text-muted small">${this.formatPrice(item.price || item.discounted_price)} x ${item.quantity}</div>
                    </div>
                    <button class="mini-cart-remove btn-icon" onclick="window.removeFromCart && removeFromCart('${item.product_id || item.id}')" style="background: none; border: none; color: #999; cursor: pointer;">&times;</button>
                </div>
            `;
        }
        
        if (this.cart.length > 5) {
            html += `<div class="text-center small text-muted mt-2">+${this.cart.length - 5} more items</div>`;
        }
        
        container.innerHTML = html;
        
        // Update footer if exists
        const footer = document.querySelector('.mini-cart-footer');
        if (footer) {
            footer.innerHTML = `
                <div class="d-flex justify-between mb-2">
                    <span>Subtotal:</span>
                    <span class="fw-bold">${this.formatPrice(this.subtotal)}</span>
                </div>
                <div class="d-flex justify-between mb-2">
                    <span>Shipping:</span>
                    <span>${this.shipping === 0 ? 'Free' : this.formatPrice(this.shipping)}</span>
                </div>
                <div class="d-flex justify-between fw-bold fs-5 mt-2 pt-2 border-top">
                    <span>Total:</span>
                    <span>${this.formatPrice(this.total)}</span>
                </div>
                <a href="/cart/checkout" class="btn btn-primary w-100 mt-3">Checkout →</a>
            `;
        }
    }
    
    formatPrice(price) {
        if (price === undefined || price === null) return '0 ETB';
        const num = parseFloat(price);
        if (isNaN(num)) return '0 ETB';
        return num.toLocaleString('en-US') + ' ETB';
    }
    
    truncate(text, length) {
        if (!text) return '';
        const str = String(text);
        return str.length > length ? str.substring(0, length) + '...' : str;
    }
    
    addItem(productId, quantity = 1) {
        this.isLoading = true;
        const pid = parseInt(productId);
        const qty = parseInt(quantity);
        const fallback = () => { window.location.href = '/cart/go/add/' + pid + '?qty=' + qty; };
        const url = CART_API.add + '?product_id=' + pid + '&quantity=' + qty;
        return fetch(url, { method: 'GET', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(res => res.text())
        .then(text => {
            if (!text || !text.trim()) { fallback(); return { success: true, message: 'Adding to cart...' }; }
            const data = JSON.parse(text);
            if (data.success) {
                if (typeof data.cart_count === 'number') { this.count = data.cart_count; this.updateCartBadges(); }
                return this.fetchCartData().then(() => ({ success: true, message: data.message || 'Product added to cart!' }));
            } else {
                throw new Error(data.error || data.message || 'Failed to add to cart');
            }
        })
        .catch(error => {
            console.error('[Cart] Error adding to cart:', error);
            if (!error.message || error.message.includes('JSON') || error.message.includes('end of') || error.message.includes('token')) {
                fallback();
                return { success: true, message: 'Adding to cart...' };
            }
            return { success: false, message: error.message };
        })
        .finally(() => { this.isLoading = false; });
    }
    
    updateItem(productId, quantity) {
        if (quantity < 1) {
            return this.removeItem(productId);
        }
        
        const url = CART_API.update + '?product_id=' + parseInt(productId) + '&quantity=' + parseInt(quantity);
        return fetch(url, { method: 'GET', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(res => res.text())
        .then(text => {
            if (!text || !text.trim()) { window.location.href = '/cart'; return { success: true }; }
            const data = JSON.parse(text);
            if (data.success) { this.refresh(); return { success: true }; }
            throw new Error(data.error || 'Update failed');
        })
        .catch(error => {
            if (!error.message || error.message.includes('JSON') || error.message.includes('end of')) {
                window.location.href = '/cart'; return { success: true };
            }
            console.error('Error updating cart:', error);
            return { success: false, message: error.message };
        });
    }
    
    removeItem(productId) {
        const url = CART_API.remove + '?product_id=' + parseInt(productId);
        return fetch(url, { method: 'GET', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(res => res.text())
        .then(text => {
            if (!text || !text.trim()) { window.location.href = '/cart'; return { success: true }; }
            const data = JSON.parse(text);
            if (data.success) { this.refresh(); return { success: true }; }
            throw new Error(data.error || 'Remove failed');
        })
        .catch(error => {
            if (!error.message || error.message.includes('JSON') || error.message.includes('end of')) {
                window.location.href = '/cart'; return { success: true };
            }
            console.error('Error removing from cart:', error);
            return { success: false, message: error.message };
        });
    }
    
    clearCart() {
        return fetch(CART_API.clear, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(() => {
            this.refresh();
            return { success: true };
        })
        .catch(error => {
            console.error('Error clearing cart:', error);
            return { success: false, message: error.message };
        });
    }
    
    destroy() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }
}

// ==================== Image URL Helper ====================
function getProductImageUrl(thumbnail) {
    if (!thumbnail || thumbnail === 'None' || String(thumbnail).trim() === '') {
        return '/static/images/placeholder.png';
    }
    const t = String(thumbnail).trim();
    if (t.startsWith('http') || t.startsWith('/static/')) return t;
    if (t.startsWith('uploads/')) return '/static/' + t;
    return '/static/uploads/products/' + t;
}

// Initialize cart manager
let cartManagerInstance = null;

function getCartManager() {
    if (!cartManagerInstance) {
        cartManagerInstance = new CartManager();
    }
    return cartManagerInstance;
}

// ==================== Global Cart Functions ====================
function updateCartCount(count) {
    const manager = getCartManager();
    manager.count = count;
    manager.updateCartBadges();
}

function fetchCartCount() {
    getCartManager().fetchCartData();
}

function addToCart(productId, quantity = 1, btn = null) {
    // Show loading state on button
    const originalText = btn ? btn.innerHTML : '';
    const originalDisabled = btn ? btn.disabled : false;
    
    if (btn) {
        btn.innerHTML = '<span class="spinner-sm"></span> Adding...';
        btn.disabled = true;
    }
    
    getCartManager().addItem(productId, quantity)
        .then(result => {
            if (result.success) {
                if (window.showSuccess) {
                    window.showSuccess(result.message || 'Added to cart!');
                } else if (window.showToast) {
                    window.showToast(result.message || 'Added to cart!', 'success');
                }
                
                // Animate cart icon
                const cartIcon = document.querySelector('.cart-icon, .cart-link, .fa-shopping-cart')?.closest('a, button');
                if (cartIcon) {
                    cartIcon.classList.add('cart-bounce');
                    setTimeout(() => cartIcon.classList.remove('cart-bounce'), 500);
                }
                
                // Show mini cart slide-in
                showMiniCart();
            } else {
                if (window.showError) {
                    window.showError(result.message || 'Error adding to cart');
                } else if (window.showToast) {
                    window.showToast(result.message || 'Error adding to cart', 'error');
                }
            }
        })
        .finally(() => {
            if (btn) {
                btn.innerHTML = originalText;
                btn.disabled = originalDisabled;
            }
        });
}

function updateCartItem(productId, quantity, inputElement = null) {
    if (quantity < 1) {
        removeFromCart(productId);
        return;
    }
    
    // Show loading on input
    if (inputElement) {
        inputElement.disabled = true;
    }
    
    getCartManager().updateItem(productId, quantity)
        .then(result => {
            if (!result.success) {
                if (window.showError) {
                    window.showError(result.message || 'Error updating cart');
                }
                // Restore previous value
                const manager = getCartManager();
                const item = manager.cart.find(i => (i.product_id || i.id) == productId);
                if (inputElement && item) {
                    inputElement.value = item.quantity;
                }
            }
        })
        .finally(() => {
            if (inputElement) {
                inputElement.disabled = false;
            }
        });
}

function removeFromCart(productId) {
    if (window.showConfirm) {
        window.showConfirm('Remove Item', 'Are you sure you want to remove this item from your cart?', () => {
            performRemove(productId);
        });
    } else {
        if (confirm('Are you sure you want to remove this item from your cart?')) {
            performRemove(productId);
        }
    }
}

function performRemove(productId) {
    if (window.showLoading) window.showLoading(true);
    
    getCartManager().removeItem(productId)
        .then(result => {
            if (result.success) {
                if (window.showSuccess) window.showSuccess('Item removed from cart');
                
                // Remove item from DOM
                const itemRow = document.querySelector(`.cart-item[data-id="${productId}"], .cart-item[data-product-id="${productId}"]`);
                if (itemRow) {
                    itemRow.style.transition = 'opacity 0.3s';
                    itemRow.style.opacity = '0';
                    setTimeout(() => itemRow.remove(), 300);
                }
                
                // Check if cart is empty
                const cartItems = document.querySelectorAll('.cart-item');
                if (cartItems.length === 0 && window.location.pathname === '/cart') {
                    location.reload();
                }
            } else {
                if (window.showError) window.showError(result.message || 'Error removing item');
            }
        })
        .finally(() => {
            if (window.showLoading) window.showLoading(false);
        });
}

function clearCart() {
    const confirmFn = window.showConfirm || confirm;
    const callback = () => {
        getCartManager().clearCart()
            .then(() => {
                if (window.showSuccess) window.showSuccess('Cart cleared');
                location.reload();
            })
            .catch(() => {
                if (window.showError) window.showError('Error clearing cart');
            });
    };
    
    if (window.showConfirm) {
        window.showConfirm('Clear Cart', 'Are you sure you want to remove all items from your cart?', callback);
    } else {
        if (confirm('Are you sure you want to remove all items from your cart?')) {
            callback();
        }
    }
}

// ==================== Mini Cart Slide-in Panel ====================
function showMiniCart() {
    let miniCart = document.querySelector('.mini-cart-panel');
    
    if (!miniCart) {
        miniCart = document.createElement('div');
        miniCart.className = 'mini-cart-panel';
        miniCart.style.cssText = `
            position: fixed;
            top: 0;
            right: -400px;
            bottom: 0;
            width: 400px;
            max-width: 90vw;
            background: var(--bg-white, white);
            box-shadow: -2px 0 20px rgba(0,0,0,0.15);
            z-index: 10001;
            transition: right 0.3s ease;
            display: flex;
            flex-direction: column;
        `;
        
        miniCart.innerHTML = `
            <div class="mini-cart-header" style="
                padding: 20px;
                background: linear-gradient(135deg, #1a73e8, #0d47a1);
                color: white;
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <h3 style="margin: 0;">🛒 Your Cart</h3>
                <button class="mini-cart-close" style="
                    background: none;
                    border: none;
                    color: white;
                    font-size: 24px;
                    cursor: pointer;
                    line-height: 1;
                ">&times;</button>
            </div>
            <div class="mini-cart-items" style="
                flex: 1;
                overflow-y: auto;
                padding: 20px;
            "></div>
            <div class="mini-cart-footer" style="
                padding: 20px;
                border-top: 1px solid var(--border-color, #eee);
            "></div>
        `;
        
        document.body.appendChild(miniCart);
        
        // Close button
        miniCart.querySelector('.mini-cart-close').addEventListener('click', hideMiniCart);
        
        // Overlay
        const overlay = document.createElement('div');
        overlay.className = 'mini-cart-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 10000;
            display: none;
        `;
        overlay.addEventListener('click', hideMiniCart);
        document.body.appendChild(overlay);
        
        miniCart.overlay = overlay;
    }
    
    // Update content
    updateMiniCartPanelContent(miniCart);
    
    // Show panel
    miniCart.style.right = '0';
    if (miniCart.overlay) miniCart.overlay.style.display = 'block';
}

function hideMiniCart() {
    const miniCart = document.querySelector('.mini-cart-panel');
    if (miniCart) {
        miniCart.style.right = '-400px';
        if (miniCart.overlay) miniCart.overlay.style.display = 'none';
    }
}

function updateMiniCartPanelContent(panel) {
    const manager = getCartManager();
    const itemsContainer = panel.querySelector('.mini-cart-items');
    const footer = panel.querySelector('.mini-cart-footer');
    
    if (manager.cart.length === 0) {
        itemsContainer.innerHTML = `
            <div style="text-align: center; padding: 40px 20px;">
                <div style="font-size: 48px; margin-bottom: 16px;">🛒</div>
                <p>Your cart is empty</p>
                <button class="btn btn-primary" onclick="hideMiniCart();">Continue Shopping</button>
            </div>
        `;
        footer.innerHTML = '';
        return;
    }
    
    // Render items
    let itemsHtml = '';
    manager.cart.forEach(item => {
        itemsHtml += `
            <div class="mini-cart-item" style="
                display: flex;
                gap: 12px;
                padding: 12px 0;
                border-bottom: 1px solid var(--border-color, #eee);
            " data-id="${item.product_id || item.id}">
                <div style="width: 60px; height: 60px; background: #f5f5f5; border-radius: 8px; overflow: hidden;">
                    <img src="${item.thumbnail || item.image || '/static/images/placeholder.png'}" style="width: 100%; height: 100%; object-fit: cover;">
                </div>
                <div style="flex: 1;">
                    <div style="font-weight: 500;">${manager.truncate(item.name || item.product_name, 30)}</div>
                    <div>${manager.formatPrice(item.price || item.discounted_price)} x ${item.quantity}</div>
                </div>
                <button class="mini-cart-remove" onclick="removeFromCart('${item.product_id || item.id}')" style="
                    background: none;
                    border: none;
                    color: #999;
                    cursor: pointer;
                    font-size: 18px;
                ">&times;</button>
            </div>
        `;
    });
    itemsContainer.innerHTML = itemsHtml;
    
    // Render footer
    footer.innerHTML = `
        <div style="margin-bottom: 16px;">
            <div class="d-flex justify-between" style="margin-bottom: 8px;">
                <span>Subtotal:</span>
                <span>${manager.formatPrice(manager.subtotal)}</span>
            </div>
            ${manager.discount > 0 ? `
            <div class="d-flex justify-between text-success" style="margin-bottom: 8px;">
                <span>Discount (10%):</span>
                <span>- ${manager.formatPrice(manager.discount)}</span>
            </div>
            ` : ''}
            <div class="d-flex justify-between" style="margin-bottom: 8px;">
                <span>Shipping:</span>
                <span>${manager.shipping === 0 ? 'Free' : manager.formatPrice(manager.shipping)}</span>
            </div>
            <div class="d-flex justify-between fw-bold fs-5" style="margin-top: 12px; padding-top: 12px; border-top: 2px solid var(--border-color, #eee);">
                <span>Total:</span>
                <span>${manager.formatPrice(manager.total)}</span>
            </div>
        </div>
        <a href="/cart/checkout" class="btn btn-primary w-100" style="text-align: center;">Checkout →</a>
        <button onclick="hideMiniCart();" class="btn btn-outline w-100 mt-2">Continue Shopping</button>
    `;
}

// ==================== Quantity Input Handlers ====================
function initQuantityInputs() {
    const inputs = document.querySelectorAll('.cart-item-quantity');
    inputs.forEach(input => {
        // Remove existing listener by cloning
        const newInput = input.cloneNode(true);
        if (input.parentNode) {
            input.parentNode.replaceChild(newInput, input);
        }
        
        newInput.addEventListener('change', function() {
            const productId = this.dataset.id || this.getAttribute('data-id');
            if (productId) {
                updateCartItem(productId, parseInt(this.value, 10), this);
            }
        });
    });
    
    // Quantity increment/decrement buttons
    // Skip buttons without data-id — those are managed by inline onclick handlers (e.g. cart page)
    document.querySelectorAll('.quantity-btn').forEach(btn => {
        const productId = btn.dataset.id || btn.getAttribute('data-id');
        if (!productId) return;
        btn.removeEventListener('click', btn._listener);
        btn._listener = function() {
            const pid = this.dataset.id || this.getAttribute('data-id');
            const input = document.querySelector(`.cart-item-quantity[data-id="${pid}"], input[data-id="${pid}"]`);
            if (input) {
                let newVal = parseInt(input.value, 10) + (this.classList.contains('plus') ? 1 : -1);
                if (newVal < 1) newVal = 1;
                input.value = newVal;
                updateCartItem(pid, newVal, input);
            }
        };
        btn.addEventListener('click', btn._listener);
    });
}

// ==================== Coupon Application ====================
function applyCoupon() {
    const code = document.getElementById('coupon-code')?.value;
    if (!code) {
        if (window.showWarning) window.showWarning('Please enter a coupon code');
        return;
    }
    
    if (window.showLoading) window.showLoading(true);
    
    fetch('/api/apply-coupon', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ code: code })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            if (window.showSuccess) window.showSuccess(`Coupon applied! You saved ${getCartManager().formatPrice(data.discount)}`);
            getCartManager().refresh();
        } else {
            if (window.showError) window.showError(data.error || 'Invalid coupon code');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        if (window.showError) window.showError('Failed to apply coupon');
    })
    .finally(() => {
        if (window.showLoading) window.showLoading(false);
    });
}

// ==================== CSS Animations ====================
(function addCartStyles() {
    if (document.getElementById('cart-styles')) return;
    
    const cartStyles = document.createElement('style');
    cartStyles.id = 'cart-styles';
    cartStyles.textContent = `
        .cart-badge-animate {
            animation: cartBadgePulse 0.3s ease;
        }
        
        .cart-bounce {
            animation: cartBounce 0.5s ease;
        }
        
        @keyframes cartBadgePulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.3); }
        }
        
        @keyframes cartBounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-5px); }
        }
        
        .progress-bar {
            background: #e0e0e0;
            border-radius: 10px;
            height: 6px;
            margin-top: 8px;
            overflow: hidden;
        }
        
        .progress-bar .progress {
            background: #4caf50;
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        
        @media (max-width: 576px) {
            .mini-cart-panel {
                width: 100% !important;
                max-width: 100% !important;
            }
        }
    `;
    document.head.appendChild(cartStyles);
})();

// ==================== Initialize ====================
document.addEventListener('DOMContentLoaded', function() {
    // Initialize cart manager
    getCartManager();
    
    // Initialize quantity inputs
    initQuantityInputs();
});

// ==================== Exports ====================
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        CartManager,
        getCartManager,
        addToCart,
        updateCartItem,
        removeFromCart,
        clearCart,
        showMiniCart,
        hideMiniCart,
        applyCoupon
    };
}

// Make globally available
window.getCartManager = getCartManager;
window.addToCart = addToCart;
window.updateCartItem = updateCartItem;
window.removeFromCart = removeFromCart;
window.clearCart = clearCart;
window.showMiniCart = showMiniCart;
window.hideMiniCart = hideMiniCart;
window.applyCoupon = applyCoupon;