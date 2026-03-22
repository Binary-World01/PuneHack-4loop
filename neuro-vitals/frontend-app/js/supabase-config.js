/**
 * Centralized Supabase Configuration
 * Used for standardizing database and auth interactions across the Neuro-Vitals platform.
 */

const SUPABASE_URL = "https://raboyinovwxdynswpoak.supabase.co";
const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJhYm95aW5vdnd4ZHluc3dwb2FrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE2NjA5NzIsImV4cCI6MjA4NzIzNjk3Mn0.bh3R2qcAFIwhbJ3BoBQXWv9NdlYeKBt7a25CCQYb50A";

// Handle script loading or direct use
if (typeof supabase === "undefined") {
    console.error("Supabase script not loaded! Please include <script src=\"https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2\"></script> before this config.");
}

const _supabase = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

// Export to window for global access
window.supabaseClient = _supabase;

/**
 * Helper to get current session/user
 */
async function getCurrentUser() {
    const { data: { user }, error } = await _supabase.auth.getUser();
    if (error) return null;
    return user;
}

/**
 * Helper to save/update user profile in database
 * @param {Object} profileData - { email, full_name, age, gender, etc. }
 */
async function upsertUserProfile(profileData) {
    if (!profileData.email) return { error: "Email required for profile upsert" };

    // Map 'full_name' to 'name' for existing schema compatibility
    const dataToSave = {
        name: profileData.full_name || profileData.name || 'Anonymous',
        email: profileData.email,
        updated_at: new Date().toISOString()
    };
    
    // Crucial: Use the ID from auth.users if provided
    if (profileData.id) dataToSave.id = profileData.id;
    
    // Add other fields if present
    if (profileData.age) dataToSave.age = profileData.age;
    if (profileData.gender) dataToSave.gender = profileData.gender;
    if (profileData.password) dataToSave.password = profileData.password;
    
    // Add location fields
    if (profileData.latitude) dataToSave.latitude = profileData.latitude;
    if (profileData.longitude) dataToSave.longitude = profileData.longitude;
    if (profileData.location_city) dataToSave.location_city = profileData.location_city;
    if (profileData.location_country) dataToSave.location_country = profileData.location_country;

    const { data, error } = await _supabase
        .from('profiles')
        .upsert(dataToSave, { onConflict: 'email' })
        .select();

    if (error) console.error("Error upserting profile:", error);
    return { data, error };
}

/**
 * Centralized Admin Sync (Outbreak & Risk Mapping)
 * @param {Object} adminData - { latitude, longitude, symptoms, location_city, etc. }
 */
async function syncToAdminTable(adminData) {
    const existingId = localStorage.getItem('current_admin_node_id');
    
    // Prepare data payload
    const dataToSave = {
        latitude: adminData.latitude,
        longitude: adminData.longitude,
        location_city: adminData.location_city,
        location_region: adminData.location_region,
        location_country: adminData.location_country,
        location: adminData.location || `${adminData.location_city || 'Unknown'}, ${adminData.location_country || 'Unknown'}`,
        disease_category: adminData.disease_category || "monitoring",
        spreadable: adminData.spreadable || false,
        updated_at: new Date().toISOString()
    };

    // Only include symptoms if specifically provided (don't overwrite with default on update)
    if (adminData.symptoms && adminData.symptoms !== "No symptoms reported") {
        dataToSave.symptoms = adminData.symptoms;
    }

    let result;
    if (existingId) {
        // Update existing row for this session
        result = await _supabase
            .from('admin')
            .update(dataToSave)
            .eq('id', existingId)
            .select();
    } else {
        // Initial insert for new session
        dataToSave.created_at = new Date().toISOString();
        if (!dataToSave.symptoms) dataToSave.symptoms = "Routine Checkup"; // Initial default
        
        result = await _supabase
            .from('admin')
            .insert(dataToSave)
            .select();
    }

    const { data, error } = result;

    if (error) console.error("Error syncing to admin table:", error);
    else {
        console.log("Admin Node Synchronized.");
        if (data && data[0]) {
            localStorage.setItem('current_admin_node_id', data[0].id);
        }
    }
    
    return { data, error };
}

/**
 * Update existing admin record symptoms (e.g. after AI Verification)
 */
async function updateAdminSymptoms(recordId, symptoms) {
    if (!recordId) return { error: "No record ID provided" };

    const { data, error } = await _supabase
        .from('admin')
        .update({ symptoms, updated_at: new Date().toISOString() })
        .eq('id', recordId)
        .select();

    if (error) console.error("Error updating admin symptoms:", error);
    else console.log("Admin Node Symptoms Updated.");

    return { data, error };
}

/**
 * Custom Login Helper (Checks Profiles table)
 * @param {string} email
 * @param {string} password
 */
async function loginUser(email, password) {
    const { data, error } = await _supabase
        .from('profiles')
        .select('*')
        .eq('email', email)
        .eq('password', password)
        .single();
    
    return { data, error };
}
