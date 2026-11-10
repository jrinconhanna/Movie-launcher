#!/bin/bash
# Movie Launcher · V2.3 · a small read-only web server on Whatbox so Infuse can play
# a video straight from a link. Serves ~/files/Javi only, GET/HEAD only, with its own
# username and password (not your Whatbox password). Based on Whatbox's "Userland Nginx" guide.
# Run on Whatbox over SSH:  bash whatbox-player-setup.sh      Stop it:  pkill -f launcher-nginx/nginx.conf
set -e
D="$HOME/.config/launcher-nginx"
ROOT="$HOME/files/Javi"
[ -d "$ROOT" ] || { echo "Can't find $ROOT"; exit 1; }
mkdir -p "$D/tmp"
PORT=$(sed -n 's/.*listen \([0-9]*\) default.*/\1/p' "$D/nginx.conf" 2>/dev/null | head -1)
[ -n "$PORT" ] || PORT=$(shuf -i 10000-32767 -n 1)

echo "Pick a username and password just for the launcher (NOT your Whatbox password)."
read -r -p "Launcher username: " U
read -r -s -p "Launcher password: " P; echo
[ -n "$U" ] && [ -n "$P" ] || { echo "Both are needed."; exit 1; }
if command -v crypt >/dev/null 2>&1; then H=$(crypt "$P"); else H=$(openssl passwd -apr1 "$P"); fi
echo "$U:$H" > "$D/htpasswd.conf"; chmod 600 "$D/htpasswd.conf"

cat > "$D/nginx.conf" <<CONF
error_log $D/error.log warn;
pid /dev/null;
events { worker_connections 128; }
http {
    types { video/mp4 mp4 m4v; video/x-matroska mkv; video/quicktime mov; video/x-msvideo avi; image/png png; image/jpeg jpg jpeg; }
    default_type application/octet-stream;
    access_log $D/access.log combined;
    client_body_temp_path $D/tmp/client_body; proxy_temp_path $D/tmp/proxy; fastcgi_temp_path $D/tmp/fastcgi; uwsgi_temp_path $D/tmp/uwsgi; scgi_temp_path $D/tmp/scgi;
    server_tokens off; sendfile on; tcp_nopush on; keepalive_timeout 15;
    server {
        listen $PORT default;
        listen [::]:$PORT default;
        root $ROOT/;
        autoindex on;
        auth_basic "Movie Launcher";
        auth_basic_user_file $D/htpasswd.conf;
        location / { limit_except GET { deny all; } }
    }
}
CONF

cat > "$D/start" <<START
#!/bin/bash
/usr/sbin/nginx -c $D/nginx.conf &> /dev/null
START
chmod +x "$D/start"
( crontab -l 2>/dev/null | grep -v "launcher-nginx/start"; echo "@reboot $D/start" ) | crontab -

pkill -f "launcher-nginx/nginx.conf" 2>/dev/null || true
sleep 1; "$D/start"; sleep 1
A=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$PORT/")
B=$(curl -s -o /dev/null -w "%{http_code}" -u "$U:$P" "http://127.0.0.1:$PORT/")
echo
echo "Check without login (should be 401): $A"
echo "Check with login    (should be 200): $B"
echo "PORT: $PORT"
echo "Next: Whatbox › Manage Links › add a custom app named player with port $PORT, then tell Claude the https address it shows."
