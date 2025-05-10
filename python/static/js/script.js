document.addEventListener('DOMContentLoaded', async () => {
    // Load Plotly safely
    await loadPlotly();
    
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
            monthly_saving: 1000
        };
        
        try {
            const response = await fetch('/submit_goal', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Server error');
            }
            
            const result = await response.json();
            displayResults(data, result);
            
        } catch (error) {
            console.error('Submission error:', error);
            alert(`Error: ${error.message || 'Failed to submit form'}`);
        }
    });
    
    // Save data button
    document.getElementById('save-data').addEventListener('click', () => {
        alert('Data saved successfully!');
    });
    
    // Helper functions
    async function loadPlotly() {
        if (typeof Plotly === 'undefined') {
            await loadScript('https://cdn.plot.ly/plotly-basic-2.24.1.min.js');
        }
    }
    
    function loadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
            document.head.appendChild(script);
        });
    }
    
    function displayResults(formData, result) {
        resultsDiv.style.display = 'block';
        document.getElementById('estimated-date').textContent = result.estimated_date;
        document.getElementById('down-payment').textContent = result.down_payment;
        document.getElementById('car-price').textContent = result.car_price;
        document.getElementById('promotion').style.display = result.promotion ? 'block' : 'none';
        
        if (result.promotion) {
            const carType = formData.is_new ? 'New' : 'Used';
            alert(`The ${carType} car ${formData.model} ${formData.year} is on sale this month!`);
        }
        
        renderChart(result.time_chart);
    }
    
    function renderChart(chartData) {
        const plotElement = document.getElementById('time-chart');
        
        // Clear previous plot
        Plotly.purge(plotElement);
        
        const trace = {
            x: chartData.map(d => d.Month),
            y: chartData.map(d => d.Savings),
            type: 'scatter',
            mode: 'lines+markers',
            line: { shape: 'spline', smoothing: 1.3 }
        };
        
        const layout = {
            title: 'Savings Progress',
            xaxis: { title: 'Months' },
            yaxis: { title: 'Savings ($)' },
            margin: { t: 40, l: 60, r: 40, b: 60 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)'
        };
        
        Plotly.newPlot(plotElement, [trace], layout, {
            displayModeBar: true,
            responsive: true
        });
    }
});