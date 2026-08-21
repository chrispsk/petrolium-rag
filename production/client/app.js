const queryInput = document.getElementById("query");
const sendButton = document.getElementById("send");
const chat = document.getElementById("chat");

const ingestButton = document.getElementById("ingest-button");
const notification = document.getElementById("notification");

const navButtons = document.querySelectorAll("[data-section]");
const dashboardSections = document.querySelectorAll(".dashboard-section");


const API_BASE = "http://192.168.1.237:8000";

const LOGIN_URL = `${API_BASE}/login`;
const API_URL = `${API_BASE}/query`;
const INGEST_URL = `${API_BASE}/ingest`;
const STATS_URL = `${API_BASE}/stats`;


let THREAD_ID = localStorage.getItem("rag_thread_id");

if (!THREAD_ID) {
    THREAD_ID = "thread-" + Date.now() + "-" + Math.random().toString(36).substring(2, 10);
    localStorage.setItem("rag_thread_id", THREAD_ID);
}


async function login() {
    const password = prompt("Enter RAG Assistant password:");

    if (!password) {
        return false;
    }

    try {
        const response = await fetch(
            LOGIN_URL,
            {
                method: "POST",
                credentials: "include",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    password: password
                })
            }
        );

        if (!response.ok) {
            const data = await response.json();
            showNotification(data.detail || "Login failed.");
            return false;
        }

        showNotification("Authenticated successfully.");

        return true;
    }

    catch (error) {
        showNotification("Could not connect to the API.");
        console.error(error);

        return false;
    }
}


async function ensureAuthenticated() {
    try {
        const response = await fetch(
            STATS_URL,
            {
                method: "GET",
                credentials: "include"
            }
        );

        if (response.status === 401) {
            return await login();
        }

        return response.ok;
    }

    catch (error) {
        showNotification("Could not connect to the API.");
        console.error(error);

        return false;
    }
}


function addUserMessage(query) {
    const message = document.createElement("div");
    message.className = "message";

    const title = document.createElement("div");
    title.className = "user";
    title.textContent = "You";

    const content = document.createElement("div");
    content.textContent = query;

    message.appendChild(title);
    message.appendChild(content);

    chat.appendChild(message);
}


function addAssistantMessage(answer, sources) {
    const message = document.createElement("div");
    message.className = "message";

    const title = document.createElement("div");
    title.className = "user";
    title.textContent = "RAG Assistant";

    const answerElement = document.createElement("div");
    answerElement.className = "answer";

    if (typeof answer === "object" && answer !== null) {
        answerElement.textContent = answer.content || answer.answer || JSON.stringify(answer);
    } else {
        answerElement.textContent = answer;
    }

    const sourcesElement = document.createElement("div");
    sourcesElement.className = "sources";

    if (sources && sources.length > 0) {
        const sourcesText = sources
            .map(item => `${item.source} > ${item.path}`)
            .join("\n");

        sourcesElement.textContent = "Sources:\n" + sourcesText;
    }

    message.appendChild(title);
    message.appendChild(answerElement);
    message.appendChild(sourcesElement);

    chat.appendChild(message);
}


function addErrorMessage(errorMessage) {
    const message = document.createElement("div");
    message.className = "message";

    const title = document.createElement("div");
    title.className = "user";
    title.textContent = "RAG Assistant";

    const content = document.createElement("div");
    content.className = "answer";
    content.textContent = errorMessage;

    message.appendChild(title);
    message.appendChild(content);

    chat.appendChild(message);
}


function showNotification(message) {
    notification.textContent = message;
    notification.classList.add("show");

    setTimeout(() => {
        notification.classList.remove("show");
    }, 3000);
}


async function sendQuery() {
    const query = queryInput.value.trim();

    if (!query) {
        return;
    }

    sendButton.disabled = true;
    sendButton.textContent = "Thinking...";

    addUserMessage(query);
    chat.scrollTo({top: chat.scrollHeight, behavior: "smooth"});

    queryInput.value = "";

    try {
        let response = await fetch(
            API_URL,
            {
                method: "POST",
                credentials: "include",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    query: query,
                    thread_id: THREAD_ID
                })
            }
        );

        if (response.status === 401) {
            const authenticated = await login();

            if (!authenticated) {
                throw new Error("Authentication required.");
            }

            response = await fetch(
                API_URL,
                {
                    method: "POST",
                    credentials: "include",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        query: query,
                        thread_id: THREAD_ID
                    })
                }
            );
        }

        if (!response.ok) {
            const errorData = await response.json();

            let errorMessage = "API request failed.";

            if (Array.isArray(errorData.detail)) {
                errorMessage = errorData.detail.map(item => item.msg).join(", ");
            } else if (errorData.detail) {
                errorMessage = errorData.detail;
            }

            throw new Error(errorMessage);
        }

        const data = await response.json();

        addAssistantMessage(data.answer, data.sources);
        chat.scrollTo({top: chat.scrollHeight, behavior: "smooth"});
    }

    catch (error) {
        addErrorMessage(error.message);
        console.error(error);
    }

    finally {
        sendButton.disabled = false;
        sendButton.textContent = "Send";
        queryInput.focus();
    }
}


async function runIngestion() {
    ingestButton.disabled = true;
    ingestButton.textContent = "Running...";

    try {
        let response = await fetch(
            INGEST_URL,
            {
                method: "POST",
                credentials: "include"
            }
        );

        if (response.status === 401) {
            const authenticated = await login();

            if (!authenticated) {
                throw new Error("Authentication required.");
            }

            response = await fetch(
                INGEST_URL,
                {
                    method: "POST",
                    credentials: "include"
                }
            );
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Ingestion failed.");
        }

        showNotification("Ingestion started successfully.");
    }

    catch (error) {
        showNotification(error.message);
        console.error(error);
    }

    finally {
        ingestButton.disabled = false;
        ingestButton.textContent = "Run Ingestion";
    }
}


async function loadStatistics() {
    try {
        let response = await fetch(
            STATS_URL,
            {
                method: "GET",
                credentials: "include"
            }
        );

        if (response.status === 401) {
            const authenticated = await login();

            if (!authenticated) {
                throw new Error("Authentication required.");
            }

            response = await fetch(
                STATS_URL,
                {
                    method: "GET",
                    credentials: "include"
                }
            );
        }

        if (!response.ok) {
            const errorData = await response.json();

            throw new Error(
                errorData.detail || "Could not load statistics."
            );
        }

        const data = await response.json();

        document.getElementById("documents-count").textContent = data.documents;
        document.getElementById("chunks-count").textContent = data.chunks;
        document.getElementById("cache-count").textContent = data.cached_queries;
        document.getElementById("queries-count").textContent = data.total_queries;
        document.getElementById("cache-hit-rate").textContent = data.cache_hit_rate + "%";
    }

    catch (error) {
        showNotification(error.message);
        console.error(error);
    }
}


navButtons.forEach(button => {
    button.addEventListener("click", async function() {
        const sectionId = button.dataset.section;

        dashboardSections.forEach(section => {
            section.classList.remove("active");
        });

        navButtons.forEach(item => {
            item.classList.remove("active");
        });

        document.getElementById(sectionId).classList.add("active");
        button.classList.add("active");

        if (sectionId === "statistics-section") {
            await loadStatistics();
        }
    });
});


sendButton.addEventListener(
    "click",
    sendQuery
);


queryInput.addEventListener(
    "keydown",
    function(event) {
        if (event.key === "Enter") {
            sendQuery();
        }
    }
);


ingestButton.addEventListener(
    "click",
    runIngestion
);


ensureAuthenticated();