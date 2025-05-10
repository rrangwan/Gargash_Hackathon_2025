document.addEventListener('DOMContentLoaded', function() {
    // Show/hide financing options based on payment method
    const paymentRadios = document.querySelectorAll('input[name="payment_method"]');
    const financingOptions = document.getElementById('financing-options');
    
    paymentRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            financingOptions.style.display = (this.value === 'financing') ? 'block' : 'none';
        });
    });

    // Handle form submission
    const goalForm = document.getElementById('goal-form');
    if (goalForm) {
        goalForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading indicator
            const submitButton = this.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.textContent;
            submitButton.textContent = 'Calculating...';
            submitButton.disabled = true;
            
            // Get form data
            const formData = new FormData(goalForm);
            const jsonData = {};
            
            // Convert FormData to JSON
            formData.forEach((value, key) => {
                // Convert string values to appropriate types
                if (key === 'is_new') {
                    jsonData[key] = value === 'true';
                } else if (['year', 'max_mileage', 'max_emi', 'max_term', 'down_payment', 'interest_rate'].includes(key)) {
                    jsonData[key] = parseFloat(value);
                } else {
                    jsonData[key] = value;
                }
            });
            
            // Get the selected car model for display
            const modelSelect = document.getElementById('model');
            const selectedModel = modelSelect.options[modelSelect.selectedIndex].text;
            
            // Send data to server
            fetch('/submit_goal', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(jsonData)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Add the car model to the data
                data.model = selectedModel;
                
                // Display results
                displayResults(data);
                
                // Reset button
                submitButton.textContent = originalButtonText;
                submitButton.disabled = false;
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error calculating plan: ' + error.message);
                
                // Reset button
                submitButton.textContent = originalButtonText;
                submitButton.disabled = false;
            });
        });
    }

    // Save button click handler
    const saveButton = document.getElementById('save-data');
    if (saveButton) {
        saveButton.addEventListener('click', function() {
            alert('Plan saved successfully!');
        });
    }
});

function displayResults(data) {
    // Show results div
    document.getElementById('results').style.display = 'block';
    
    // Set text content
    document.getElementById('car-model').textContent = data.model || 'Not specified';
    document.getElementById('estimated-date').textContent = data.estimated_date;
    document.getElementById('down-payment').textContent = data.down_payment.toLocaleString(undefined, {maximumFractionDigits: 0});
    document.getElementById('car-price').textContent = data.car_price.toLocaleString(undefined, {maximumFractionDigits: 0});
    
    // Show EMI details if available
    const emiDetails = document.getElementById('emi-details');
    if (data.monthly_payment && data.payment_period) {
        document.getElementById('monthly-emi').textContent = data.monthly_payment.toLocaleString(undefined, {maximumFractionDigits: 0});
        document.getElementById('payment-period').textContent = data.payment_period;
        emiDetails.style.display = 'block';
    } else {
        emiDetails.style.display = 'none';
    }
    
    // Show promotion if available
    const promotionElem = document.getElementById('promotion');
    if (data.promotion) {
        promotionElem.style.display = 'block';
    } else {
        promotionElem.style.display = 'none';
    }
    
    // Create time chart
    if (data.time_chart && data.time_chart.length > 0) {
        const dates = data.time_chart.map(item => item.date);
        const savings = data.time_chart.map(item => item.savings);
        
        const purchaseDate = new Date(data.estimated_date);
        
        // Find purchase point index
        let purchaseIndex = -1;
        for (let i = 0; i < dates.length; i++) {
            const chartDate = new Date(dates[i]);
            if (chartDate >= purchaseDate) {
                purchaseIndex = i;
                break;
            }
        }
        
        // Create data for the chart
        const chartData = [{
            x: dates,
            y: savings,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Savings',
            line: {
                color: 'rgb(31, 119, 180)'
            }
        }];
        
        // Add purchase point annotation if found
        const annotations = [];
        if (purchaseIndex >= 0) {
            annotations.push({
                x: dates[purchaseIndex],
                y: savings[purchaseIndex],
                text: 'Purchase Date',
                showarrow: true,
                arrowhead: 7,
                ax: 0,
                ay: -40
            });
        }
        
        Plotly.newPlot('time-chart', chartData, {
            title: 'Savings Over Time',
            xaxis: { title: 'Date' },
            yaxis: { title: 'Amount (AED)' },
            annotations: annotations
        });
    }
}