document.addEventListener('DOMContentLoaded', loadUsers);

function loadUsers() {
    fetch('/get_users')
        .then(response => response.json())
        .then(users => {
            const userList = document.getElementById('user-list');
            userList.innerHTML = users.map(user => `
                <tr>
                    <td><a href="#" onclick="showHistory('${user.email}')">${user.name}</a></td>
                    <td>${user.email}</td>
                    <td><span class="status ${user.status}">${user.status}</span></td>
                    <td>${user.last_active}</td>
                    <td><button class="${user.status === 'active' ? 'block-btn' : 'unblock-btn'}" onclick="toggleStatus(this, '${user.email}', '${user.status === 'active' ? 'blocked' : 'active'}')">
                        ${user.status === 'active' ? 'Block' : 'Unblock'}
                    </button></td>
                </tr>
            `).join('');
        });
}

function showHistory(email) {
    fetch(`/get_history?email=${email}`)
        .then(response => response.json())
        .then(history => {
            const historySection = document.getElementById('user-history');
            const historyContent = document.getElementById('history-content');
            historyContent.innerHTML = history.map(h => `<p>${h}</p>`).join('');
            historySection.style.display = 'block';
        });
}

function toggleStatus(button, email, newStatus) {
    fetch(`/toggle_status?email=${email}&status=${newStatus}`, { method: 'POST' })
        .then(response => response.json())
        .then(() => loadUsers());
}
function logout() {
    fetch('/logout', {
        method: 'GET'
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
            // Stop further code execution
            return;
        }
    })
    .catch(error => console.error('Error:', error));
}
