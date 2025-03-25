document.addEventListener('DOMContentLoaded', () => {
    const chatList = document.querySelector('.chat-list');
    const chatOptionsBtn = document.getElementById('chatOptionsBtn');

    // Function to fetch and display chats
    function fetchChats() {
      fetch('/chats/', {
          method: 'GET',
          headers: {
              'Content-Type': 'application/json',
              'Authorization': `Token ${getAuthToken()}`  // Ensure authentication if needed
          }
      })
      .then(response => response.json())
      .then(data => {
          chatList.innerHTML = ''; // Clear existing content before updating

          if (data.length === 0) {
              chatList.innerHTML = '<p>No chats found.</p>';
              return;
          }

          data.forEach(chat => {
              const chatItem = document.createElement('li');
              chatItem.classList.add('chat-item');
              chatItem.dataset.chatId = chat.id;

              chatItem.innerHTML = `
                <h3>${chat.title}</h3>
                <p>Last message: "${chat.last_message ? chat.last_message.slice(0, 50) + (chat.last_message.length > 50 ? '...' : '') : 'No messages yet.'}"</p>
              `;

              chatItem.addEventListener('click', () => {
                  window.location.href = `/chat/${chat.id}/`;  // Redirect to chat
              });

              chatList.appendChild(chatItem);
          });
      })
      .catch(error => console.error('Error fetching chats:', error));
    }

    // Function to get auth token (modify based on your authentication system)
    function getAuthToken() {
      return localStorage.getItem('authToken');  // Ensure user is authenticated
    }

    // Redirect to home
    chatOptionsBtn.addEventListener('click', () => {
        window.location.href = '/';
    });

    // Load chats when the page loads
    fetchChats();
  });