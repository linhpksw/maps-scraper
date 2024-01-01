# Project Setup Guide

This guide provides step-by-step instructions to set up and run the project on a Windows environment. Please follow these instructions carefully to ensure a smooth setup.

## Prerequisites

Before beginning, ensure you have Python installed on your machine. You can download Python from the official website: [python.org](https://www.python.org/downloads/).

## Installation Steps

### Step 1: Install Poetry

Poetry is a tool for dependency management and packaging in Python. To install Poetry on Windows, open PowerShell and execute the following command:

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

### Step 2: Verify Poetry Installation

To ensure that Poetry has been installed successfully, check its version by executing:

```powershell
poetry --version
```

### Step 3: Install Dependencies

Install the required packages for this project with Poetry. Navigate to the project's root directory and run:

```powershell
poetry install
```

### Step 4: Check PYTHONPATH Environment Variable

The PYTHONPATH variable should include the path to your project. To set it temporarily for your PowerShell session, use the following command (modify the path according to your project's location):

```powershell
$Env:PYTHONPATH = "C:\\Users\\YourUsername\\Desktop\\maps-scraper\\src"
```

### Step 5: Run the Project

Now, you can run the project using the following command:

```powershell
poetry run python src\\maps_scraper\\main.py
```
