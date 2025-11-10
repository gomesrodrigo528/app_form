from setuptools import setup, find_packages

setup(
    name="formapp",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'Flask==3.0.0',
        'Flask-Login==0.6.3',
        'Flask-WTF==1.2.1',
        'python-dotenv==1.0.0',
        'supabase==2.24.0',
        'httpx==0.28.1',
        'httpcore==1.0.9',
        'websockets==15.0.1',
        'bcrypt==4.1.2',
        'email-validator==2.1.0',
        'Werkzeug==3.0.1',
        'WTForms==3.1.1',
        'gunicorn==21.2.0',
    ],
    python_requires='>=3.8',
)
