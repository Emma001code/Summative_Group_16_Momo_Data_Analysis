// Global variables for pagination
let currentPage = 1;
const itemsPerPage = 10;
let totalItems = 0;
let retryCount = 0;
const maxRetries = 3;
let justCleared = false;

// Global variables for charts
let typeChart = null;
let volumeChart = null;
let monthlyTrendsChart = null;
let paymentDepositChart = null;

// Chart colors
const chartColors = {
    primary: '#0d6efd',
    success: '#198754',
    warning: '#ffc107',
    danger: '#dc3545',
    info: '#0dcaf0',
    secondary: '#6c757d'
};

// Initialize date range picker
$(document).ready(function() {
    // Show loading state immediately
    showLoadingState();
    
    // Initialize daterangepicker with a 30-day range
    const endDate = moment('2025-01-16');
    const startDate = moment('2024-05-10');
    
    $('#dateRange').daterangepicker({
        startDate: endDate.clone().subtract(30, 'days'),
        endDate: endDate,
        minDate: startDate,
        maxDate: endDate,
        ranges: {
           'Last 7 Days': [endDate.clone().subtract(6, 'days'), endDate],
           'Last 30 Days': [endDate.clone().subtract(29, 'days'), endDate],
           'This Month': [endDate.clone().startOf('month'), endDate.clone().endOf('month')],
           'Last Month': [endDate.clone().subtract(1, 'month').startOf('month'), endDate.clone().subtract(1, 'month').endOf('month')],
           'All Time': [startDate, endDate]
        }
    });

    // Add a small delay before loading data to ensure database is ready
    setTimeout(function() {
        loadInitialData();
    }, 1000);

    // Set up event listeners
    $('#applyFilters').click(function() {
        currentPage = 1;
        loadTransactions();
        loadSummary();
    });

    $('#searchTerm').on('keyup', function(e) {
        if (e.key === 'Enter') {
            currentPage = 1;
            loadTransactions();
        }
    });

    // Add change event listener for transaction type
    $('#transactionType').on('change', function() {
        currentPage = 1;
        loadTransactions();
    });

    // Add change event listener for date range
    $('#dateRange').on('apply.daterangepicker', function() {
        currentPage = 1;
        loadTransactions();
    });

    // Add input event listeners for amount range
    $('#minAmount, #maxAmount').on('input', function() {
        // Remove non-numeric characters
        this.value = this.value.replace(/[^0-9]/g, '');
        
        // Ensure min amount is not greater than max amount
        const minAmount = parseInt($('#minAmount').val()) || 0;
        const maxAmount = parseInt($('#maxAmount').val()) || 0;
        
        if (minAmount > maxAmount && maxAmount !== 0) {
            if (this.id === 'minAmount') {
                this.value = maxAmount;
            } else {
                this.value = minAmount;
            }
        }
    });

    // Handle file upload
    $('#uploadForm').on('submit', function(e) {
        e.preventDefault();
        const fileInput = $('#xmlFile')[0];
        const file = fileInput.files[0];
        
        if (!file) {
            alert('Please select a file to upload');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        const statusSpan = $('#uploadStatus');
        statusSpan.text('Uploading and processing...');

        $.ajax({
            url: '/upload',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                statusSpan.text('File processed successfully!');
                statusSpan.removeClass('text-danger').addClass('text-success');
                currentPage = 1;
                loadTransactions();
                loadSummary();
                fileInput.value = '';
                setTimeout(() => statusSpan.text(''), 3000);
            },
            error: function(xhr) {
                const error = xhr.responseJSON ? xhr.responseJSON.error : 'Upload failed';
                statusSpan.text(error);
                statusSpan.removeClass('text-success').addClass('text-danger');
            }
        });
    });

    // Handle truncate button click with custom modal
    $('#truncateBtn').on('click', function() {
        // Check if there are transactions displayed
        const hasTransactions = $('#transactionsTable tr').length > 0 && !$('#transactionsTable tr td').hasClass('text-danger');
        if (hasTransactions) {
            // Show the custom modal
            $('#clearTransactionsModal').modal('show');
        } else {
            // Show red notification if no transactions
            showClearNotification('No transaction found', 'red');
        }
    });

    // Handle confirmation in the modal
    $('#confirmClearBtn').on('click', function() {
        $.ajax({
            url: '/api/truncate',
            type: 'POST',
            success: function(response) {
                $('#clearTransactionsModal').modal('hide');
                currentPage = 1;
                justCleared = true;
                loadTransactions();
                loadSummary();
                showClearNotification('All transactions cleared', 'blue');
            },
            error: function(xhr) {
                $('#clearTransactionsModal').modal('hide');
                const error = xhr.responseJSON ? xhr.responseJSON.error : 'Failed to clear transactions';
                showClearNotification(error, 'red');
            }
        });
    });
});

// Show loading state for all summary cards
function showLoadingState() {
    $('#totalTransactions').text('Loading...');
    $('#totalVolume').text('Loading...');
    $('#avgTransactionAmount').text('Loading...');
    $('#largestTransaction').text('Loading...');
    $('#totalFees').text('Loading...');
    $('#mostActiveDay').text('Loading...');
    $('#transactionsTable').html(`
        <tr>
            <td colspan="6" class="text-center">Loading transactions...</td>
        </tr>
    `);
}

// Function to load initial data with retry logic
function loadInitialData() {
    retryCount = 0;
    loadDataWithRetry();
}

function loadDataWithRetry() {
    // First try to load summary data
    $.ajax({
        url: '/api/summary',
        method: 'GET',
        timeout: 5000
    }).then(function(summaryResponse) {
        if (summaryResponse && typeof summaryResponse === 'object') {
            // Update summary data
            $('#totalTransactions').text(summaryResponse.total_transactions.toLocaleString());
            $('#totalVolume').text(formatAmount(summaryResponse.total_volume) + ' RWF');
            $('#avgTransactionAmount').text(formatAmount(summaryResponse.statistics.avg_amount) + ' RWF');
            $('#largestTransaction').text(formatAmount(summaryResponse.statistics.max_amount) + ' RWF');
            $('#totalFees').text(formatAmount(summaryResponse.statistics.total_fees) + ' RWF');
            if (summaryResponse.statistics.most_active_day) {
                $('#mostActiveDay').text(moment(summaryResponse.statistics.most_active_day).format('MMM D, YYYY'));
            } else {
                $('#mostActiveDay').text('-');
            }
            updateCharts(summaryResponse);
        }
        
        // Then load transactions
        return $.ajax({
            url: '/api/transactions',
            method: 'GET',
            data: { page: 1, per_page: itemsPerPage },
            timeout: 5000
        });
    }).then(function(transactionsResponse) {
        if (transactionsResponse && typeof transactionsResponse === 'object') {
            totalItems = transactionsResponse.total || 0;
            updateTransactionsTable(transactionsResponse.transactions || []);
            updatePagination();
        }
    }).fail(function(jqXHR, textStatus, errorThrown) {
        console.error('Error loading data:', textStatus, errorThrown);
        
        if (retryCount < maxRetries) {
            retryCount++;
            console.log(`Retrying... Attempt ${retryCount} of ${maxRetries}`);
            setTimeout(loadDataWithRetry, 1000 * retryCount);
        } else {
            showZeroState();
        }
    });
}

// Show zero state for all summary cards
function showZeroState() {
    $('#totalTransactions').text('0');
    $('#totalVolume').text('0 RWF');
    $('#avgTransactionAmount').text('0 RWF');
    $('#largestTransaction').text('0 RWF');
    $('#totalFees').text('0 RWF');
    $('#mostActiveDay').text('-');
    $('#transactionsTable').html(`
        <tr>
            <td colspan="6" class="text-center">No transactions found</td>
        </tr>
    `);
}

// Load transactions with filters
function loadTransactions() {
    const filters = getFilters();
    filters.page = currentPage;
    filters.per_page = itemsPerPage;
    
    $.ajax({
        url: '/api/transactions',
        method: 'GET',
        data: filters,
        success: function(data) {
            if (data && typeof data === 'object') {
                totalItems = data.total || 0;
                const transactions = data.transactions || [];
                updateTransactionsTable(transactions);
                updatePagination();
                
                // Log the data for debugging
                console.log('Transactions loaded:', {
                    total: data.total,
                    transactions: transactions
                });
            } else {
                console.error('Invalid response format:', data);
                $('#transactionsTable').html(`
                    <tr>
                        <td colspan="6" class="text-center">Error loading transactions. Please try again.</td>
                    </tr>
                `);
            }
        },
        error: function(xhr, status, error) {
            console.error('Error loading transactions:', {
                status: status,
                error: error,
                response: xhr.responseText
            });
            $('#transactionsTable').html(`
                <tr>
                    <td colspan="6" class="text-center">Error loading transactions. Please try again.</td>
                </tr>
            `);
        }
    });
}

// Load summary data
function loadSummary() {
    // Show loading state
    $('#totalTransactions').text('Loading...');
    $('#totalVolume').text('Loading...');
    $('#avgTransactionAmount').text('Loading...');
    $('#largestTransaction').text('Loading...');
    $('#totalFees').text('Loading...');
    $('#mostActiveDay').text('Loading...');

    $.ajax({
        url: '/api/summary',
        method: 'GET',
        success: function(data) {
            if (data && typeof data === 'object') {
                // Format numbers with commas
                $('#totalTransactions').text(data.total_transactions.toLocaleString());
                $('#totalVolume').text(formatAmount(data.total_volume) + ' RWF');
                
                // Update statistics with proper formatting
                $('#avgTransactionAmount').text(formatAmount(data.statistics.avg_amount) + ' RWF');
                $('#largestTransaction').text(formatAmount(data.statistics.max_amount) + ' RWF');
                $('#totalFees').text(formatAmount(data.statistics.total_fees) + ' RWF');
                
                // Format the date
                if (data.statistics.most_active_day) {
                    $('#mostActiveDay').text(moment(data.statistics.most_active_day).format('MMM D, YYYY'));
                } else {
                    $('#mostActiveDay').text('-');
                }
                
                // Update charts
                updateCharts(data);
            } else {
                console.error('Invalid summary response format:', data);
                showErrorState();
            }
        },
        error: function(xhr, status, error) {
            console.error('Error loading summary:', error);
            showErrorState();
        }
    });
}

// Show error state for summary cards
function showErrorState() {
    $('#totalTransactions').text('0');
    $('#totalVolume').text('0 RWF');
    $('#avgTransactionAmount').text('0 RWF');
    $('#largestTransaction').text('0 RWF');
    $('#totalFees').text('0 RWF');
    $('#mostActiveDay').text('-');
}

// Get current filter values
function getFilters() {
    const dateRange = $('#dateRange').data('daterangepicker');
    const minAmount = $('#minAmount').val().trim();
    const maxAmount = $('#maxAmount').val().trim();
    
    const filters = {
        type: $('#transactionType').val(),
        start_date: dateRange.startDate.format('YYYY-MM-DD'),
        end_date: dateRange.endDate.format('YYYY-MM-DD'),
        search: $('#searchTerm').val().trim(),
        min_amount: minAmount ? parseInt(minAmount) : null,
        max_amount: maxAmount ? parseInt(maxAmount) : null
    };
    
    // Log filters for debugging
    console.log('Applied filters:', filters);
    return filters;
}

// Update transactions table
function updateTransactionsTable(transactions) {
    const tbody = $('#transactionsTable');
    tbody.empty();

    if (!transactions || transactions.length === 0) {
        tbody.append(`
            <tr>
                <td colspan="6" class="text-center text-danger">No transaction found</td>
            </tr>
        `);
        if (!justCleared) {
            showClearNotification('No transaction found', 'red');
        }
        justCleared = false;
        return;
    }

    transactions.forEach(transaction => {
        // Format the date
        const date = moment(transaction.transaction_date).format('YYYY-MM-DD HH:mm:ss');
        // Format the amount
        const amount = formatAmount(transaction.amount);
        // Format the transaction type
        const type = formatTransactionType(transaction.transaction_type);
        // Create the row
        const row = $('<tr>');
        row.append(`
            <td>${date}</td>
            <td><span class="badge bg-primary">${type}</span></td>
            <td class="text-end">${amount} RWF</td>
            <td>${transaction.sender || '-'}</td>
            <td>${transaction.recipient || '-'}</td>
            <td>
                <button class="btn btn-sm btn-info" onclick="showTransactionDetails('${transaction.transaction_id}')">
                    <i class="fas fa-info-circle"></i> Details
                </button>
            </td>
        `);
        tbody.append(row);
    });
}

// Update pagination
function updatePagination() {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    const pagination = $('#pagination');
    pagination.empty();

    if (totalPages <= 1) return;

    // Previous button
    pagination.append(`
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage - 1})">Previous</a>
        </li>
    `);

    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        if (
            i === 1 || // First page
            i === totalPages || // Last page
            (i >= currentPage - 2 && i <= currentPage + 2) // Pages around current page
        ) {
            pagination.append(`
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
                </li>
            `);
        } else if (
            i === currentPage - 3 ||
            i === currentPage + 3
        ) {
            pagination.append('<li class="page-item disabled"><span class="page-link">...</span></li>');
        }
    }

    // Next button
    pagination.append(`
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage + 1})">Next</a>
        </li>
    `);
}

// Change page
function changePage(page) {
    if (page >= 1 && page <= Math.ceil(totalItems / itemsPerPage)) {
        currentPage = page;
        loadTransactions();
    }
}

// Update summary cards
function updateSummaryCards(data) {
    $('#totalTransactions').text(data.total_transactions.toLocaleString());
    $('#totalVolume').text(formatAmount(data.total_volume) + ' RWF');
    
    // Update statistics
    $('#avgTransactionAmount').text(formatAmount(data.statistics.avg_amount) + ' RWF');
    $('#largestTransaction').text(formatAmount(data.statistics.max_amount) + ' RWF');
    $('#totalFees').text(formatAmount(data.statistics.total_fees) + ' RWF');
    $('#mostActiveDay').text(moment(data.statistics.most_active_day).format('MMM D, YYYY'));
    
    updateCharts(data);
}

// Update all charts
function updateCharts(data) {
    updateTypeDistributionChart(data.by_type);
    updateVolumeByTypeChart(data.by_type);
    updateMonthlyTrendsChart(data.monthly_trends);
    updatePaymentDepositChart(data.payment_deposit);
}

// Update Transaction Types Distribution Chart
function updateTypeDistributionChart(typeData) {
    const ctx = document.getElementById('typeChart').getContext('2d');
    
    if (typeChart) {
        typeChart.destroy();
    }
    
    typeChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: typeData.map(item => formatTransactionType(item.transaction_type)),
            datasets: [{
                data: typeData.map(item => item.count),
                backgroundColor: Object.values(chartColors)
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

// Update Transaction Volume by Type Chart
function updateVolumeByTypeChart(typeData) {
    const ctx = document.getElementById('volumeChart').getContext('2d');
    
    if (volumeChart) {
        volumeChart.destroy();
    }
    
    volumeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: typeData.map(item => formatTransactionType(item.transaction_type)),
            datasets: [{
                label: 'Total Volume',
                data: typeData.map(item => item.total_amount),
                backgroundColor: chartColors.primary,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: value => formatAmount(value) + ' RWF'
                    }
                }
            }
        }
    });
}

// Update Monthly Transaction Trends Chart
function updateMonthlyTrendsChart(monthlyData) {
    const ctx = document.getElementById('monthlyTrendsChart').getContext('2d');
    
    if (monthlyTrendsChart) {
        monthlyTrendsChart.destroy();
    }
    
    monthlyTrendsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: monthlyData.map(item => moment(item.month).format('MMM YYYY')),
            datasets: [
                {
                    label: 'Total Volume',
                    data: monthlyData.map(item => item.total_amount),
                    borderColor: chartColors.primary,
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Number of Transactions',
                    data: monthlyData.map(item => item.count),
                    borderColor: chartColors.success,
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.4,
                    yAxisID: 'count'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: value => formatAmount(value) + ' RWF'
                    }
                },
                count: {
                    position: 'right',
                    beginAtZero: true,
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

// Update Payment vs Deposit Distribution Chart
function updatePaymentDepositChart(paymentData) {
    const ctx = document.getElementById('paymentDepositChart').getContext('2d');
    
    if (paymentDepositChart) {
        paymentDepositChart.destroy();
    }
    
    const colors = {
        'Deposits': chartColors.success,
        'Payments': chartColors.danger,
        'Others': chartColors.secondary
    };
    
    paymentDepositChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: paymentData.map(item => item.category),
            datasets: [{
                data: paymentData.map(item => item.total_amount),
                backgroundColor: paymentData.map(item => colors[item.category])
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Show transaction details
function showTransactionDetails(transactionId) {
    $.get(`/api/transaction/${transactionId}`, function(transaction) {
        const modalBody = $('.modal-body');
        modalBody.html(`
            <div class="table-responsive">
                <table class="table">
                    <tr>
                        <th>Transaction ID</th>
                        <td>${transaction.transaction_id}</td>
                    </tr>
                    <tr>
                        <th>Type</th>
                        <td>${formatTransactionType(transaction.transaction_type)}</td>
                    </tr>
                    <tr>
                        <th>Amount</th>
                        <td>${formatAmount(transaction.amount)} RWF</td>
                    </tr>
                    <tr>
                        <th>Fee</th>
                        <td>${formatAmount(transaction.fee)} RWF</td>
                    </tr>
                    <tr>
                        <th>Date</th>
                        <td>${moment(transaction.transaction_date).format('YYYY-MM-DD HH:mm:ss')}</td>
                    </tr>
                    <tr>
                        <th>Sender</th>
                        <td>${transaction.sender || '-'}</td>
                    </tr>
                    <tr>
                        <th>Recipient</th>
                        <td>${transaction.recipient || '-'}</td>
                    </tr>
                    <tr>
                        <th>Phone Number</th>
                        <td>${transaction.phone_number || '-'}</td>
                    </tr>
                    <tr>
                        <th>Balance</th>
                        <td>${formatAmount(transaction.balance)} RWF</td>
                    </tr>
                    <tr>
                        <th>Message</th>
                        <td>${transaction.message}</td>
                    </tr>
                </table>
            </div>
        `);
        
        const modal = new bootstrap.Modal(document.getElementById('transactionModal'));
        modal.show();
    }).fail(function(xhr) {
        alert('Error loading transaction details. Please try again.');
    });
}

// Format transaction type for display
function formatTransactionType(type) {
    return type.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
    ).join(' ');
}

// Format amount with thousands separator
function formatAmount(amount) {
    return new Intl.NumberFormat('en-US').format(amount);
}

// Show notification
function showClearNotification(message, color) {
    const notification = $('#clearNotification');
    notification.text(message);
    notification.css({
        'background-color': color === 'red' ? '#dc3545' : '#0d6efd',
        'color': '#fff',
        'display': 'block'
    });
    setTimeout(() => notification.fadeOut(), 3000);
} 
