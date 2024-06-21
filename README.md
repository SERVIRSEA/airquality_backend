# AirQuality Explorer

Backend API setup for airquality explorer tool.

## Installation

### Prerequisites

Ensure you have the following prerequisites installed:

- python version >= 3.11
- PostgreSQL  (prefer latest version)
- THREDDS data path

### Steps

**Step 1: Update VM Packages**
    ```bash
    ssh vm_username@ip # put the login password 
    sudo apt update && sudo apt upgrade -y
    ```

**Step 2: Check Python Version and Upgrade to >= 3.11**
    ```bash
    # Add deadsnake repo
    sudo add-apt-repository ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install python3.11

    # Make python 3.11 as the default python3 interpreter
    sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11
    sudo update-alternatives --config python3
    python3 --version
    sudo apt install python-is-python3
    python --version

    # Install pip for python3.11
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python get-pip.py

    #Check pip version
    python -m pip --version

    # Configure bash or zshell
    nano ~/.bashrc # ~/.zshrc for Mac

    # Add alias to the end of file, save and exit the file
    alias pip='python -m pip'

    # Check and update pip version
    pip --version
    pip install --upgrade pip

    # Clean and remove unnecessary packages from vm
    sudo apt autoclean 
    sudo apt autoremove
    ```
**Step - 3: Clone the airquality backend git repository**
    ```bash
    git clone https://github.com/SERVIRSEA/airquality_backend.git

    # Rename the repo
    sudo mv airquality_backend airquality
    ```
**Step - 4: Create python3 virtual environment and installed necessary packages**
    ```bash  
    python3 -m venv airquality_env

    # Activate env to install packages
    source activate airquality_env/bin/activate

    # Change the dir to airquality
    cd airquality

    # Install required packages from requirements.tx
    pip install -r requirements.txt

    # If face any issues reqarding the dependency, you can try to install the required pagkages directly without specifying packages version or try with conda environment i.e.

    pip install django psycopg2-binary numpy shapely netcdf4 xarray pillow urllib3 geopy gunicorn python-dotenv djangorestframework django-cors-headers requests
    ```

**Step - 5: Create an .env file to manage secrets and credentials**
    ```bash

    # Change the dir again where settings.py file exist
    cd airquality

    # Create a new .env configuration file
    nano .env

    # Fill the credientials 
    # example .env file
    DJANGO_SECRET_KEY=<your-django-key>
    DEBUG=True
    ALLOWED_HOSTS=*
    CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
    CSRF_COOKIE_SECURE=False

    # Database 1 for django
    POSTGRES_HOST=<your-postgres-host-address>
    POSTGRES_USER=<your postgres-user>
    POSTGRES_PASS=<your postgres-pass>
    POSTGRES_DB=<your postgres-db-name>
    POSTGRES_PORT=5432

    # Database 2 for pcd data
    PCD_POSTGRES_HOST=localhost
    PCD_POSTGRES_USER=postgres
    PCD_POSTGRES_PASS=Kamal@2022
    PCD_POSTGRES_DB=aiq_pcd
    PCD_POSTGRES_PORT=5432

    # THREDDS path
    THREDDS_WMS_URL=<your-thredds-wms-url>
    THREDDS_CATALOG=<your-thredds-catalog>
    THREDDS_OPANDAP=<your-thredds-opandap-path>
    ```

**Step - 6: Run migrations, create superuser for accessing admin panel**
    ```bash
    # Navigate to main dir again where manage.py exists
    cd ..

    # Run migrations
    python manage.py makemigrations
    python manage.py migrate

    # Create superuser
    python manage.py createsuperuser 

    # Hit enter from keyboard, it will ask you to specify the username and password
    # Store this username and password to login the admin panel
    # If you are setting up in your local PC, you can access the admin panel by http://127.0.0.1:8000/admin with this credientials (you also need to generate the key (in step 8) to secure the api)
    # If you are are setting up in the remote server, you need additinal server configurations (see step 7 and beyond) to access the admin interface 
    ```

**Step - 7: Configure supervisor and nginx**  
    ```bash
    gunicorn --bind 0.0.0.0:8000 airquality.wsgi:application

    # If everything is okay, follow next step to setup nginx 
    sudo apt install supervisor nginx

    # Create supervisor configuration file
    sudo nano /etc/supervisor/conf.d/airquality.conf

    # example configuration file
    [program:airquality]
    command = <path_of_the_environment>/airquality_env/bin/gunicorn airquality.wsgi:application -b 127.0.0.1:8000airquality.wsgi:application -b 127.0.0.1:8000 -w 3 # /home/ubuntu/backend/airquality_env/bin/gunicorn airquality.wsgi:application -b 127.0.0.1:8000
    directory = <path_of_the_project_dir> # /home/ubuntu/backend/airquality
    user=ubuntu # username who own this dir
    autostart=true
    autorestart=true
    stopasgroup=true
    killasgroup=true
    redirect_stderr=true
    stdout_logfile=/var/log/supervisor/airquality.log # log file
    stderr_logfile=/var/log/supervisor/airquality.err.log
    environment=LANG=en_US.UTF-8,LC_ALL=en_US.UTF-8,DJANGO_SETTINGS_MODULE="airquality.settings"

    # Check and run supervisor
    sudo supervisorctl reread
    sudo supervisorctl update
    sudo supervisorctl start airquality

    # Check the status of supervisor
    sudo supervisorctl status airquality

    # If everything is okay, configure nginx
    # Create nginx .conf file
    sudo nano /etc/nginx/sites-available/airquality.com # use your own domain name if domain is not avilable just use airquality

    # example airquality configuration file

    server {
        listen 80;
        server_name <ip_or_domain_name>;  

        location = /favicon.ico { access_log off; log_not_found off; }

        location / {
            proxy_pass http://127.0.0.1:8000/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /static/ {
            alias /home/ubuntu/backend/static/; # path of the static dir
        }
    }

    # Remove the default config file
    sudo rm -r /etc/nginx/sites-available/default
    sudo rm -r /etc/nginx/sites-enabled/default

    # Create a symbolink
    sudo ln -s /etc/nginx/sites-available/airquality.com /etc/nginx/sites-enabled

    # Test, restart nginx and supervisor
    sudo nginx -t
    sudo systemctl restart nginx
    sudo supervisorctl restart airquality

    # you can now access the backend with your IP or domain
    ```

**Step - 8: Generate authorization key in admin to secure the backend API**
    ```bash
    # Login to admin panel
    http://127.0.0.1:8000/admin # if setup in local PC 
    http://<server_ip_or_domain>/admin # if setup in server

    # Generate key
    click on key and select the user from dropdown, then provide the key name and save. It will automatically generate the key. You can use this key to secure your api request.
    ```
**Link to front end code repository**
    https://github.com/SERVIRSEA/airquality_frontend
