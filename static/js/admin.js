// ==================== ETHIOSADAT - ADMIN JAVASCRIPT ====================
// Professional Admin Panel Functionality

// ==================== DOM Ready ====================
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all admin components
    initProductManagement();
    initOrderManagement();
    initDashboardCharts();
    initImagePreviews();
    initAutoSave();
    initSearchFilters();
    initSortableTables();
    initBulkActions();
    initExportButtons();
    
    // Add event listeners
    const selectAllCheckbox = document.getElementById('select-all');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            document.querySelectorAll('.product-select, .item-select').forEach(cb => {
                cb.checked = this.checked;
            });
        });
    }
    
    // Mobile sidebar toggle
    const menuToggle = document.querySelector('.menu-toggle');
    if (menuToggle) {
        menuToggle.addEventListener('click', toggleSidebar);
    }
    
    // Close sidebar on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const sidebar = document.querySelector('.admin-sidebar.open');
            if (sidebar) toggleSidebar();
        }
    });
});

// ==================== Product Management ====================
function deleteProduct(productId, productName) {
    if (!productId) return;

    const _confirm = window.showConfirm || function(t, m, cb) { if (confirm(m)) cb(); };
    const _success = window.showSuccess || function(m) { alert(m); };
    const _error   = window.showError   || function(m) { alert(m); };

    _confirm('Delete Product', `Are you sure you want to delete "${productName || 'this product'}"? This action cannot be undone.`, () => {
        showLoading(true);
        fetch(`/admin/products/delete/${productId}`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (response.ok) {
                _success(`${productName || 'Product'} deleted successfully`);
                setTimeout(() => location.reload(), 1500);
            } else {
                throw new Error('Delete failed');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            _error('Failed to delete product');
        })
        .finally(() => showLoading(false));
    });
}

function deleteAd(adId) {
    if (!adId) return;

    const _confirm = window.showConfirm || function(t, m, cb) { if (confirm(m)) cb(); };
    const _success = window.showSuccess || function(m) { alert(m); };
    const _error   = window.showError   || function(m) { alert(m); };

    _confirm('Delete Advertisement', 'Are you sure you want to delete this advertisement?', () => {
        showLoading(true);
        fetch(`/admin/ads/delete/${adId}`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (response.ok) {
                _success('Advertisement deleted successfully');
                setTimeout(() => location.reload(), 1500);
            } else {
                throw new Error('Delete failed');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            _error('Failed to delete advertisement');
        })
        .finally(() => showLoading(false));
    });
}

function toggleProductStatus(productId, currentStatus) {
    if (!productId) return;
    
    const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
    const statusText = newStatus === 'active' ? 'activate' : 'deactivate';
    
    showConfirm('Update Status', `Are you sure you want to ${statusText} this product?`, () => {
        showLoading(true);
        fetch(`/admin/products/toggle-status/${productId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ status: newStatus })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccess(`Product ${statusText}d successfully`);
                location.reload();
            } else {
                showError(data.error || 'Failed to update status');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Failed to update status');
        })
        .finally(() => showLoading(false));
    });
}

function initProductManagement() {
    // Add any product-specific initialization here
}

// ==================== Image Preview ====================
function previewImage(input, previewId) {
    const preview = document.getElementById(previewId);
    if (!preview) return;
    
    if (input.files && input.files[0]) {
        const file = input.files[0];
        
        // Validate file type
        if (!file.type.match('image.*')) {
            showError('Please select an image file');
            input.value = '';
            return;
        }
        
        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            showError('Image size should be less than 5MB');
            input.value = '';
            return;
        }
        
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
            preview.classList.add('fade-in');
        };
        reader.readAsDataURL(input.files[0]);
    }
}

function initImagePreviews() {
    const imageInputs = document.querySelectorAll('.image-input');
    imageInputs.forEach(input => {
        const previewId = input.dataset.preview;
        if (previewId) {
            input.addEventListener('change', function() {
                previewImage(this, previewId);
            });
        }
    });
}

// ==================== Bulk Actions ====================
function getSelectedItems() {
    return Array.from(document.querySelectorAll('.product-select:checked, .item-select:checked'))
        .map(cb => cb.value)
        .filter(value => value);
}

function bulkDelete() {
    const selected = getSelectedItems();
    
    if (selected.length === 0) {
        showWarning('No items selected');
        return;
    }
    
    showConfirm('Bulk Delete', `Are you sure you want to delete ${selected.length} item(s)? This action cannot be undone.`, () => {
        showLoading(true);
        
        fetch('/admin/bulk-delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ ids: selected })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccess(`${data.deleted || selected.length} item(s) deleted successfully`);
                setTimeout(() => location.reload(), 1500);
            } else {
                showError(data.error || 'Failed to delete items');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Failed to delete items');
        })
        .finally(() => showLoading(false));
    });
}

function bulkUpdateStatus(status) {
    const selected = getSelectedItems();
    
    if (selected.length === 0) {
        showWarning('No items selected');
        return;
    }
    
    const statusText = status === 'active' ? 'activate' : status === 'inactive' ? 'deactivate' : status;
    
    showConfirm('Bulk Update', `Are you sure you want to update ${selected.length} item(s) to ${statusText}?`, () => {
        showLoading(true);
        
        fetch('/admin/bulk-update-status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ ids: selected, status: status })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccess(`${data.updated || selected.length} item(s) updated successfully`);
                setTimeout(() => location.reload(), 1500);
            } else {
                showError(data.error || 'Failed to update items');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Failed to update items');
        })
        .finally(() => showLoading(false));
    });
}

function initBulkActions() {
    const bulkDeleteBtn = document.getElementById('bulk-delete');
    if (bulkDeleteBtn) {
        bulkDeleteBtn.addEventListener('click', bulkDelete);
    }
    
    const bulkStatusSelect = document.getElementById('bulk-status');
    if (bulkStatusSelect) {
        bulkStatusSelect.addEventListener('change', (e) => {
            if (e.target.value) {
                bulkUpdateStatus(e.target.value);
                e.target.value = '';
            }
        });
    }
}

// ==================== Order Management ====================
function updateOrderStatus(orderId, status) {
    if (!orderId || !status) return;
    
    showLoading(true);
    
    fetch(`/admin/orders/update/${orderId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: `status=${encodeURIComponent(status)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess('Order status updated successfully');
            // Update status badge without reload
            const statusBadge = document.querySelector(`#order-${orderId} .status-badge`);
            if (statusBadge) {
                statusBadge.className = `status-badge status-${status}`;
                statusBadge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
                statusBadge.style.backgroundColor = getStatusColor(status);
            }
        } else {
            showError(data.error || 'Failed to update order status');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Failed to update order status');
    })
    .finally(() => showLoading(false));
}

function viewOrderDetails(orderId) {
    if (!orderId) return;
    
    showLoading(true);
    // Fetch order details via AJAX
    fetch(`/api/admin/orders/${orderId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showModal('Order Details', formatOrderDetails(data.order), null, { showCancel: false });
            } else {
                showError(data.error || 'Failed to load order details');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Failed to load order details');
        })
        .finally(() => showLoading(false));
}

function formatOrderDetails(order) {
    if (!order) return '<p>No order data available</p>';
    
    return `
        <div style="max-width: 500px;">
            <p><strong>Order #:</strong> ${escapeHtml(order.order_number || 'N/A')}</p>
            <p><strong>Customer:</strong> ${escapeHtml(order.customer_name || order.shipping_address || 'N/A')}</p>
            <p><strong>Phone:</strong> ${escapeHtml(order.shipping_phone || order.customer_phone || 'N/A')}</p>
            <p><strong>Address:</strong> ${escapeHtml(order.shipping_address || 'Not provided')}</p>
            <p><strong>Subtotal:</strong> ${order.subtotal || 0} ETB</p>
            <p><strong>Shipping:</strong> ${order.shipping_fee || 0} ETB</p>
            <p><strong>Total:</strong> ${order.total || 0} ETB</p>
            <p><strong>Status:</strong> <span style="background:${getStatusColor(order.status)};color:white;padding:2px 10px;border-radius:20px;">${order.status || 'pending'}</span></p>
            <p><strong>Date:</strong> ${order.created_at ? new Date(order.created_at).toLocaleString() : 'N/A'}</p>
            ${order.notes ? `<p><strong>Notes:</strong> ${escapeHtml(order.notes)}</p>` : ''}
        </div>
    `;
}

function initOrderManagement() {
    const statusSelects = document.querySelectorAll('.order-status-select');
    statusSelects.forEach(select => {
        select.addEventListener('change', function() {
            updateOrderStatus(this.dataset.orderId, this.value);
        });
    });
}

// ==================== Dashboard Charts ====================
function initDashboardCharts() {
    initSalesChart();
    initCategoryChart();
    initOrdersChart();
}

function initSalesChart() {
    const salesCanvas = document.getElementById('sales-chart');
    if (!salesCanvas) return;
    
    fetch('/api/admin/sales-data')
        .then(response => response.json())
        .then(data => {
            if (typeof Chart !== 'undefined') {
                new Chart(salesCanvas, {
                    type: 'line',
                    data: {
                        labels: data.labels || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                        datasets: [{
                            label: 'Sales (ETB)',
                            data: data.values || [0, 0, 0, 0, 0, 0],
                            borderColor: '#1a73e8',
                            backgroundColor: 'rgba(26, 115, 232, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'top' },
                            tooltip: { 
                                callbacks: { 
                                    label: (ctx) => `${ctx.raw.toLocaleString()} ETB` 
                                } 
                            }
                        }
                    }
                });
            }
        })
        .catch(error => console.error('Error loading sales chart:', error));
}

function initCategoryChart() {
    const categoryCanvas = document.getElementById('category-chart');
    if (!categoryCanvas) return;
    
    fetch('/api/admin/category-data')
        .then(response => response.json())
        .then(data => {
            if (typeof Chart !== 'undefined' && data.categories && data.counts) {
                new Chart(categoryCanvas, {
                    type: 'doughnut',
                    data: {
                        labels: data.categories,
                        datasets: [{
                            data: data.counts,
                            backgroundColor: ['#1a73e8', '#ff9800', '#4caf50', '#f44336', '#9c27b0', '#00bcd4']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
            }
        })
        .catch(error => console.error('Error loading category chart:', error));
}

function initOrdersChart() {
    const ordersCanvas = document.getElementById('orders-chart');
    if (!ordersCanvas) return;
    
    fetch('/api/admin/orders-data')
        .then(response => response.json())
        .then(data => {
            if (typeof Chart !== 'undefined') {
                new Chart(ordersCanvas, {
                    type: 'bar',
                    data: {
                        labels: data.labels || ['Pending', 'Confirmed', 'Shipped', 'Delivered', 'Cancelled'],
                        datasets: [{
                            label: 'Orders',
                            data: data.values || [0, 0, 0, 0, 0],
                            backgroundColor: '#1a73e8',
                            borderRadius: 8
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
            }
        })
        .catch(error => console.error('Error loading orders chart:', error));
}

// ==================== Settings Management ====================
function saveSettings() {
    const form = document.getElementById('settings-form');
    if (!form) return;
    
    // Validate form
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    showLoading(true);
    const formData = new FormData(form);
    
    fetch('/admin/settings', {
        method: 'POST',
        body: formData,
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess('Settings saved successfully');
            if (data.reload) setTimeout(() => location.reload(), 1500);
        } else {
            showError(data.error || 'Error saving settings');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Failed to save settings');
    })
    .finally(() => showLoading(false));
}

// ==================== Export Data ====================
function exportData(type, format = 'csv') {
    if (!type) return;
    
    showLoading(true);
    
    fetch(`/admin/export/${type}?format=${format}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => {
        if (!response.ok) throw new Error('Export failed');
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${type}_export_${new Date().toISOString().slice(0,19)}.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        showSuccess('Export completed successfully');
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Failed to export data');
    })
    .finally(() => showLoading(false));
}

function initExportButtons() {
    const exportBtns = document.querySelectorAll('.export-btn');
    exportBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const type = btn.dataset.type || 'products';
            const format = btn.dataset.format || 'csv';
            exportData(type, format);
        });
    });
}

// ==================== Search and Filter ====================
let searchTimeout = null;

function initSearchFilters() {
    const searchInput = document.getElementById('admin-search');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            if (searchTimeout) clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(e.target.value);
            }, 300);
        });
    }
    
    const tableSearch = document.getElementById('table-search');
    if (tableSearch) {
        tableSearch.addEventListener('keyup', filterTable);
    }
}

function performSearch(query) {
    const currentUrl = new URL(window.location.href);
    if (query && query.trim()) {
        currentUrl.searchParams.set('search', query.trim());
    } else {
        currentUrl.searchParams.delete('search');
    }
    window.location.href = currentUrl.toString();
}

function filterTable() {
    const searchTerm = document.getElementById('table-search')?.value.toLowerCase().trim() || '';
    const rows = document.querySelectorAll('tbody tr');
    let visibleCount = 0;
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
    const resultCount = document.getElementById('result-count');
    if (resultCount) {
        resultCount.textContent = `${visibleCount} result(s) found`;
    }
}

// ==================== Sortable Tables ====================
function initSortableTables() {
    const tables = document.querySelectorAll('.sortable-table');
    tables.forEach(table => {
        const headers = table.querySelectorAll('th[data-sort]');
        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => sortTable(table, header.dataset.sort));
        });
    });
}

function sortTable(table, column) {
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const isAscending = table.dataset.sortOrder !== 'asc';
    
    rows.sort((a, b) => {
        let aVal = a.querySelector(`td[data-column="${column}"]`)?.textContent || '';
        let bVal = b.querySelector(`td[data-column="${column}"]`)?.textContent || '';
        
        // Try numeric comparison
        const aNum = parseFloat(aVal);
        const bNum = parseFloat(bVal);
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAscending ? aNum - bNum : bNum - aNum;
        }
        
        return isAscending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    });
    
    rows.forEach(row => tbody.appendChild(row));
    table.dataset.sortOrder = isAscending ? 'asc' : 'desc';
}

// ==================== Auto-save Draft ====================
let autoSaveTimer = null;

function autoSaveDraft() {
    if (autoSaveTimer) clearTimeout(autoSaveTimer);
    
    autoSaveTimer = setTimeout(() => {
        const form = document.querySelector('.auto-save-form');
        if (form) {
            const formData = new FormData(form);
            fetch('/admin/products/draft', {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showInfo('Draft saved', 1500);
                }
            })
            .catch(error => console.error('Auto-save error:', error));
        }
    }, 3000);
}

function initAutoSave() {
    const autoSaveForms = document.querySelectorAll('.auto-save-form');
    autoSaveForms.forEach(form => {
        form.addEventListener('input', autoSaveDraft);
    });
}

// ==================== Loading States ====================
let loaderElement = null;

function showLoading(show) {
    if (show) {
        if (!loaderElement) {
            loaderElement = document.createElement('div');
            loaderElement.id = 'global-loader';
            loaderElement.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                backdrop-filter: blur(2px);
            `;
            loaderElement.innerHTML = '<div class="spinner"></div>';
            document.body.appendChild(loaderElement);
        } else {
            loaderElement.style.display = 'flex';
        }
    } else if (loaderElement) {
        loaderElement.style.display = 'none';
    }
}

// ==================== Utility Functions ====================
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

function toggleSidebar() {
    const sidebar = document.querySelector('.admin-sidebar');
    if (!sidebar) return;
    
    sidebar.classList.toggle('open');
    
    // Add overlay for mobile
    if (window.innerWidth <= 768) {
        let overlay = document.querySelector('.sidebar-overlay');
        if (!overlay && sidebar.classList.contains('open')) {
            overlay = document.createElement('div');
            overlay.className = 'sidebar-overlay';
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.5);
                z-index: 999;
                backdrop-filter: blur(2px);
            `;
            overlay.addEventListener('click', toggleSidebar);
            document.body.appendChild(overlay);
        } else if (overlay && !sidebar.classList.contains('open')) {
            overlay.remove();
        }
    } else if (sidebar.classList.contains('open')) {
        // On desktop, close after a delay or keep open based on preference
        const overlay = document.querySelector('.sidebar-overlay');
        if (overlay) overlay.remove();
    }
}

function getStatusColor(status) {
    const colors = {
        'pending': '#ff9800',
        'confirmed': '#4caf50',
        'processing': '#2196f3',
        'shipped': '#2196f3',
        'delivered': '#1a73e8',
        'cancelled': '#f44336',
        'active': '#4caf50',
        'inactive': '#999'
    };
    return colors[status] || '#999';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==================== Notification Preview ====================
function previewNotification() {
    const title = document.getElementById('notification-title')?.value || '';
    const body = document.getElementById('notification-body')?.value || '';
    
    if (title || body) {
        showInfo(`Preview: ${title} - ${body}`, 3000);
    }
}

function sendNotification() {
    const title = document.getElementById('notification-title')?.value;
    const body = document.getElementById('notification-body')?.value;
    
    if (!title || !body) {
        showWarning('Please fill both title and body');
        return;
    }
    
    showConfirm('Send Notification', `Send notification: "${title}" to all users?`, () => {
        showLoading(true);
        
        fetch('/admin/send-notification', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ title, body })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccess('Notification sent successfully');
                document.getElementById('notification-title').value = '';
                document.getElementById('notification-body').value = '';
            } else {
                showError(data.error || 'Failed to send notification');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Failed to send notification');
        })
        .finally(() => showLoading(false));
    });
}

// Make functions globally available
window.deleteProduct = deleteProduct;
window.deleteAd = deleteAd;
window.toggleProductStatus = toggleProductStatus;
window.updateOrderStatus = updateOrderStatus;
window.viewOrderDetails = viewOrderDetails;
window.saveSettings = saveSettings;
window.exportData = exportData;
window.previewNotification = previewNotification;
window.sendNotification = sendNotification;
window.bulkDelete = bulkDelete;
window.bulkUpdateStatus = bulkUpdateStatus;
window.toggleSidebar = toggleSidebar;