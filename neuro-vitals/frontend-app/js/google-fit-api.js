/**
 * Google Fit API Integration — Neuro-Vitals
 * Real OAuth 2.0 + Google Fitness REST API client.
 * Data flow: Noise Watch → NoiseFit App → Google Fit → This website
 */
const GoogleFitAPI = (() => {
    // ─── CONFIG ────────────────────────────────────────────────────────────────
    const CLIENT_ID = '993273774998-s2ftrtqpsambtul5qhkl8mf58pjs8ql0.apps.googleusercontent.com';

    const SCOPES = [
        'https://www.googleapis.com/auth/fitness.activity.read',
        'https://www.googleapis.com/auth/fitness.heart_rate.read',
        'https://www.googleapis.com/auth/fitness.sleep.read',
        'https://www.googleapis.com/auth/fitness.body.read',
    ].join(' ');

    const FIT_API = 'https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate';

    // ─── STATE ─────────────────────────────────────────────────────────────────
    let accessToken = null;
    let tokenClient = null;
    let isGsiLoaded = false;
    let pollInterval = null;
    const STORAGE_KEY = 'gfit_email';

    // ─── HELPERS ───────────────────────────────────────────────────────────────
    function log(msg, colorClass = 'text-slate-400') {
        const consoleOut = document.getElementById('consoleOutput');
        if (!consoleOut) return;
        const div = document.createElement('div');
        div.className = `mb-1 font-mono text-xs ${colorClass}`;
        div.innerText = `> ${msg}`;
        consoleOut.appendChild(div);
        consoleOut.scrollTop = consoleOut.scrollHeight;
        if (consoleOut.children.length > 60) consoleOut.removeChild(consoleOut.firstChild);
    }

    function logDataRow(data) {
        const consoleOut = document.getElementById('consoleOutput');
        if (!consoleOut) return;
        const time = new Date().toISOString().split('T')[1].replace('Z', '');
        const div = document.createElement('div');
        div.className = 'mb-1 font-mono text-[10px] md:text-xs border-l-2 border-transparent hover:border-white/20 pl-2 transition-all';
        div.innerHTML = `
            <span class="text-slate-600">[${time}]</span>
            <span class="text-green-400 font-bold"> GOOGLE_FIT</span>
            <span class="text-slate-500"> :: </span>
            <span class="text-slate-500">{</span>
            <span class="text-primary"> HR:${data.heartRate ?? '—'}</span>,
            <span class="text-accent-cyan"> STEPS:${data.steps != null ? data.steps.toLocaleString() : '—'}</span>,
            <span class="text-purple-400"> SLEEP:${data.sleepHours ?? '—'}h</span>,
            <span class="text-yellow-400"> CAL:${data.calories ?? '—'}</span>
            <span class="text-slate-500"> }</span>
            <span class="text-green-500 bg-green-500/10 px-1 rounded ml-1">LIVE</span>
        `;
        consoleOut.appendChild(div);
        consoleOut.scrollTop = consoleOut.scrollHeight;
        if (consoleOut.children.length > 60) consoleOut.removeChild(consoleOut.firstChild);
    }

    // ─── API FETCH ─────────────────────────────────────────────────────────────
    async function fetchAggregate(body) {
        const res = await fetch(FIT_API, {
            method: 'POST',
            headers: { Authorization: `Bearer ${accessToken}`, 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error(`Fit API ${res.status}: ${res.statusText}`);
        return res.json();
    }

    async function fetchAllData() {
        const now = Date.now();
        const startOfDay = new Date(); startOfDay.setHours(0, 0, 0, 0);

        const [stepsRes, hrRes, calRes, sleepRes] = await Promise.allSettled([
            // Today's steps
            fetchAggregate({
                aggregateBy: [{ dataTypeName: 'com.google.step_count.delta' }],
                bucketByTime: { durationMillis: String(24 * 60 * 60 * 1000) },
                startTimeMillis: String(startOfDay.getTime()),
                endTimeMillis: String(now),
            }),
            // Heart rate (last 2 hours)
            fetchAggregate({
                aggregateBy: [{ dataTypeName: 'com.google.heart_rate.bpm' }],
                bucketByTime: { durationMillis: String(30 * 60 * 1000) },
                startTimeMillis: String(now - 2 * 60 * 60 * 1000),
                endTimeMillis: String(now),
            }),
            // Calories today
            fetchAggregate({
                aggregateBy: [{ dataTypeName: 'com.google.calories.expended' }],
                bucketByTime: { durationMillis: String(24 * 60 * 60 * 1000) },
                startTimeMillis: String(startOfDay.getTime()),
                endTimeMillis: String(now),
            }),
            // Sleep last 24h
            fetchAggregate({
                aggregateBy: [{ dataTypeName: 'com.google.sleep.segment' }],
                bucketByTime: { durationMillis: String(24 * 60 * 60 * 1000) },
                startTimeMillis: String(now - 24 * 60 * 60 * 1000),
                endTimeMillis: String(now),
            }),
        ]);

        // Parse steps
        let steps = null;
        if (stepsRes.status === 'fulfilled') {
            steps = (stepsRes.value.bucket || []).reduce((sum, b) =>
                sum + (b.dataset?.[0]?.point || []).reduce((s, p) => s + (p.value?.[0]?.intVal || 0), 0), 0);
        }

        // Parse heart rate (most recent reading)
        let heartRate = null;
        if (hrRes.status === 'fulfilled') {
            for (const b of (hrRes.value.bucket || []).reverse()) {
                const pts = b.dataset?.[0]?.point || [];
                if (pts.length > 0) { heartRate = Math.round(pts[pts.length - 1].value?.[0]?.fpVal || 0); break; }
            }
        }

        // Parse calories
        let calories = null;
        if (calRes.status === 'fulfilled') {
            const total = (calRes.value.bucket || []).reduce((sum, b) =>
                sum + (b.dataset?.[0]?.point || []).reduce((s, p) => s + (p.value?.[0]?.fpVal || 0), 0), 0);
            calories = Math.round(total);
        }

        // Parse sleep (total hours)
        let sleepHours = null;
        if (sleepRes.status === 'fulfilled') {
            let totalMs = 0;
            (sleepRes.value.bucket || []).forEach(b => {
                (b.dataset?.[0]?.point || []).forEach(p => {
                    totalMs += (parseInt(p.endTimeNanos || 0) - parseInt(p.startTimeNanos || 0)) / 1e6;
                });
            });
            sleepHours = totalMs > 0 ? (totalMs / (1000 * 60 * 60)).toFixed(1) : null;
        }

        return { steps, heartRate, calories, sleepHours };
    }

    // ─── UI UPDATE ─────────────────────────────────────────────────────────────
    function updateStatCards(data) {
        const map = {
            'gfit-steps': data.steps != null ? data.steps.toLocaleString() : '—',
            'gfit-hr': data.heartRate != null ? `${data.heartRate} bpm` : '—',
            'gfit-sleep': data.sleepHours != null ? `${data.sleepHours}h` : '—',
            'gfit-calories': data.calories != null ? `${data.calories} kcal` : '—',
        };
        Object.entries(map).forEach(([id, val]) => {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = val;
                el.style.transition = 'color 0.3s';
                el.style.color = '#34d399';
                setTimeout(() => { el.style.color = ''; }, 600);
            }
        });
        // Update packet rate display
        const pr = document.getElementById('packetRate');
        if (pr && data.heartRate) pr.textContent = (data.heartRate * 12 + Math.floor(Math.random() * 50)).toLocaleString();

        // ── Persist to localStorage so dashboard.html can read it ──
        localStorage.setItem('gfit_live_data', JSON.stringify({
            heartRate: data.heartRate,
            steps: data.steps,
            sleepHours: data.sleepHours,
            calories: data.calories,
            updatedAt: new Date().toISOString(),
        }));

        // ── SYNC TO SUPABASE ──
        syncVitalsToSupabase(data);
    }

    async function syncVitalsToSupabase(data) {
        try {
            const currentUser = JSON.parse(localStorage.getItem('neurovitals_currentUser'));
            if (!currentUser || !currentUser.email || !window.supabaseClient) return;

            const { error } = await window.supabaseClient
                .from('latest_vitals')
                .upsert({
                    user_email: currentUser.email,
                    heart_rate: data.heartRate,
                    steps: data.steps,
                    // sleep_hours and calories_burned removed to match actual Supabase schema
                    updated_at: new Date().toISOString()
                }, { onConflict: 'user_email' });

            if (error) console.warn('Supabase Vitals Sync Error:', error);
        } catch (err) {
            console.error('Vitals sync failed:', err);
        }
    }

    function setConnectedState(email) {
        window.isConnected = true;

        // Header badge
        const badge = document.getElementById('connectionBadge');
        if (badge) {
            badge.className = 'flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/20 border border-green-500/30 transition-all duration-300 shadow-[0_0_15px_rgba(34,197,94,0.3)]';
            badge.innerHTML = `<span class="material-symbols-rounded text-green-400 text-sm animate-pulse">wifi</span><span class="text-xs font-bold text-green-400">LIVE FEED</span>`;
        }
        const dot = document.getElementById('systemStatusDot');
        const txt = document.getElementById('systemStatusText');
        if (dot) dot.className = 'w-2 h-2 rounded-full bg-green-500 animate-pulse';
        if (txt) { txt.className = 'text-xs font-mono text-green-400'; txt.innerText = 'SYSTEM_OPTIMAL'; }
        const count = document.getElementById('activeDeviceCount');
        if (count) count.innerText = '01';
        const packetIcon = document.getElementById('packetIcon');
        const packetRate = document.getElementById('packetRate');
        if (packetIcon) packetIcon.className = 'w-10 h-10 rounded-full bg-accent-cyan/10 flex items-center justify-center text-accent-cyan';
        if (packetRate) packetRate.className = 'text-2xl font-display font-bold text-accent-cyan';

        // Connect button
        const btn = document.getElementById('gfitConnectBtn');
        if (btn) {
            btn.innerHTML = `<span class="material-symbols-rounded text-sm">check_circle</span> Connected as ${email ? email.split('@')[0] : 'User'}`;
            btn.className = 'w-full py-3 rounded-xl bg-green-500/20 border border-green-500/50 text-green-400 text-sm font-bold transition-all flex items-center justify-center gap-2 cursor-default';
        }

        // Show live panel with animation
        const panel = document.getElementById('gfitLivePanel');
        if (panel) {
            panel.classList.remove('hidden');
            panel.style.animation = 'gfit-slide-in 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards';
        }
    }

    // ─── POLL LOOP ─────────────────────────────────────────────────────────────
    async function startPolling() {
        if (pollInterval) clearInterval(pollInterval);
        const doFetch = async () => {
            try {
                const data = await fetchAllData();
                updateStatCards(data);
                logDataRow(data);
            } catch (err) {
                log(`Fetch error: ${err.message}`, 'text-red-400');
            }
        };
        await doFetch(); // Immediate fetch
        pollInterval = setInterval(doFetch, 30000); // Then every 30s
    }

    // ─── OAUTH FLOW ────────────────────────────────────────────────────────────
    function initAndRequestToken(forcePrompt = false) {
        tokenClient = google.accounts.oauth2.initTokenClient({
            client_id: CLIENT_ID,
            scope: SCOPES,
            callback: async (response) => {
                if (response.error) {
                    console.error('Google OAuth Error Response:', response);
                    const errorMsg = response.error_description || response.error;
                    log(`OAuth Error: ${errorMsg}`, 'text-red-400');

                    if (forcePrompt) {
                        const btn = document.getElementById('gfitConnectBtn');
                        if (btn) {
                            btn.innerHTML = `<span>Connection Failed</span>`;
                            btn.className = 'w-full py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-bold flex items-center justify-center gap-2';
                        }

                        if (confirm(`Google Fit connection failed: "${errorMsg}".\n\nThis is often due to a "redirect_uri_mismatch". Would you like to use "Demo Mode" instead for this session?`)) {
                            if (typeof window.openDataSourceModal === 'function') {
                                window.openDataSourceModal();
                            }
                        }
                    } else {
                        log('Silent auth unavailable — click "Connect Google Fit" to sign in.', 'text-slate-500');
                    }
                    return;
                }
                accessToken = response.access_token;
                log('OAuth2 Access Token received ✓', 'text-green-400');
                log('Fetching your Noise watch data from Google Fit...', 'text-white');

                // Get user email
                let email = localStorage.getItem(STORAGE_KEY) || '';
                try {
                    const ui = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
                        headers: { Authorization: `Bearer ${accessToken}` }
                    });
                    const info = await ui.json();
                    email = info.email || email;
                    if (email) localStorage.setItem(STORAGE_KEY, email);
                    log(`Authenticated as ${email}`, 'text-blue-400');
                } catch (_) { }

                setConnectedState(email);
                await startPolling();
            },
        });
        // prompt='' = silent (no popup). prompt='consent' = force popup.
        tokenClient.requestAccessToken({ prompt: forcePrompt ? 'consent' : '' });
    }

    // ─── PUBLIC ────────────────────────────────────────────────────────────────
    function connect() {
        if (window.isConnected) { log('Already connected to Google Fit.', 'text-yellow-400'); return; }

        const btn = document.getElementById('gfitConnectBtn');
        if (btn) { btn.innerHTML = `<span class="material-symbols-rounded animate-spin text-sm">sync</span> Connecting...`; btn.disabled = true; }
        log('Initializing Google OAuth2...', 'text-slate-400');

        if (!isGsiLoaded) {
            const script = document.createElement('script');
            script.src = 'https://accounts.google.com/gsi/client';
            script.onload = () => {
                isGsiLoaded = true;
                log('Google Identity Services loaded ✓', 'text-green-400');
                initAndRequestToken(true); // force popup on manual connect
            };
            script.onerror = () => {
                log('Failed to load Google Identity Services. Check internet.', 'text-red-400');
                if (btn) { btn.innerHTML = `<span>Retry</span>`; btn.disabled = false; }
            };
            document.head.appendChild(script);
        } else {
            initAndRequestToken(true); // force popup on manual connect
        }
    }

    // Auto-connect silently on page load (no popup)
    function autoConnect() {
        if (window.isConnected) return;
        log('Auto-connecting to Google Fit...', 'text-slate-500');
        const script = document.createElement('script');
        script.src = 'https://accounts.google.com/gsi/client';
        script.onload = () => {
            isGsiLoaded = true;
            initAndRequestToken(false); // silent — no popup
        };
        document.head.appendChild(script);
    }

    function disconnect() {
        if (pollInterval) clearInterval(pollInterval);
        accessToken = null;
        window.isConnected = false;
        const btn = document.getElementById('gfitConnectBtn');
        if (btn) {
            btn.innerHTML = `<span>Connect Google Fit</span><span class="material-symbols-rounded text-xs">fitness_center</span>`;
            btn.disabled = false;
            btn.className = 'w-full py-3 rounded-xl bg-primary/20 hover:bg-primary/30 border border-primary/20 text-sm font-semibold text-primary transition-all flex items-center justify-center gap-2';
        }
        const panel = document.getElementById('gfitLivePanel');
        if (panel) panel.classList.add('hidden');
        log('Disconnected from Google Fit.', 'text-yellow-400');
    }

    return { connect, disconnect, autoConnect };
})();

window.GoogleFitAPI = GoogleFitAPI;

// Auto-connect silently when page finishes loading
document.addEventListener('DOMContentLoaded', () => {
    // Small delay so the page UI renders first
    setTimeout(() => GoogleFitAPI.autoConnect(), 800);
});
