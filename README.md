# LBD Subject Data Management App

This repository contains a Django-based web application for managing and exporting LBD subject data across various modalities such as acoustic, actigraphy, handwriting, psychology, TCS, and CEI. The application provides detailed views and update views for each modality, as well as functionality to export data and reports in CSV and PDF formats. 

## Installation

### 1. Install the database
Install postgresql from https://www.postgresql.org/download/. Username and password of the database admin user that are set are those that will be used in the environments as `DB_USER` and `DB_PASSWORD`.

### 2. Install the package
```
# Clone the repository
git clone https://github.com/BDALab/lbd_analysis_tool.git

# Install packaging utils
pip install --upgrade pip
pip install --upgrade virtualenv

# Change directory
cd lbd-analysis-tool

# Activate virtual environment
# Linux
# Windows

# Linux
virtualenv .venv
source .venv/bin/activate

# Windows
virtualenv venv
venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

### 3. Set the environments
Set `.env` file at `lbd-analysis-tool/app/.env` as (replace `<...>` with your own settings):
```
DEBUG=True
SECRET_KEY='<secret key>'
DB_NAME=<database name>
DB_USER=<database username>
DB_PASSWORD=<database password>
DB_HOST=localhost
DB_PORT=5432
```

### 4. Create the database
Create a database using pgAdmin (named as `DB_NAME`)

### 5. Run the migrations
Call the following commands:
```
python manage.py makemigrations
python manage.py migrate
```

### 6. Create the superuser
`python manage.py createsuperuser`

### 7. Run the server
`python manage.py runserver`