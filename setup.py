from setuptools import setup, find_packages
import os

def get_requirements():
    with open('requirements.txt', 'r') as file:
        dependencies = file.readlines()
    
    dependencies = [d.strip() for d in dependencies if '#' not in d.strip() and d.strip()]
    
    return dependencies


setup(
    name="text_to_sql_agentic_bot",
    version="0.1.0",
    description="Text to SQL Agentic Bot project",
    author="Swatantra Jain",
    author_email="",
    url="https://github.com/SwatantraJain-02/Text_To_SQL-Agentic_Bot",
    packages=find_packages(),
    include_package_data=True,
    install_requires=get_requirements(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
