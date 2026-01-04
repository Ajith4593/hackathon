import React from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    Filler,
    ArcElement,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    Filler,
    ArcElement
);

// ... (FleetPerformanceChart and AccuracyChart remain unchanged) ...

export const FleetPerformanceChart = ({ liveData = [] }) => {
    // Generate labels based on timestamp or index if not provided
    const labels = liveData.length > 0
        ? liveData.map(d => d.time)
        : ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'];

    const activeData = liveData.length > 0
        ? liveData.map(d => d.active)
        : [12, 19, 65, 87, 72, 45];

    const anomalyData = liveData.length > 0
        ? liveData.map(d => d.anomalies)
        : [1, 2, 4, 8, 3, 2];

    const data = {
        labels,
        datasets: [
            {
                label: 'Active Vehicles',
                data: activeData,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4,
                yAxisID: 'y',
            },
            {
                label: 'Anomalies',
                data: anomalyData,
                borderColor: '#f43f5e',
                backgroundColor: 'rgba(244, 63, 94, 0.1)',
                fill: true,
                tension: 0.4,
                yAxisID: 'y1',
            }
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true, // Show legend so user knows which axis is which
                labels: { color: '#94a3b8' }
            },
        },
        scales: {
            y: {
                type: 'linear',
                display: true,
                position: 'left',
                grid: { color: 'rgba(255, 255, 255, 0.05)' },
                ticks: { color: '#3b82f6' }, // Blue text for Active
                min: 0,
            },
            y1: {
                type: 'linear',
                display: true,
                position: 'right',
                grid: { drawOnChartArea: false }, // Only show grid for left axis
                ticks: { color: '#f43f5e' }, // Red text for Anomalies
                min: 0,
                suggestedMax: 10
            },
            x: {
                grid: { display: false },
                ticks: { color: '#64748b', maxTicksLimit: 6 }
            }
        },
        animation: {
            duration: 0
        }
    };

    return <Line data={data} options={options} />;
};

export const AccuracyChart = ({ accuracy = 95 }) => {
    // Create a mock history based on the current accuracy fluctuation
    // In a real scenario, this would also take a history array
    const data = {
        labels: ['-50s', '-40s', '-30s', '-20s', '-10s', 'Now'],
        datasets: [
            {
                label: 'GPS Accuracy (%)',
                data: [92, 94, 89, 96, 98, accuracy],
                borderColor: '#10b981', // Emerald green
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                fill: true,
                tension: 0.4,
            }
        ],
    };

    const options = {
        responsive: true,
        plugins: {
            legend: { display: false },
        },
        scales: {
            y: {
                min: 80,
                max: 100,
                grid: { color: 'rgba(255, 255, 255, 0.05)' },
                ticks: { color: '#64748b' }
            },
            x: {
                grid: { display: false },
                ticks: { color: '#64748b' }
            }
        },
        animation: { duration: 0 }
    };

    return <Line data={data} options={options} />;
};

export const RegionalDistributionChart = ({ vehicles = [] }) => {
    // Aggregate vehicles by hub
    const hubCounts = vehicles.reduce((acc, v) => {
        const hub = v.hub || 'Unknown';
        acc[hub] = (acc[hub] || 0) + 1;
        return acc;
    }, {});

    const labels = Object.keys(hubCounts);
    const dataValues = Object.values(hubCounts);

    const data = {
        labels: labels,
        datasets: [
            {
                label: 'Vehicles',
                data: dataValues,
                backgroundColor: [
                    'rgba(59, 130, 246, 0.7)', // Blue
                    'rgba(16, 185, 129, 0.7)', // Green
                    'rgba(245, 158, 11, 0.7)', // Amber
                    'rgba(239, 68, 68, 0.7)', // Red
                    'rgba(139, 92, 246, 0.7)', // Purple
                    'rgba(236, 72, 153, 0.7)', // Pink
                    'rgba(20, 184, 166, 0.7)', // Teal
                    'rgba(99, 102, 241, 0.7)', // Indigo
                ],
                borderColor: 'rgba(0,0,0,0)',
                borderWidth: 1,
            },
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'right',
                labels: { color: '#94a3b8', boxWidth: 12 }
            },
        },
    };

    return <Doughnut data={data} options={options} />;
};
