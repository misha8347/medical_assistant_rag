document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatMessages = document.getElementById('chatMessages');
    const chatOptionsBtn = document.getElementById('chatOptionsBtn');

    // Get chat ID from the template
    const chatContainer = document.getElementById('chatContainer');
    const chatId = chatContainer.getAttribute('data-chat-id');

    // Function to fetch previous messages from the server
    function loadMessages() {
        fetch(`/messages/?chat_id=${chatId}`)
        .then(response => response.json())
        .then(data => {
            chatMessages.innerHTML = '';  // Clear existing messages
            data.messages.forEach(msg => {
                addMessage(msg.text, msg.sender.toLowerCase() == 'user');
            });
        })
        .catch(() => showToast('Error loading messages.'));
    }
    // Function to format message text (converts newlines, lists, and bold text)
    function formatMessage(text) {
        // Convert newlines to `<br>` for spacing
        text = text.replace(/\n/g, '<br>');

        // Convert `* Item` lists to HTML `<ul><li>Item</li></ul>`
        text = text.replace(/\* (.+)/g, '<li>$1</li>');
        text = text.replace(/<\/li>\s*<li>/g, '</li><li>'); // Ensure proper spacing
        text = text.replace(/<li>.+<\/li>/g, '<ul>$&</ul>'); // Wrap with <ul>

        // Bold case report titles and important text
        text = text.replace(/"([^"]+)" \(PMID: (\d+)\)/g, '<strong>"$1"</strong> (PMID: $2)');

        return text;
    }

    // Function to add a new message to the chat area
    function addMessage(text, self = true) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        if (self) messageDiv.classList.add('self');

        // Use innerHTML to allow formatted text
        messageDiv.innerHTML = formatMessage(text);

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;  // Auto-scroll
    }

    // Function to generate response using Llama
    async function generateHealthRecommendation(message) {
        console.log("🔵 Sending query to ML service:", message);
        const response = await fetch("http://localhost:8083/generate_health_recommendation/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ query: message })
        });
    
        const data = await response.json();
        return data;
    }
    

    // Function to send a new message
    function sendMessageToBackend(message, sender) {
        fetch('/messages/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                chat: chatId,
                sender: sender,
                text: message
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                addMessage(message, sender.toLowerCase() == 'user'); // Show user message
            } else {
                showToast('Error sending message.');
            }
        })
        .catch(() => showToast('Server error. Try again later.'));
    }

    // Send message handler
    sendBtn.addEventListener('click', async () => {
        const message = chatInput.value.trim();
        if (message === '') {
            showToast('Please enter a message.');
            return;
        }

        chatInput.value = '';
        sendMessageToBackend(message, 'User'); // Send user message immediately

        let health_recommendation = await generateHealthRecommendation(message)
        console.log(health_recommendation.response)
        setTimeout(() => {
            sendMessageToBackend(health_recommendation.response, 'Bot'); // Send bot response after delay
        }, 1000); // 2000ms = 2 seconds delay
    });

    // Allow sending message with Enter key
    chatInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            sendBtn.click();
        }
    });

    // Redirect to home
    chatOptionsBtn.addEventListener('click', () => {
        window.location.href = '/';
    });

    // Function to get CSRF token
    function getCSRFToken() {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            document.cookie.split(';').forEach(cookie => {
                cookie = cookie.trim();
                if (cookie.startsWith('csrftoken=')) {
                    cookieValue = cookie.substring('csrftoken='.length);
                }
            });
        }
        return cookieValue;
    }

    // Function to display a toast message
    function showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => toast.classList.add('fade-out'), 9000);
        setTimeout(() => toast.remove(), 10000);
    }

    // Load messages on page load
    loadMessages();
});