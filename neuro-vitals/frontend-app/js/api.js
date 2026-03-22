/**
 * Neuro-Vitals API Layer
 * Redirects all AI requests to the secure backend server.
 */

const BACKEND_URL = "http://127.0.0.1:8000/api";

/**
 * Analyzes symptoms using the backend service (powered by GitHub Models)
 * @param {Object} data - Patient data
 * @returns {Promise<Object>} - Analysis result
 */
async function analyzeSymptoms(data) {
    try {
        const formData = new FormData();
        formData.append("name", data.name || "Anonymous");
        formData.append("age", data.age);
        formData.append("gender", data.gender);
        formData.append("symptoms", data.symptoms);
        formData.append("severity", data.severity);
        formData.append("duration", data.duration || 1);
        
        const response = await fetch(`${BACKEND_URL}/outbreak/analyze`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) throw new Error(`Backend Error: ${response.status}`);
        
        const result = await response.json();
        return {
            analysis: result.analysis,
            success: true
        };
    } catch (error) {
        console.error("Analyze Error:", error);
        return {
            analysis: "AI service error. Please ensure the backend is running.",
            success: false
        };
    }
}

/**
 * Orchestrates the Adversarial Debate via the backend
 * @param {Object} data - Patient data
 * @returns {Promise<Object>} - Prosecutor and Defense arguments
 */
async function generateAdversarialDebate(data) {
    try {
        // Prepare patient profile for the backend
        const patientProfile = {
            name: data.name || "Patient",
            age: parseInt(data.age),
            gender: data.gender,
            symptoms: data.symptoms,
            medical_history: data.history ? [data.history] : [],
            severity: parseInt(data.severity) || 5,
            duration: parseInt(data.duration) || 1
        };

        const response = await fetch(`${BACKEND_URL}/adversarial/debate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(patientProfile)
        });

        if (!response.ok) throw new Error(`Backend Error: ${response.status}`);
        
        const result = await response.json();
        
        // Cache the result for the judge verdict call (which follows immediately in the UI)
        window._lastDebateResult = result;

        return {
            prosecutor: {
                diagnosis: result.prosecutor.diagnosis,
                confidence: result.prosecutor.confidence,
                points: result.prosecutor.points.map(p => ({ title: p.title, description: p.description }))
            },
            defense: {
                diagnosis: result.defense.diagnosis,
                confidence: result.defense.confidence,
                points: result.defense.points.map(p => ({ title: p.title, description: p.description }))
            }
        };
    } catch (error) {
        console.error("Adversarial Error:", error);
        throw error;
    }
}

/**
 * Retrieves the Judge Verdict from the cached backend result
 */
async function generateJudgeVerdict(data, prosecutor, defense) {
    // If we have the result from the combined debate call, use it
    if (window._lastDebateResult) {
        const result = window._lastDebateResult.verdict;
        return {
            verdict: result.verdict,
            confidence: result.confidence,
            highlights: result.highlights || [],
            synthesis: result.synthesis,
            next_step: result.next_step
        };
    }
    
    return {
        verdict: "Verdict Unavailable",
        confidence: 0,
        synthesis: "The Judge could not reach a verdict due to connection issues.",
        next_step: "Consult a human specialist."
    };
}

// Export for window global
window.neuroApi = {
    analyzeSymptoms,
    generateAdversarialDebate,
    generateJudgeVerdict
};
