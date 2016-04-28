How to install
===============

This file is for nginx. You need to do the following tasks:

1. Copy file to --> /etc/nginx/sites-available/
2. Create a symbolic link to nginx sites-enabled:
    ```bash
       sudo ln -s /etc/nginx/sites-available/nginxCity4ageAPI /etc/nginx/sites-enabled
    ```

3. Remember to destroy _default_ symbolic link in --> etc/nginx/sites-enabled
4. Create SSL folder:
    ```bash
       sudo mkdir /etc/nginx/ssl
    ```
5. Create a new SSL key:
    ```bash
       sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/nginx/ssl/nginx.key -out /etc/nginx/ssl/nginx.crt
    ```

    or use existing keys in _ssl_ folder
