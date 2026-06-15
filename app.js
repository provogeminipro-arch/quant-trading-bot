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

    // Aggiornamento Metriche base
    const totalSignalsEl = document.getElementById('totalSignals');
    if (totalSignalsEl) totalSignalsEl.innerText = data.length;
    
    const lastRow = data[data.length - 1];
    // Estrai solo la data ignorando l'ora per la UI
    const lastDate = lastRow ? lastRow['Data'].split(' ')[0] : 'N/D';
    const lastSignalDateEl = document.getElementById('lastSignalDate');
    if (lastSignalDateEl) lastSignalDateEl.innerText = lastDate;

    // Prepara la tabella Segnali (dal più recente al più vecchio)
    const tableBody = document.querySelector('#signalsTable tbody');
    tableBody.innerHTML = '';

    const reversedData = [...data].reverse();

    reversedData.forEach((row, index) => {
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
}

function processPortfolio(data) {
    if (data.length === 0) return;
    
    const tableBody = document.querySelector('#portfolioTable tbody');
    tableBody.innerHTML = '';
    
    let totalTrades = 0;
    let wonTrades = 0;
    let cumulativeProfit = 0;
    
    const chartLabels = [];
    const chartData = [];
    
    // Ordiniamo cronologicamente (il CSV è già in ordine cronologico dall'alto al basso)
    data.forEach(row => {
        if (!row['Esito Reale']) return; // Skip righe vuote
        
        totalTrades++;
        if (row['Esito Reale'] === 'VINTO') wonTrades++;
        
        const profStr = row['Profitto/Perdita %'].replace('%', '');
        const profNum = parseFloat(profStr);
        cumulativeProfit += profNum;
        
        // Punti per il grafico
        chartLabels.push(row['Ticker']);
        chartData.push(cumulativeProfit.toFixed(2));
    });
    
    // Scrivi Statistiche in Dashboard
    const realWinRate = totalTrades > 0 ? ((wonTrades / totalTrades) * 100).toFixed(1) : 0;
    document.getElementById('realWinRate').innerText = `${realWinRate}%`;
    
    const profitColor = cumulativeProfit >= 0 ? 'var(--success)' : 'var(--danger)';
    const sign = cumulativeProfit > 0 ? '+' : '';
    document.getElementById('totalProfit').innerText = `${sign}${cumulativeProfit.toFixed(2)}%`;
    document.getElementById('totalProfit').style.color = profitColor;
    
    // Prepara la tabella Portafoglio (dal più recente al più vecchio)
    const reversedData = [...data].reverse();
    
    reversedData.forEach(row => {
        if (!row['Esito Reale']) return;
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
    
    // Disegna il grafico storico dei profitti
    renderPortfolioChart(chartLabels, chartData);
}

function renderPortfolioChart(labels, data) {
    const ctx = document.getElementById('portfolioChart').getContext('2d');
    
    // Gradiente per l'area sotto la curva
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(0, 255, 204, 0.4)');
    gradient.addColorStop(1, 'rgba(0, 255, 204, 0.0)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Profitto Cumulato %',
                data: data,
                borderColor: '#00ffcc',
                backgroundColor: gradient,
                borderWidth: 3,
                tension: 0.4, // Curva morbida
                fill: true,
                pointBackgroundColor: '#141419',
                pointBorderColor: '#00ffcc',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
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
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return ` ${context.parsed.y}%`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { 
                        color: '#888899', 
                        font: { family: 'JetBrains Mono' },
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#888899', font: { family: 'JetBrains Mono' } }
                }
            }
        }
    });
}
