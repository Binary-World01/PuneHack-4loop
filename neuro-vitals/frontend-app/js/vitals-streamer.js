/**
 * Neuro-Vitals Persistent Streamer (V2 - Centralized)
 * Handles background vital generation, Google Sheets fetching, and cross-page synchronization.
 */

class VitalsStreamer {
    constructor() {
        this.interval = null;
        this.currentUser = null;
        this.hrSim = {
            rate: 72,
            target: 72,
            next() {
                if (Math.random() > 0.8) {
                    this.target = 70 + Math.floor(Math.random() * 20 - 10);
                }
                const drift = (this.target - this.rate) * 0.1;
                const noise = (Math.random() - 0.5) * 2;
                this.rate += drift + noise;
                return Math.max(55, Math.min(110, Math.floor(this.rate)));
            }
        };
    }

    async init() {
        // Try to get user from localStorage or Supabase
        const localUser = JSON.parse(localStorage.getItem('neurovitals_currentUser') || '{}');
        if (localUser && localUser.id) {
            this.currentUser = localUser;
        } else if (window.supabaseClient) {
            const { data: { user } } = await window.supabaseClient.auth.getUser();
            if (user) {
                this.currentUser = user;
                localStorage.setItem('neurovitals_currentUser', JSON.stringify(user));
            }
        }
        
        // Auto-start if previously connected
        if (localStorage.getItem('wearable_connected') === 'true') {
            this.start();
        }
    }

    start() {
        const isConnected = localStorage.getItem('wearable_connected') === 'true';
        if (!isConnected) return;

        const sheetUrl = localStorage.getItem('wearable_sheet_url');
        const source = sheetUrl ? 'Google Sheets' : 'Simulation';
        const pollRate = source === 'Google Sheets' ? 5000 : 2000;

        if (this.interval) clearInterval(this.interval);

        console.log(`[VitalsStreamer] 🚀 Starting ${source} stream...`);
        
        this.interval = setInterval(async () => {
            // 1. Re-check connection status
            if (localStorage.getItem('wearable_connected') !== 'true') {
                this.stop();
                return;
            }

            // 2. Strict User Verification (Email OR ID)
            const hasIdentifier = this.currentUser && (this.currentUser.id || this.currentUser.email) || localStorage.getItem('gfit_email');
            if (!hasIdentifier) {
                console.warn("[VitalsStreamer] Lost user context. Retrying init...");
                await this.init(); 
                const retryHasIdentifier = this.currentUser && (this.currentUser.id || this.currentUser.email) || localStorage.getItem('gfit_email');
                if (!retryHasIdentifier) {
                    console.error("[VitalsStreamer] No user found. Stopping stream for safety.");
                    this.stop();
                    return;
                }
            }

            let liveData = null;
            const time = new Date().toISOString();

            if (source === 'Google Sheets' && sheetUrl) {
                liveData = await this.fetchFromSheets(sheetUrl);
            } else {
                liveData = this.generateSimData();
            }

            if (liveData) {
                liveData.updatedAt = time;
                localStorage.setItem('gfit_live_data', JSON.stringify(liveData));
                
                // Sync to Database via Backend API
                if (hasIdentifier) {
                    console.log(`[VitalsStreamer] Syncing to backend for user: ${this.currentUser?.email || localStorage.getItem('gfit_email')}`);
                    this.syncToSupabase(liveData, source);
                }

                // Notify UI
                window.dispatchEvent(new CustomEvent('vitalsUpdated', { detail: liveData }));
            }
        }, pollRate);
    }

    generateSimData() {
        const prev = JSON.parse(localStorage.getItem('gfit_live_data') || '{"steps":0}');
        const stepsIncr = Math.random() > 0.95 ? Math.floor(Math.random() * 5) : 0;
        
        return {
            heartRate: this.hrSim.next(),
            steps: (prev.steps || 0) + stepsIncr,
            sleepHours: 7.2,
            calories: 850 + (prev.steps || 0) * 0.04
        };
    }

    async fetchFromSheets(url) {
        try {
            const res = await fetch(url);
            const csv = await res.text();
            const rows = csv.split('\n').filter(r => r.trim() !== '');
            if (rows.length < 2) return null;
            
            const lastRow = rows[rows.length - 1].split(',');
            // CSV structure: Timestamp, HR, Steps, Sleep, Calories
            return {
                heartRate: parseInt(lastRow[1]) || 70,
                steps: parseInt(lastRow[2]) || 0,
                sleepHours: parseFloat(lastRow[3]) || 7.0,
                calories: parseInt(lastRow[4]) || 2000
            };
        } catch (e) {
            console.warn("[VitalsStreamer] Sheets fetch failed", e);
            return null;
        }
    }

    async syncToSupabase(data, source) {
        const email = (this.currentUser && this.currentUser.email) || localStorage.getItem('gfit_email');
        if (!email) return;

        try {
            const payload = {
                user_email: email,
                steps: data.steps,
                heart_rate: data.heartRate,
                sleep_hours: data.sleepHours,
                calories: data.calories,
                source: source === 'Google Sheets' ? 'google_sheets_bridge' : 'simulation',
                recorded_at: data.updatedAt
            };

            const response = await fetch('http://localhost:8000/api/vitals/save-vitals', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                console.error("[VitalsStreamer] ❌ Backend Sync Failed");
            } else {
                console.log("[VitalsStreamer] ✅ Database Updated Successfully.");
            }
        } catch (e) {
            console.error("[VitalsStreamer] 🚨 Fatal Sync Error:", e);
        }
    }

    stop() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
            console.log("[VitalsStreamer] 🛑 Stream stopped.");
        }
    }
}

// Global instance
window.vitalsStreamer = new VitalsStreamer();

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    window.vitalsStreamer.init();
});
