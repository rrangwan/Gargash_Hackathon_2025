document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('goal-form');
    const financingOptions = document.getElementById('financing-options');
    const paymentMethodRadios = document.querySelectorAll('input[name="payment_method"]');
    const resultsDiv = document.getElementById('results');
    
    // Toggle financing options
    paymentMethodRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            financingOptions.style.display = radio.value === 'financing' ? 'block' : 'none';
        });
    });
    
    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        const data = {
            is_new: formData.get('is_new') === 'true',
            model: formData.get('model') || 'Mercedes S-Class',
            year: parseInt(formData.get('year')) || 2025,
            max_mileage: parseInt(formData.get('max_mileage')) || 50000,
            payment_method: formData.get('payment_method') || 'cash',
            max_emi: parseInt(formData.get('max_emi')) || 1000,
            max_term: parseInt(formData.get('max_term')) || 60,
            down_payment: parseInt(formData.get('down_payment')) || 20000,
            monthly_saving: 1000  // Mock value (overridden in financing case)
        };
        
        try {
            const response = await fetch('/submit_goal', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            
            if (response.ok) {
                resultsDiv.style.display = 'block';
                document.getElementById('estimated-date').textContent = result.estimated_date;
                document.getElementById('down-payment').textContent = result.down_payment;
                document.getElementById('car-price').textContent = result.car_price;
                document.getElementById('promotion').style.display = result.promotion ? 'block' : 'none';
                
                // Promotion alert
                if (result.promotion) {
                    const carType = data.is_new ? 'New' : 'Used';
                    alert(`The ${carType} car ${data.model} and ${data.year} selected is on sale this month at a discount!`);
                }
                
                Plotly.newPlot('time-chart', [{
                    x: result.time_chart.map(d => d.Month),
                    y: result.time_chart.map(d => d.Savings),
                    type: 'scatter',
                    mode: 'lines+markers'
                }], {
                    title: 'Savings Progress',
                    xaxis: { title: 'Months' },
                    yaxis: { title: 'Savings ($)' }
                });
            } else {
                console.error('Server error:', result.error);
                alert(`Error: ${result.error}`);
            }
        } catch (error) {
            console.error('Fetch error:', error);
            alert('Failed to submit form. Please try again.');
        }
    });
    
    // Save data button
    document.getElementById('save-data').addEventListener('click', () => {
        alert('Data saved successfully!');
    });
});