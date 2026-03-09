<?php
session_start();
require_once __DIR__ . '/utils/parser.php';

$defaults = ['nickname'=>'Guest', 'bio'=>'', 'motto'=>'', 'theme'=>'light'];
foreach ($defaults as $k => $v) if (!isset($_SESSION[$k])) $_SESSION[$k] = $v;

$allowed_fields = ['nickname', 'bio', 'motto', 'theme', 'security_integrity_lock'];

$msg = "";
if ($_SERVER['REQUEST_METHOD'] === 'POST') {

    if (isset($_POST['save_manual'])) {
        if (($_SESSION['security_integrity_lock'] ?? 'false') !== 'true') {
            foreach ($allowed_fields as $field) {
                if (isset($_POST[$field])) {
                    $_SESSION[$field] = htmlspecialchars($_POST[$field]);
                }
            }
            $msg = "Profile updated successfully.";
        } 
        else {
            $msg = "Security Integrity has been enabled. Updates are disabled.";
        }
    }

    if (isset($_FILES['config_file']) && $_FILES['config_file']['error'] === 0) {

				$baseDir = '/tmp';
				$filename = basename($_FILES['config_file']['name']);
				$filename = preg_replace('/[^A-Za-z0-9._-]/', '_', $filename);

				$path = $baseDir . '/' . $filename;

				$realBase = realpath($baseDir);
				$realDir  = realpath(dirname($path));

				if ($realDir !== $realBase) {
						die("Invalid file name");
				}

				if (is_link($path)) {
						die("Invalid file name");
				}

        if (move_uploaded_file($_FILES['config_file']['tmp_name'], $path)) {
            $settings = parse_settings_file($path);
            if (($_SESSION['security_integrity_lock'] ?? 'false') !== 'true') {
                foreach ($allowed_fields as $field) {
                    if (isset($settings[$field])) {
                        $_SESSION[$field] = htmlspecialchars($settings[$field]);
                    }
                }
                $msg = "Configuration restored.";
            } 
            else {
                $msg = "Security Integrity has been enabled. Updates are disabled.";
            }
        }
    }
}

$is_locked = ($_SESSION['security_integrity_lock'] ?? 'false') === 'true';
$disabled_attr = $is_locked ? 'disabled' : '';
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Settings</title>
    <link rel="stylesheet" href="static/style.css">
    <style>
        input:disabled, textarea:disabled, select:disabled {
            background-color: #f0f0f0;
            color: #888;
            cursor: not-allowed;
            border-color: #ddd;
        }
        button:disabled {
            background-color: #ccc !important;
            cursor: not-allowed;
            opacity: 0.7;
        }
    </style>
</head>
<body class="<?php echo $_SESSION['theme']; ?>">

    <nav class="navbar">
        <a href="index.php" class="brand">LocalVault</a>
        <div class="nav-links">
            <a href="index.php">Dashboard</a>
            <a href="profile.php" class="active">Settings</a>
            <a href="tokens.php">Tokens</a>
        </div>
    </nav>

    <div class="container">
        <?php if ($msg): ?>
            <div class="alert"><?php echo $msg; ?></div>
        <?php endif; ?>

        <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 24px;">
             
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h2>Edit Profile</h2>
                    <?php if($is_locked): ?>
                        <span style="background:#e53e3e; color:white; padding: 4px 8px; border-radius:4px; font-size:0.8rem; font-weight:bold;">LOCKED</span>
                    <?php endif; ?>
                </div>

                <form method="POST">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <label>Nickname</label>
                            <input type="text" name="nickname" value="<?php echo $_SESSION['nickname']; ?>" <?php echo $disabled_attr; ?>>
                        </div>
                        <div>
                            <label>Motto</label>
                            <input type="text" name="motto" value="<?php echo $_SESSION['motto']; ?>" <?php echo $disabled_attr; ?>>
                        </div>
                    </div>

                    <label>Biography</label>
                    <textarea name="bio" rows="4" <?php echo $disabled_attr; ?>><?php echo $_SESSION['bio']; ?></textarea>

                    <label>Interface Theme</label>
                    <select name="theme" style="margin-bottom: 20px;" <?php echo $disabled_attr; ?>>
                        <option value="light" <?php echo $_SESSION['theme']=='light'?'selected':''; ?>>Light Mode</option>
                        <option value="dark" <?php echo $_SESSION['theme']=='dark'?'selected':''; ?>>Dark Mode</option>
                    </select>

                    <?php if (!$is_locked): ?>
                        <div style="background-color: #fff5f5; border: 1px solid #fc8181; border-left: 5px solid #e53e3e; padding: 16px; margin-bottom: 24px; border-radius: 4px; display: flex; gap: 16px;">
                            <div style="padding-top: 4px;">
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#c53030" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                                    <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                                </svg>
                            </div>
                            <div>
                                <h4 style="margin: 0 0 8px 0; color: #c53030; font-size: 1.1rem;">Security Integrity Lock</h4>
                                <p style="margin: 0 0 16px 0; font-size: 0.9rem; line-height: 1.5; color: #742a2a;">
                                    Enable this to permanently freeze your profile settings. 
                                    <strong>This action cannot be undone.</strong>
                                </p>
                                <label style="display: flex; align-items: center; cursor: pointer; color: #9b2c2c; font-weight: bold;">
                                    <input type="checkbox" name="security_integrity_lock" value="true" style="margin: 0 10px 0 0; width: 18px; height: 18px; cursor: pointer;">
                                    <span style="position: relative; top: 1px;">Enable Security Lock</span>
                                </label>
                            </div>
                        </div>
                        <button type="submit" name="save_manual">Save Changes</button>
                    
                    <?php else: ?>
                        <div style="background-color: #f0fff4; border: 1px solid #68d391; border-left: 5px solid #2f855a; padding: 16px; margin-bottom: 24px; border-radius: 4px; display: flex; gap: 16px;">
                            <div style="padding-top: 4px;">
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2f855a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                                    <path d="M9 12l2 2 4-4"/>
                                </svg>
                            </div>
                            <div>
                                <h4 style="margin: 0 0 5px 0; color: #2f855a; font-size: 1.1rem;">Profile is Locked</h4>
                                <p style="margin: 0; font-size: 0.9rem; color: #276749;">
                                    Security Integrity is active. Changes to this profile are permanently disabled.
                                </p>
                            </div>
                        </div>
                        <button type="button" disabled>Updates Disabled</button>
                    <?php endif; ?>
                </form>
            </div>

            <div class="card">
                <h3>Backup & Restore</h3>
                <p style="font-size: 0.9rem; margin-bottom: 20px;">
                    Upload a <code>.txt</code> configuration file to bulk-update your profile settings.
                </p>
                <form method="POST" enctype="multipart/form-data">
                    <label>Configuration File</label>
                    <input type="file" name="config_file" style="padding: 6px;" <?php echo $disabled_attr; ?>>
                    <button type="submit" style="background-color: var(--text-color);" <?php echo $disabled_attr; ?>>Restore Backup</button>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
