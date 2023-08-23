# BlogFlaskProject
## Flask Blog Project

This is a simple blog project developed using Flask, a micro web framework for Python. It allows users to create, edit, and delete blog posts.
Before you begin, ensure you have met the following requirements:

- Python 3.x installed
- [SQLite](https://www.sqlite.org/) (for the database)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/flask-blog-project.git

  Navigate to the project directory:

```bash
cd flask-blog-project
```
Create and activate a virtual environment (optional but recommended):


```bash
python -m venv venv
source venv/bin/activate
```
Install the required dependencies:


```bash
pip install -r requirements.txt
```
Set the environment variable for the Flask secret key (replace 'your_secret_key' with your actual secret key):


```bash
export FLASK_KEY='your_secret_key'
```
Initialize the database:


```bash
flask db upgrade
```
Start the Flask development server:


```bash
flask run
```
By default, the application will be accessible at http://localhost:5000.


### Usage
Visit the application in your web browser.
Create a new blog post by clicking the "Create New Post" button.
Edit or delete existing blog posts.
Explore other sections like "About" and "Contact."
Features
User-friendly blog creation and management.
CKEditor for rich text editing.
SQLite database for data storage.
Bootstrap 5 for a responsive design.
Flash messages for user feedback.

