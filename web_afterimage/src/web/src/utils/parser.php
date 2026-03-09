<?php

/**
 * Reads a file and returns an array of settings.
 * Format expected: key: value
 */
function parse_settings_file($filepath) {
    if (!file_exists($filepath)) {
        return [];
    }

    $lines = file($filepath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    if ($lines === false) {
        return [];
    }

    $data = [];

    foreach ($lines as $line) {
        // Skip comments
        if (strpos(trim($line), '#') === 0) continue;

        // Split at first colon
        $parts = explode(':', $line, 2);

        if (count($parts) === 2) {
            $key = trim($parts[0]);
            $value = trim($parts[1]);
            
            // Clean quotes
            $value = trim($value, "\"'"); 

            $data[$key] = $value;
        }
    }

    return $data;
}
