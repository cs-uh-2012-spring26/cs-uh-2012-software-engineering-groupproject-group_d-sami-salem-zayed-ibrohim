const TOKEN_KEY = "fitness_frontend_token";
const USER_KEY = "fitness_frontend_user";

let token = localStorage.getItem(TOKEN_KEY);
let user = readStoredUser();

const authStatus = document.getElementById("auth-status");
const authPanel = document.getElementById("auth-panel");
const logoutButton = document.getElementById("logout-button");
const createPanel = document.getElementById("create-panel");
const bookingsPanel = document.getElementById("bookings-panel");
const classList = document.getElementById("class-list");
const bookingList = document.getElementById("booking-list");
const statusMessage = document.getElementById("status-message");

document.getElementById("login-form").addEventListener("submit", handleLogin);
document.getElementById("register-form").addEventListener("submit", handleRegister);
document.getElementById("create-class-form").addEventListener("submit", handleCreateClass);
document.getElementById("refresh-classes").addEventListener("click", loadClasses);
document.getElementById("refresh-bookings").addEventListener("click", loadBookings);
logoutButton.addEventListener("click", logout);

initializeDefaults();
renderAuthState();
loadClasses();
loadBookings();

function readStoredUser() {
    try {
        return JSON.parse(localStorage.getItem(USER_KEY));
    } catch {
        return null;
    }
}

function initializeDefaults() {
    const now = new Date();
    now.setDate(now.getDate() + 1);
    now.setMinutes(0, 0, 0);

    const end = new Date(now);
    end.setHours(end.getHours() + 1);

    const form = document.getElementById("create-class-form");
    form.elements.start_date.value = toDatetimeLocal(now);
    form.elements.end_date.value = toDatetimeLocal(end);
    form.elements.capacity.value = 10;
}

function toDatetimeLocal(date) {
    const pad = (value) => String(value).padStart(2, "0");
    return [
        date.getFullYear(),
        pad(date.getMonth() + 1),
        pad(date.getDate()),
    ].join("-") + "T" + [pad(date.getHours()), pad(date.getMinutes())].join(":");
}

function toApiDatetime(value) {
    return value.replace("T", " ") + ":00";
}

function renderAuthState() {
    const loggedIn = Boolean(token && user);
    authPanel.classList.toggle("hidden", loggedIn);
    logoutButton.classList.toggle("hidden", !loggedIn);
    createPanel.classList.toggle("hidden", !loggedIn || user.role !== "trainer");
    bookingsPanel.classList.toggle("hidden", !loggedIn || user.role !== "member");

    authStatus.textContent = loggedIn
        ? `${user.name || user.email} (${user.role})`
        : "Viewing as guest";
}

async function apiRequest(path, options = {}) {
    const headers = new Headers(options.headers || {});

    if (options.body && !headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
    }

    if (options.auth && token) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    const response = await fetch(path, {
        ...options,
        headers,
    });
    const payload = await parseJson(response);

    if (!response.ok) {
        throw new Error(payload.message || payload.error || response.statusText);
    }

    return payload;
}

async function parseJson(response) {
    try {
        return await response.json();
    } catch {
        return {};
    }
}

async function handleLogin(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form));

    try {
        const result = await apiRequest("/auth/login", {
            method: "POST",
            body: JSON.stringify(data),
        });
        saveSession(result);
        form.reset();
        setStatus("Logged in.");
        await afterAuthChange();
    } catch (error) {
        setStatus(error.message);
    }
}

async function handleRegister(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form));

    try {
        const result = await apiRequest("/auth/register", {
            method: "POST",
            body: JSON.stringify(data),
        });
        saveSession(result);
        form.reset();
        setStatus("Registered and logged in.");
        await afterAuthChange();
    } catch (error) {
        setStatus(error.message);
    }
}

function saveSession(result) {
    token = result.access_token;
    user = result.user;
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
}

async function afterAuthChange() {
    renderAuthState();
    await loadClasses();
    await loadBookings();
}

function logout() {
    token = null;
    user = null;
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    bookingList.innerHTML = "";
    renderAuthState();
    loadClasses();
    setStatus("Logged out.");
}

async function handleCreateClass(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form));
    const recurrenceFrequency = data.recurrence_frequency;
    const recurrenceOccurrences = Number(data.recurrence_occurrences);

    data.capacity = Number(data.capacity);
    data.start_date = toApiDatetime(data.start_date);
    data.end_date = toApiDatetime(data.end_date);
    delete data.recurrence_frequency;
    delete data.recurrence_occurrences;

    if (recurrenceFrequency) {
        data.recurrence = {
            frequency: recurrenceFrequency,
            occurrences: recurrenceOccurrences,
        };
    }

    try {
        await apiRequest("/classes", {
            method: "POST",
            auth: true,
            body: JSON.stringify(data),
        });
        form.reset();
        initializeDefaults();
        setStatus("Class created.");
        await loadClasses();
    } catch (error) {
        setStatus(error.message);
    }
}

async function loadClasses() {
    classList.innerHTML = "<p>Loading classes...</p>";

    try {
        const classes = await apiRequest("/classes");
        renderClasses(classes);
    } catch (error) {
        classList.innerHTML = "";
        setStatus(error.message);
    }
}

function renderClasses(classes) {
    if (!classes.length) {
        classList.innerHTML = "<p>No upcoming classes.</p>";
        return;
    }

    classList.innerHTML = "";
    classes.forEach((fitnessClass) => {
        const item = document.createElement("article");
        item.className = "list-item";

        const title = escapeText(fitnessClass.title || "Untitled class");
        const id = fitnessClass._id;
        const spots = fitnessClass.remaining_spots;
        const canBook = token && user && user.role === "member";

        item.innerHTML = `
            <div class="list-item-header">
                <div>
                    <h3>${title}</h3>
                    <p>${escapeText(fitnessClass.description || "")}</p>
                </div>
                ${canBook ? `<button type="button" data-book="${escapeText(id)}">RSVP</button>` : ""}
            </div>
            <div class="meta">
                <span>${escapeText(fitnessClass.start_date || "")} to ${escapeText(fitnessClass.end_date || "")}</span>
                <span>${escapeText(fitnessClass.location || "")}</span>
                <span>Trainer: ${escapeText(fitnessClass.trainer_name || "unknown")}</span>
                <span>Capacity: ${escapeText(fitnessClass.capacity)} | Remaining spots: ${escapeText(spots)}</span>
            </div>
        `;

        const button = item.querySelector("[data-book]");
        if (button) {
            button.disabled = spots <= 0;
            button.addEventListener("click", () => bookClass(id));
        }

        classList.appendChild(item);
    });
}

async function bookClass(classId) {
    try {
        await apiRequest("/bookings", {
            method: "POST",
            auth: true,
            body: JSON.stringify({ class_id: classId }),
        });
        setStatus("RSVP saved.");
        await loadClasses();
        await loadBookings();
    } catch (error) {
        setStatus(error.message);
    }
}

async function loadBookings() {
    if (!token || !user || user.role !== "member") {
        return;
    }

    bookingList.innerHTML = "<p>Loading bookings...</p>";

    try {
        const bookings = await apiRequest("/bookings/my-classes", { auth: true });
        renderBookings(bookings);
    } catch (error) {
        bookingList.innerHTML = "<p>No booked classes yet.</p>";
        if (!/no booked classes/i.test(error.message)) {
            setStatus(error.message);
        }
    }
}

function renderBookings(bookings) {
    if (!bookings.length) {
        bookingList.innerHTML = "<p>No booked classes yet.</p>";
        return;
    }

    bookingList.innerHTML = "";
    bookings.forEach((booking) => {
        const item = document.createElement("article");
        item.className = "list-item";
        item.innerHTML = `
            <h3>${escapeText(booking.title || "Booked class")}</h3>
            <div class="meta">
                <span>${escapeText(booking.start_date || "")} to ${escapeText(booking.end_date || "")}</span>
                <span>${escapeText(booking.location || "")}</span>
                <span>Trainer: ${escapeText(booking.trainer_name || "unknown")}</span>
            </div>
        `;
        bookingList.appendChild(item);
    });
}

function setStatus(message) {
    statusMessage.textContent = message || "";
}

function escapeText(value) {
    const div = document.createElement("div");
    div.textContent = value == null ? "" : String(value);
    return div.innerHTML;
}
