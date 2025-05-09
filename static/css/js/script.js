/**
 * Enhanced Expense Tracker - Main JavaScript
 * A comprehensive JavaScript file for the expense tracker application
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeTooltips();
    initializePopovers();
    initializeAlerts();
    initializeDateInputs();
    initializeDeleteConfirmations();
    initializeCharts();
    initializeFormValidation();
    initializeCurrencyFormatting();
    initializeDarkMode();
    initializeNotifications();
    initializeRecurringExpenses();
    initializeCurrencyConverter();
    initializeExportOptions();
    initializeDataTables();
    initializePrintButtons();
    initializeGoalContributions();
    initializeExpenseAnalytics();
    initializeSearchFilters();
    initializeResponsiveNavigation();
    initializeAnimations();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            boundary: document.body
        });
    });
}

/**
 * Initialize Bootstrap popovers
 */
function initializePopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl, {
            html: true,
            sanitize: false
        });
    });
}

/**
 * Initialize auto-dismissing alerts
 */
function initializeAlerts() {
    // Auto-dismiss flash messages after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            if (alert && typeof bootstrap !== 'undefined') {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } else {
                // Fallback if bootstrap is not available
                alert.style.display = 'none';
            }
        });
    }, 5000);

    // Add click event to close buttons
    const closeButtons = document.querySelectorAll('.alert .btn-close');
    closeButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const alert = this.closest('.alert');
            if (alert && typeof bootstrap !== 'undefined') {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } else {
                // Fallback if bootstrap is not available
                alert.style.display = 'none';
            }
        });
    });
}

/**
 * Initialize date inputs with default values and date pickers
 */
function initializeDateInputs() {
    // Set default date to today for date inputs if not already set
    const dateInputs = document.querySelectorAll('input[type="date"]');
    const today = new Date().toISOString().split('T')[0];

    dateInputs.forEach(function(input) {
        if (!input.value) {
            input.value = today;
        }
    });

    // Initialize date range pickers if available
    const dateRangePickers = document.querySelectorAll('.date-range-picker');
    if (dateRangePickers.length > 0) {
        dateRangePickers.forEach(function(picker) {
            const startDate = picker.querySelector('.start-date');
            const endDate = picker.querySelector('.end-date');
            
            if (startDate && endDate) {
                // Set default start date to first day of current month if not set
                if (!startDate.value) {
                    const firstDay = new Date(new Date().getFullYear(), new Date().getMonth(), 1);
                    startDate.value = firstDay.toISOString().split('T')[0];
                }
                
                // Set default end date to today if not set
                if (!endDate.value) {
                    endDate.value = today;
                }
                
                // Ensure end date is not before start date
                startDate.addEventListener('change', function() {
                    if (endDate.value && startDate.value > endDate.value) {
                        endDate.value = startDate.value;
                    }
                    
                    // Update any associated filters
                    const filterForm = this.closest('form');
                    if (filterForm && filterForm.classList.contains('auto-submit')) {
                        filterForm.submit();
                    }
                });
                
                endDate.addEventListener('change', function() {
                    if (startDate.value && endDate.value < startDate.value) {
                        startDate.value = endDate.value;
                    }
                    
                    // Update any associated filters
                    const filterForm = this.closest('form');
                    if (filterForm && filterForm.classList.contains('auto-submit')) {
                        filterForm.submit();
                    }
                });
            }
        });
    }
}

/**
 * Initialize delete confirmations
 */
function initializeDeleteConfirmations() {
    // Add confirmation for delete actions
    const deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            const message = this.dataset.confirm || 'Are you sure you want to delete this item?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
}

/**
 * Initialize charts for data visualization
 */
function initializeCharts() {
    // Check if Chart.js is available
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js is not loaded. Charts will not be initialized.');
        return;
    }

    // Set default Chart.js options
    Chart.defaults.font.family = "'Nunito', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif";
    Chart.defaults.color = '#858796';
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    Chart.defaults.plugins.tooltip.bodyFont = {
        family: "'Nunito', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
        size: 14
    };
    Chart.defaults.plugins.tooltip.titleFont = {
        family: "'Nunito', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
        size: 14,
        weight: 'bold'
    };
    Chart.defaults.plugins.tooltip.padding = 12;
    Chart.defaults.plugins.tooltip.cornerRadius = 4;

    // Initialize expense category chart
    const expenseChartEl = document.getElementById('expenseChart');
    if (expenseChartEl) {
        const ctx = expenseChartEl.getContext('2d');
        
        // Get data from the element's data attributes or from global variables
        let labels = [];
        let data = [];
        
        try {
            labels = JSON.parse(expenseChartEl.dataset.labels || '[]');
            data = JSON.parse(expenseChartEl.dataset.values || '[]');
        } catch (e) {
            console.error('Error parsing chart data:', e);
            
            // Try to get data from global variables as fallback
            if (typeof categoryNames !== 'undefined' && typeof categoryData !== 'undefined') {
                labels = categoryNames;
                data = categoryData;
            }
        }
        
        if (labels.length > 0 && data.length > 0) {
            // Generate colors for each category
            const colors = generateChartColors(labels.length);
            
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: colors,
                        hoverBackgroundColor: colors.map(color => adjustColorBrightness(color, -15)),
                        hoverBorderColor: "rgba(234, 236, 244, 1)",
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                padding: 20,
                                usePointStyle: true,
                                pointStyle: 'circle'
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    let label = context.label || '';
                                    let value = context.raw || 0;
                                    let total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    let percentage = Math.round((value / total) * 100);
                                    
                                    // Format currency based on locale
                                    const formattedValue = formatCurrency(value);
                                    
                                    return `${label}: ${formattedValue} (${percentage}%)`;
                                }
                            }
                        }
                    },
                    cutout: '70%',
                    animation: {
                        animateScale: true,
                        animateRotate: true,
                        duration: 1000,
                        easing: 'easeOutQuart'
                    }
                }
            });
            
            // Add center text if container exists
            const centerTextContainer = document.getElementById('expenseChartCenterText');
            if (centerTextContainer) {
                const total = data.reduce((a, b) => a + b, 0);
                centerTextContainer.innerHTML = `
                    <div class="chart-center-text">
                        <div class="chart-center-value">${formatCurrency(total)}</div>
                        <div class="chart-center-label">Total Expenses</div>
                    </div>
                `;
            }
        }
    }

    // Initialize monthly comparison chart
    const monthlyChartEl = document.getElementById('monthlyChart');
    if (monthlyChartEl) {
        const ctx = monthlyChartEl.getContext('2d');
        
        // Get data from the element's data attributes or from global variables
        let months = [];
        let expenseData = [];
        let incomeData = [];
        
        try {
            months = JSON.parse(monthlyChartEl.dataset.months || '[]');
            expenseData = JSON.parse(monthlyChartEl.dataset.expenses || '[]');
            incomeData = JSON.parse(monthlyChartEl.dataset.incomes || '[]');
        } catch (e) {
            console.error('Error parsing chart data:', e);
            
            // Try to get data from global variables as fallback
            if (typeof monthLabels !== 'undefined' && typeof monthlyExpenses !== 'undefined' && typeof monthlyIncomes !== 'undefined') {
                months = monthLabels;
                expenseData = monthlyExpenses;
                incomeData = monthlyIncomes;
            }
        }
        
        if (months.length > 0) {
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: months,
                    datasets: [
                        {
                            label: 'Income',
                            backgroundColor: 'rgba(28, 200, 138, 0.7)',
                            borderColor: 'rgba(28, 200, 138, 1)',
                            borderWidth: 1,
                            data: incomeData
                        },
                        {
                            label: 'Expenses',
                            backgroundColor: 'rgba(231, 74, 59, 0.7)',
                            borderColor: 'rgba(231, 74, 59, 1)',
                            borderWidth: 1,
                            data: expenseData
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            grid: {
                                display: false
                            }
                        },
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return formatCurrency(value, true);
                                }
                            }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    let label = context.dataset.label || '';
                                    let value = context.raw || 0;
                                    return `${label}: ${formatCurrency(value)}`;
                                }
                            }
                        }
                    },
                    animation: {
                        duration: 1000,
                        easing: 'easeOutQuart'
                    }
                }
            });
        }
    }

    // Initialize daily expense trend chart
    const dailyTrendChartEl = document.getElementById('dailyTrendChart');
    if (dailyTrendChartEl) {
        const ctx = dailyTrendChartEl.getContext('2d');
        
        // Get data from the element's data attributes or from global variables
        let dates = [];
        let amounts = [];
        
        try {
            dates = JSON.parse(dailyTrendChartEl.dataset.dates || '[]');
            amounts = JSON.parse(dailyTrendChartEl.dataset.amounts || '[]');
        } catch (e) {
            console.error('Error parsing chart data:', e);
            
            // Try to get data from global variables as fallback
            if (typeof dailyDates !== 'undefined' && typeof dailyAmounts !== 'undefined') {
                dates = dailyDates;
                amounts = dailyAmounts;
            }
        }
        
        if (dates.length > 0) {
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: dates,
                    datasets: [{
                        label: 'Daily Expenses',
                        data: amounts,
                        backgroundColor: 'rgba(78, 115, 223, 0.05)',
                        borderColor: 'rgba(78, 115, 223, 1)',
                        pointBackgroundColor: 'rgba(78, 115, 223, 1)',
                        pointBorderColor: 'rgba(78, 115, 223, 1)',
                        pointHoverBackgroundColor: 'rgba(78, 115, 223, 0.8)',
                        pointHoverBorderColor: 'rgba(78, 115, 223, 0.8)',
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        tension: 0.3,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                maxTicksLimit: 7
                            }
                        },
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return formatCurrency(value, true);
                                }
                            }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    let label = context.dataset.label || '';
                                    let value = context.raw || 0;
                                    return `${label}: ${formatCurrency(value)}`;
                                }
                            }
                        }
                    },
                    animation: {
                        duration: 1000,
                        easing: 'easeOutQuart'
                    }
                }
            });
        }
    }

    // Initialize budget progress chart
    const budgetChartEls = document.querySelectorAll('.budget-chart');
    budgetChartEls.forEach(function(chartEl) {
        const ctx = chartEl.getContext('2d');
        
        // Get data from the element's data attributes
        const categoryName = chartEl.dataset.category || 'Category';
        const budgetAmount = parseFloat(chartEl.dataset.budget || 0);
        const spentAmount = parseFloat(chartEl.dataset.spent || 0);
        const remainingAmount = budgetAmount - spentAmount;
        
        // Calculate percentage
        const percentage = budgetAmount > 0 ? (spentAmount / budgetAmount) * 100 : 0;
        
        // Determine color based on percentage
        let color = '#1cc88a'; // Green for < 80%
        if (percentage > 100) {
            color = '#e74a3b'; // Red for > 100%
        } else if (percentage > 80) {
            color = '#f6c23e'; // Yellow for 80-100%
        }
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Spent', 'Remaining'],
                datasets: [{
                    data: [spentAmount, Math.max(0, remainingAmount)],
                    backgroundColor: [color, '#eaecf4'],
                    hoverBackgroundColor: [adjustColorBrightness(color, -15), '#d4d6e0'],
                    hoverBorderColor: "rgba(234, 236, 244, 1)",
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '75%',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.label || '';
                                let value = context.raw || 0;
                                return `${label}: ${formatCurrency(value)}`;
                            }
                        }
                    }
                },
                animation: {
                    animateScale: true,
                    animateRotate: true,
                    duration: 1000,
                    easing: 'easeOutQuart'
                }
            }
        });
        
        // Add center text if container exists
        const centerTextContainer = chartEl.parentElement.querySelector('.budget-chart-center');
        if (centerTextContainer) {
            centerTextContainer.innerHTML = `
                <div class="chart-center-text">
                    <div class="chart-center-value">${Math.round(percentage)}%</div>
                    <div class="chart-center-label">of budget</div>
                </div>
            `;
        }
    });
}

/**
 * Generate an array of colors for charts
 * @param {number} count - Number of colors needed
 * @returns {Array} - Array of color strings
 */
function generateChartColors(count) {
    // Predefined colors for up to 10 categories
    const baseColors = [
        '#4e73df', // Primary blue
        '#1cc88a', // Success green
        '#36b9cc', // Info teal
        '#f6c23e', // Warning yellow
        '#e74a3b', // Danger red
        '#6f42c1', // Purple
        '#fd7e14', // Orange
        '#20c997', // Teal
        '#6c757d', // Gray
        '#5a5c69'  // Dark gray
    ];
    
    // If we need more colors than predefined, generate them
    if (count <= baseColors.length) {
        return baseColors.slice(0, count);
    } else {
        const colors = [...baseColors];
        
        // Generate additional colors with slight variations
        for (let i = baseColors.length; i < count; i++) {
            const baseColor = baseColors[i % baseColors.length];
            const variation = (i - baseColors.length + 1) * 20;
            colors.push(adjustColorBrightness(baseColor, variation));
        }
        
        return colors;
    }
}

/**
 * Adjust the brightness of a color
 * @param {string} color - Hex color code
 * @param {number} percent - Percentage to adjust (-100 to 100)
 * @returns {string} - Adjusted hex color
 */
function adjustColorBrightness(color, percent) {
    let R = parseInt(color.substring(1, 3), 16);
    let G = parseInt(color.substring(3, 5), 16);
    let B = parseInt(color.substring(5, 7), 16);

    R = parseInt(R * (100 + percent) / 100);
    G = parseInt(G * (100 + percent) / 100);
    B = parseInt(B * (100 + percent) / 100);

    R = (R < 255) ? R : 255;
    G = (G < 255) ? G : 255;
    B = (B < 255) ? B : 255;

    R = Math.max(0, R);
    G = Math.max(0, G);
    B = Math.max(0, B);

    const RR = ((R.toString(16).length === 1) ? "0" + R.toString(16) : R.toString(16));
    const GG = ((G.toString(16).length === 1) ? "0" + G.toString(16) : G.toString(16));
    const BB = ((B.toString(16).length === 1) ? "0" + B.toString(16) : B.toString(16));

    return "#" + RR + GG + BB;
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    // Get all forms that need validation
    const forms = document.querySelectorAll('.needs-validation');
    
    // Loop over them and prevent submission if invalid
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
        
        // Add custom validation for specific fields
        const amountInputs = form.querySelectorAll('input[type="number"][min]');
        amountInputs.forEach(function(input) {
            input.addEventListener('input', function() {
                const min = parseFloat(this.getAttribute('min'));
                const value = parseFloat(this.value);
                
                if (value < min) {
                    this.setCustomValidity(`Value must be at least ${min}`);
                } else {
                    this.setCustomValidity('');
                }
            });
        });
        
        // Add validation for date range inputs
        const startDateInputs = form.querySelectorAll('.start-date');
        const endDateInputs = form.querySelectorAll('.end-date');
        
        startDateInputs.forEach(function(startInput, index) {
            const endInput = endDateInputs[index];
            
            if (startInput && endInput) {
                startInput.addEventListener('change', function() {
                    if (endInput.value && startInput.value > endInput.value) {
                        startInput.setCustomValidity('Start date cannot be after end date');
                    } else {
                        startInput.setCustomValidity('');
                    }
                });
                
                endInput.addEventListener('change', function() {
                    if (startInput.value && endInput.value < startInput.value) {
                        endInput.setCustomValidity('End date cannot be before start date');
                    } else {
                        endInput.setCustomValidity('');
                    }
                });
            }
        });
    });
}

/**
 * Initialize currency formatting
 */
function initializeCurrencyFormatting() {
    // Format all elements with the currency-format class
    const currencyElements = document.querySelectorAll('.currency-format');
    currencyElements.forEach(function(element) {
        const value = parseFloat(element.textContent);
        if (!isNaN(value)) {
            element.textContent = formatCurrency(value);
        }
    });
    
    // Format all elements with the currency-compact class (shorter format)
    const compactElements = document.querySelectorAll('.currency-compact');
    compactElements.forEach(function(element) {
        const value = parseFloat(element.textContent);
        if (!isNaN(value)) {
            element.textContent = formatCurrency(value, true);
        }
    });
    
    // Add input event listeners to currency input fields
    const currencyInputs = document.querySelectorAll('.currency-input');
    currencyInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            const value = parseFloat(this.value);
            if (!isNaN(value)) {
                // Store the raw value as a data attribute
                this.dataset.rawValue = value;
                
                // Format the displayed value
                this.value = formatCurrency(value, false, false);
            }
        });
        
        input.addEventListener('focus', function() {
            // Restore the raw value for editing
            if (this.dataset.rawValue) {
                this.value = this.dataset.rawValue;
            }
        });
    });
}

/**
 * Format a number as currency
 * @param {number} value - The value to format
 * @param {boolean} compact - Whether to use compact notation for large numbers
 * @param {boolean} symbol - Whether to include the currency symbol
 * @returns {string} - Formatted currency string
 */
function formatCurrency(value, compact = false, symbol = true) {
    // Get currency code and symbol from data attribute or default to USD
    const currencyCode = document.documentElement.dataset.currencyCode || 'USD';
    const currencySymbol = document.documentElement.dataset.currencySymbol || '$';
    
    // Format options
    const options = {
        style: symbol ? 'currency' : 'decimal',
        currency: currencyCode,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    };
    
    // Add compact notation for large numbers if requested
    if (compact) {
        options.notation = 'compact';
    }
    
    try {
        // Try to use Intl.NumberFormat for formatting
        return new Intl.NumberFormat(navigator.language, options).format(value);
    } catch (e) {
        // Fallback to basic formatting
        const formatted = value.toFixed(2);
        return symbol ? `${currencySymbol}${formatted}` : formatted;
    }
}

/**
 * Initialize dark mode functionality
 */
function initializeDarkMode() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        // Check for saved dark mode preference or system preference
        const savedDarkMode = localStorage.getItem('darkMode');
        const prefersDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        // Apply dark mode if saved preference exists or system prefers it
        if (savedDarkMode === 'true' || (savedDarkMode === null && prefersDarkMode)) {
            document.documentElement.classList.add('dark-mode');
            darkModeToggle.checked = true;
        }
        
        // Toggle dark mode on change
        darkModeToggle.addEventListener('change', function() {
            if (this.checked) {
                document.documentElement.classList.add('dark-mode');
                localStorage.setItem('darkMode', 'true');
            } else {
                document.documentElement.classList.remove('dark-mode');
                localStorage.setItem('darkMode', 'false');
            }
            
            // Redraw charts if they exist
            if (typeof Chart !== 'undefined') {
                Chart.instances.forEach(chart => {
                    chart.update();
                });
            }
        });
    }
    
    // Add dark mode toggle button if it doesn't exist
    const darkModeButton = document.querySelector('.dark-mode-toggle');
    if (!darkModeToggle && !darkModeButton) {
        const navbarNav = document.querySelector('.navbar-nav');
        if (navbarNav) {
            const darkModeItem = document.createElement('li');
            darkModeItem.className = 'nav-item';
            
            const isDarkMode = document.documentElement.classList.contains('dark-mode');
            
            darkModeItem.innerHTML = `
                <a class="nav-link dark-mode-toggle" href="#" title="Toggle Dark Mode">
                    <i class="fas ${isDarkMode ? 'fa-sun' : 'fa-moon'}"></i>
                </a>
            `;
            
            navbarNav.appendChild(darkModeItem);
            
            // Add event listener to the new button
            const newDarkModeButton = darkModeItem.querySelector('.dark-mode-toggle');
            newDarkModeButton.addEventListener('click', function(e) {
                e.preventDefault();
                
                const isDarkMode = document.documentElement.classList.contains('dark-mode');
                
                if (isDarkMode) {
                    document.documentElement.classList.remove('dark-mode');
                    localStorage.setItem('darkMode', 'false');
                    this.querySelector('i').className = 'fas fa-moon';
                } else {
                    document.documentElement.classList.add('dark-mode');
                    localStorage.setItem('darkMode', 'true');
                    this.querySelector('i').className = 'fas fa-sun';
                }
                
                // Redraw charts if they exist
                if (typeof Chart !== 'undefined') {
                    Chart.instances.forEach(chart => {
                        chart.update();
                    });
                }
            });
        }
    }
}

/**
 * Initialize notifications system
 */
function initializeNotifications() {
    // Check for notification elements
    const notificationBadge = document.querySelector('.notification-badge');
    const notificationDropdown = document.querySelector('.notification-dropdown');
    
    if (notificationBadge && notificationDropdown) {
        // Mark notifications as read when dropdown is opened
        notificationDropdown.addEventListener('show.bs.dropdown', function() {
            const unreadNotifications = document.querySelectorAll('.notification-item.unread');
            if (unreadNotifications.length > 0) {
                // Update UI to mark as read
                unreadNotifications.forEach(function(notification) {
                    notification.classList.remove('unread');
                });
                
                // Update the badge count
                const badge = notificationBadge.querySelector('.badge');
                if (badge) {
                    badge.textContent = '0';
                    badge.classList.add('d-none');
                }
                
                // Send AJAX request to mark notifications as read
                const userId = notificationBadge.dataset.userId;
                if (userId) {
                    fetch('/mark_all_notifications_read', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        body: JSON.stringify({ user_id: userId })
                    })
                    .catch(error => console.error('Error marking notifications as read:', error));
                }
            }
        });
    }
    
    // Initialize toast notifications
    const toastContainer = document.querySelector('.toast-container');
    if (toastContainer) {
        const toasts = toastContainer.querySelectorAll('.toast');
        toasts.forEach(function(toast) {
            new bootstrap.Toast(toast, {
                autohide: true,
                delay: 5000
            }).show();
        });
    }
    
    // Create notification panel if it doesn't exist
    if (!document.querySelector('.notification-panel')) {
        const panel = document.createElement('div');
        panel.className = 'notification-panel';
        document.body.appendChild(panel);
    }
}

/**
 * Show a notification toast
 * @param {string} title - Notification title
 * @param {string} message - Notification message
 * @param {string} type - Notification type (info, success, warning, danger)
 * @param {number} duration - Duration in milliseconds (0 for no auto-hide)
 */
function showNotification(title, message, type = 'info', duration = 5000) {
    const panel = document.querySelector('.notification-panel');
    if (!panel) return;
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification-item notification-${type}`;
    notification.innerHTML = `
        <div class="notification-header">
            <div class="notification-title">${title}</div>
            <div class="notification-close">
                <i class="fas fa-times"></i>
            </div>
        </div>
        <div class="notification-body">
            ${message}
        </div>
    `;
    
    // Add close button functionality
    const closeButton = notification.querySelector('.notification-close');
    closeButton.addEventListener('click', function() {
        notification.remove();
    });
    
    // Add to notification panel
    panel.appendChild(notification);
    
    // Auto-remove after duration (if not 0)
    if (duration > 0) {
        setTimeout(function() {
            notification.remove();
        }, duration);
    }
    
    // Add animation
    setTimeout(function() {
        notification.classList.add('show');
    }, 10);
}

/**
 * Initialize recurring expenses functionality
 */
function initializeRecurringExpenses() {
    // Handle frequency selection in recurring expense forms
    const frequencySelect = document.getElementById('frequency');
    const endDateGroup = document.getElementById('endDateGroup');
    
    if (frequencySelect && endDateGroup) {
        frequencySelect.addEventListener('change', function() {
            // Show end date field for longer frequencies
            const value = this.value;
            if (value === 'monthly' || value === 'quarterly' || value === 'yearly') {
                endDateGroup.classList.remove('d-none');
            } else {
                endDateGroup.classList.add('d-none');
            }
        });
    }
    
    // Handle generate recurring expenses button
    const generateButton = document.getElementById('generateRecurringExpenses');
    if (generateButton) {
        generateButton.addEventListener('click', function() {
            // Show loading spinner
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
            this.disabled = true;
            
            // Submit the form or follow the link
            const form = this.closest('form');
            if (form) {
                form.submit();
            } else {
                window.location.href = this.getAttribute('href');
            }
        });
    }
}

/**
 * Initialize currency converter functionality
 */
function initializeCurrencyConverter() {
    const converter = document.querySelector('.currency-converter');
    if (!converter) return;
    
    const amountInput = converter.querySelector('#converterAmount');
    const fromSelect = converter.querySelector('#converterFrom');
    const toSelect = converter.querySelector('#converterTo');
    const resultElement = converter.querySelector('.currency-converter-result');
    const convertButton = converter.querySelector('#convertButton');
    
    if (amountInput && fromSelect && toSelect && resultElement && convertButton) {
        convertButton.addEventListener('click', function() {
            const amount = parseFloat(amountInput.value);
            if (isNaN(amount)) {
                resultElement.textContent = 'Please enter a valid amount';
                return;
            }
            
            const fromCurrency = fromSelect.value;
            const toCurrency = toSelect.value;
            
            // Show loading state
            resultElement.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Converting...';
            
            // Make API request to get exchange rate
            fetch(`/api/exchange_rate?from=${fromCurrency}&to=${toCurrency}`)
                .then(response => response.json())
                .then(data => {
                    if (data.rate) {
                        const convertedAmount = amount * data.rate;
                        resultElement.textContent = `${amount} ${fromCurrency} = ${formatCurrency(convertedAmount, false, false)} ${toCurrency}`;
                    } else {
                        resultElement.textContent = 'Exchange rate not available';
                    }
                })
                .catch(error => {
                    console.error('Error fetching exchange rate:', error);
                    resultElement.textContent = 'Error fetching exchange rate';
                });
        });
        
        // Swap currencies button
        const swapButton = converter.querySelector('#swapCurrencies');
        if (swapButton) {
            swapButton.addEventListener('click', function() {
                const fromValue = fromSelect.value;
                const toValue = toSelect.value;
                
                fromSelect.value = toValue;
                toSelect.value = fromValue;
            });
        }
    }
}

/**
 * Initialize export options
 */
function initializeExportOptions() {
    const exportButtons = document.querySelectorAll('.export-button');
    exportButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const format = this.dataset.format;
            const url = new URL(this.href);
            
            // Add format parameter to URL
            url.searchParams.set('format', format);
            
            // Add any filter parameters from the form
            const filterForm = document.querySelector('.filter-form');
            if (filterForm) {
                const formData = new FormData(filterForm);
                for (const [key, value] of formData.entries()) {
                    url.searchParams.set(key, value);
                }
            }
            
            // Navigate to the export URL
            window.location.href = url.toString();
        });
    });
}

/**
 * Initialize DataTables for enhanced table functionality
 */
function initializeDataTables() {
    // Check if DataTables is available
    if (typeof $.fn.DataTable === 'undefined') {
        return;
    }
    
    // Initialize DataTables for tables with the datatable class
    $('.datatable').each(function() {
        $(this).DataTable({
            responsive: true,
            language: {
                search: "_INPUT_",
                searchPlaceholder: "Search...",
                lengthMenu: "Show _MENU_ entries",
                info: "Showing _START_ to _END_ of _TOTAL_ entries",
                infoEmpty: "Showing 0 to 0 of 0 entries",
                infoFiltered: "(filtered from _MAX_ total entries)"
            },
            dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
                 '<"row"<"col-sm-12"tr>>' +
                 '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
            pageLength: 10,
            lengthMenu: [[5, 10, 25, 50, -1], [5, 10, 25, 50, "All"]]
        });
    });
}

/**
 * Initialize print buttons
 */
function initializePrintButtons() {
    const printButtons = document.querySelectorAll('.print-button');
    printButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get the element to print
            const targetId = this.dataset.target;
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                // Create a new window for printing
                const printWindow = window.open('', '_blank');
                
                // Get styles from current page
                const styles = Array.from(document.styleSheets)
                    .map(styleSheet => {
                        try {
                            return Array.from(styleSheet.cssRules)
                                .map(rule => rule.cssText)
                                .join('\n');
                        } catch (e) {
                            // Likely a CORS issue with external stylesheets
                            return '';
                        }
                    })
                    .join('\n');
                
                // Create print content
                printWindow.document.write(`
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Print</title>
                        <style>
                            ${styles}
                            @media print {
                                body {
                                    padding: 20px;
                                    font-family: Arial, sans-serif;
                                }
                                .no-print {
                                    display: none !important;
                                }
                                button, .btn {
                                    display: none !important;
                                }
                            }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            ${targetElement.outerHTML}
                        </div>
                        <script>
                            window.onload = function() {
                                setTimeout(function() {
                                    window.print();
                                    window.close();
                                }, 500);
                            };
                        </script>
                    </body>
                    </html>
                `);
                
                printWindow.document.close();
            }
        });
    });
}

/**
 * Initialize goal contributions functionality
 */
function initializeGoalContributions() {
    // Handle goal contribution form
    const contributionForm = document.getElementById('goalContributionForm');
    if (contributionForm) {
        contributionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const amount = parseFloat(this.querySelector('#amount').value);
            if (isNaN(amount) || amount <= 0) {
                showNotification('Error', 'Please enter a valid amount', 'danger');
                return;
            }
            
            // Show loading state
            const submitButton = this.querySelector('button[type="submit"]');
            const originalText = submitButton.innerHTML;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Adding...';
            submitButton.disabled = true;
            
            // Submit form via AJAX
            const formData = new FormData(this);
            
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show success message
                    showNotification('Success', 'Contribution added successfully', 'success');
                    
                    // Update goal progress if available
                    if (data.current_amount && data.target_amount) {
                        const progressBar = document.querySelector('.goal-progress .progress-bar');
                        const currentAmountEl = document.querySelector('.goal-current-amount');
                        const percentageEl = document.querySelector('.goal-percentage');
                        
                        if (progressBar && currentAmountEl && percentageEl) {
                            const percentage = (data.current_amount / data.target_amount) * 100;
                            progressBar.style.width = `${Math.min(percentage, 100)}%`;
                            currentAmountEl.textContent = formatCurrency(data.current_amount);
                            percentageEl.textContent = `${Math.round(percentage)}%`;
                        }
                    }
                    
                    // Reset form
                    this.reset();
                    
                    // Reload contributions list if available
                    if (data.html) {
                        const contributionsList = document.querySelector('.contributions-list');
                        if (contributionsList) {
                            contributionsList.innerHTML = data.html;
                        }
                    } else {
                        // Fallback to page reload
                        window.location.reload();
                    }
                } else {
                    showNotification('Error', data.message || 'An error occurred', 'danger');
                }
            })
            .catch(error => {
                console.error('Error adding contribution:', error);
                showNotification('Error', 'An error occurred while adding the contribution', 'danger');
            })
            .finally(() => {
                // Restore button state
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
            });
        });
    }
}

/**
 * Initialize expense analytics functionality
 */
function initializeExpenseAnalytics() {
    // Handle expense prediction
    const predictionElement = document.getElementById('expensePrediction');
    if (predictionElement) {
        // Get prediction data
        const monthlyData = predictionElement.dataset.monthly ? JSON.parse(predictionElement.dataset.monthly) : [];
        
        if (monthlyData.length >= 3) {
            // Calculate prediction based on last 3 months
            const lastThreeMonths = monthlyData.slice(-3);
            const average = lastThreeMonths.reduce((a, b) => a + b, 0) / 3;
            
            // Display prediction
            const predictionValue = predictionElement.querySelector('.prediction-value');
            if (predictionValue) {
                predictionValue.textContent = formatCurrency(average);
            }
            
            // Calculate trend
            const lastMonth = monthlyData[monthlyData.length - 1];
            const trend = ((average - lastMonth) / lastMonth) * 100;
            
            const trendElement = predictionElement.querySelector('.prediction-trend');
            if (trendElement) {
                if (trend > 0) {
                    trendElement.innerHTML = `<i class="fas fa-arrow-up text-danger"></i> ${Math.abs(trend).toFixed(1)}%`;
                    trendElement.classList.add('text-danger');
                } else if (trend < 0) {
                    trendElement.innerHTML = `<i class="fas fa-arrow-down text-success"></i> ${Math.abs(trend).toFixed(1)}%`;
                    trendElement.classList.add('text-success');
                } else {
                    trendElement.innerHTML = `<i class="fas fa-equals text-info"></i> 0%`;
                    trendElement.classList.add('text-info');
                }
            }
        }
    }
    
    // Handle expense breakdown by day of week
    const weekdayChartEl = document.getElementById('weekdayChart');
    if (weekdayChartEl && typeof Chart !== 'undefined') {
        const ctx = weekdayChartEl.getContext('2d');
        
        // Get data from the element's data attributes
        let weekdays = [];
        let amounts = [];
        
        try {
            weekdays = JSON.parse(weekdayChartEl.dataset.weekdays || '[]');
            amounts = JSON.parse(weekdayChartEl.dataset.amounts || '[]');
        } catch (e) {
            console.error('Error parsing weekday chart data:', e);
        }
        
        if (weekdays.length > 0 && amounts.length > 0) {
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: weekdays,
                    datasets: [{
                        label: 'Average Expense by Day of Week',
                        data: amounts,
                        backgroundColor: 'rgba(78, 115, 223, 0.7)',
                        borderColor: 'rgba(78, 115, 223, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return formatCurrency(value, true);
                                }
                            }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    let label = context.dataset.label || '';
                                    let value = context.raw || 0;
                                    return `${label}: ${formatCurrency(value)}`;
                                }
                            }
                        }
                    }
                }
            });
        }
    }
}

/**
 * Initialize search and filter functionality
 */
function initializeSearchFilters() {
    // Handle filter form submission
    const filterForms = document.querySelectorAll('.filter-form');
    filterForms.forEach(function(form) {
        // Auto-submit on select change if the form has auto-submit class
        if (form.classList.contains('auto-submit')) {
            const selects = form.querySelectorAll('select');
            selects.forEach(function(select) {
                select.addEventListener('change', function() {
                    form.submit();
                });
            });
        }
        
        // Handle clear filters button
        const clearButton = form.querySelector('.clear-filters');
        if (clearButton) {
            clearButton.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Reset all form fields
                form.reset();
                
                // Submit the form if auto-submit
                if (form.classList.contains('auto-submit')) {
                    form.submit();
                }
            });
        }
    });
    
    // Handle search input
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        const tableRows = document.querySelectorAll('table tbody tr');
        
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            
            tableRows.forEach(function(row) {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
}

/**
 * Initialize responsive navigation
 */
function initializeResponsiveNavigation() {
    // Handle mobile navigation toggle
    const navbarToggler = document.querySelector('.navbar-toggler');
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            const target = document.querySelector(this.dataset.bsTarget || this.dataset.target);
            if (target) {
                target.classList.toggle('show');
            }
        });
    }
    
    // Handle dropdown menus on mobile
    const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
    dropdownToggles.forEach(function(toggle) {
        toggle.addEventListener('click', function(e) {
            // Only handle click on mobile
            if (window.innerWidth < 992) {
                e.preventDefault();
                e.stopPropagation();
                
                const dropdown = this.nextElementSibling;
                if (dropdown && dropdown.classList.contains('dropdown-menu')) {
                    dropdown.classList.toggle('show');
                }
            }
        });
    });
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function(e) {
        if (window.innerWidth < 992) {
            const dropdowns = document.querySelectorAll('.dropdown-menu.show');
            dropdowns.forEach(function(dropdown) {
                if (!dropdown.contains(e.target) && !e.target.classList.contains('dropdown-toggle')) {
                    dropdown.classList.remove('show');
                }
            });
        }
    });
}

/**
 * Initialize animations
 */
function initializeAnimations() {
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(function(card, index) {
        // Add animation with delay based on index
        setTimeout(function() {
            card.classList.add('fade-in');
        }, index * 100);
    });
    
    // Add slide-in animation to stat cards
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach(function(card, index) {
        // Add animation with delay based on index
        setTimeout(function() {
            card.classList.add('slide-in');
        }, index * 100);
    });
    
    // Add animation to charts
    const chartContainers = document.querySelectorAll('.chart-container');
    chartContainers.forEach(function(container) {
        container.classList.add('chart-animate-in');
    });
}