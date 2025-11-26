document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('reports-container');
    if (!container) return;

    // Завантажуємо дані звітів через fetch
    fetch('/reports.json')
        .then(res => res.json())
        .then(reportsData => {
            if (!Array.isArray(reportsData) || reportsData.length === 0) {
                container.textContent = 'Немає доступних звітів.';
                return;
            }

            reportsData.forEach((art, idx) => {
                // Створюємо блок для звіту
                const reportBlock = document.createElement('div');
                reportBlock.className = 'report-block';

                // Заголовок статті
                const titleEl = document.createElement('h3');
                titleEl.textContent = art.title;
                reportBlock.appendChild(titleEl);

                // Таблиця Summary та Full Text
                const table = document.createElement('table');
                table.className = 'table table-bordered';
                table.style.marginBottom = '20px';

                const tbody = document.createElement('tbody');

                // Summary
                const trSummary = document.createElement('tr');
                const tdLabelSummary = document.createElement('th');
                tdLabelSummary.textContent = 'Summary';
                const tdSummary = document.createElement('td');
                tdSummary.textContent = art.summary_text;
                trSummary.appendChild(tdLabelSummary);
                trSummary.appendChild(tdSummary);
                tbody.appendChild(trSummary);

                // Full Text
                const trText = document.createElement('tr');
                const tdLabelText = document.createElement('th');
                tdLabelText.textContent = 'Full Text';
                const tdText = document.createElement('td');
                tdText.textContent = art.text;
                trText.appendChild(tdLabelText);
                trText.appendChild(tdText);
                tbody.appendChild(trText);

                table.appendChild(tbody);
                reportBlock.appendChild(table);

                // Pie Chart
                const canvas = document.createElement('canvas');
                canvas.id = `chart-${idx+1}`;
                canvas.width = 300;
                canvas.height = 300;
                reportBlock.appendChild(canvas);

                container.appendChild(reportBlock);

                const summary = art.summary || { Positive: 1, Neutral: 1, Negative: 1 };
                const labels = Object.keys(summary);
                const values = Object.values(summary);

                new Chart(canvas.getContext('2d'), {
                    type: 'pie',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Кількість текстів',
                            data: values,
                            backgroundColor: ['#FF6384','#36A2EB','#FFCE56','#8B0000','#006400']
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { position: 'bottom' } }
                    }
                });
            });
        })
        .catch(err => {
            console.error('Помилка завантаження звітів:', err);
            container.textContent = 'Не вдалося завантажити звіти.';
        });
});
