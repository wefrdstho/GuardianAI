/* ═══════════════════════════════════════════════════════════
   GuardianAI — Main Application Script
   Vanilla JS SPA with API integration
   ═══════════════════════════════════════════════════════════ */

(() => {
    'use strict';

    // ─── Configuration ───
    const API_BASE = 'http://localhost:8000';
    const WS_BASE = 'ws://localhost:8000';

    // ─── State ───
    const state = {
        token: localStorage.getItem('guardianai_token') || null,
        user: JSON.parse(localStorage.getItem('guardianai_user') || 'null'),
        currentPanel: 'sos-panel',
        location: { lat: null, lng: null, address: null },
        ws: null,
        wsReconnectTimer: null,
        map: null,
        mapMarkers: [],
        userMarker: null,
        sosHoldTimer: null,
        sosHolding: false,
    };

    // ═══════════════════════════════════════════════════════
    // API SERVICE
    // ═══════════════════════════════════════════════════════
    const api = {
        async request(method, path, body = null) {
            const headers = { 'Content-Type': 'application/json' };
            if (state.token) headers['Authorization'] = `Bearer ${state.token}`;

            const opts = { method, headers };
            if (body) opts.body = JSON.stringify(body);

            const res = await fetch(`${API_BASE}${path}`, opts);
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Request failed');
            return data;
        },

        // Auth
        login: (username, password) => api.request('POST', '/api/auth/login', { username, password }),
        register: (data) => api.request('POST', '/api/auth/register', data),
        getMe: () => api.request('GET', '/api/auth/me'),

        // Emergency
        analyze: (text, lat, lng) => api.request('POST', '/api/emergency/analyze', {
            text, latitude: lat, longitude: lng
        }),
        triggerSOS: (lat, lng, message) => api.request('POST', '/api/emergency/sos', {
            latitude: lat, longitude: lng, message
        }),

        // Guardians
        getGuardians: () => api.request('GET', '/api/guardians/'),
        addGuardian: (data) => api.request('POST', '/api/guardians/', data),
        deleteGuardian: (id) => api.request('DELETE', `/api/guardians/${id}`),

        // Incidents
        getIncidents: () => api.request('GET', '/api/incidents/'),
        getAnalytics: () => api.request('GET', '/api/incidents/analytics'),
    };

    // ═══════════════════════════════════════════════════════
    // TOAST NOTIFICATIONS
    // ═══════════════════════════════════════════════════════
    function showToast(message, type = 'info', duration = 4000) {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icons = {
            success: 'check-circle', error: 'x-circle',
            warning: 'alert-triangle', info: 'info'
        };
        toast.innerHTML = `<i data-lucide="${icons[type] || 'info'}"></i><span>${message}</span>`;
        container.appendChild(toast);
        lucide.createIcons({ nodes: [toast] });

        setTimeout(() => {
            toast.classList.add('removing');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    // ═══════════════════════════════════════════════════════
    // AUTH
    // ═══════════════════════════════════════════════════════
    function initAuth() {
        const loginForm = document.getElementById('login-form');
        const registerForm = document.getElementById('register-form');
        const showRegBtn = document.getElementById('show-register');
        const showLogBtn = document.getElementById('show-login');
        const authError = document.getElementById('auth-error');

        showRegBtn.addEventListener('click', (e) => {
            e.preventDefault();
            loginForm.classList.remove('active');
            registerForm.classList.add('active');
            authError.classList.remove('show');
        });

        showLogBtn.addEventListener('click', (e) => {
            e.preventDefault();
            registerForm.classList.remove('active');
            loginForm.classList.add('active');
            authError.classList.remove('show');
        });

        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('login-btn');
            btn.disabled = true;
            btn.querySelector('span').textContent = 'Signing in...';

            try {
                const username = document.getElementById('login-username').value;
                const password = document.getElementById('login-password').value;
                const data = await api.login(username, password);
                saveAuth(data);
                showDashboard();
            } catch (err) {
                authError.textContent = err.message;
                authError.classList.add('show');
            } finally {
                btn.disabled = false;
                btn.querySelector('span').textContent = 'Sign In';
            }
        });

        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('register-btn');
            btn.disabled = true;
            btn.querySelector('span').textContent = 'Creating...';

            try {
                const data = await api.register({
                    full_name: document.getElementById('reg-fullname').value,
                    username: document.getElementById('reg-username').value,
                    email: document.getElementById('reg-email').value,
                    phone: document.getElementById('reg-phone').value,
                    password: document.getElementById('reg-password').value,
                });
                saveAuth(data);
                showDashboard();
            } catch (err) {
                authError.textContent = err.message;
                authError.classList.add('show');
            } finally {
                btn.disabled = false;
                btn.querySelector('span').textContent = 'Create Account';
            }
        });

        document.getElementById('logout-btn').addEventListener('click', logout);
    }

    function saveAuth(data) {
        state.token = data.access_token;
        state.user = data.user;
        localStorage.setItem('guardianai_token', data.access_token);
        localStorage.setItem('guardianai_user', JSON.stringify(data.user));
    }

    function logout() {
        state.token = null;
        state.user = null;
        localStorage.removeItem('guardianai_token');
        localStorage.removeItem('guardianai_user');
        if (state.ws) state.ws.close();
        document.getElementById('auth-screen').classList.remove('hidden');
        document.getElementById('dashboard').classList.add('hidden');
    }

    function showDashboard() {
        document.getElementById('auth-screen').classList.add('hidden');
        document.getElementById('dashboard').classList.remove('hidden');

        // Update user info
        const user = state.user;
        document.getElementById('user-name').textContent = user.full_name || user.username;
        document.getElementById('user-role').textContent = user.role;
        document.getElementById('user-avatar').textContent = (user.full_name || user.username).charAt(0).toUpperCase();

        // Init dashboard features
        fetchLocation();
        connectWebSocket();
        switchPanel('sos-panel');
    }

    // ═══════════════════════════════════════════════════════
    // LOCATION
    // ═══════════════════════════════════════════════════════
    function fetchLocation() {
        const locText = document.getElementById('current-location-text');

        if (!navigator.geolocation) {
            locText.textContent = 'Geolocation not supported';
            // Use default coords (New Delhi)
            state.location = { lat: 28.6139, lng: 77.2090, address: 'New Delhi, India' };
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (pos) => {
                state.location.lat = pos.coords.latitude;
                state.location.lng = pos.coords.longitude;
                locText.textContent = `${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}`;

                // Reverse geocode
                fetch(`https://nominatim.openstreetmap.org/reverse?lat=${pos.coords.latitude}&lon=${pos.coords.longitude}&format=json`)
                    .then(r => r.json())
                    .then(data => {
                        const addr = data.display_name || `${pos.coords.latitude}, ${pos.coords.longitude}`;
                        state.location.address = addr;
                        const short = addr.split(',').slice(0, 3).join(',');
                        locText.textContent = short;
                    })
                    .catch(() => {});
            },
            () => {
                locText.textContent = 'Location access denied';
                // Fallback
                state.location = { lat: 28.6139, lng: 77.2090, address: 'New Delhi, India (default)' };
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );

        // Watch position updates
        navigator.geolocation.watchPosition(
            (pos) => {
                state.location.lat = pos.coords.latitude;
                state.location.lng = pos.coords.longitude;
                if (state.userMarker && state.map) {
                    state.userMarker.setLatLng([pos.coords.latitude, pos.coords.longitude]);
                }
            },
            () => {},
            { enableHighAccuracy: true }
        );
    }

    // ═══════════════════════════════════════════════════════
    // WEBSOCKET
    // ═══════════════════════════════════════════════════════
    function connectWebSocket() {
        if (!state.user) return;
        const wsStatus = document.getElementById('ws-status');

        try {
            state.ws = new WebSocket(`${WS_BASE}/ws/${state.user.id}`);

            state.ws.onopen = () => {
                wsStatus.className = 'ws-status connected';
                wsStatus.querySelector('span').textContent = 'Connected';
            };

            state.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleWSMessage(data);
                } catch (e) {}
            };

            state.ws.onclose = () => {
                wsStatus.className = 'ws-status';
                wsStatus.querySelector('span').textContent = 'Disconnected';
                // Reconnect after 5s
                if (state.token) {
                    state.wsReconnectTimer = setTimeout(connectWebSocket, 5000);
                }
            };

            state.ws.onerror = () => {
                wsStatus.className = 'ws-status error';
                wsStatus.querySelector('span').textContent = 'Connection error';
            };

            // Keepalive ping
            setInterval(() => {
                if (state.ws && state.ws.readyState === WebSocket.OPEN) {
                    state.ws.send(JSON.stringify({ type: 'ping' }));
                }
            }, 30000);
        } catch (e) {
            wsStatus.className = 'ws-status error';
            wsStatus.querySelector('span').textContent = 'Cannot connect';
        }
    }

    function handleWSMessage(data) {
        if (data.type === 'alert') {
            showToast(data.message, 'warning');
        } else if (data.type === 'status_update') {
            showToast(data.message, 'info');
        }
    }

    // ═══════════════════════════════════════════════════════
    // NAVIGATION
    // ═══════════════════════════════════════════════════════
    function initNavigation() {
        const navItems = document.querySelectorAll('.nav-item[data-panel]');
        const panelTitles = {
            'sos-panel': 'Emergency SOS',
            'analyze-panel': 'AI Emergency Brain',
            'map-panel': 'Live Map',
            'guardians-panel': 'Guardian Network',
            'incidents-panel': 'Incident Log',
            'analytics-panel': 'Analytics Dashboard',
        };

        navItems.forEach(item => {
            item.addEventListener('click', () => {
                const panelId = item.dataset.panel;
                switchPanel(panelId);
                document.getElementById('panel-title').textContent = panelTitles[panelId] || '';

                // Close mobile sidebar
                document.getElementById('sidebar').classList.remove('open');
            });
        });

        // Mobile menu toggle
        document.getElementById('menu-toggle').addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('open');
        });

        // Close sidebar on outside click (mobile)
        document.querySelector('.main-content').addEventListener('click', () => {
            document.getElementById('sidebar').classList.remove('open');
        });
    }

    function switchPanel(panelId) {
        // Deactivate all
        document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
        document.querySelectorAll('.nav-item[data-panel]').forEach(n => n.classList.remove('active'));

        // Activate target
        document.getElementById(panelId).classList.add('active');
        const navBtn = document.querySelector(`.nav-item[data-panel="${panelId}"]`);
        if (navBtn) navBtn.classList.add('active');

        state.currentPanel = panelId;

        // Panel-specific init
        if (panelId === 'map-panel') initMap();
        if (panelId === 'guardians-panel') loadGuardians();
        if (panelId === 'incidents-panel') loadIncidents();
        if (panelId === 'analytics-panel') loadAnalytics();
    }

    // ═══════════════════════════════════════════════════════
    // SOS BUTTON
    // ═══════════════════════════════════════════════════════
    function initSOS() {
        const btn = document.getElementById('sos-button');
        const statusEl = document.getElementById('sos-status');
        let holdStart = 0;

        btn.addEventListener('mousedown', startHold);
        btn.addEventListener('touchstart', (e) => { e.preventDefault(); startHold(); });
        btn.addEventListener('mouseup', endHold);
        btn.addEventListener('mouseleave', endHold);
        btn.addEventListener('touchend', endHold);
        btn.addEventListener('touchcancel', endHold);

        function startHold() {
            holdStart = Date.now();
            state.sosHolding = true;
            btn.classList.add('holding');
            statusEl.innerHTML = '<p style="color: var(--accent-amber);">⏳ Keep holding... 2 seconds to activate</p>';

            state.sosHoldTimer = setTimeout(() => {
                if (state.sosHolding) {
                    triggerSOS();
                }
            }, 2000);
        }

        function endHold() {
            if (!state.sosHolding) return;
            state.sosHolding = false;
            btn.classList.remove('holding');
            clearTimeout(state.sosHoldTimer);

            const held = Date.now() - holdStart;
            if (held < 2000) {
                statusEl.innerHTML = '<p>Released too early. Hold for 2 full seconds to trigger SOS.</p>';
            }
        }

        async function triggerSOS() {
            const btn = document.getElementById('sos-button');
            btn.classList.add('activated');
            const statusEl = document.getElementById('sos-status');
            statusEl.innerHTML = '<p style="color: var(--accent-red);">🚨 SOS ACTIVATED — Processing emergency...</p>';

            try {
                const lat = state.location.lat || 28.6139;
                const lng = state.location.lng || 77.2090;

                const result = await api.triggerSOS(lat, lng, 'SOS Emergency Triggered');
                showSOSResponse(result);
                showToast('🚨 SOS Emergency — Guardians notified!', 'error', 8000);
                statusEl.innerHTML = '<p style="color: var(--accent-green);">✅ Emergency response activated. Help is on the way.</p>';
            } catch (err) {
                statusEl.innerHTML = `<p style="color: var(--accent-red);">❌ Error: ${err.message}. Make sure the backend is running.</p>`;
                showToast('Failed to send SOS. Check backend connection.', 'error');
            } finally {
                setTimeout(() => btn.classList.remove('activated'), 5000);
            }
        }
    }

    function showSOSResponse(result) {
        const container = document.getElementById('sos-response');
        const body = document.getElementById('sos-response-body');
        container.classList.remove('hidden');

        body.innerHTML = `
            <div class="ai-detail-grid">
                <div class="ai-detail-item">
                    <div class="label">Emergency Type</div>
                    <div class="value">${result.intent?.intent?.toUpperCase() || 'SOS'}</div>
                </div>
                <div class="ai-detail-item">
                    <div class="label">Risk Level</div>
                    <div class="value"><span class="risk-badge ${result.risk?.level}">${result.risk?.level?.toUpperCase()} (${result.risk?.score}/100)</span></div>
                </div>
                <div class="ai-detail-item">
                    <div class="label">Incident ID</div>
                    <div class="value">#${result.incident_id}</div>
                </div>
                <div class="ai-detail-item">
                    <div class="label">Location</div>
                    <div class="value" style="font-size:0.78rem;">${result.location?.address || 'GPS Coordinates sent'}</div>
                </div>
            </div>
            <h4 style="margin-top:16px; margin-bottom:8px; font-size:0.9rem; color:var(--accent-amber);">Actions Taken</h4>
            <div class="action-list">
                ${(result.actions || []).map(a => `
                    <div class="action-item priority-${a.priority}">
                        <div>
                            <div class="action-name">${formatActionName(a.action)}</div>
                            <div class="action-detail">${a.details}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        lucide.createIcons({ nodes: [body] });
    }

    // ═══════════════════════════════════════════════════════
    // EMERGENCY ANALYZE (CHAT)
    // ═══════════════════════════════════════════════════════
    function initChat() {
        const form = document.getElementById('chat-form');
        const input = document.getElementById('chat-input');
        const messages = document.getElementById('chat-messages');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const text = input.value.trim();
            if (!text) return;

            // Add user message
            addChatMessage('user', text);
            input.value = '';

            // Show loading
            const loadingId = addChatMessage('ai', '<div class="spinner"></div> Analyzing situation...');

            try {
                const lat = state.location.lat || 28.6139;
                const lng = state.location.lng || 77.2090;
                const result = await api.analyze(text, lat, lng);

                // Remove loading
                const loadingEl = document.getElementById(loadingId);
                if (loadingEl) loadingEl.remove();

                // Add AI response
                addAnalysisResult(result);
            } catch (err) {
                const loadingEl = document.getElementById(loadingId);
                if (loadingEl) loadingEl.remove();
                addChatMessage('ai', `<p style="color:var(--accent-red);">❌ ${err.message}</p><p style="font-size:0.8rem; color:var(--text-muted); margin-top:4px;">Make sure the backend server is running at ${API_BASE}</p>`);
            }
        });
    }

    function addChatMessage(type, content) {
        const messages = document.getElementById('chat-messages');
        const id = 'msg-' + Date.now();
        const iconMap = { user: 'user', ai: 'bot', system: 'bot' };

        const div = document.createElement('div');
        div.className = `chat-message ${type}`;
        div.id = id;
        div.innerHTML = `
            <div class="message-icon"><i data-lucide="${iconMap[type]}"></i></div>
            <div class="message-content">${content}</div>
        `;
        messages.appendChild(div);
        lucide.createIcons({ nodes: [div] });
        messages.scrollTop = messages.scrollHeight;
        return id;
    }

    function addAnalysisResult(result) {
        const riskColors = { critical: '#ff1744', high: '#ff5722', medium: '#ff9800', low: '#4caf50' };
        const summary = result.response_summary || (result.intent?.intent ? `${result.intent.intent.toUpperCase()} detected` : 'Analysis Complete');
        const html = `
            <div class="analysis-result">
                <p style="margin-bottom:8px;"><strong>${summary}</strong></p>
                <div class="ai-detail-grid">
                    <div class="ai-detail-item">
                        <div class="label">Intent Detected</div>
                        <div class="value">${result.intent?.intent?.toUpperCase() || 'Unknown'}</div>
                    </div>
                    <div class="ai-detail-item">
                        <div class="label">Confidence</div>
                        <div class="value">${((result.intent?.confidence || 0) * 100).toFixed(1)}%</div>
                    </div>
                    <div class="ai-detail-item">
                        <div class="label">Risk Level</div>
                        <div class="value"><span class="risk-badge ${result.risk?.level}">${result.risk?.level?.toUpperCase()} — ${result.risk?.score}/100</span></div>
                    </div>
                    <div class="ai-detail-item">
                        <div class="label">Incident ID</div>
                        <div class="value">#${result.incident_id}</div>
                    </div>
                </div>

                ${result.intent?.keywords_found?.length ? `<p style="margin-top:12px; font-size:0.8rem; color:var(--text-muted);">Keywords: ${result.intent.keywords_found.join(', ')}</p>` : ''}

                <h4 style="margin-top:16px; margin-bottom:8px; font-size:0.85rem; color:var(--accent-amber);">🎯 Actions</h4>
                <div class="action-list">
                    ${(result.actions || []).map(a => `
                        <div class="action-item priority-${a.priority}">
                            <div>
                                <div class="action-name">${formatActionName(a.action)}</div>
                                <div class="action-detail">${a.details}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>

                ${result.recommendations?.length ? `
                    <h4 style="margin-top:16px; margin-bottom:8px; font-size:0.85rem; color:var(--accent-cyan);">💡 Recommendations</h4>
                    <ul class="recommendations-list">
                        ${result.recommendations.map(r => `<li>${r}</li>`).join('')}
                    </ul>
                ` : ''}
            </div>
        `;
        addChatMessage('ai', html);
    }

    function formatActionName(action) {
        return action.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    }

    // ═══════════════════════════════════════════════════════
    // LIVE MAP
    // ═══════════════════════════════════════════════════════
    function initMap() {
        if (state.map) {
            state.map.invalidateSize();
            return;
        }

        const lat = state.location.lat || 28.6139;
        const lng = state.location.lng || 77.2090;

        state.map = L.map('map-container', {
            zoomControl: true,
        }).setView([lat, lng], 14);

        // Dark tile layer
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
            maxZoom: 19,
        }).addTo(state.map);

        // User marker
        const userIcon = L.divIcon({
            className: 'user-map-marker',
            html: `<div style="width:20px;height:20px;background:var(--accent-blue);border:3px solid white;border-radius:50%;box-shadow:0 0 15px rgba(68,138,255,0.6);"></div>`,
            iconSize: [20, 20],
            iconAnchor: [10, 10],
        });

        state.userMarker = L.marker([lat, lng], { icon: userIcon })
            .addTo(state.map)
            .bindPopup('<b>📍 Your Location</b>');

        // Accuracy circle
        L.circle([lat, lng], {
            radius: 200,
            color: '#448aff',
            fillColor: '#448aff',
            fillOpacity: 0.08,
            weight: 1,
        }).addTo(state.map);

        // Load nearby services
        loadNearbyServices(lat, lng);

        // Fix map size issues
        setTimeout(() => state.map.invalidateSize(), 300);
    }

    async function loadNearbyServices(lat, lng) {
        const servicesList = document.getElementById('services-list');
        servicesList.innerHTML = '<p class="muted">Searching nearby emergency services...</p>';

        try {
            // Use Overpass API to find nearby services
            const query = `[out:json][timeout:10];(node["amenity"="hospital"](around:5000,${lat},${lng});node["amenity"="police"](around:5000,${lat},${lng});node["amenity"="fire_station"](around:5000,${lat},${lng});node["amenity"="clinic"](around:5000,${lat},${lng}););out body 15;`;

            const res = await fetch('https://overpass-api.de/api/interpreter', {
                method: 'POST',
                body: `data=${encodeURIComponent(query)}`,
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            });

            const data = await res.json();
            const services = data.elements || [];

            if (services.length === 0) {
                // Use fallback
                displayFallbackServices(lat, lng);
                return;
            }

            servicesList.innerHTML = '';
            services.forEach(s => {
                const tags = s.tags || {};
                const type = tags.amenity || 'unknown';
                addServiceToMap(s.lat, s.lon, tags.name || type, type, tags.phone);
                addServiceCard(tags.name || 'Emergency Service', type, tags.phone, tags['addr:street']);
            });
        } catch (err) {
            displayFallbackServices(lat, lng);
        }
    }

    function displayFallbackServices(lat, lng) {
        const fallback = [
            { name: 'Nearest Hospital', type: 'hospital', lat: lat + 0.01, lng: lng + 0.008, phone: '108' },
            { name: 'Police Station', type: 'police', lat: lat - 0.005, lng: lng + 0.012, phone: '100' },
            { name: 'Fire Station', type: 'fire_station', lat: lat + 0.008, lng: lng - 0.006, phone: '101' },
        ];

        const servicesList = document.getElementById('services-list');
        servicesList.innerHTML = '';

        fallback.forEach(s => {
            addServiceToMap(s.lat, s.lng, s.name, s.type, s.phone);
            addServiceCard(s.name, s.type, s.phone, 'Contact local emergency');
        });
    }

    function addServiceToMap(lat, lng, name, type, phone) {
        const colors = {
            hospital: '#ff3b5c', police: '#448aff',
            fire_station: '#ff8c42', clinic: '#00e676', pharmacy: '#b388ff'
        };
        const emojis = {
            hospital: '🏥', police: '🚔',
            fire_station: '🚒', clinic: '🏥', pharmacy: '💊'
        };

        const icon = L.divIcon({
            className: 'service-map-marker',
            html: `<div style="width:32px;height:32px;background:${colors[type] || '#448aff'};border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:16px;box-shadow:0 2px 8px rgba(0,0,0,0.4);border:2px solid rgba(255,255,255,0.3);">${emojis[type] || '📍'}</div>`,
            iconSize: [32, 32],
            iconAnchor: [16, 16],
        });

        const marker = L.marker([lat, lng], { icon })
            .addTo(state.map)
            .bindPopup(`<b>${name}</b><br>${type}${phone ? `<br>📞 ${phone}` : ''}`);

        state.mapMarkers.push(marker);
    }

    function addServiceCard(name, type, phone, address) {
        const list = document.getElementById('services-list');
        const card = document.createElement('div');
        card.className = `service-card ${type}`;
        card.innerHTML = `
            <div class="service-name">${name}</div>
            <div class="service-type">${type.replace('_', ' ')}</div>
            ${phone ? `<div class="service-phone">📞 ${phone}</div>` : ''}
            ${address ? `<div style="font-size:0.75rem;color:var(--text-muted);margin-top:2px;">${address}</div>` : ''}
        `;
        list.appendChild(card);
    }

    // ═══════════════════════════════════════════════════════
    // GUARDIANS
    // ═══════════════════════════════════════════════════════
    function initGuardians() {
        const addBtn = document.getElementById('add-guardian-btn');
        const formContainer = document.getElementById('add-guardian-form');
        const cancelBtn = document.getElementById('cancel-guardian');
        const form = document.getElementById('guardian-form');

        addBtn.addEventListener('click', () => {
            formContainer.classList.toggle('hidden');
        });

        cancelBtn.addEventListener('click', () => {
            formContainer.classList.add('hidden');
            form.reset();
        });

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                await api.addGuardian({
                    name: document.getElementById('g-name').value,
                    phone: document.getElementById('g-phone').value,
                    email: document.getElementById('g-email').value || null,
                    relationship_type: document.getElementById('g-relationship').value,
                });
                showToast('Guardian added successfully!', 'success');
                formContainer.classList.add('hidden');
                form.reset();
                loadGuardians();
            } catch (err) {
                showToast(`Failed: ${err.message}`, 'error');
            }
        });
    }

    async function loadGuardians() {
        const grid = document.getElementById('guardians-grid');
        const empty = document.getElementById('no-guardians');

        try {
            const guardians = await api.getGuardians();

            if (guardians.length === 0) {
                grid.innerHTML = '';
                empty.classList.remove('hidden');
                lucide.createIcons({ nodes: [empty] });
                return;
            }

            empty.classList.add('hidden');
            grid.innerHTML = guardians.map(g => `
                <div class="guardian-card" data-id="${g.id}">
                    <div class="guardian-card-header">
                        <div class="guardian-info-row">
                            <div class="guardian-avatar">${g.name.charAt(0).toUpperCase()}</div>
                            <div>
                                <div class="guardian-name">${g.name}</div>
                                <div class="guardian-relationship">${g.relationship_type || 'Contact'}</div>
                            </div>
                        </div>
                        <button class="guardian-delete-btn" onclick="window.deleteGuardian(${g.id})">
                            <i data-lucide="trash-2"></i>
                        </button>
                    </div>
                    <div class="guardian-contact">
                        <i data-lucide="phone"></i>
                        <span>${g.phone}</span>
                    </div>
                    ${g.email ? `<div class="guardian-contact"><i data-lucide="mail"></i><span>${g.email}</span></div>` : ''}
                </div>
            `).join('');

            lucide.createIcons({ nodes: [grid] });
        } catch (err) {
            grid.innerHTML = `<p class="muted">Failed to load guardians. Is the backend running?</p>`;
        }
    }

    window.deleteGuardian = async function(id) {
        if (!confirm('Remove this guardian?')) return;
        try {
            await api.deleteGuardian(id);
            showToast('Guardian removed', 'info');
            loadGuardians();
        } catch (err) {
            showToast(`Failed: ${err.message}`, 'error');
        }
    };

    // ═══════════════════════════════════════════════════════
    // INCIDENTS
    // ═══════════════════════════════════════════════════════
    async function loadIncidents() {
        const timeline = document.getElementById('incidents-timeline');
        const empty = document.getElementById('no-incidents');

        try {
            const incidents = await api.getIncidents();

            if (incidents.length === 0) {
                timeline.innerHTML = '';
                empty.classList.remove('hidden');
                lucide.createIcons({ nodes: [empty] });
                return;
            }

            empty.classList.add('hidden');
            timeline.innerHTML = incidents.map(inc => {
                const date = new Date(inc.created_at);
                const timeStr = date.toLocaleString();
                return `
                    <div class="incident-card">
                        <div class="incident-risk-indicator ${inc.risk_level}"></div>
                        <div class="incident-body">
                            <div class="incident-header">
                                <span class="incident-type">${inc.incident_type.replace('_', ' ')}</span>
                                <span class="incident-time">${timeStr}</span>
                            </div>
                            <div class="incident-description">${inc.description || 'No description'}</div>
                            <div class="incident-meta">
                                <span class="risk-badge ${inc.risk_level}">${inc.risk_level} (${inc.risk_score})</span>
                                <span class="incident-status ${inc.status}">${inc.status}</span>
                                ${inc.address ? `<span class="muted" style="font-size:0.75rem;">📍 ${inc.address.split(',').slice(0,2).join(',')}</span>` : ''}
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        } catch (err) {
            timeline.innerHTML = `<p class="muted">Failed to load incidents. Is the backend running?</p>`;
        }
    }

    // ═══════════════════════════════════════════════════════
    // ANALYTICS
    // ═══════════════════════════════════════════════════════
    async function loadAnalytics() {
        try {
            const data = await api.getAnalytics();

            // Stat cards
            document.querySelector('#stat-total .stat-value').textContent = data.total_incidents;
            document.querySelector('#stat-critical .stat-value').textContent = data.by_risk_level?.critical || 0;
            document.querySelector('#stat-high .stat-value').textContent = data.by_risk_level?.high || 0;
            document.querySelector('#stat-active .stat-value').textContent = data.by_status?.active || 0;

            // Charts
            renderBarChart('chart-by-type', data.by_type, {
                fire: '#ff5722', medical: '#ff1744', accident: '#ff9800',
                crime: '#b388ff', natural_disaster: '#18ffff', sos: '#ff3b5c', general: '#666'
            });
            renderBarChart('chart-by-risk', data.by_risk_level, {
                critical: '#ff1744', high: '#ff5722', medium: '#ff9800', low: '#4caf50'
            });
        } catch (err) {
            // Silent fail — user might not have data yet
        }
    }

    function renderBarChart(containerId, data, colors) {
        const container = document.getElementById(containerId);
        if (!data || Object.keys(data).length === 0) {
            container.innerHTML = '<p class="muted" style="text-align:center; padding:20px;">No data yet</p>';
            return;
        }

        const max = Math.max(...Object.values(data), 1);

        container.innerHTML = Object.entries(data).map(([label, value]) => {
            const pct = (value / max) * 100;
            const color = colors[label] || '#448aff';
            return `
                <div class="chart-bar-row">
                    <div class="chart-bar-label">${label.replace('_', ' ')}</div>
                    <div class="chart-bar-track">
                        <div class="chart-bar-fill" style="width:${pct}%;background:${color};">${value}</div>
                    </div>
                </div>
            `;
        }).join('');
    }

    // ═══════════════════════════════════════════════════════
    // INIT
    // ═══════════════════════════════════════════════════════
    function init() {
        // Render Lucide icons
        lucide.createIcons();

        // Init modules
        initAuth();
        initNavigation();
        initSOS();
        initChat();
        initGuardians();

        // Check existing session
        if (state.token && state.user) {
            showDashboard();
        }
    }

    // Start app when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
