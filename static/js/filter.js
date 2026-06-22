// ==================== ETHIOSADAT - FILTER JAVASCRIPT ====================
// Professional Product Filter with Native JavaScript
// Part 1 of 2: ProductFilter Class, Price Slider, Mobile Toggle

// ==================== Product Filter Class ====================
class ProductFilter {
    constructor(productsContainer, options = {}) {
        this.container = productsContainer;
        this.options = {
            persistFilters: true,
            storageKey: 'product_filters',
            animateResults: true,
            ...options
        };
        
        this.allProducts = options.products || [];
        this.filteredProducts = [];
        
        this.filters = {
            category: 'all',
            priceMin: 0,
            priceMax: 100000,
            search: '',
            sortBy: 'newest',
            rating: 0,
            inStockOnly: false
        };
        
        this.init();
    }
    
    init() {
        // Load saved filters from localStorage
        if (this.options.persistFilters) {
            this.loadSavedFilters();
        }
        
        this.bindEvents();
        this.applyFilters();
        this.updateUI();
    }
    
    bindEvents() {
        // Category filter
        const categoryBtns = document.querySelectorAll('.filter-category, .category-chip');
        categoryBtns.forEach(btn => {
            btn.removeEventListener('click', this.handleCategoryClick);
            btn.addEventListener('click', this.handleCategoryClick.bind(this, btn));
        });
        
        // Price range filter - native range slider
        const priceRange = document.getElementById('price-range');
        const priceMinInput = document.getElementById('price-min-input');
        const priceMaxInput = document.getElementById('price-max-input');
        
        if (priceRange) {
            priceRange.addEventListener('input', (e) => {
                const value = parseInt(e.target.value, 10);
                if (!isNaN(value)) {
                    this.filters.priceMax = value;
                    if (priceMaxInput) priceMaxInput.value = this.filters.priceMax;
                    this.updatePriceDisplay();
                    this.applyFilters();
                    this.saveFilters();
                }
            });
        }
        
        // Min price input
        if (priceMinInput) {
            priceMinInput.addEventListener('change', (e) => {
                let val = parseInt(e.target.value, 10) || 0;
                val = Math.max(0, Math.min(val, this.filters.priceMax));
                this.filters.priceMin = val;
                priceMinInput.value = this.filters.priceMin;
                this.updatePriceDisplay();
                this.applyFilters();
                this.saveFilters();
            });
        }
        
        // Max price input
        if (priceMaxInput) {
            priceMaxInput.addEventListener('change', (e) => {
                let val = parseInt(e.target.value, 10) || 100000;
                val = Math.min(100000, Math.max(val, this.filters.priceMin));
                this.filters.priceMax = val;
                priceMaxInput.value = this.filters.priceMax;
                if (priceRange) priceRange.value = this.filters.priceMax;
                this.updatePriceDisplay();
                this.applyFilters();
                this.saveFilters();
            });
        }
        
        // Search filter with debounce
        const searchInput = document.getElementById('filter-search');
        if (searchInput) {
            searchInput.value = this.filters.search;
            searchInput.addEventListener('input', this.debounce((e) => {
                this.filters.search = e.target.value.toLowerCase();
                this.applyFilters();
                this.saveFilters();
            }, 300));
        }
        
        // Sort filter
        const sortSelect = document.getElementById('sort-by');
        if (sortSelect) {
            sortSelect.value = this.filters.sortBy;
            sortSelect.addEventListener('change', (e) => {
                this.filters.sortBy = e.target.value;
                this.applyFilters();
                this.saveFilters();
            });
        }
        
        // Rating filter
        const ratingStars = document.querySelectorAll('.rating-filter');
        ratingStars.forEach(star => {
            star.removeEventListener('click', star._clickHandler);
            star._clickHandler = () => {
                const rating = parseInt(star.dataset.rating, 10);
                if (!isNaN(rating)) {
                    this.filters.rating = rating;
                    this.applyFilters();
                    this.saveFilters();
                    this.updateRatingUI();
                }
            };
            star.addEventListener('click', star._clickHandler);
        });
        
        // Stock filter
        const stockCheckbox = document.getElementById('stock-filter');
        if (stockCheckbox) {
            stockCheckbox.checked = this.filters.inStockOnly;
            stockCheckbox.addEventListener('change', (e) => {
                this.filters.inStockOnly = e.target.checked;
                this.applyFilters();
                this.saveFilters();
            });
        }
        
        // Clear filters button
        const clearBtn = document.getElementById('clear-filters');
        if (clearBtn) {
            clearBtn.removeEventListener('click', clearBtn._clickHandler);
            clearBtn._clickHandler = () => this.clearFilters();
            clearBtn.addEventListener('click', clearBtn._clickHandler);
        }
        
        // Apply filters button (for mobile)
        const applyBtn = document.getElementById('apply-filters');
        if (applyBtn) {
            applyBtn.removeEventListener('click', applyBtn._clickHandler);
            applyBtn._clickHandler = () => {
                this.applyFilters();
                this.closeFilterPanel();
            };
            applyBtn.addEventListener('click', applyBtn._clickHandler);
        }
    }
    
    handleCategoryClick(btn, event) {
        const category = btn.dataset.category || btn.getAttribute('data-category');
        if (category) {
            this.filters.category = category;
            this.updateActiveCategory(category);
            this.applyFilters();
            this.saveFilters();
        }
    }
    
    updateActiveCategory(category) {
        const categoryBtns = document.querySelectorAll('.filter-category, .category-chip');
        categoryBtns.forEach(btn => {
            const btnCategory = btn.dataset.category || btn.getAttribute('data-category');
            if (btnCategory === category) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }
    
    updatePriceDisplay() {
        const priceMinDisplay = document.getElementById('price-min');
        const priceMaxDisplay = document.getElementById('price-max');
        const priceRange = document.getElementById('price-range');
        
        if (priceMinDisplay) priceMinDisplay.textContent = this.formatPrice(this.filters.priceMin);
        if (priceMaxDisplay) priceMaxDisplay.textContent = this.formatPrice(this.filters.priceMax);
        if (priceRange) priceRange.value = this.filters.priceMax;
    }
    
    updateRatingUI() {
        const ratingStars = document.querySelectorAll('.rating-filter');
        ratingStars.forEach(star => {
            const rating = parseInt(star.dataset.rating, 10);
            if (!isNaN(rating) && rating <= this.filters.rating) {
                star.classList.add('active');
            } else {
                star.classList.remove('active');
            }
        });
    }
    
    applyFilters() {
        let products = [...this.allProducts];
        const originalCount = products.length;
        
        // Category filter
        if (this.filters.category !== 'all') {
            products = products.filter(p => 
                p.category === this.filters.category || 
                p.category_am === this.filters.category ||
                p.category_en === this.filters.category
            );
        }
        
        // Price filter
        products = products.filter(p => {
            const price = parseFloat(p.price);
            return !isNaN(price) && price >= this.filters.priceMin && price <= this.filters.priceMax;
        });
        
        // Search filter
        if (this.filters.search && this.filters.search.trim() !== '') {
            const searchTerm = this.filters.search.toLowerCase().trim();
            products = products.filter(p => {
                const nameAm = (p.name_am || '').toLowerCase();
                const nameEn = (p.name_en || p.name || '').toLowerCase();
                const descAm = (p.description_am || '').toLowerCase();
                const descEn = (p.description_en || p.description || '').toLowerCase();
                return nameAm.includes(searchTerm) || nameEn.includes(searchTerm) || 
                       descAm.includes(searchTerm) || descEn.includes(searchTerm);
            });
        }
        
        // Rating filter
        if (this.filters.rating > 0) {
            products = products.filter(p => (p.rating || 0) >= this.filters.rating);
        }
        
        // Stock filter
        if (this.filters.inStockOnly) {
            products = products.filter(p => (p.stock_quantity || p.stock || 0) > 0);
        }
        
        // Sort products
        products = this.sortProducts(products);
        
        this.filteredProducts = products;
        
        // Update counter
        this.updateCounter(products.length, originalCount);
        
        // Render products
        this.renderProducts(products);
        
        // Trigger event
        const event = new CustomEvent('filtersApplied', { 
            detail: { count: products.length, filters: this.filters }
        });
        document.dispatchEvent(event);
        
        return products;
    }
    
    sortProducts(products) {
        const sorted = [...products];
        
        switch(this.filters.sortBy) {
            case 'price_asc':
                sorted.sort((a, b) => parseFloat(a.price) - parseFloat(b.price));
                break;
            case 'price_desc':
                sorted.sort((a, b) => parseFloat(b.price) - parseFloat(a.price));
                break;
            case 'name_asc':
                sorted.sort((a, b) => {
                    const nameA = a.name_am || a.name_en || a.name || '';
                    const nameB = b.name_am || b.name_en || b.name || '';
                    return nameA.localeCompare(nameB);
                });
                break;
            case 'name_desc':
                sorted.sort((a, b) => {
                    const nameA = a.name_am || a.name_en || a.name || '';
                    const nameB = b.name_am || b.name_en || b.name || '';
                    return nameB.localeCompare(nameA);
                });
                break;
            case 'rating_desc':
                sorted.sort((a, b) => (b.rating || 0) - (a.rating || 0));
                break;
            case 'popularity':
                sorted.sort((a, b) => (b.sales_count || b.sold || 0) - (a.sales_count || a.sold || 0));
                break;
            default: // newest
                sorted.sort((a, b) => {
                    const idA = a.id || 0;
                    const idB = b.id || 0;
                    return idB - idA;
                });
        }
        
        return sorted;
    }
    
    renderProducts(products) {
        if (!this.container) return;
        
        if (this.options.renderCallback) {
            // Animate removal
            if (this.options.animateResults) {
                this.container.style.opacity = '0.5';
                setTimeout(() => {
                    this.options.renderCallback(products);
                    this.container.style.opacity = '1';
                }, 200);
            } else {
                this.options.renderCallback(products);
            }
        } else {
            this.container.innerHTML = this.generateProductHTML(products);
        }
        
        // Add animation to new products
        if (this.options.animateResults) {
            const newProducts = this.container.querySelectorAll('.product-card');
            newProducts.forEach((product, index) => {
                product.style.animation = `fadeInUp 0.3s ease forwards`;
                product.style.animationDelay = `${index * 0.03}s`;
            });
        }
        
        // Dispatch event after render
        const renderedEvent = new CustomEvent('productsRendered', { 
            detail: { count: products.length }
        });
        document.dispatchEvent(renderedEvent);
    }
    
    generateProductHTML(products) {
        if (!products || products.length === 0) {
            return `
                <div class="no-results" style="
                    text-align: center;
                    padding: 60px 20px;
                    grid-column: 1 / -1;
                ">
                    <div style="font-size: 48px; margin-bottom: 16px;">🔍</div>
                    <h3>No products found</h3>
                    <p>Try adjusting your filters or search term</p>
                    <button class="btn btn-primary" onclick="if(window.productFilter) productFilter.clearFilters()">Clear Filters</button>
                </div>
            `;
        }
        
        return products.map(product => `
            <div class="product-card" data-id="${product.id}">
                <div class="product-image">
                    <img src="${product.thumbnail || product.image || '/static/images/placeholder.png'}" alt="${product.name_am || product.name || 'Product'}" loading="lazy">
                    ${product.compare_price && product.compare_price > product.price ? `
                        <span class="discount-badge">-${Math.round((product.compare_price - product.price) / product.compare_price * 100)}%</span>
                    ` : ''}
                    ${(product.stock_quantity || product.stock || 0) === 0 ? '<span class="stock-badge out-of-stock">Out of Stock</span>' : ''}
                </div>
                <div class="product-info">
                    <h3 class="product-title">${this.escapeHtml(product.name_am || product.name || '')}</h3>
                    <div class="product-price">
                        ${this.formatPrice(product.price)}
                        ${product.compare_price ? `<span class="product-old-price">${this.formatPrice(product.compare_price)}</span>` : ''}
                    </div>
                    ${product.rating ? `
                        <div class="product-rating">
                            ${this.renderStars(product.rating)}
                            <span>(${product.reviews || 0})</span>
                        </div>
                    ` : ''}
                    <button class="btn-add-to-cart" onclick="if(window.addToCart) addToCart('${product.id}', 1, this)">
                        🛒 Add to Cart
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    renderStars(rating) {
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 >= 0.5;
        let stars = '';
        
        for (let i = 0; i < fullStars; i++) stars += '★';
        if (hasHalfStar) stars += '½';
        for (let i = stars.length; i < 5; i++) stars += '☆';
        
        return `<span class="stars" style="color: #ff9800;">${stars}</span>`;
    }
    
    updateCounter(filtered, total) {
        const counter = document.getElementById('filter-count');
        const resultCount = document.getElementById('result-count');
        
        if (counter) {
            counter.innerHTML = `${filtered} of ${total} products`;
            if (filtered === 0) {
                counter.classList.add('no-results-text');
            } else {
                counter.classList.remove('no-results-text');
            }
        }
        
        if (resultCount) {
            resultCount.textContent = `${filtered} product${filtered !== 1 ? 's' : ''} found`;
        }
    }
    
    updateUI() {
        this.updateActiveCategory(this.filters.category);
        this.updatePriceDisplay();
        this.updateRatingUI();
        
        const searchInput = document.getElementById('filter-search');
        if (searchInput) searchInput.value = this.filters.search;
        
        const sortSelect = document.getElementById('sort-by');
        if (sortSelect) sortSelect.value = this.filters.sortBy;
        
        const stockCheckbox = document.getElementById('stock-filter');
        if (stockCheckbox) stockCheckbox.checked = this.filters.inStockOnly;
    }
    
    clearFilters() {
        this.filters = {
            category: 'all',
            priceMin: 0,
            priceMax: 100000,
            search: '',
            sortBy: 'newest',
            rating: 0,
            inStockOnly: false
        };
        
        this.updateUI();
        this.applyFilters();
        this.saveFilters();
        
        if (window.showToast) {
            window.showToast('All filters cleared', 'info', 2000);
        }
    }
    
    saveFilters() {
        if (!this.options.persistFilters) return;
        
        try {
            localStorage.setItem(this.options.storageKey, JSON.stringify(this.filters));
        } catch (e) {
            console.error('Error saving filters:', e);
        }
    }
    
    loadSavedFilters() {
        try {
            const saved = localStorage.getItem(this.options.storageKey);
            if (saved) {
                const filters = JSON.parse(saved);
                this.filters = { ...this.filters, ...filters };
            }
        } catch (e) {
            console.error('Error loading filters:', e);
        }
    }
    
    formatPrice(price) {
        if (price === undefined || price === null) return '0 ETB';
        const num = parseFloat(price);
        if (isNaN(num)) return '0 ETB';
        return num.toLocaleString('en-US') + ' ETB';
    }
    
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
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
    
    closeFilterPanel() {
        const filterPanel = document.querySelector('.filters-sidebar');
        if (filterPanel) {
            filterPanel.classList.remove('open');
        }
        const overlay = document.querySelector('.filter-overlay');
        if (overlay) overlay.remove();
        document.body.style.overflow = '';
    }
    
    getCurrentFilters() {
        return { ...this.filters };
    }
    
    setProducts(products) {
        this.allProducts = [...products];
        this.applyFilters();
    }
}

// ==================== Price Slider (Native) ====================
function initPriceSlider() {
    const priceRange = document.getElementById('price-range');
    if (!priceRange) return;
    
    // Set attributes
    priceRange.min = 0;
    priceRange.max = 100000;
    priceRange.step = 500;
    
    // Initial value
    priceRange.value = 100000;
    
    // Update display
    const priceMaxDisplay = document.getElementById('price-max');
    if (priceMaxDisplay) {
        priceMaxDisplay.textContent = formatPrice(100000);
    }
}

function formatPrice(price) {
    const num = parseFloat(price);
    if (isNaN(num)) return '0 ETB';
    return num.toLocaleString('en-US') + ' ETB';
}

// ==================== Mobile Filter Toggle ====================
function toggleFilters() {
    const filters = document.querySelector('.filters-sidebar');
    const overlay = document.querySelector('.filter-overlay');
    
    if (filters) {
        filters.classList.toggle('open');
        
        // Create/remove overlay for mobile
        if (filters.classList.contains('open')) {
            if (!overlay) {
                const newOverlay = document.createElement('div');
                newOverlay.className = 'filter-overlay';
                newOverlay.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0,0,0,0.5);
                    z-index: 998;
                `;
                newOverlay.addEventListener('click', toggleFilters);
                document.body.appendChild(newOverlay);
            }
            document.body.style.overflow = 'hidden';
        } else {
            const existingOverlay = document.querySelector('.filter-overlay');
            if (existingOverlay) existingOverlay.remove();
            document.body.style.overflow = '';
        }
    }
}


// ==================== ETHIOSADAT - FILTER JAVASCRIPT ====================
// Professional Product Filter with Native JavaScript
// Part 2 of 2: InfiniteScroll, Quick Filters, Filter Summary, CSS Styles

// ==================== Infinite Scroll ====================
class InfiniteScroll {
    constructor(options = {}) {
        this.loading = false;
        this.page = 1;
        this.hasMore = true;
        this.container = options.container || null;
        this.loadCallback = options.loadCallback || null;
        this.threshold = options.threshold || 500;
        this.scrollHandler = null;
        this.init();
    }
    
    init() {
        if (!this.container || !this.loadCallback) {
            console.warn('InfiniteScroll: container or loadCallback not provided');
            return;
        }
        
        this.scrollHandler = this.debounce(() => {
            if (this.loading || !this.hasMore) return;
            
            const scrollPosition = window.innerHeight + window.scrollY;
            const threshold = document.body.scrollHeight - this.threshold;
            
            if (scrollPosition >= threshold) {
                this.loadMore();
            }
        }, 200);
        
        window.addEventListener('scroll', this.scrollHandler);
    }
    
    loadMore() {
        if (this.loading || !this.hasMore) return;
        
        this.loading = true;
        this.showLoader();
        
        this.loadCallback(this.page, (hasMore) => {
            this.hasMore = hasMore !== undefined ? hasMore : true;
            this.loading = false;
            this.hideLoader();
            
            if (hasMore !== false) {
                this.page++;
            }
        });
    }
    
    showLoader() {
        let loader = document.getElementById('infinite-loader');
        if (!loader && this.container) {
            loader = document.createElement('div');
            loader.id = 'infinite-loader';
            loader.className = 'infinite-loader';
            loader.style.cssText = `
                text-align: center;
                padding: 20px;
                grid-column: 1 / -1;
            `;
            loader.innerHTML = '<div class="spinner-sm"></div><p style="margin-top: 8px;">Loading more products...</p>';
            this.container.appendChild(loader);
        } else if (loader) {
            loader.style.display = 'block';
        }
    }
    
    hideLoader() {
        const loader = document.getElementById('infinite-loader');
        if (loader) {
            loader.style.display = 'none';
        }
    }
    
    reset() {
        this.page = 1;
        this.hasMore = true;
        this.loading = false;
        if (this.container) {
            const products = this.container.querySelectorAll('.product-card');
            products.forEach(p => {
                if (p.parentNode === this.container) {
                    p.remove();
                }
            });
        }
        this.hideLoader();
    }
    
    destroy() {
        if (this.scrollHandler) {
            window.removeEventListener('scroll', this.scrollHandler);
        }
        this.hideLoader();
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
}

// ==================== Quick Filter Bar ====================
function initQuickFilters(productFilterInstance) {
    const quickFilters = document.querySelectorAll('.quick-filter');
    quickFilters.forEach(filter => {
        filter.removeEventListener('click', filter._clickHandler);
        filter._clickHandler = function() {
            const filterType = this.dataset.filter;
            const filterValue = this.dataset.value;
            
            if (productFilterInstance) {
                if (filterType === 'category') {
                    productFilterInstance.filters.category = filterValue;
                    productFilterInstance.updateActiveCategory(filterValue);
                    productFilterInstance.applyFilters();
                    productFilterInstance.saveFilters();
                    
                    // Update active state on quick filters
                    quickFilters.forEach(qf => {
                        if (qf.dataset.filter === 'category') {
                            if (qf.dataset.value === filterValue) {
                                qf.classList.add('active');
                            } else {
                                qf.classList.remove('active');
                            }
                        }
                    });
                } else if (filterType === 'sort') {
                    productFilterInstance.filters.sortBy = filterValue;
                    const sortSelect = document.getElementById('sort-by');
                    if (sortSelect) sortSelect.value = filterValue;
                    productFilterInstance.applyFilters();
                    productFilterInstance.saveFilters();
                }
            }
        };
        filter.addEventListener('click', filter._clickHandler);
    });
}

// ==================== Filter Summary Tags ====================
function updateFilterSummary(productFilterInstance) {
    const summaryContainer = document.getElementById('filter-summary');
    if (!summaryContainer || !productFilterInstance) return;
    
    const filters = productFilterInstance.getCurrentFilters ? 
                    productFilterInstance.getCurrentFilters() : 
                    productFilterInstance.filters;
    
    const activeFilters = [];
    
    // Category filter
    if (filters.category && filters.category !== 'all') {
        const categoryName = getCategoryDisplayName(filters.category);
        activeFilters.push({ 
            type: 'category', 
            value: filters.category, 
            label: categoryName,
            displayText: `Category: ${categoryName}`
        });
    }
    
    // Price filter
    const maxPrice = 100000;
    if (filters.priceMin > 0 || filters.priceMax < maxPrice) {
        activeFilters.push({ 
            type: 'price', 
            value: `${filters.priceMin}-${filters.priceMax}`, 
            label: 'Price',
            displayText: `Price: ${formatPrice(filters.priceMin)} - ${formatPrice(filters.priceMax)}`
        });
    }
    
    // Search filter
    if (filters.search && filters.search.trim() !== '') {
        activeFilters.push({ 
            type: 'search', 
            value: filters.search, 
            label: 'Search',
            displayText: `Search: "${filters.search}"`
        });
    }
    
    // Rating filter
    if (filters.rating > 0) {
        activeFilters.push({ 
            type: 'rating', 
            value: filters.rating, 
            label: 'Rating',
            displayText: `Rating: ${filters.rating}+ stars`
        });
    }
    
    // Stock filter
    if (filters.inStockOnly) {
        activeFilters.push({ 
            type: 'stock', 
            value: 'in_stock', 
            label: 'Stock',
            displayText: 'In Stock Only'
        });
    }
    
    if (activeFilters.length === 0) {
        summaryContainer.innerHTML = '';
        return;
    }
    
    summaryContainer.innerHTML = `
        <div class="filter-summary" style="
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 16px;
            align-items: center;
        ">
            <span style="font-size: 13px; color: #666;">Active filters:</span>
            ${activeFilters.map(filter => `
                <span class="filter-tag" style="
                    background: #f0f0f0;
                    padding: 5px 12px;
                    border-radius: 20px;
                    font-size: 12px;
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                ">
                    ${filter.displayText}
                    <button onclick="removeFilter('${filter.type}')" style="
                        background: none;
                        border: none;
                        cursor: pointer;
                        font-size: 14px;
                        padding: 0 4px;
                        color: #666;
                    ">&times;</button>
                </span>
            `).join('')}
            <button onclick="if(window.productFilter) productFilter.clearFilters()" class="clear-all-btn" style="
                background: none;
                border: none;
                color: #1a73e8;
                cursor: pointer;
                font-size: 12px;
                font-weight: 500;
            ">Clear all</button>
        </div>
    `;
}

function getCategoryDisplayName(categoryValue) {
    const categoryMap = {
        'all': 'All',
        'sofa': 'ሶፋ',
        'bed': 'አልጋ',
        'mejlis': 'መጅሊስ',
        'curtain': 'መጋረጃ',
        'wardrobe': 'ቁምሳጥን',
        'other': 'ሌላ'
    };
    return categoryMap[categoryValue] || categoryValue;
}

function removeFilter(filterType) {
    if (!window.productFilter) return;
    
    const pf = window.productFilter;
    
    switch(filterType) {
        case 'category':
            pf.filters.category = 'all';
            pf.updateActiveCategory('all');
            break;
        case 'price':
            pf.filters.priceMin = 0;
            pf.filters.priceMax = 100000;
            pf.updatePriceDisplay();
            break;
        case 'search':
            pf.filters.search = '';
            const searchInput = document.getElementById('filter-search');
            if (searchInput) searchInput.value = '';
            break;
        case 'rating':
            pf.filters.rating = 0;
            pf.updateRatingUI();
            break;
        case 'stock':
            pf.filters.inStockOnly = false;
            const stockCheckbox = document.getElementById('stock-filter');
            if (stockCheckbox) stockCheckbox.checked = false;
            break;
        default:
            return;
    }
    
    pf.applyFilters();
    pf.saveFilters();
}

// ==================== CSS Styles ====================
(function addFilterStyles() {
    if (document.getElementById('filter-styles')) return;
    
    const filterStyles = document.createElement('style');
    filterStyles.id = 'filter-styles';
    filterStyles.textContent = `
        /* Filter Sidebar */
        .filters-sidebar {
            transition: transform 0.3s ease;
        }
        
        .filters-sidebar.open {
            transform: translateX(0) !important;
        }
        
        /* Product Card Animation */
        .product-card {
            animation: fadeInUp 0.3s ease forwards;
            opacity: 0;
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
        
        /* Rating Filter Stars */
        .rating-filter {
            cursor: pointer;
            transition: transform 0.2s;
            font-size: 20px;
        }
        
        .rating-filter:hover {
            transform: scale(1.1);
        }
        
        .rating-filter.active {
            color: #ff9800;
        }
        
        /* Price Range Slider */
        #price-range {
            width: 100%;
            height: 4px;
            -webkit-appearance: none;
            background: #e0e0e0;
            border-radius: 5px;
            outline: none;
        }
        
        #price-range::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 16px;
            height: 16px;
            background: #1a73e8;
            border-radius: 50%;
            cursor: pointer;
            border: none;
        }
        
        #price-range::-webkit-slider-thumb:hover {
            transform: scale(1.2);
        }
        
        /* Filter Summary */
        .filter-summary {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .filter-tag {
            background: #e9ecef;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
        }
        
        /* No Results */
        .no-results {
            text-align: center;
            padding: 60px 20px;
            background: #f8f9fa;
            border-radius: 12px;
        }
        
        /* Infinite Loader */
        .infinite-loader {
            text-align: center;
            padding: 30px;
        }
        
        .spinner-sm {
            display: inline-block;
            width: 30px;
            height: 30px;
            border: 3px solid #f0f0f0;
            border-top-color: #1a73e8;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Mobile Filter Sidebar */
        @media (max-width: 768px) {
            .filters-sidebar {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: var(--bg-white, white);
                z-index: 999;
                transform: translateX(-100%);
                transition: transform 0.3s ease;
                overflow-y: auto;
                padding: 20px;
                max-width: 85%;
            }
            
            .filters-sidebar.open {
                transform: translateX(0);
            }
            
            .filter-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.5);
                z-index: 998;
            }
        }
        
        /* Tablet Filters */
        @media (min-width: 769px) and (max-width: 1024px) {
            .filters-sidebar {
                width: 280px;
            }
        }
        
        /* Quick Filter Chips */
        .quick-filter {
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .quick-filter.active {
            background: #1a73e8;
            color: white;
        }
        
        /* Reduced Motion Preference */
        @media (prefers-reduced-motion: reduce) {
            .product-card,
            .filters-sidebar,
            .filter-tag {
                animation: none;
                transition: none;
            }
            
            .product-card {
                opacity: 1;
            }
        }
        
        /* Dark Mode Support */
        @media (prefers-color-scheme: dark) {
            .filter-summary {
                background: #1a1a2e;
            }
            
            .filter-tag {
                background: #2a2a3e;
                color: #eee;
            }
            
            .filter-tag button {
                color: #aaa;
            }
            
            .no-results {
                background: #16213e;
            }
            
            #price-range {
                background: #2a2a3e;
            }
        }
    `;
    document.head.appendChild(filterStyles);
})();

// ==================== Initialize All Filter Components ====================
function initFiltersContainer() {
    const productsGrid = document.querySelector('.products-grid, .products-container');
    if (!productsGrid) {
        console.log('Filter container not found');
        return null;
    }
    
    // Get initial products from data attribute or global variable
    let initialProducts = [];
    if (window.initialProducts) {
        initialProducts = window.initialProducts;
    } else if (productsGrid.dataset.products) {
        try {
            initialProducts = JSON.parse(productsGrid.dataset.products);
        } catch (e) {
            console.error('Error parsing products data:', e);
        }
    }
    
    // Create product filter instance
    const productFilter = new ProductFilter(productsGrid, {
        products: initialProducts,
        persistFilters: true,
        animateResults: true,
        renderCallback: null
    });
    
    // Initialize quick filters
    initQuickFilters(productFilter);
    
    // Initialize price slider
    initPriceSlider();
    
    // Store globally
    window.productFilter = productFilter;
    
    // Listen for filter events to update summary
    document.addEventListener('filtersApplied', () => {
        updateFilterSummary(productFilter);
    });
    
    // Initial summary update
    updateFilterSummary(productFilter);
    
    return productFilter;
}

// ==================== Load More Products (AJAX) ====================
function loadMoreProducts(page, callback) {
    const category = window.productFilter?.filters?.category || 'all';
    const search = window.productFilter?.filters?.search || '';
    const sortBy = window.productFilter?.filters?.sortBy || 'newest';
    
    fetch(`/api/products?page=${page}&category=${encodeURIComponent(category)}&search=${encodeURIComponent(search)}&sort=${sortBy}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.products && data.products.length > 0) {
                const container = document.querySelector('.products-grid, .products-container');
                if (container) {
                    data.products.forEach(product => {
                        const productHtml = generateProductCardHTML(product);
                        container.insertAdjacentHTML('beforeend', productHtml);
                    });
                }
                callback(data.has_more !== false);
            } else {
                callback(false);
            }
        })
        .catch(error => {
            console.error('Error loading more products:', error);
            callback(false);
        });
}

function generateProductCardHTML(product) {
    const discount = product.compare_price && product.compare_price > product.price 
        ? Math.round((product.compare_price - product.price) / product.compare_price * 100) 
        : null;
    
    return `
        <div class="product-card" data-id="${product.id}">
            <div class="product-image">
                <img src="${product.thumbnail || product.image || '/static/images/placeholder.png'}" alt="${product.name_am || product.name || 'Product'}" loading="lazy">
                ${discount ? `<span class="discount-badge">-${discount}%</span>` : ''}
                ${(product.stock_quantity || 0) === 0 ? '<span class="stock-badge out-of-stock">Out of Stock</span>' : ''}
            </div>
            <div class="product-info">
                <h3 class="product-title">${escapeHtml(product.name_am || product.name || '')}</h3>
                <div class="product-price">
                    ${formatPrice(product.price)}
                    ${product.compare_price ? `<span class="product-old-price">${formatPrice(product.compare_price)}</span>` : ''}
                </div>
                <button class="btn-add-to-cart" onclick="if(window.addToCart) addToCart('${product.id}', 1, this)">
                    🛒 Add to Cart
                </button>
            </div>
        </div>
    `;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==================== URL Filter Sync (Optional) ====================
function syncFiltersWithURL() {
    const urlParams = new URLSearchParams(window.location.search);
    
    if (window.productFilter) {
        const category = urlParams.get('category');
        if (category) {
            window.productFilter.filters.category = category;
        }
        
        const search = urlParams.get('search');
        if (search) {
            window.productFilter.filters.search = search;
            const searchInput = document.getElementById('filter-search');
            if (searchInput) searchInput.value = search;
        }
        
        const sort = urlParams.get('sort');
        if (sort) {
            window.productFilter.filters.sortBy = sort;
            const sortSelect = document.getElementById('sort-by');
            if (sortSelect) sortSelect.value = sort;
        }
        
        const minPrice = urlParams.get('min_price');
        if (minPrice) {
            window.productFilter.filters.priceMin = parseInt(minPrice, 10) || 0;
        }
        
        const maxPrice = urlParams.get('max_price');
        if (maxPrice) {
            window.productFilter.filters.priceMax = parseInt(maxPrice, 10) || 100000;
        }
        
        window.productFilter.applyFilters();
    }
}

// ==================== DOM Ready Initialization ====================
document.addEventListener('DOMContentLoaded', function() {
    // Initialize filters
    const filterInstance = initFiltersContainer();
    
    // Sync with URL if needed
    if (window.location.search) {
        syncFiltersWithURL();
    }
    
    // Initialize infinite scroll if enabled
    const infiniteScrollContainer = document.querySelector('.infinite-scroll-container');
    if (infiniteScrollContainer && window.enableInfiniteScroll) {
        window.infiniteScroll = new InfiniteScroll({
            container: infiniteScrollContainer,
            loadCallback: loadMoreProducts,
            threshold: 500
        });
    }
});

// ==================== Exports ====================
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        ProductFilter,
        InfiniteScroll,
        initFiltersContainer,
        initQuickFilters,
        updateFilterSummary,
        removeFilter,
        toggleFilters,
        loadMoreProducts,
        syncFiltersWithURL
    };
}

// Make globally available
window.InfiniteScroll = InfiniteScroll;
window.initQuickFilters = initQuickFilters;
window.updateFilterSummary = updateFilterSummary;
window.removeFilter = removeFilter;
window.loadMoreProducts = loadMoreProducts;
window.syncFiltersWithURL = syncFiltersWithURL;
window.initFiltersContainer = initFiltersContainer;
// ==================== Export for Part 1 ====================
window.ProductFilter = ProductFilter;
window.initPriceSlider = initPriceSlider;
window.toggleFilters = toggleFilters;
window.formatPrice = formatPrice;
