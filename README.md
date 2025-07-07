# Nginx Configuration for thingdata-server

This document provides instructions on how to set up Nginx to act as a reverse proxy for your `thingdata-server` application. This configuration will handle HTTP to HTTPS redirection and proxy pass requests to your application.

**Note on Docker Commands:** This guide assumes you are using Docker Compose V2, where commands are typically run as `docker compose ...` (no hyphen). If you are using an older, standalone version of Docker Compose (V1), your commands would be `docker-compose ...` (with a hyphen). It is recommended to use Docker Compose V2.

## Prerequisites

*   A running instance of `thingdata-server`. If you are running it via Docker as per a typical setup for this project, you would usually start it with `docker compose up --build`. (Assumed to be on `http://localhost:3000` as exposed by Nginx, though the actual app port might be different, e.g., 8000, inside Docker).
*   A domain name or subdomain pointed to your server's IP address.
*   Root or sudo access to your server.

## 1. Install Nginx

If you don't have Nginx installed, you can install it using your system's package manager.

**For Debian/Ubuntu:**

```bash
sudo apt update
sudo apt install nginx
```

**For CentOS/RHEL:**

```bash
sudo yum install epel-release
sudo yum install nginx
```

After installation, enable and start the Nginx service:

```bash
sudo systemctl enable nginx
sudo systemctl start nginx
```

## 2. Configure Nginx

The provided `thingdata.conf` file is a template for your Nginx configuration.

### 2.1. Copy the Configuration File

Copy `thingdata.conf` to Nginx's `sites-available` directory. It's good practice to name it after your domain.

```bash
sudo cp thingdata.conf /etc/nginx/sites-available/your_domain_or_subdomain.com.conf
```

### 2.2. Customize the Configuration

Open the copied configuration file with a text editor (e.g., `nano`, `vim`):

```bash
sudo nano /etc/nginx/sites-available/your_domain_or_subdomain.com.conf
```

You **must** customize the following:

*   **`server_name`**: Replace `your_domain_or_subdomain.com` with your actual domain or subdomain in both server blocks (HTTP and HTTPS).
*   **SSL Certificates**:
    *   If you already have SSL certificates, uncomment and update these lines with the correct paths:
        ```nginx
        # ssl_certificate /path/to/your/fullchain.pem;
        # ssl_certificate_key /path/to/your/privkey.pem;
        ```
    *   If you don't have SSL certificates, see section 3 for instructions on obtaining them with Let's Encrypt.
*   **`proxy_pass` (if needed)**: If your `thingdata-server` is running on a port other than `3000`, change `http://localhost:3000` accordingly.

### 2.3. Enable the Site Configuration

Create a symbolic link from the `sites-available` directory to the `sites-enabled` directory:

```bash
sudo ln -s /etc/nginx/sites-available/your_domain_or_subdomain.com.conf /etc/nginx/sites-enabled/
```

**Important**: Ensure there are no conflicting default configurations. You might need to remove or disable the default Nginx configuration if it listens on port 80 for the same server name:

```bash
# Check if the default site is enabled
ls /etc/nginx/sites-enabled/

# If 'default' is present and you don't need it, remove the symlink
# sudo rm /etc/nginx/sites-enabled/default
```

### 2.4. Test Nginx Configuration

Before restarting Nginx, test your configuration for syntax errors:

```bash
sudo nginx -t
```

If the test is successful, you'll see output like:

```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

If there are errors, the output will indicate the file and line number causing the issue.

### 2.5. Reload Nginx

If the configuration test is successful, reload Nginx to apply the changes:

```bash
sudo systemctl reload nginx
```

## 3. Obtain SSL Certificates (Let's Encrypt)

Let's Encrypt provides free SSL/TLS certificates. The easiest way to use Let's Encrypt with Nginx is by using `certbot`.

### 3.1. Install Certbot

**For Debian/Ubuntu:**

```bash
sudo apt install certbot python3-certbot-nginx
```

**For CentOS/RHEL:** (Instructions may vary slightly based on version)

```bash
sudo yum install certbot python2-certbot-nginx # Or python3-certbot-nginx if available
```

### 3.2. Obtain and Install Certificate

Run Certbot, specifying your domain(s). Certbot will automatically detect your Nginx configuration for the specified domain and offer to modify it for HTTPS.

```bash
sudo certbot --nginx -d your_domain_or_subdomain.com
```

Follow the on-screen prompts. Certbot will:
1.  Ask for your email address (for renewal notices).
2.  Ask you to agree to the Terms of Service.
3.  Ask if you want to share your email with the EFF.
4.  Detect your server block from `your_domain_or_subdomain.com.conf`.
5.  Offer to automatically configure HTTPS for you (it will update the SSL directives in your Nginx config). Choose this option.

Certbot will then obtain the certificate and update your Nginx configuration to use it. It will also set up automatic renewal.

If you chose to let Certbot modify your Nginx configuration, it will automatically uncomment and fill in the `ssl_certificate` and `ssl_certificate_key` lines in `/etc/nginx/sites-available/your_domain_or_subdomain.com.conf`.

### 3.3. Verify Auto-Renewal

Certbot should set up a cron job or systemd timer to automatically renew your certificates. You can test the renewal process with a dry run:

```bash
sudo certbot renew --dry-run
```

## 3.bis. Alternative: Creating Self-Signed SSL Certificates (for Development/Testing)

If you are setting up a development or testing environment and do not need a publicly trusted SSL certificate, you can generate a self-signed certificate. Browsers will display a warning for self-signed certificates, but they can be useful for local development.

**Warning:** Self-signed certificates do not provide the same level of trust as certificates issued by a Certificate Authority (CA) like Let's Encrypt. **Do not use self-signed certificates for production environments.**

### 3.bis.1. Generate a Self-Signed Certificate and Key

You can use OpenSSL to generate a private key and a self-signed certificate.

1.  **Create a directory for your SSL certificates (if it doesn't exist):**
    ```bash
    sudo mkdir -p /etc/nginx/ssl
    ```

2.  **Generate the key and certificate:**
    This command will create a 2048-bit RSA private key (`nginx-selfsigned.key`) and a self-signed certificate (`nginx-selfsigned.crt`) valid for 365 days. You will be prompted to enter information for the certificate (Country Name, State, Organization Name, etc.). You can leave most of these blank or fill them as you see fit. For "Common Name", it's good practice to use your domain name or server's IP address.

    ```bash
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/nginx-selfsigned.key \
        -out /etc/nginx/ssl/nginx-selfsigned.crt
    ```
    *   `req -x509`: Specifies that we want to create a self-signed certificate.
    *   `-nodes`: Skips the option to secure our key with a passphrase. Nginx needs to be able to read this file without intervention when starting.
    *   `-days 365`: Sets the validity period of the certificate.
    *   `-newkey rsa:2048`: Creates a new private key using RSA encryption with a 2048-bit key length.
    *   `-keyout`: Specifies the output file for the private key.
    *   `-out`: Specifies the output file for the certificate.

3.  **Restrict permissions for the private key:**
    ```bash
    sudo chmod 600 /etc/nginx/ssl/nginx-selfsigned.key
    ```

### 3.bis.2. Configure Nginx to Use the Self-Signed Certificate

Edit your Nginx site configuration file (e.g., `/etc/nginx/sites-available/your_domain_or_subdomain.com.conf`):

```bash
sudo nano /etc/nginx/sites-available/your_domain_or_subdomain.com.conf
```

In the `server` block that listens on port `443 ssl`, uncomment or add the following lines, pointing to the key and certificate you just created:

```nginx
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;

    server_name your_domain_or_subdomain.com_or_localhost; # Adjust as needed

    ssl_certificate /etc/nginx/ssl/nginx-selfsigned.crt;
    ssl_certificate_key /etc/nginx/ssl/nginx-selfsigned.key;

    # ... other SSL settings and location block ...
}
```

Make sure to replace `your_domain_or_subdomain.com_or_localhost` with the actual server name you are using for this development setup (e.g., `localhost`, `dev.example.com`).

### 3.bis.3. Test and Reload Nginx

After making these changes:

1.  **Test your Nginx configuration:**
    ```bash
    sudo nginx -t
    ```
2.  **If the test is successful, reload Nginx:**
    ```bash
    sudo systemctl reload nginx
    ```

Now, when you access your site via HTTPS, it will use the self-signed certificate. Your browser will show a warning, which you'll need to accept to proceed.

## 4. Firewall Configuration

If you have a firewall enabled (e.g., `ufw` on Ubuntu, `firewalld` on CentOS), ensure that HTTP (port 80) and HTTPS (port 443) traffic are allowed.

**For `ufw` (Ubuntu):**

```bash
sudo ufw allow 'Nginx Full' # Allows both HTTP and HTTPS
# or individually:
# sudo ufw allow 'Nginx HTTP'
# sudo ufw allow 'Nginx HTTPS'
sudo ufw enable
sudo ufw status
```

**For `firewalld` (CentOS/RHEL):**

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## 5. Testing

Open your web browser and navigate to `http://your_domain_or_subdomain.com`. You should be automatically redirected to `https://your_domain_or_subdomain.com`, and you should see your `thingdata-server` application.

Check the SSL certificate by clicking the padlock icon in your browser's address bar.

## Customization Notes

*   **Upstream Application Port**: If your `thingdata-server` runs on a port other than `3000`, update the `proxy_pass http://localhost:3000;` line in `thingdata.conf`.
*   **WebSocket Support**: If your application uses WebSockets, uncomment the following lines in the `location /` block of your HTTPS server configuration:
    ```nginx
    # proxy_http_version 1.1;
    # proxy_set_header Upgrade $http_upgrade;
    # proxy_set_header Connection "upgrade";
    ```
*   **Advanced SSL/TLS Settings**: The `thingdata.conf` includes commented-out lines for recommended SSL/TLS security enhancements (cipher suites, HSTS, etc.). You can uncomment and adjust these as needed after you have HTTPS working. Research these settings to understand their implications.

This completes the setup. Your Nginx server is now configured to securely proxy requests to your `thingdata-server`.
