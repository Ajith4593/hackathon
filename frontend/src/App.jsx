import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Truck, Navigation2, Clock, Activity, Map as MapIcon, AlertTriangle, Settings, BarChart3, Download, FileText, Bell, Zap, Sliders, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { FleetPerformanceChart, AccuracyChart } from './components/Analytics';

// Fix for default marker icons in React-Leaflet
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

const App = () => {
    const [vehicles, setVehicles] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [activeTab, setActiveTab] = useState('overview');
    const wsRef = useRef(null);

    // Configuration State
    const [config, setConfig] = useState({
        realtime: true,
        notifications: true,
        ai: true,
        refreshRate: 1000
    });

    // Real-time Analytics State
    const [analyticsData, setAnalyticsData] = useState([]);
    const [metrics, setMetrics] = useState({
        totalDistance: 12450,
        fuelConsumed: 1240,
        efficiency: 94
    });

    // Generate Pan-India Mock Data
    const generateFleet = () => {
        const hubs = [
            { name: 'Mumbai', lat: 19.0760, lng: 72.8777 },
            { name: 'Delhi', lat: 28.6139, lng: 77.2090 },
            { name: 'Bangalore', lat: 12.9716, lng: 77.5946 },
            { name: 'Chennai', lat: 13.0827, lng: 80.2707 },
            { name: 'Kolkata', lat: 22.5726, lng: 88.3639 },
            { name: 'Hyderabad', lat: 17.3850, lng: 78.4867 },
            { name: 'Ahmedabad', lat: 23.0225, lng: 72.5714 },
            { name: 'Pune', lat: 18.5204, lng: 73.8567 },
            { name: 'Jaipur', lat: 26.9124, lng: 75.7873 },
            { name: 'Lucknow', lat: 26.8467, lng: 80.9461 },
            { name: 'Indore', lat: 22.7196, lng: 75.8577 },
            { name: 'Patna', lat: 25.5941, lng: 85.1376 },
            { name: 'Bhopal', lat: 23.2599, lng: 77.4126 },
            { name: 'Chandigarh', lat: 30.7333, lng: 76.7794 }
        ];

        let fleet = [];
        let idCounter = 1;

        hubs.forEach(hub => {
            // Generate 8-12 vehicles per hub for a denser map
            const count = 8 + Math.floor(Math.random() * 5);
            for (let i = 0; i < count; i++) {
                fleet.push({
                    id: idCounter++,
                    number: `IND-${hub.name.substring(0, 2).toUpperCase()}-${1000 + idCounter}`,
                    type: Math.random() > 0.5 ? 'Truck' : 'Van',
                    lat: hub.lat + (Math.random() - 0.5) * 0.15,
                    lng: hub.lng + (Math.random() - 0.5) * 0.15,
                    speed: Math.floor(40 + Math.random() * 40),
                    status: Math.random() > 0.2 ? 'Active' : 'Idle',
                    hub: hub.name
                });
            }
        });
        return fleet;
    };

    const generateAlerts = (fleet) => {
        const types = ['Overspeed', 'Route Deviation', 'Maintenance Due', 'Low Fuel', 'Harsh Braking'];
        const severities = ['High', 'Medium', 'Low'];

        // Pick random vehicles to have alerts
        const alertedVehicles = fleet.filter(() => Math.random() < 0.15); // 15% chance

        return alertedVehicles.map((v, index) => ({
            id: Date.now() + index, // Unique ID based on time
            type: types[Math.floor(Math.random() * types.length)],
            vehicle: v.number,
            location: v.hub,
            severity: severities[Math.floor(Math.random() * severities.length)],
            time: 'Just now'
        }));
    };

    // Initial Data Setup
    useEffect(() => {
        const initialFleet = generateFleet();
        setVehicles(initialFleet);
        setAlerts(generateAlerts(initialFleet));

        // WebSocket Logic
        const connectWebSocket = () => {
            if (!config.realtime) return; // Don't connect if disabled

            const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/tracking';
            wsRef.current = new WebSocket(wsUrl);

            wsRef.current.onopen = () => console.log('✅ Connected to Real-time Tracking System');
            wsRef.current.onmessage = (event) => {
                if (!config.realtime) return;
                try {
                    const update = JSON.parse(event.data);
                    setVehicles(prev => {
                        const idx = prev.findIndex(v => v.id === update.vehicle_id);
                        if (idx >= 0) {
                            const newVehicles = [...prev];
                            newVehicles[idx] = { ...newVehicles[idx], ...update };
                            return newVehicles;
                        }
                        return prev;
                    });
                } catch (e) { console.error(e); }
            };
        };
        // connectWebSocket(); // Keep WS but rely on sim for now

        // Simulation Loop
        const interval = setInterval(() => {
            if (!config.realtime) return;

            const now = new Date();
            const timeStr = `${now.getHours()}:${now.getMinutes() < 10 ? '0' : ''}${now.getMinutes()}:${now.getSeconds() < 10 ? '0' : ''}${now.getSeconds()}`;

            // 1. Move Vehicles
            setVehicles(prev => prev.map(v => {
                if (v.status === 'Idle') return v;
                return {
                    ...v,
                    lat: v.lat + (Math.random() - 0.5) * 0.002,
                    lng: v.lng + (Math.random() - 0.5) * 0.002,
                    speed: Math.max(0, Math.min(100, v.speed + (Math.random() - 0.5) * 5))
                };
            }));

            // 2. Dynamic Alerts (Randomly add new alerts)
            if (Math.random() > 0.7) { // 30% chance every tick
                setAlerts(prev => {
                    const randomVehicle = vehicles[Math.floor(Math.random() * vehicles.length)];
                    if (!randomVehicle) return prev;

                    const newAlert = {
                        id: Date.now(),
                        type: ['Overspeed', 'Geofence Breach', 'Low Battery', 'SOS'].sort(() => 0.5 - Math.random())[0],
                        vehicle: randomVehicle.number,
                        location: randomVehicle.hub,
                        severity: Math.random() > 0.5 ? 'High' : 'Medium',
                        time: 'Just now'
                    };
                    const newAlerts = [newAlert, ...prev];
                    if (newAlerts.length > 20) newAlerts.pop(); // Keep list manageable
                    return newAlerts;
                });
            }

            // 3. Update time on existing alerts
            setAlerts(prev => prev.map(a => {
                if (a.time === 'Just now') return { ...a, time: '1m ago' };
                if (a.time === '1m ago') return { ...a, time: '2m ago' };
                return a;
            }));

            // 4. Update Analytics
            setAnalyticsData(current => {
                const activeCount = vehicles.filter(v => v.status === 'Active').length;
                const newData = [...current, { time: timeStr, active: activeCount, anomalies: Math.floor(Math.random() * 5) }];
                if (newData.length > 10) newData.shift();
                return newData;
            });

            setMetrics(m => ({
                totalDistance: m.totalDistance + (vehicles.length * 0.1), // Increased increment
                fuelConsumed: m.fuelConsumed + (vehicles.length * 0.02),
                efficiency: 90 + Math.random() * 5
            }));

        }, config.refreshRate);

        return () => {
            if (wsRef.current) wsRef.current.close();
            clearInterval(interval);
        };
    }, [config.realtime, config.refreshRate]);

    const renderContent = () => {
        switch (activeTab) {
            case 'overview': return <OverviewView vehicles={vehicles} alerts={alerts} analyticsData={analyticsData} />;
            case 'analytics': return <AnalyticsView vehicles={vehicles} metrics={metrics} analyticsData={analyticsData} />;
            case 'alerts': return <AlertsView alerts={alerts} />;
            case 'reports': return <ReportsView alerts={alerts} />;
            case 'config': return <ConfigView config={config} setConfig={setConfig} />;
            default: return <OverviewView vehicles={vehicles} alerts={alerts} analyticsData={analyticsData} />;
        }
    };

    return (
        <div className="app-container">
            <aside className="sidebar">
                <div className="brand">
                    <div className="brand-icon"><Navigation2 size={24} color="white" /></div>
                    <h1 className="premium-gradient-text">TRAXION</h1>
                </div>

                <nav className="nav-menu">
                    <NavItem icon={<MapIcon size={20} />} label="Fleet Overview" active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} />
                    <NavItem icon={<Activity size={20} />} label="Live Analytics" active={activeTab === 'analytics'} onClick={() => setActiveTab('analytics')} />
                    <NavItem icon={<AlertTriangle size={20} />} label="Alert Center" count={alerts.length} active={activeTab === 'alerts'} onClick={() => setActiveTab('alerts')} />
                    <NavItem icon={<BarChart3 size={20} />} label="Reports" active={activeTab === 'reports'} onClick={() => setActiveTab('reports')} />
                    <NavItem icon={<Settings size={20} />} label="System Config" active={activeTab === 'config'} onClick={() => setActiveTab('config')} />
                </nav>

                <div style={{ marginTop: 'auto' }}>
                    <div className="glass-panel" style={{ padding: '1rem' }}>
                        <h4 style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem', textTransform: 'uppercase' }}>System Health</h4>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                            <span>Cloud Status</span>
                            <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent)' }}>
                                <span className={`animate-pulse`} style={{ width: 8, height: 8, borderRadius: '50%', background: config.realtime ? 'var(--accent)' : '#ef4444' }}></span>
                                {config.realtime ? 'Active' : 'Paused'}
                            </span>
                        </div>
                    </div>
                </div>
            </aside>

            <main className="main-content">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={activeTab}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.2 }}
                        style={{ height: '100%', width: '100%' }}
                    >
                        {renderContent()}
                    </motion.div>
                </AnimatePresence>
            </main>
        </div>
    );
};

// --- Sub-Views ---

const OverviewView = ({ vehicles, alerts, analyticsData }) => (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
        <div className="map-container" style={{ width: '100%', height: '100%' }}>
            {/* Center map on India roughly */}
            <MapContainer center={[20.5937, 78.9629]} zoom={5} style={{ width: '100%', height: '100%' }} zoomControl={false}>
                <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" attribution='&copy; OpenStreetMap &copy; CARTO' />
                {vehicles.map(v => (
                    <Marker key={v.id} position={[v.lat, v.lng]}>
                        <Popup>
                            <div style={{ padding: '0.5rem' }}>
                                <h3 style={{ borderBottom: '1px solid #333', paddingBottom: '0.25rem', marginBottom: '0.5rem', fontWeight: 'bold' }}>{v.number}</h3>
                                <div style={{ fontSize: '0.75rem' }}>
                                    <p>Speed: <b>{v.speed} km/h</b></p>
                                    <p>Location: <b>{v.hub} Region</b></p>
                                    <p>Status: <span style={{ color: v.status === 'Active' ? '#10b981' : '#94a3b8' }}>{v.status}</span></p>
                                </div>
                            </div>
                        </Popup>
                    </Marker>
                ))}
            </MapContainer>
        </div>

        <div className="top-overlay-left">
            <div className="glass-panel stats-bar">
                <StatItem icon={<Truck className="text-blue-400" />} label="Pan-India Fleet" value={vehicles.length} />
                <div className="divider"></div>
                <StatItem icon={<AlertTriangle className="text-amber-400" />} label="Active Alerts" value={alerts.length} />
                <div className="divider"></div>
                <StatItem icon={<Clock className="text-purple-400" />} label="Avg. Latency" value="24ms" />
            </div>
        </div>

        <div className="top-overlay-right">
            {alerts.length > 0 && (
                <div className="glass-panel" style={{ padding: '1.25rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <AlertTriangle size={16} className="text-red-500" />
                            Critical Alerts (Top 3)
                        </h3>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                        {alerts.slice(0, 3).map(a => (
                            <div key={a.id} style={{ padding: '0.75rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '8px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.25rem' }}>
                                    <span style={{ color: '#ef4444', fontWeight: 700 }}>{a.type}</span>
                                    <span style={{ color: '#94a3b8' }}>{a.location}</span>
                                </div>
                                <p style={{ fontSize: '0.875rem', fontWeight: 500 }}>{a.vehicle}</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>

        <div className="bottom-analytics">
            <div className="glass-panel chart-card main">
                <div className="chart-title"><Activity size={16} className="text-blue-400" /> Fleet Activity Correlation</div>
                <div style={{ flex: 1, position: 'relative' }}><FleetPerformanceChart liveData={analyticsData} /></div>
            </div>
            <div className="glass-panel chart-card side">
                <div className="chart-title"><Zap size={16} className="text-emerald-400" /> Real-Time Accuracy</div>
                <div style={{ flex: 1, position: 'relative' }}><AccuracyChart accuracy={90 + Math.random() * 5} /></div>
            </div>
        </div>
    </div>
);

const AnalyticsView = ({ vehicles, metrics, analyticsData }) => (
    <div style={{ padding: '2rem', height: '100%', overflowY: 'auto' }}>
        <h2 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '2rem' }}>Live Analytics</h2>

        {/* Top Metrics Row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.5rem', marginBottom: '2rem' }}>
            <div className="glass-panel" style={{ padding: '1.5rem' }}>
                <h4 style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.5rem' }}>TOTAL DISTANCE</h4>
                <p style={{ fontSize: '2rem', fontWeight: 'bold' }}>{metrics.totalDistance.toFixed(1)} <span style={{ fontSize: '1rem', color: '#94a3b8' }}>km</span></p>
                <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#10b981', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <span style={{ padding: '2px 6px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '4px' }}>+{(vehicles.length * 0.1).toFixed(1)} km</span> since start
                </div>
            </div>
            <div className="glass-panel" style={{ padding: '1.5rem' }}>
                <h4 style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.5rem' }}>FUEL CONSUMED</h4>
                <p style={{ fontSize: '2rem', fontWeight: 'bold' }}>{metrics.fuelConsumed.toFixed(1)} <span style={{ fontSize: '1rem', color: '#94a3b8' }}>L</span></p>
                <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <span style={{ padding: '2px 6px', background: 'rgba(245, 158, 11, 0.1)', borderRadius: '4px' }}>Normal</span> consumption
                </div>
            </div>
            <div className="glass-panel" style={{ padding: '1.5rem' }}>
                <h4 style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.5rem' }}>AVG EFFICIENCY</h4>
                <p style={{ fontSize: '2rem', fontWeight: 'bold', color: '#10b981' }}>{metrics.efficiency.toFixed(1)}%</p>
                <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#10b981', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <span style={{ padding: '2px 6px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '4px' }}>+2.4%</span> improvement
                </div>
            </div>
            <div className="glass-panel" style={{ padding: '1.5rem' }}>
                <h4 style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.5rem' }}>ACTIVE FLEET</h4>
                <p style={{ fontSize: '2rem', fontWeight: 'bold' }}>{vehicles.filter(v => v.status === 'Active').length}/{vehicles.length}</p>
                <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#3b82f6', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <span style={{ padding: '2px 6px', background: 'rgba(59, 130, 246, 0.1)', borderRadius: '4px' }}>98%</span> operational
                </div>
            </div>
        </div>

        {/* Charts Row - Full Width */}
        <div className="glass-panel" style={{ padding: '2rem', height: '400px', marginBottom: '2rem', display: 'flex', flexDirection: 'column' }}>
            <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Activity size={18} className="text-blue-400" /> Fleet Performance Overview
            </h3>
            <div style={{ flex: 1, position: 'relative' }}>
                <FleetPerformanceChart liveData={analyticsData} />
            </div>
        </div>
    </div>
);

const AlertsView = ({ alerts }) => (
    <div style={{ padding: '2rem', height: '100%', overflowY: 'auto', maxWidth: '800px', margin: '0 auto' }}>
        <h2 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <AlertTriangle size={32} className="text-red-500" /> Alert Center
        </h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {alerts.map(a => (
                <div key={a.id} className="glass-panel" style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                        <div style={{ width: 40, height: 40, borderRadius: '50%', background: 'rgba(239, 68, 68, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <AlertTriangle size={20} className="text-red-500" />
                        </div>
                        <div>
                            <h4 style={{ fontSize: '1.125rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>{a.type}</h4>
                            <p style={{ color: '#94a3b8' }}>Vehicle: <span style={{ color: 'white' }}>{a.vehicle}</span> • Loc: {a.location}</p>
                        </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                        <div style={{ padding: '4px 12px', borderRadius: '20px', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', fontSize: '0.75rem', fontWeight: 'bold', display: 'inline-block', marginBottom: '0.5rem' }}>
                            {a.severity.toUpperCase()} PRIORITY
                        </div>
                        <p style={{ fontSize: '0.875rem', color: '#94a3b8' }}>{a.time}</p>
                    </div>
                </div>
            ))}
        </div>
    </div>
);

const ReportsView = ({ alerts = [] }) => {
    const [selectedReport, setSelectedReport] = useState(null);

    // Dynamic Live Report + Static History
    const reports = [
        {
            id: `LIVE-${new Date().toLocaleDateString().replace(/\//g, '')}`,
            date: 'Today (Live)',
            type: 'Real-time Alert Log',
            status: 'ACTIVE',
            content: `Contains ${alerts.length} real-time alerts from current session.`,
            isLive: true,
            data: alerts
        },
        { id: 'RPT-2024-001', date: 'Jan 11, 2024', type: 'Monthly Fleet Efficiency', status: 'COMPLETED', content: 'Efficiency rating: 94%. Total Fuel: 1240L. Active time: 842hrs.' },
        { id: 'RPT-2024-002', date: 'Jan 12, 2024', type: 'Route Deviation Analysis', status: 'COMPLETED', content: 'Deviations detected: 3. Critical: 1. Resolved: 2.' },
        { id: 'RPT-2024-003', date: 'Jan 13, 2024', type: 'Vehicle Maintenance Log', status: 'PENDING', content: 'Scheduled maintenance for: IND-MH-1002, IND-DL-1005.' },
        { id: 'RPT-2024-004', date: 'Jan 14, 2024', type: 'Driver Performance Review', status: 'COMPLETED', content: 'Top driver: Rajesh Kumar (Score 98). Needs improvement: Suresh (Score 72).' }
    ];

    const downloadReport = (report) => {
        let csvContent = "data:text/csv;charset=utf-8,";
        let filename = `${report.id}.csv`;

        if (report.isLive) {
            // Detailed CSV for Alerts
            const headers = ["Alert ID", "Type", "Vehicle", "Location", "Severity", "Time"];
            const rows = report.data.map(a => [a.id, a.type, a.number || a.vehicle, a.location || a.hub, a.severity, a.time]);
            csvContent += headers.join(",") + "\n" + rows.map(e => e.join(",")).join("\n");
        } else {
            // Simple Summary for Static Reports
            csvContent += "Report ID,Date,Type,Content\n";
            csvContent += `${report.id},${report.date},${report.type},"${report.content}"`;
        }

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <div style={{ padding: '2rem', height: '100%', overflowY: 'auto', position: 'relative' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <h2 style={{ fontSize: '2rem', fontWeight: 'bold' }}>Generated Reports</h2>
            </div>
            <div className="glass-panel" style={{ overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead style={{ background: 'rgba(255,255,255,0.05)', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                        <tr>
                            <th style={{ padding: '1.25rem', fontWeight: 600, color: '#94a3b8' }}>REPORT ID</th>
                            <th style={{ padding: '1.25rem', fontWeight: 600, color: '#94a3b8' }}>DATE</th>
                            <th style={{ padding: '1.25rem', fontWeight: 600, color: '#94a3b8' }}>TYPE</th>
                            <th style={{ padding: '1.25rem', fontWeight: 600, color: '#94a3b8' }}>STATUS</th>
                            <th style={{ padding: '1.25rem', fontWeight: 600, color: '#94a3b8' }}>ACTION</th>
                        </tr>
                    </thead>
                    <tbody>
                        {reports.map((report, i) => (
                            <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', transition: 'background 0.2s' }} className="hover:bg-white/5">
                                <td style={{ padding: '1.25rem', fontFamily: 'monospace' }}>{report.id}</td>
                                <td style={{ padding: '1.25rem' }}>{report.date}</td>
                                <td style={{ padding: '1.25rem' }}>{report.type}</td>
                                <td style={{ padding: '1.25rem' }}>
                                    <span style={{
                                        padding: '4px 8px',
                                        borderRadius: '4px',
                                        background: report.status === 'COMPLETED' ? 'rgba(16, 185, 129, 0.1)' : (report.status === 'ACTIVE' ? 'rgba(59, 130, 246, 0.1)' : 'rgba(245, 158, 11, 0.1)'),
                                        color: report.status === 'COMPLETED' ? '#10b981' : (report.status === 'ACTIVE' ? '#3b82f6' : '#f59e0b'),
                                        fontSize: '0.75rem',
                                        fontWeight: 'bold'
                                    }}>
                                        {report.status}
                                    </span>
                                </td>
                                <td style={{ padding: '1.25rem', display: 'flex', gap: '1rem' }}>
                                    <button
                                        onClick={() => setSelectedReport(report)}
                                        style={{ background: 'none', border: 'none', color: '#60a5fa', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                                    >
                                        <FileText size={16} /> View
                                    </button>
                                    <button
                                        onClick={() => downloadReport(report)}
                                        style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                                        title="Download CSV"
                                    >
                                        <Download size={16} />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* View Report Modal */}
            <AnimatePresence>
                {selectedReport && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}
                        onClick={() => setSelectedReport(null)}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            className="glass-panel"
                            style={{ width: '500px', padding: '2rem', background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)' }}
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
                                <div>
                                    <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>Report Details</h3>
                                    <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>{selectedReport.id}</p>
                                </div>
                                <button onClick={() => setSelectedReport(null)} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '1.5rem' }}>&times;</button>
                            </div>

                            <div style={{ marginBottom: '1.5rem' }}>
                                <label style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 'bold' }}>Type</label>
                                <p style={{ fontSize: '1.125rem' }}>{selectedReport.type}</p>
                            </div>

                            <div style={{ marginBottom: '1.5rem' }}>
                                <label style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 'bold' }}>Date Generated</label>
                                <p>{selectedReport.date}</p>
                            </div>

                            <div style={{ marginBottom: '2rem', padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                                <label style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>Summary Content</label>
                                <p style={{ lineHeight: 1.6 }}>{selectedReport.content}</p>
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                                <button
                                    onClick={() => setSelectedReport(null)}
                                    style={{ padding: '0.5rem 1rem', background: 'none', border: '1px solid rgba(255,255,255,0.1)', color: 'white', borderRadius: '6px', cursor: 'pointer' }}
                                >
                                    Close
                                </button>
                                <button
                                    onClick={() => { downloadCSV(); setSelectedReport(null); }}
                                    style={{ padding: '0.5rem 1rem', background: '#3b82f6', color: 'white', borderRadius: '6px', border: 'none', cursor: 'pointer' }}
                                >
                                    Download
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

const ConfigView = ({ config, setConfig }) => (
    <div style={{ padding: '2rem', height: '100%', overflowY: 'auto', maxWidth: '600px', margin: '0 auto' }}>
        <h2 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '2rem' }}>System Configuration</h2>

        <div className="glass-panel" style={{ padding: '2rem', marginBottom: '1.5rem' }}>
            <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}><Sliders size={20} className="text-blue-400" /> General Settings</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <ConfigToggle
                    label="Real-Time Data Streams"
                    desc="Enable WebSocket connections for live tracking"
                    active={config.realtime}
                    onClick={() => setConfig(prev => ({ ...prev, realtime: !prev.realtime }))}
                />
                <ConfigToggle
                    label="Push Notifications"
                    desc="Receive alerts directly to your desktop"
                    active={config.notifications}
                    onClick={() => setConfig(prev => ({ ...prev, notifications: !prev.notifications }))}
                />
                <ConfigToggle
                    label="AI Predictions"
                    desc="Use LSTM models for ETA calculation"
                    active={config.ai}
                    onClick={() => setConfig(prev => ({ ...prev, ai: !prev.ai }))}
                />
            </div>
        </div>

        <div className="glass-panel" style={{ padding: '2rem' }}>
            <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}><Zap size={20} className="text-amber-400" /> Performance</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <label style={{ fontSize: '0.875rem', fontWeight: 600 }}>Data Refresh Rate ({config.refreshRate}ms)</label>
                <input
                    type="range"
                    min="100"
                    max="5000"
                    value={config.refreshRate}
                    onChange={(e) => setConfig(prev => ({ ...prev, refreshRate: parseInt(e.target.value) }))}
                    style={{ width: '100%', accentColor: '#3b82f6' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#94a3b8' }}>
                    <span>100ms (High CPU)</span>
                    <span>5000ms (Battery Saver)</span>
                </div>
            </div>
        </div>
    </div>
);

const ConfigToggle = ({ label, desc, active, onClick }) => (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
            <h4 style={{ fontWeight: 600, marginBottom: '0.25rem' }}>{label}</h4>
            <p style={{ fontSize: '0.875rem', color: '#94a3b8' }}>{desc}</p>
        </div>
        <div
            onClick={onClick}
            style={{ width: 44, height: 24, background: active ? '#3b82f6' : '#334155', borderRadius: 999, position: 'relative', cursor: 'pointer', transition: 'background 0.2s' }}
        >
            <div style={{ width: 20, height: 20, background: 'white', borderRadius: '50%', position: 'absolute', top: 2, left: active ? 22 : 2, transition: 'left 0.2s' }}></div>
        </div>
    </div>
);

const NavItem = ({ icon, label, active, count, onClick }) => (
    <div className={`nav-item ${active ? 'active' : ''}`} onClick={onClick}>
        <div className="nav-content">{icon}<span>{label}</span></div>
        {count > 0 && <span className="badge">{count}</span>}
    </div>
);

const StatItem = ({ icon, label, value }) => (
    <div className="stat-item">
        <div className="stat-icon">{icon}</div>
        <div className="stat-text"><div>{label}</div><div>{value}</div></div>
    </div>
);

export default App;
