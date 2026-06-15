document.addEventListener('DOMContentLoaded', () => {
    loadData();
});

async function loadData() {
    try {
        // Tentiamo di scaricare il file CSV. Se stiamo usando GitHub Pages, questo sarà il path corretto.
        // Se non esiste, mostreremo dei dati vuoti o gestiremo l'errore.
        const responseSignals = await fetch('registro_segnali.csv');
        if (responseSignals.ok) {
            const csvText = await responseSignals.text();
            Papa.parse(csvText, { header: true, skipEmptyLines: true, complete: function(results) { processData(results.data); } });
        }
        
        const responsePort = await fetch('portafoglio_virtuale.csv');
        if (responsePort.ok) {
            const csvPortText = await responsePort.text();
            Papa.parse(csvPortText, { header: true, skipEmptyLines: true, complete: function(results) { processPortfolio(results.data); } });
        }
        
        try {
            const responseSub = await fetch('iscritti.json');
            if (responseSub.ok) {
                const subscribers = await responseSub.json();
                document.getElementById('totalSubscribers').innerText = subscribers.length;
            } else {
                document.getElementById('totalSubscribers').innerText = '1 (Tu)';
            }
        } catch(e) {
            document.getElementById('totalSubscribers').innerText = '1 (Tu)';
        }
        
    } catch (error) {
        console.error('Errore caricamento CSV:', error);
        document.getElementById('totalSignals').innerText = 'Err';
    }
}

function processData(data) {
    if (data.length === 0) return;

    // Aggiornamento Metriche
    document.getElementById('totalSignals').innerText = data.length;
    
    const lastRow = data[data.length - 1];
    // Estrai solo la data ignorando l'ora per la UI
    const lastDate = lastRow['Data'].split(' ')[0];
    document.getElementById('lastSignalDate').innerText = lastDate;

    let totalWinRate = 0;
    const chartLabels = [];
    const chartData = [];

    // Prepara la tabella (dal più recente al più vecchio)
    const tableBody = document.querySelector('#signalsTable tbody');
    tableBody.innerHTML = '';

    const reversedData = [...data].reverse();

    reversedData.forEach((row, index) => {
        // Pulizia Win Rate string (es. "68.5%") -> Number
        const wrStr = row['Win Rate'].replace('%', '');
        const wrNum = parseFloat(wrStr);
        totalWinRate += wrNum;

        // Dati per il grafico (prendiamo gli ultimi 15 per non affollarlo)
        if (index < 15) {
            chartLabels.unshift(row['Ticker']);
            chartData.unshift(wrNum);
        }

        // Creazione riga tabella
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${row['Data'].split(' ')[0]}</td>
            <td><span class="badge">${row['Ticker']}</span></td>
            <td style="color: var(--accent); font-weight: bold;">${row['Win Rate']}</td>
            <td>${row['Casi Passati']}</td>
            <td>$${row['Prezzo Acquisto']}</td>
            <td>$${row['Target Price']}</td>
            <td style="color: var(--text-muted);">${row['Time Out']}</td>
        `;
        tableBody.appendChild(tr);
    });

    const avg = (totalWinRate / data.length).toFixed(1);
    document.getElementById('avgWinRate').innerText = `${avg}%`;

    renderChart(chartLabels, chartData);
}

function renderChart(labels, data) {
    const ctx = document.getElementById('winRateChart').getContext('2d');
    
    // Gradiente per la barra
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(0, 255, 204, 0.8)');
    gradient.addColorStop(1, 'rgba(0, 255, 204, 0.1)');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Win Rate %',
                data: data,
                backgroundColor: gradient,
                borderRadius: 6,
                borderWidth: 0,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(20, 20, 25, 0.9)',
                    titleFont: { family: 'Outfit', size: 14 },
                    bodyFont: { family: 'JetBrains Mono', size: 14 },
                    padding: 12,
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1
                }
            },
            scales: {
                y: {
                    min: 50,
                    max: 100,
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#888899', font: { family: 'JetBrains Mono' } }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#888899', font: { family: 'JetBrains Mono' } }
                }
            }
        }
    });
}

function processPortfolio(data) {
    if (data.length === 0) return;
    
    const tableBody = document.querySelector('#portfolioTable tbody');
    tableBody.innerHTML = '';
    
    const reversedData = [...data].reverse();
    
    reversedData.forEach(row => {
        const esitoClass = row['Esito Reale'] === 'VINTO' ? 'color: var(--success); font-weight: bold;' : 'color: var(--danger); font-weight: bold;';
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${row['Data'].split(' ')[0]}</td>
            <td><span class="badge">${row['Ticker']}</span></td>
            <td>${row['Win Rate Previsto']}</td>
            <td style="${esitoClass}">${row['Esito Reale']}</td>
            <td style="${esitoClass}">${row['Profitto/Perdita %']}</td>
        `;
        tableBody.appendChild(tr);
    });
}
