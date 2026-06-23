// ==================== PWA (Progressive Web App) FOR ETHIOSADAT ====================
// Professional PWA functionality including offline support, push notifications,
// installation prompt, and background sync

// ==================== PWA Configuration ====================
const PWA_CONFIG = {
    manifestUrl: '/static/manifest.json',
    swUrl: '/static/service-worker.js',
    offlinePage: '/offline',
    cacheName: 'semirafashion-cache-v1',
    apiCacheName: 'semirafashion-api-v1',
    offlineSupport: true,
    autoUpdate: true,
    updateCheckInterval: 3600000, // 1 hour
    criticalAssets: [
        '/',
        '/static/css/style.css',
        '/static/js/main.js',
        '/static/images/logo/logo.png',
        '/offline'
    ]
};

// ==================== Service Worker Registration ====================
class PWAManager {
    constructor() {
        this.swRegistration = null;
        this.swUpdateFound = false;
        this.deferredPrompt = null;
        this.isOnline = navigator.onLine;
        this.updateCheckInterval = null;
        this.init();
    }

    init() {
        this.registerServiceWorker();
        this.setupEventListeners();
        this.setupNetworkListeners();
        this.checkForUpdates();
        this.setupUpdateCheck();
    }

    registerServiceWorker() {
        // Service worker disabled — unregister any existing registrations.
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.getRegistrations().then(regs => {
                regs.forEach(r => r.unregister());
            });
        }
    }

    setupEventListeners() {
        // Installation prompt
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallPrompt();
        });
        
        // App installed
        window.addEventListener('appinstalled', () => {
            console.log('App was installed');
            this.deferredPrompt = null;
            this.showToast('App installed successfully!', 'success');
        });
    }

    setupNetworkListeners() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.showToast('Back online!', 'success');
            document.body.classList.remove('offline-mode');
            this.syncOfflineData();
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.showToast('You are offline. Some features may be limited.', 'warning');
            document.body.classList.add('offline-mode');
        });
    }

    setupUpdateCheck() {
        if (PWA_CONFIG.autoUpdate && this.updateCheckInterval) {
            clearInterval(this.updateCheckInterval);
        }
        
        if (PWA_CONFIG.autoUpdate) {
            this.updateCheckInterval = setInterval(() => {
                this.checkForUpdates();
            }, PWA_CONFIG.updateCheckInterval);
        }
    }

    checkForUpdates() {
        if (!this.swRegistration) return;
        
        this.swRegistration.update()
            .then(() => {
                console.log('Checked for Service Worker updates');
            })
            .catch(error => {
                console.error('Error checking for updates:', error);
            });
    }

    showUpdateNotification() {
        // Show toast notification
        this.showToast('New version available! Refresh to update.', 'info', 10000);
        
        // Create update banner
        const updateBanner = document.createElement('div');
        updateBanner.className = 'update-banner';
        updateBanner.innerHTML = `
            <div class="update-banner-content">
                <span>🔄 New version available!</span>
                <button class="btn-update">Update Now</button>
                <button class="btn-dismiss">Dismiss</button>
            </div>
        `;
        updateBanner.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 20px;
            right: 20px;
            background: #1a73e8;
            color: white;
            padding: 12px 20px;
            border-radius: 12px;
            z-index: 10000;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideInUp 0.3s ease;
        `;
        
        const updateBtn = updateBanner.querySelector('.btn-update');
        const dismissBtn = updateBanner.querySelector('.btn-dismiss');
        
        updateBtn.style.cssText = `
            background: white;
            color: #1a73e8;
            border: none;
            padding: 6px 16px;
            border-radius: 20px;
            cursor: pointer;
            margin-left: 10px;
        `;
        
        dismissBtn.style.cssText = `
            background: transparent;
            color: white;
            border: 1px solid white;
            padding: 6px 16px;
            border-radius: 20px;
            cursor: pointer;
            margin-left: 10px;
        `;
        
        updateBtn.addEventListener('click', () => {
            this.applyUpdate();
        });
        
        dismissBtn.addEventListener('click', () => {
            updateBanner.remove();
        });
        
        document.body.appendChild(updateBanner);
        
        // Auto dismiss after 30 seconds
        setTimeout(() => {
            if (updateBanner && updateBanner.parentNode) {
                updateBanner.remove();
            }
        }, 30000);
    }

    applyUpdate() {
        if (this.swRegistration && this.swRegistration.waiting) {
            this.swRegistration.waiting.postMessage({ type: 'SKIP_WAITING' });
        }
        
        // Reload the page
        window.location.reload();
    }

    showInstallPrompt() {
        // Check if already installed or dismissed
        if (localStorage.getItem('installPromptDismissed') === 'true') return;
        
        // Create install banner
        const installBanner = document.createElement('div');
        installBanner.className = 'install-banner';
        installBanner.innerHTML = `
            <div class="install-banner-content">
                <div class="install-icon">📱</div>
                <div class="install-text">
                    <strong>Install Ethiosadat App</strong>
                    <span>Get faster access and offline support</span>
                </div>
                <button class="btn-install">Install</button>
                <button class="btn-dismiss">✕</button>
            </div>
        `;
        installBanner.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 20px;
            right: 20px;
            background: var(--bg-white, white);
            border-radius: 16px;
            padding: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            z-index: 10000;
            animation: slideInUp 0.3s ease;
            border: 1px solid var(--border-color, #eee);
        `;
        
        const content = installBanner.querySelector('.install-banner-content');
        content.style.cssText = `
            display: flex;
            align-items: center;
            gap: 12px;
        `;
        
        const installIcon = installBanner.querySelector('.install-icon');
        installIcon.style.cssText = `
            font-size: 32px;
        `;
        
        const installText = installBanner.querySelector('.install-text');
        installText.style.cssText = `
            flex: 1;
            display: flex;
            flex-direction: column;
        `;
        
        const installBtn = installBanner.querySelector('.btn-install');
        installBtn.style.cssText = `
            background: #1a73e8;
            color: white;
            border: none;
            padding: 8px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 500;
        `;
        
        const dismissBtn = installBanner.querySelector('.btn-dismiss');
        dismissBtn.style.cssText = `
            background: none;
            border: none;
            font-size: 20px;
            cursor: pointer;
            color: #999;
            padding: 5px;
        `;
        
        installBtn.addEventListener('click', () => {
            this.showInstallPromptDialog();
            installBanner.remove();
        });
        
        dismissBtn.addEventListener('click', () => {
            installBanner.remove();
            localStorage.setItem('installPromptDismissed', 'true');
        });
        
        document.body.appendChild(installBanner);
        
        // Auto hide after 10 seconds
        setTimeout(() => {
            if (installBanner && installBanner.parentNode) {
                installBanner.remove();
            }
        }, 10000);
    }

    showInstallPromptDialog() {
        if (!this.deferredPrompt) {
            this.showToast('Installation is not available right now', 'warning');
            return;
        }
        
        this.deferredPrompt.prompt();
        
        this.deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('User accepted the install prompt');
            } else {
                console.log('User dismissed the install prompt');
            }
            this.deferredPrompt = null;
        });
    }

    syncOfflineData() {
        // Sync pending orders
        const pendingOrders = this.getPendingOrders();
        if (pendingOrders.length > 0) {
            this.syncOrders(pendingOrders);
        }
        
        // Sync pending cart items
        const pendingCart = this.getPendingCart();
        if (pendingCart) {
            this.syncCart(pendingCart);
        }
        
        // Sync pending analytics
        this.syncAnalytics();
    }

    getPendingOrders() {
        try {
            const orders = localStorage.getItem('pending_orders');
            return orders ? JSON.parse(orders) : [];
        } catch {
            return [];
        }
    }

    getPendingCart() {
        try {
            return localStorage.getItem('pending_cart');
        } catch {
            return null;
        }
    }

    syncOrders(orders) {
        orders.forEach(order => {
            fetch('/api/orders', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(order)
            })
            .then(response => {
                if (response.ok) {
                    this.removePendingOrder(order.id);
                }
            })
            .catch(error => console.error('Order sync failed:', error));
        });
    }

    syncCart(cartData) {
        if (!cartData) return;
        
        fetch('/api/cart/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: cartData
        })
        .then(response => {
            if (response.ok) {
                localStorage.removeItem('pending_cart');
                this.showToast('Cart synced successfully', 'success');
            }
        })
        .catch(error => console.error('Cart sync failed:', error));
    }

    syncAnalytics() {
        const offlineEvents = localStorage.getItem('offline_analytics');
        if (offlineEvents) {
            try {
                const events = JSON.parse(offlineEvents);
                fetch('/api/analytics/sync', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ events })
                })
                .then(response => {
                    if (response.ok) {
                        localStorage.removeItem('offline_analytics');
                    }
                })
                .catch(error => console.error('Analytics sync failed:', error));
            } catch (e) {
                console.error('Failed to parse offline events:', e);
            }
        }
    }

    removePendingOrder(orderId) {
        const orders = this.getPendingOrders();
        const updatedOrders = orders.filter(o => o.id !== orderId);
        localStorage.setItem('pending_orders', JSON.stringify(updatedOrders));
    }

    savePendingOrder(order) {
        const orders = this.getPendingOrders();
        orders.push({ ...order, id: Date.now() });
        localStorage.setItem('pending_orders', JSON.stringify(orders));
        this.showToast('Order saved offline. Will sync when online.', 'info');
    }

    showToast(message, type = 'info', duration = 3000) {
        if (window.showToast) {
            window.showToast(message, type, duration);
        } else {
            // Fallback toast
            const toast = document.createElement('div');
            toast.textContent = message;
            toast.style.cssText = `
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: ${type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : '#333'};
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                z-index: 10001;
                font-size: 14px;
            `;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), duration);
        }
    }
}

// ==================== Push Notifications ====================
class PushNotificationManager {
    constructor() {
        this.isSupported = 'Notification' in window && 'serviceWorker' in navigator;
        this.swRegistration = null;
        this.subscription = null;
    }

    async init(swRegistration) {
        this.swRegistration = swRegistration;
        await this.requestPermission();
    }

    async requestPermission() {
        if (!this.isSupported) return false;
        
        if (Notification.permission === 'default') {
            const permission = await Notification.requestPermission();
            if (permission === 'granted') {
                await this.subscribeToPush();
                return true;
            }
        } else if (Notification.permission === 'granted') {
            await this.subscribeToPush();
            return true;
        }
        
        return false;
    }

    async subscribeToPush() {
        if (!this.swRegistration) return;
        
        try {
            const subscription = await this.swRegistration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(
                    localStorage.getItem('vapid_public_key') || 'YOUR_VAPID_PUBLIC_KEY'
                )
            });
            
            this.subscription = subscription;
            await this.sendSubscriptionToServer(subscription);
            console.log('Push subscription successful');
            
        } catch (error) {
            console.error('Push subscription failed:', error);
        }
    }

    async sendSubscriptionToServer(subscription) {
        try {
            const response = await fetch('/api/notifications/subscribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(subscription)
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('Subscription saved to server');
            }
        } catch (error) {
            console.error('Failed to send subscription to server:', error);
        }
    }

    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    async unsubscribe() {
        if (!this.subscription) return;
        
        try {
            await this.subscription.unsubscribe();
            await fetch('/api/notifications/unsubscribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ endpoint: this.subscription.endpoint })
            });
            this.subscription = null;
            console.log('Unsubscribed from push notifications');
        } catch (error) {
            console.error('Failed to unsubscribe:', error);
        }
    }

    async sendTestNotification() {
        if (Notification.permission !== 'granted') {
            const granted = await this.requestPermission();
            if (!granted) {
                alert('Please enable notifications first');
                return;
            }
        }
        
        const notification = new Notification('ኢትዮሳዳት ፈርኒቸር ወድ ሰሚራ', {
            body: 'Welcome to Ethiosadat! Discover our latest furniture collections.',
            icon: '/static/images/logo/logo-192.png',
            badge: '/static/images/logo/badge.png',
            vibrate: [200, 100, 200],
            data: { url: '/products' }
        });
        
        notification.onclick = (event) => {
            event.preventDefault();
            window.open('/products', '_blank');
            notification.close();
        };
        
        setTimeout(() => notification.close(), 5000);
    }
}

// ==================== Background Sync ====================
class BackgroundSyncManager {
    constructor() {
        this.isSupported = 'serviceWorker' in navigator && 'SyncManager' in window;
    }

    async registerSync(tag, options = {}) {
        if (!this.isSupported) {
            console.warn('Background sync not supported');
            return false;
        }
        
        const swRegistration = await navigator.serviceWorker.ready;
        
        try {
            await swRegistration.sync.register(tag, options);
            console.log(`Background sync registered: ${tag}`);
            return true;
        } catch (error) {
            console.error('Background sync registration failed:', error);
            return false;
        }
    }

    async getTags() {
        if (!this.isSupported) return [];
        
        const swRegistration = await navigator.serviceWorker.ready;
        return await swRegistration.sync.getTags();
    }
}

// ==================== Offline Storage ====================
class OfflineStorage {
    constructor() {
        this.storagePrefix = 'semirafashion_';
    }

    save(key, data) {
        try {
            const item = {
                data: data,
                timestamp: Date.now(),
                version: 1
            };
            localStorage.setItem(this.storagePrefix + key, JSON.stringify(item));
            return true;
        } catch (e) {
            console.error('Failed to save to offline storage:', e);
            return false;
        }
    }

    get(key) {
        try {
            const item = localStorage.getItem(this.storagePrefix + key);
            if (item) {
                return JSON.parse(item).data;
            }
            return null;
        } catch (e) {
            console.error('Failed to get from offline storage:', e);
            return null;
        }
    }

    remove(key) {
        localStorage.removeItem(this.storagePrefix + key);
    }

    clear() {
        const keys = Object.keys(localStorage);
        keys.forEach(key => {
            if (key.startsWith(this.storagePrefix)) {
                localStorage.removeItem(key);
            }
        });
    }

    getAll() {
        const result = {};
        const keys = Object.keys(localStorage);
        keys.forEach(key => {
            if (key.startsWith(this.storagePrefix)) {
                const originalKey = key.replace(this.storagePrefix, '');
                result[originalKey] = this.get(originalKey);
            }
        });
        return result;
    }
}

// ==================== PWA Utilities ====================
function showInstallPrompt() {
    if (window.pwaManager) {
        window.pwaManager.showInstallPrompt();
    }
}

function checkForAppUpdates() {
    if (window.pwaManager) {
        window.pwaManager.checkForUpdates();
    }
}

function requestNotificationPermission() {
    if (window.pushManager) {
        return window.pushManager.requestPermission();
    }
}

function sendTestNotification() {
    if (window.pushManager) {
        return window.pushManager.sendTestNotification();
    }
}

function getOfflineStatus() {
    return !navigator.onLine;
}

async function getOfflineData(key) {
    if (window.offlineStorage) {
        return window.offlineStorage.get(key);
    }
    return null;
}

async function saveOfflineData(key, data) {
    if (window.offlineStorage) {
        return window.offlineStorage.save(key, data);
    }
    return false;
}

// ==================== CSS Styles ====================
(function addPWAstyles() {
    if (document.querySelector('#pwa-styles')) return;
    
    const styles = document.createElement('style');
    styles.id = 'pwa-styles';
    styles.textContent = `
        @keyframes slideInUp {
            from {
                transform: translateY(100%);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
        
        .offline-mode {
            filter: grayscale(0.1);
        }
        
        .update-banner,
        .install-banner {
            animation: slideInUp 0.3s ease;
        }
        
        @media (prefers-reduced-motion: reduce) {
            .update-banner,
            .install-banner {
                animation: none;
            }
        }
        
        @media (max-width: 576px) {
            .install-banner .install-banner-content {
                flex-wrap: wrap;
            }
            
            .btn-install {
                order: 2;
            }
            
            .btn-dismiss {
                order: 3;
            }
            
            .install-text {
                order: 1;
                width: 100%;
                margin-bottom: 10px;
            }
        }
    `;
    document.head.appendChild(styles);
})();

// ==================== Initialize PWA ====================
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize PWA Manager
    window.pwaManager = new PWAManager();
    
    // Initialize Offline Storage
    window.offlineStorage = new OfflineStorage();
    
    // Initialize Background Sync
    window.bgSync = new BackgroundSyncManager();
    
    // Register background sync for orders
    if (window.bgSync.isSupported) {
        await window.bgSync.registerSync('sync-orders', { minDelay: 5000 });
    }
    
    // Wait for service worker to be ready before initializing push
    if ('serviceWorker' in navigator) {
        const registration = await navigator.serviceWorker.ready;
        window.pushManager = new PushNotificationManager();
        await window.pushManager.init(registration);
    }
});

// ==================== Exports ====================
window.PWAManager = PWAManager;
window.PushNotificationManager = PushNotificationManager;
window.BackgroundSyncManager = BackgroundSyncManager;
window.OfflineStorage = OfflineStorage;
window.showInstallPrompt = showInstallPrompt;
window.checkForAppUpdates = checkForAppUpdates;
window.requestNotificationPermission = requestNotificationPermission;
window.sendTestNotification = sendTestNotification;
window.getOfflineStatus = getOfflineStatus;
window.getOfflineData = getOfflineData;
window.saveOfflineData = saveOfflineData;