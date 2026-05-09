/**
 * NYUAD Fitness Portal - Frontend Logic
 * Refactored for clean API handling, XSS protection, and modular function blocks.
 */

// Automatically switches between local testing and the public VM
const API = `${window.location.protocol}//${window.location.hostname}:8000`;
const TOKEN_KEY = "fitness_token";
const ROLE_KEY = "fitness_role";

// --- HELPERS ---

/**
 * XSS PROTECTION: Escapes HTML characters to prevent malicious scripts 
 * from running if a user enters a script tag into a class description.
 */
function escapeText(value) {
    const div = document.createElement("div");
    div.textContent = value == null ? "" : String(value);
    return div.innerHTML;
}

/**
 * API WRAPPER: A centralized function for all fetch calls. 
 * Handles JWT attachment, Content-Type headers, and standardized error parsing.
 */
async function apiRequest(path, options = {}) {
    const token = localStorage.getItem(TOKEN_KEY);
    const headers = new Headers(options.headers || {});

    // Automatically set JSON header if a body is present
    if (options.body && !headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
    }

    // Attach Bearer token if user is logged in
    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    const response = await fetch(`${API}${path}`, { ...options, headers });
    
    // Safely parse JSON or return empty object if response is empty
    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(payload.message || payload.error || "API Error");
    }
    return payload;
}

// --- AUTHENTICATION ---

/**
 * UI Toggle between Login and Registration modes.
 */
function toggleAuth() {
    const title = document.getElementById('auth-title');
    const btn = document.getElementById('auth-btn');
    const toggleLink = document.getElementById('toggle-link');
    const regFields = document.getElementById('register-fields');
    const isLogin = title.innerText.includes("Login");

    if (isLogin) {
        title.innerText = "NYUAD Gym Sign Up";
        btn.innerText = "Register";
        toggleLink.innerText = "Login";
        document.getElementById('toggle-text').innerText = "Already have an account?";
        regFields.classList.remove('hidden');
    } else {
        title.innerText = "NYUAD Gym Login";
        btn.innerText = "Login";
        toggleLink.innerText = "Sign Up";
        document.getElementById('toggle-text').innerText = "Need an account?";
        regFields.classList.add('hidden');
    }
}

/**
 * Handles both Login and Registration based on the current UI state.
 * Decodes the JWT to store the user role for UI permission logic.
 */
async function handleAuth() {
    const email = document.getElementById('auth-email').value;
    const password = document.getElementById('auth-pass').value;
    const isLogin = document.getElementById('auth-title').innerText.includes("Login");
    
    const path = isLogin ? '/auth/login' : '/auth/register';
    const body = isLogin ? { email, password } : {
        email, password,
        name: document.getElementById('reg-name').value,
        birthday: document.getElementById('reg-bday').value,
        role: document.getElementById('reg-role').value
    };

    try {
        const data = await apiRequest(path, { method: 'POST', body: JSON.stringify(body) });
        
        if (!isLogin) return alert("Success! Now login.");

        // Store session data and decode the JWT payload
        localStorage.setItem(TOKEN_KEY, data.access_token);
        const payload = JSON.parse(atob(data.access_token.split('.')[1]));
        localStorage.setItem(ROLE_KEY, (payload.role || 'member').toLowerCase());
        
        initApp(); 
    } catch (err) {
        alert(`Auth Failed: ${err.message}`);
    }
}

// --- CORE APP LOGIC ---

/**
 * Manages the "Single Page" navigation state.
 * Toggles visibility of Trainer vs Member sections based on the stored role.
 */
async function initApp() {
    document.getElementById('auth-section').classList.add('hidden');
    document.getElementById('app-section').classList.remove('hidden');
    
    const role = localStorage.getItem(ROLE_KEY);
    document.getElementById('welcome').innerText = `Hello, ${role}`;

    const isTrainer = role === 'trainer';
    document.getElementById('trainer-section').classList.toggle('hidden', !isTrainer);
    document.getElementById('trainer-manage-section').classList.toggle('hidden', !isTrainer);
    document.getElementById('notif-section').classList.toggle('hidden', isTrainer);
    document.getElementById('member-section').classList.toggle('hidden', isTrainer);

    // Initial data fetch based on permissions
    if (!isTrainer) {
        loadNotifs();
        loadBookings();
    }
    loadClasses();
}

// --- CLASS & BOOKING ---

/**
 * Fetches all available classes and populates the lists.
 */
async function loadClasses() {
    try {
        const data = await apiRequest('/classes');
        const userRole = localStorage.getItem(ROLE_KEY);

        document.getElementById('class-list').innerHTML = data.map(c => renderClassItem(c, userRole, false)).join('');
        
        if (userRole === 'trainer') {
            document.getElementById('trainer-class-list').innerHTML = data.map(c => renderClassItem(c, userRole, true)).join('');
        }
    } catch (err) {
        console.error("Failed to load classes:", err);
    }
}

/**
 * Generates HTML for a class item with security escaping and conditional buttons.
 */
function renderClassItem(c, userRole, isTrainerList, isBooking = false) {
    const classId = c._id || c.id;
    
    // Logic to handle different naming conventions between Class and Booking objects
    const displayTitle = c.class_title || c.title; 
    
    return `
        <div class="item" style="flex-direction: column; align-items: flex-start;">
            <div style="display: flex; justify-content: space-between; width: 100%; align-items: center;">
                <span>
                    <strong>${escapeText(displayTitle)}</strong><br>
                    <small>Time: ${escapeText(c.start_date)} ${c.end_date ? `- ${escapeText(c.end_date)}` : ''}</small><br>
                    ${c.location ? `<small>Location: ${escapeText(c.location)}</small>` : ''}
                </span>
                <div>
                    ${!isBooking ? `<span class="badge">${c.remaining_spots} spots left</span>` : ''}
                    
                    ${/* Case 1: Member viewing available classes */
                        (!isTrainerList && userRole === 'member' && !isBooking) 
                        ? `<button onclick="book('${classId}')" style="width:auto; margin:0">RSVP</button>` : ''}
                    
                    ${/* Case 2: Trainer viewing their classes */
                        isTrainerList 
                        ? `<button onclick="sendRemind('${classId}')" style="width:auto; margin:0; background:orange">Remind</button>` : ''}
                    
                    ${/* Case 3: Member viewing their confirmed bookings */
                        isBooking 
                        ? `<span class="badge" style="background:#d4edda; color:#155724; border:1px solid #c3e6cb;">Confirmed</span>` : ''}
                </div>
            </div>
            <p style="font-size: 0.9em; color: #555; margin: 8px 0 0 0; font-style: italic;">
                ${escapeText(c.description || "")}
            </p>
        </div>
    `;
}

/**
 * Handles class creation for trainers, supporting recurrence rules.
 */
async function postClass() {
    const body = {
        title: document.getElementById('c-title').value,
        start_date: document.getElementById('c-start').value,
        end_date: document.getElementById('c-end').value,
        capacity: parseInt(document.getElementById('c-cap').value) || 0,
        location: document.getElementById('c-loc').value,
        description: document.getElementById('c-desc').value
    };

    const freqInput = document.querySelector('[name="recurrence_frequency"]');
    if (freqInput && freqInput.value) {
        body.recurrence = {
            frequency: freqInput.value,
            occurrences: parseInt(document.querySelector('[name="recurrence_occurrences"]').value) || 2
        };
    }

    try {
        await apiRequest('/classes', { method: 'POST', body: JSON.stringify(body) });
        alert("Success: Class Published!");
        loadClasses();
    } catch (err) {
        alert(`Error: ${err.message}`);
    }
}

/**
 * Allows members to book a class.
 */
async function book(classId) {
    try {
        await apiRequest('/bookings', { method: 'POST', body: JSON.stringify({ class_id: classId }) });
        alert("RSVP Successful!");
        loadClasses();
        loadBookings();
    } catch (err) {
        alert(`RSVP Failed: ${err.message}`);
    }
}

/**
 * Loads the current member's confirmed bookings.
 */
async function loadBookings() {
    const list = document.getElementById('booking-list');
    if (!list) return;
    try {
        const data = await apiRequest('/bookings/my-classes');
        const userRole = localStorage.getItem(ROLE_KEY);

        list.innerHTML = data.map(b => renderClassItem(b, userRole, false, true)).join('');
    } catch (err) {
        console.error("Booking load failed:", err);
    }
}
// --- NOTIFICATIONS ---

/**
 * Fetches notification settings and the Telegram bot deep-link.
 */
async function loadNotifs() {
    try {
        const data = await apiRequest('/notifications');
        const channels = data.notification_preferences.channels;
        document.getElementById('chan-email').checked = channels.includes('email');
        document.getElementById('chan-tg').checked = channels.includes('telegram');
        
        if (data.telegram_launch_url) {
            document.getElementById('tg-area').innerHTML = `<a href="${data.telegram_launch_url}" target="_blank">Launch Telegram Bot</a>`;
        }
    } catch (err) { console.error("Notification load failed:", err); }
}

/**
 * Updates Email/Telegram preferences.
 */
async function updateNotifs() {
    const channels = [];
    if (document.getElementById('chan-email').checked) channels.push('email');
    if (document.getElementById('chan-tg').checked) channels.push('telegram');
    
    try {
        await apiRequest('/notifications', { method: 'PATCH', body: JSON.stringify({ channels }) });
        alert("Settings Updated");
    } catch (err) { alert(err.message); }
}

/**
 * Trainer action: Triggers a mass reminder for a specific class.
 */
async function sendRemind(id) {
    try {
        await apiRequest(`/classes/${id}/reminder`, { method: 'POST' });
        alert("Reminders sent!");
    } catch (err) { alert(err.message); }
}

// --- LOGOUT ---

function logout() { 
    localStorage.clear(); 
    location.reload(); 
}

// On page load: Check if user is already authenticated
if (localStorage.getItem(TOKEN_KEY)) initApp();