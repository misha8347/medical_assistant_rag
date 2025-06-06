document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatMessages = document.getElementById('chatMessages');
    const chatOptionsBtn = document.getElementById('chatOptionsBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');

    // Get chat ID from the template
    const chatContainer = document.getElementById('chatContainer');

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
        const response = await fetch("/generate_health_recommendation", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ "query": message })
        });
        if (!response.ok) {
            const errorText = await response.text();  // get raw error for debugging
            throw new Error(`Server responded with ${response.status}: ${errorText}`);
        }
        console.log(response)
        const data = await response.json();
        return data;
    }
    

    // Send message handler
    sendBtn.addEventListener('click', async () => {
        const message = chatInput.value.trim();
        if (message === '') {
            showToast('Please enter a message.');
            return;
        }

        // Display the user's message
        addMessage(message, true);
        chatInput.value = '';

        // Show spinner
        loadingSpinner.style.display = 'flex';

        try{
            console.log('sending message to ml service')
            let health_recommendation = await generateHealthRecommendation(message)
            // Hide spinner after receiving response
            loadingSpinner.style.display = 'none';
            console.log(health_recommendation.response)
            console.log('response received!')
            // Simulated echo reply after 1 second (replace with real back-end integration)
            setTimeout(() => {
                addMessage(health_recommendation.response, false);
            }, 1000);
        } catch (error) {
            console.error("❌ Error from backend:", error);
            loadingSpinner.style.display = 'none';
            addMessage("⚠️ Error getting response. Please try again.", false);
            // console.error(error);
        }
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

    // Function to display a toast message
    function showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => toast.classList.add('fade-out'), 9000);
        setTimeout(() => toast.remove(), 10000);
    }
});