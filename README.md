# Django Project

This is a Django project. Follow the steps below to set it up and run locally.

## Prerequisites

- Python 3.13.2
- pip (Python package manager)
- Virtual environment tool

## Setup Instructions

1. **Clone the repository**

   ```bash

   git clone https://github.com/valentino-strebel/22_core
   cd 22_core/core

   ```

2. **Create and activate a virtual environment**

   ```bash

   # On Linux/Mac

   python -m venv venv
   source venv/bin/activate

   ```

   ```powershell

   # On Windows

   python -m venv venv
   venv\Scripts\activate

   ```

3. **Install dependencies**

   ```bash

   pip install -r requirements.txt

   ```

4. **Create a superuser (for admin access)**

   ```bash

   python manage.py createsuperuser

   ```

5. **Run the development server**

   ```bash

   python manage.py runserver

   ```

6. **Access the project**

   ```bash

   Project: http://127.0.0.1:8000/

   Admin panel: http://127.0.0.1:8000/admin/

   ```
