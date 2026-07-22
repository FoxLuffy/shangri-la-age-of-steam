#!/bin/sh
# This script runs before Nginx starts to inject runtime environment variables into the compiled static JS files.

echo "Injecting runtime environment variables..."

BACKEND_URL="${VITE_BACKEND_URL:-http://localhost:8003}"

# Find all javascript files in the assets directory
for file in /usr/share/nginx/html/assets/*.js; do
    if [ -f "$file" ]; then
        echo "Processing $file..."
        # Replace the placeholder with the actual runtime URL
        sed -i "s|__VITE_BACKEND_URL__|$BACKEND_URL|g" "$file"
    fi
done

echo "Injection complete. Starting Nginx."
