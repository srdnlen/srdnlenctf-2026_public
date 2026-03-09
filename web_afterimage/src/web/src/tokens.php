<?php
session_start();
if (!isset($_SESSION['nickname'])) $_SESSION['nickname'] = 'Guest';
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Access Tokens</title>
    <link rel="stylesheet" href="static/style.css">
</head>
<body class="<?php echo $_SESSION['theme'] ?? 'light'; ?>">

    <nav class="navbar">
        <a href="index.php" class="brand">LocalVault</a>
        <div class="nav-links">
            <a href="index.php">Dashboard</a>
            <a href="profile.php">Settings</a>
            <a href="tokens.php" class="active">Tokens</a>
        </div>
    </nav>

    <div class="container">
        
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h2>Active Session Tokens</h2>
                <span style="background: var(--success-bg); color: var(--success-text); padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: bold;">Active</span>
            </div>
            <p>These tokens grant full access to your account. <strong>Do not share them.</strong></p>

            <div style="margin-top: 30px;">
                <label>Primary Auth Token (Session ID)</label>
                <div class="token-box">
                    <input type="password" id="sessToken" value="<?php echo session_id(); ?>" readonly>
                    <button type="button" onclick="toggleToken(this, 'sessToken')">Show</button>
                </div>
                <small style="color: var(--danger);">Warning: Anyone with this token can access your account.</small>
            </div>
        </div>

        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h2>Local Vault</h2>
                <span style="border: 1px solid var(--text-muted); color: var(--text-muted); padding: 4px 12px; border-radius: 20px; font-size: 0.85rem;">Browser Storage</span>
            </div>
            <p>Save or generate your secrets. Secrets are <strong>never sent to the server</strong>.</p>

            <div style="margin-top: 25px; border-bottom: 1px solid var(--glass-border); padding-bottom: 25px;">
                <label>Create New Secret</label>
                <div style="display: grid; grid-template-columns: 1fr 2fr auto; gap: 10px;">
                    <input type="text" id="newName" placeholder="Name" style="margin-bottom: 0;">
                    <div class="token-box" style="width: 100%;">
                        <input type="text" id="newValue" placeholder="Value or Generate..." style="margin-bottom: 0;">
                        <button type="button" onclick="generateRandom()">🎲</button>
                    </div>
                    <button type="button" onclick="saveSecret()" style="width: auto;">Save</button>
                </div>
            </div>

            <div id="secretList" style="margin-top: 25px;"></div>
        </div>

    </div>

    <script>
        function toggleToken(btn, inputId) {
            const input = document.getElementById(inputId);
            if (input.type === "password") {
                input.type = "text";
                btn.innerText = "Hide";
            } else {
                input.type = "password";
                btn.innerText = "Show";
            }
        }

        const STORAGE_KEY = 'localvault_client_secrets';

        function generateRandom() {
            const array = new Uint8Array(16);
            window.crypto.getRandomValues(array);
            const hex = Array.from(array).map(b => b.toString(16).padStart(2, '0')).join('');
            document.getElementById('newValue').value = 'localstorage_' + hex;
        }

        function escapeHtml(text) {
            if (!text) return "";
            return text
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        function saveSecret() {
            const nameInput = document.getElementById('newName');
            const valueInput = document.getElementById('newValue');
            
            const name = nameInput.value.trim();
            const value = valueInput.value.trim();

            if (!name || !value) {
                alert("Please enter both a name and a value.");
                return;
            }

            const newSecret = {
                id: Date.now(),
                name: name,
                value: value,
                created: new Date().toLocaleDateString()
            };

            const secrets = getSecrets();
            secrets.push(newSecret);
            localStorage.setItem(STORAGE_KEY, JSON.stringify(secrets));

            nameInput.value = '';
            valueInput.value = '';
            
            renderSecrets();
        }

        function getSecrets() {
            const stored = localStorage.getItem(STORAGE_KEY);
            return stored ? JSON.parse(stored) : [];
        }

        function deleteSecret(id) {
            if(!confirm("Delete this secret permanently?")) return;
            const secrets = getSecrets().filter(s => s.id !== id);
            localStorage.setItem(STORAGE_KEY, JSON.stringify(secrets));
            renderSecrets();
        }

        function renderSecrets() {
            const list = document.getElementById('secretList');
            const secrets = getSecrets();

            if (secrets.length === 0) {
                list.innerHTML = '<p style="text-align: center; color: var(--text-muted); font-style: italic;">No local secrets saved yet.</p>';
                return;
            }

            list.innerHTML = '';

            secrets.forEach(secret => {
                const uniqueId = 'sec_' + secret.id;
                
                const safeName = escapeHtml(secret.name);
                const safeValue = escapeHtml(secret.value);
                const safeDate = escapeHtml(secret.created);
                
                const item = document.createElement('div');
                item.style.marginBottom = '20px';
                item.innerHTML = `
                    <div style="display:flex; justify-content:space-between; margin-bottom: 5px;">
                        <label style="margin-bottom:0;">${safeName}</label>
                        <small style="color: var(--text-muted);">${safeDate}</small>
                    </div>
                    <div class="token-box">
                        <input type="password" id="${uniqueId}" value="${safeValue}" readonly>
                        <button type="button" onclick="toggleToken(this, '${uniqueId}')">Show</button>
                        <button type="button" onclick="deleteSecret(${secret.id})" style="border-left: 1px solid var(--glass-border); color: #e53e3e;">✕</button>
                    </div>
                `;
                list.appendChild(item);
            });
        }

        document.addEventListener('DOMContentLoaded', renderSecrets);
    </script>
</body>
</html>
