/* ==========================================================================
   SmartLeave Dashboard Analytics (Chart.js charts & Admin management)
   ========================================================================== */

function renderAdminCharts(chartsData) {
    if (!chartsData || !window.Chart) return;

    // 1. Leave Categories Doughnut Chart
    const catCtx = document.getElementById('chart-categories');
    if (catCtx) {
        new Chart(catCtx, {
            type: 'doughnut',
            data: {
                labels: ['Medical', 'Personal', 'Urgent'],
                datasets: [{
                    data: [
                        chartsData.categories.Medical || 0,
                        chartsData.categories.Personal || 0,
                        chartsData.categories.Urgent || 0
                    ],
                    backgroundColor: ['#0369A1', '#8B5CF6', '#BE123C'],
                    borderWidth: 2,
                    borderColor: 'var(--bg-card)'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }

    // 2. Status Bar Chart
    const statusCtx = document.getElementById('chart-status');
    if (statusCtx) {
        new Chart(statusCtx, {
            type: 'bar',
            data: {
                labels: ['Pending / Forwarded', 'Approved', 'Rejected'],
                datasets: [{
                    label: 'Leave Requests',
                    data: [
                        chartsData.status.Pending || 0,
                        chartsData.status.Approved || 0,
                        chartsData.status.Rejected || 0
                    ],
                    backgroundColor: ['#F59E0B', '#10B981', '#EF4444'],
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true, ticks: { precision: 0 } }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
}
