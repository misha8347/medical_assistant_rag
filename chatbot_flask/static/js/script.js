document.addEventListener("DOMContentLoaded", function () {
    const registerBtn = document.getElementById("registerBtn");
    const loginBtn = document.getElementById("loginBtn");
    const showLoginBtn = document.getElementById("showLoginBtn");
    const showRegisterBtn = document.getElementById("showRegisterBtn");

    // Option buttons
    const startChatButton = document.getElementById('startChatButton');
    const chooseChatButton = document.getElementById('chooseChatButton');
    const logOutButton = document.getElementById("logOutButton");

    const registrationDiv = document.getElementById("registrationDiv");
    const loginDiv = document.getElementById("loginDiv");
    const chatOptionsDiv = document.getElementById("chatOptionsDiv");

    // Check if user is logged in
    function checkAuthentication() {
        fetch('/check_auth/')
        .then(response => response.json())
        .then(data => {
            if (data.is_authenticated) {
                // User is logged in, show chat options
                chatOptionsDiv.classList.remove("hidden");
                loginDiv.classList.add("hidden");
                registrationDiv.classList.add("hidden");
            } else {
                // User is NOT logged in, show login form
                loginDiv.classList.remove("hidden");
                registrationDiv.classList.add("hidden");
                chatOptionsDiv.classList.add("hidden");
            }
        })
        .catch(() => {
            // Default to login form in case of an error
            loginDiv.classList.remove("hidden");
            registrationDiv.classList.add("hidden");
            chatOptionsDiv.classList.add("hidden");
        });
    }

    // Call function on page load
    checkAuthentication();

    // Toggle between login and registration forms
    showLoginBtn.addEventListener("click", function () {
        registrationDiv.classList.add("hidden");
        loginDiv.classList.remove("hidden");
    });

    showRegisterBtn.addEventListener("click", function () {
        loginDiv.classList.add("hidden");
        registrationDiv.classList.remove("hidden");
    });

    // Register User
    registerBtn.addEventListener("click", function () {
        const username = document.getElementById("regUsername").value;
        const password = document.getElementById("regPassword").value;

        fetch("/register/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
            body: JSON.stringify({ username: username, password: password })
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            if (data.success) {
                checkAuthentication();
            }
        });
    });

    // Login User
    loginBtn.addEventListener("click", function () {
        const username = document.getElementById("loginUsername").value;
        const password = document.getElementById("loginPassword").value;

        fetch("/login/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
            body: JSON.stringify({ username: username, password: password })
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            if (data.success) {
                checkAuthentication();
            }
        });
    });

    // Logout User
    logOutButton.addEventListener("click", function () {
        fetch("/logout/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            }
        })
        .then(() => {
            checkAuthentication();  // Refresh UI on logout
        });
    });

    // Create new chat
    startChatButton.addEventListener('click', () => {
        fetch('/chats/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ title: "New Chat" })  // Chat title (you can modify this)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = `/chat/${data.chat_id}/`;  // Redirect to chat
            } else {
                alert("Error creating chat.");
            }
        })
        .catch(() => alert("Server error. Try again later."));
    });

    // the chat list button
    chooseChatButton.addEventListener('click', () => {
        window.location.href = '/chat_list/';
    });

    // Function to get CSRF token
    function getCSRFToken() {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith("csrftoken=")) {
                    cookieValue = cookie.substring("csrftoken=".length, cookie.length);
                    break;
                }
            }
        }
        return cookieValue;
    }
});