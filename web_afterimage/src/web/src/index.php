<?php session_start(); ?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Dashboard</title>
    <link rel="stylesheet" href="static/style.css">
</head>
<body class="<?php echo $_SESSION['theme'] ?? 'light'; ?>">

    <nav class="navbar">
        <a href="index.php" class="brand">LocalVault</a>
        <div class="nav-links">
            <a href="index.php" class="active">Dashboard</a>
            <a href="profile.php">Settings</a>
            <a href="tokens.php">Tokens</a>
        </div>
    </nav>

    <div class="container">
        <div class="card" style="border-left: 4px solid var(--primary);">
            <h1>Welcome back, <?php echo $_SESSION['nickname'] ?? 'Guest'; ?>!</h1>
            <p>You are currently logged into the secure dashboard.</p>
        </div>

        <div class="card">
            <h2 style="border-bottom: 1px solid var(--border-color); padding-bottom: 10px; margin-bottom: 20px;">Profile Summary</h2>
            
            <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 20px;">
                <div>
                    <strong>Biography</strong>
                    <p style="background: var(--bg-color); padding: 10px; border-radius: 6px; margin-top: 5px;">
                        <?php echo $_SESSION['bio'] ?? 'No biography set.'; ?>
                    </p>
                </div>
                <div>
                    <strong>Life Motto</strong>
                    <p style="font-style: italic; color: var(--primary); font-size: 1.2rem;">
                        "<?php echo $_SESSION['motto'] ?? ''; ?>"
                    </p>
                </div>
            </div>
        </div>
    </div>

</body>
</html>
