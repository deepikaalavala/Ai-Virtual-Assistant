// DOM Elements
const profileTrigger = document.getElementById('profileTrigger');
const profileDropdown = document.getElementById('profileDropdown');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const chatArea = document.getElementById('chatArea');
const newChatBtn = document.querySelector('.new-chat-btn');
const mainContent = document.querySelector('.main-content');
const historyContainer = document.querySelector('.chat-history');



// Chat History
let chatHistory = [];
document.addEventListener("DOMContentLoaded", function () {
    const chatInput = document.getElementById("chatInput");
    const sendButton = document.getElementById("sendButton");
    const chatBox = document.getElementById("chatBox");

    // Function to send user message to Flask
    function sendMessage() {
        const userMessage = chatInput.value.trim();
        if (userMessage === "") return;

        // Display user message in chat UI
        displayMessage("You", userMessage);

        // Send message to Flask
        fetch("/command", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ command: userMessage }) // Send command as JSON
        })
        .then(response => response.json())
        .then(data => {
            // Display assistant's response
            displayMessage("Assistant", data.response);
        })
        .catch(error => console.error("Error:", error));

        chatInput.value = ""; // Clear input field
    }

    // Function to display message in chat UI
    function displayMessage(sender, message) {
        const messageElement = document.createElement("div");
        messageElement.classList.add("message");
        messageElement.innerHTML = `<strong>${sender}:</strong> ${message}`;
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to bottom
    }

    // Send message when button is clicked
    sendButton.addEventListener("click", sendMessage);

    // Send message when Enter is pressed
    chatInput.addEventListener("keypress", function (event) {
        if (event.key === "Enter") {
            sendMessage();
        }
    });
});


// Ensure elements exist before adding event listeners
if (profileTrigger && profileDropdown) {
    profileTrigger.addEventListener('click', toggleDropdown);
    document.addEventListener('click', closeDropdownOnClickOutside);
}

// Send message when pressing Enter (without Shift)
if (messageInput) {
    messageInput.addEventListener('keypress', handleKeyPress);
    messageInput.addEventListener('input', autoResizeTextarea);
}

// Send message when clicking send button
if (sendButton) {
    sendButton.addEventListener('click', sendMessage);
}

// Start a new chat
if (newChatBtn) {
    newChatBtn.addEventListener('click', startNewChat);
}

// Add click events for profile menu items
document.querySelectorAll('.dropdown-menu a').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const page = e.currentTarget.getAttribute('href').replace('#', '');
        showPage(page);
        profileDropdown.classList.remove('active');
    });
});

// Auto-resize textarea
function autoResizeTextarea() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 200) + 'px';
}

// Toggle Profile Dropdown
function toggleDropdown(e) {
    e.stopPropagation();
    profileDropdown.classList.toggle('active');
}

// Close dropdown when clicking outside
function closeDropdownOnClickOutside(e) {
    if (!profileDropdown.contains(e.target) && !profileTrigger.contains(e.target)) {
        profileDropdown.classList.remove('active');
    }
}

// Handle Enter key press to send message
function handleKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

// Format timestamp
function formatTime(date) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Send message function
function sendMessage() {
    const message = messageInput.value.trim();
    if (message === '') return;

    const timestamp = new Date();
    
    // Add message to chat history
    chatHistory.push({ content: message, timestamp });

    // Update chat area
    displayMessage('You', message, timestamp);

    // Clear input
    messageInput.value = '';
    messageInput.style.height = '40px';

    // Simulate AI response (replace with real API call)
    setTimeout(() => {
        const aiResponse = generateAIResponse(message);
        displayMessage('Assistant', aiResponse, new Date());
    }, 1000);
}

// Display message in chat area
function displayMessage(sender, message, timestamp) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('chat-message');
    messageElement.innerHTML = `
        <div class="message-header">
            <strong>${sender}</strong> <span>${formatTime(timestamp)}</span>
        </div>
        <div class="message-content">${message}</div>
    `;

    chatArea.appendChild(messageElement);
    chatArea.scrollTop = chatArea.scrollHeight;

    updateChatHistory();
}


// Update Chat History Sidebar
function updateChatHistory() {
    if (!historyContainer || chatHistory.length === 0) return;

    const lastMessage = chatHistory[chatHistory.length - 1];
    const time = formatTime(lastMessage.timestamp);

    const chatPreview = document.createElement('div');
    chatPreview.classList.add('chat-preview');
    chatPreview.style.padding = '0.5rem';
    chatPreview.style.borderBottom = '1px solid var(--border-color)';
    chatPreview.style.cursor = 'pointer';

    chatPreview.innerHTML = `
        <div style="font-weight: bold; margin-bottom: 0.25rem">Chat ${chatHistory.length}</div>
        <div style="color: var(--secondary-color); font-size: 0.9rem">${lastMessage.content.substring(0, 30)}...</div>
        <div style="color: var(--secondary-color); font-size: 0.8rem">${time}</div>
    `;

    chatPreview.addEventListener('click', () => loadChat(chatHistory.length - 1));

    // Add to beginning of history
    historyContainer.insertBefore(chatPreview, historyContainer.firstChild);
}

// Start a new chat
function startNewChat() {
    chatHistory = [];
    chatArea.innerHTML = '';
    historyContainer.innerHTML = '';
}

// Load previous chat
function loadChat(index) {
    chatArea.innerHTML = '';
    chatHistory.forEach(chat => displayMessage('You', chat.content, chat.timestamp));
}



// Show different pages
function showPage(page) {
    const pageContent = getPageContent(page);
    
    // Hide chat interface
    document.querySelector('.chat-area').style.display = 'none';
    document.querySelector('.input-area').style.display = 'none';
    
    // Remove existing page content if any
    const existingPage = document.querySelector('.page-content');
    if (existingPage) {
        existingPage.remove();
    }
    
    // Add new page content
    const pageElement = document.createElement('div');
    pageElement.className = 'page-content';
    pageElement.innerHTML = pageContent;
    
    // Add back button
    const backButton = document.createElement('button');
    backButton.className = 'back-button';
    backButton.innerHTML = '<i class="fas fa-arrow-left"></i> Back to Chat';
    backButton.addEventListener('click', showChatInterface);
    pageElement.insertBefore(backButton, pageElement.firstChild);
    
    mainContent.appendChild(pageElement);
}


document.addEventListener("DOMContentLoaded", function () {
    const logoutButton = document.querySelector('a[href="#logout"]'); // Select logout button

    if (logoutButton) {
        logoutButton.addEventListener("click", function (event) {
            event.preventDefault(); // Prevent default link behavior

            fetch('/logout', {
                method: 'GET'
            })
            .then(response => {
                if (response.redirected) {
                    window.location.href = response.url + '?logout=success';
                    
                    // Force stop the script after redirect
                    return; // Optional, but makes sure nothing else runs
                }
            })
            .catch(error => {
                console.error('Error:', error);

                // Stop execution on error as well, if needed
                return;
            });
        });
    }
});

function scrollToBottom() {
    let chatContainer = document.getElementById("chat-container");
    setTimeout(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 100); // Small delay ensures new messages are added first
}

// Function to add a new message
function addMessage(message, isUser = false) {
    let chatContainer = document.getElementById("chat-container");
    
    let messageDiv = document.createElement("div");
    messageDiv.classList.add("message");
    if (isUser) messageDiv.classList.add("user-message");
    messageDiv.innerText = message;
    
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

// Call on load
window.onload = function () {
    scrollToBottom();
};







async function saveChat(email, chatMessages) {
    if (!email || chatMessages.length === 0) return;

    try {
        const response = await fetch("/save_chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: email, chat: chatMessages }),
        });

        const data = await response.json();
        console.log("Chat save response:", data);

        if (data.success) {
            load_Chat_history(email);  // Refresh sidebar after saving chat
        }
    } catch (error) {
        console.error("Error saving chat:", error);
    }
}



// Function to stop chat 

document.addEventListener("DOMContentLoaded", function () {
    const stopChatBtn = document.getElementById("stop-chat-message");
    let aiResponseController = null;

    // Function to start AI response and show Stop button
    function startAIResponse() {
        stopChatBtn.style.display = "block"; // Show Stop button
        aiResponseController = new AbortController();
    }

    // Function to stop AI response
    function stopAIResponse() {
        if (aiResponseController) {
            aiResponseController.abort(); // Stop AI response
        }
        stopChatBtn.style.display = "none"; // Hide Stop button after stopping
    }

    stopChatBtn.addEventListener("click", stopAIResponse);
});


function stopResponse() {
    console.log("Stop button clicked!"); // Check if the click registers
    fetch('/stop', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log(data.message); // Should show "Response stopped"
        alert(data.message); // Optional, just for visibility
    })
    .catch(error => console.error('Error:', error));
}



// Show chat interface
function showChatInterface() {
    // Remove any page content
    const pageContent = document.querySelector('.page-content');
    if (pageContent) {
        pageContent.remove();
    }
    
    // Show chat interface
    document.querySelector('.chat-area').style.display = 'block';
    document.querySelector('.input-area').style.display = 'block';
}


            // Debugging: Check if elements exist
            console.log("Send Button:", sendButton);
            console.log("Message Input:", messageInput);

            // Send message when button is clicked
            sendButton.addEventListener("click", function () {
                console.log("Send button clicked"); // Debugging log
                sendMessage();
            });

            // Send message when "Enter" key is pressed
            messageInput.addEventListener("keypress", function (event) {
                if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    console.log("Enter key pressed"); // Debugging log
                    sendMessage();
                }
            });

            // Function to send message
            function sendMessage() {
                const message = messageInput.value.trim();
                if (message === "") return;

                console.log("Sending message:", message); // Debugging log

                // Add user message to chat area
                addMessage("user", message);
                messageInput.value = "";

                // Send message to Flask backend
                fetch("/command", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ command: message })
                })
                .then(response => response.json())
                .then(data => {
                    console.log("Response received:", data.response); // Debugging log
                    addMessage("ai", data.response);
                })
                .catch(error => console.error("Error sending message:", error));
            }

            // Function to add messages to chat
            function addMessage(type, content) {
                const messageDiv = document.createElement("div");
                messageDiv.classList.add("message", type === "user" ? "user-message" : "ai-message");
                messageDiv.textContent = content;
                chatArea.appendChild(messageDiv);
                chatArea.scrollTop = chatArea.scrollHeight;
            }

            // Microphone Button Functionality (Voice Command)
            micButton.addEventListener("click", function () {
                startListening();
            });
            

            function startListening() {
                console.log("Listening for voice input...");
                const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                recognition.lang = "en-US";

                recognition.onstart = function () {
                    console.log("Voice recognition started...");
                };

                recognition.onresult = function (event) {
                    const transcript = event.results[0][0].transcript;
                    console.log("Voice input received:", transcript);
                    messageInput.value = transcript;
                    sendMessage();
                };

                recognition.onerror = function (event) {
                    console.error("Voice recognition error:", event.error);
                };

                recognition.start();
            }
           





                // Add profile HTML to the page
             // document.body.innerHTML = getPageContent('profile');
                
                
                // Fetch user data and insert it into the existing HTML
                document.addEventListener('DOMContentLoaded', function() {
                    fetch('/get_user_info')
                        .then(response => response.json())
                        .then(data => {
                            if (data.name && data.email) {
                                document.getElementById('profile-name').textContent = data.name;
                                document.getElementById('profile-email').textContent = data.email;
                                document.getElementById('display-name').value = data.name;
                                document.getElementById('display-email').value = data.email;
                            } else {
                                console.error('Failed to get user info:', data.error);
                            }
                        })
                        .catch(error => console.error('Error fetching user info:', error));
                        
                });
                



            function getPageContent(page) {
                const pages = {
                    profile: `
                        <div class="page-container">
                            <h1>Profile</h1>
                            <div class="profile-info">
                                <div class="profile-header">
                                    <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=User" alt="Profile" class="large-profile-pic">
                                    <div class="profile-details">
                                        <h2 id="profile-name">Loading...</h2>
                                        <p id="profile-email">Loading...</p>
                                    </div>
                                </div>
                                <div class="profile-form">
                                    <div class="form-group">
                                        <label>Display Name</label>
                                        <input type="text" id="display-name" value="">
                                    </div>
                                    <div class="form-group">
                                        <label>Email</label>
                                        <input type="email" id="display-email" value="">
                                    </div>
                                    <div class="form-group">
                                        <label>Bio</label>
                                        <textarea rows="4">Web developer and tech enthusiast.</textarea>
                                    </div>
                                    <button class="save-button">Save Changes</button>
                                </div>
                            </div>
                           
                        </div>
                    `,
            
            
        about: `
            <div class="page-container">
                <h1>About Us</h1>
                <div class="about-content">
                    <h2>Welcome to SAM Assistant</h2>
                    <p>SAM Assistant is a state-of-the-art conversational platform designed to provide seamless communication and assistance. Our mission is to make AI-powered conversations accessible and intuitive for everyone.</p>
                    
                    <h3>Our Features</h3>
                    <ul>
                        <li>Intelligent conversation handling</li>
                        <li>Chat history management</li>
                        <li>Responsive design</li>
                        <li>User-friendly interface</li>
                    </ul>
                    
                    <h3>Version</h3>
                    <p>Current Version: 1.0.0</p>
                    
                    <h3>Contact</h3>
                    <p>For support or inquiries, please contact us at support@modernchatbot.com</p>
                </div>
            </div>
        `,
        settings: `
            <div class="page-container">
                <h1>Settings</h1>
                <div class="settings-content">
                    <section class="settings-section">
                        <h3>Appearance</h3>
                        <div class="setting-item">
                            <label>Theme</label>
                            <select>
                                <option>Light</option>
                                <option>Dark</option>
                                <option>System</option>
                            </select>
                        </div>
                        <div class="setting-item">
                            <label>Font Size</label>
                            <select>
                                <option>Small</option>
                                <option selected>Medium</option>
                                <option>Large</option>
                            </select>
                        </div>
                    </section>
                    
                    <section class="settings-section">
                        <h3>Notifications</h3>
                        <div class="setting-item">
                            <label>Desktop Notifications</label>
                            <label class="switch">
                                <input type="checkbox" checked>
                                <span class="slider"></span>
                            </label>
                        </div>
                        <div class="setting-item">
                            <label>Sound</label>
                            <label class="switch">
                                <input type="checkbox">
                                <span class="slider"></span>
                            </label>
                        </div>
                    </section>
                    
                    <section class="settings-section">
                        <h3>Privacy</h3>
                        <div class="setting-item">
                            <label>Save Chat History</label>
                            <label class="switch">
                                <input type="checkbox" checked>
                                <span class="slider"></span>
                            </label>
                        </div>
                    </section>
                    
                    <button class="save-button">Save Settings</button>
                </div>
            </div>
        `,
        help: `
            <div class="page-container">
                <h1>Help Center</h1>
                <div class="help-content">
                    <section class="help-section">
                        <h2>Getting Started</h2>
                        <div class="help-item">
                            <h3>Starting a New Chat</h3>
                            <p>Click the "New Chat" button in the sidebar to start a fresh conversation with the chatbot.</p>
                        </div>
                        <div class="help-item">
                            <h3>Sending Messages</h3>
                            <p>Type your message in the input field at the bottom and press Enter or click the send button.</p>
                        </div>
                    </section>
                    
                    <section class="help-section">
                        <h2>Features</h2>
                        <div class="help-item">
                            <h3>Chat History</h3>
                            <p>Your chat history is saved in the sidebar. Click on any previous chat to continue the conversation.</p>
                        </div>
                        <div class="help-item">
                            <h3>Profile Settings</h3>
                            <p>Click on your profile picture to access profile settings, about page, and help center.</p>
                        </div>
                    </section>
                    
                    <section class="help-section">
                        <h2>FAQ</h2>
                        <div class="help-item">
                            <h3>How do I clear my chat history?</h3>
                            <p>Go to Settings > Privacy and toggle off "Save Chat History". Then click "Clear History".</p>
                        </div>
                        <div class="help-item">
                            <h3>Is my data secure?</h3>
                            <p>Yes, we use industry-standard encryption to protect your conversations and personal data.</p>
                        </div>
                    </section>
                    
                    <section class="help-section">
                        <h2>Support</h2>
                        <p>Need more help? Contact our support team at support@modernchatbot.com</p>
                    </section>
                </div>
            </div>
        `
    };
    
    return pages[page] || '';
}

// Initialie
startNewChat();