# Amazon Product Review Visualizer

## Introduction
Team 21 - DVA Project

## Dataset

### Dataset Link
The dataset used was the [Amazon product data](https://cseweb.ucsd.edu/~jmcauley/datasets/amazon/links.html) dataset from UCSD. The [5-core electronics reviews](http://snap.stanford.edu/data/amazon/productGraph/categoryFiles/reviews_Electronics_5.json.gz) (9 GB) were used for our application. Product [metadata](http://snap.stanford.edu/data/amazon/productGraph/metadata.json.gz) (11 GB) was also included in the application.

### Populating Database
A script was used to populate a PostgreSQL database with the dataset from UCSD in order for the application to run smoothly as well as be deployable to the cloud. The steps to accomplish this are outlined below:

1. Install [Poetry](#setup) and install dependencies
2. Set `DATABASE_URL` environment variable to allow the `seed_db.py` script to insert rows into the database
3. Run `poetry run prisma db push` to create the table with the appropriate schema and generate a local client
4. Run `poetry run python3 seed_db.py` to push the dataset to the PostgreSQL database

## Poetry
This project uses [Poetry](https://python-poetry.org/) for dependency management. To install Poetry, follow the instructions [here](https://python-poetry.org/docs/#installation).

## Setup
To install the dependencies, run `poetry install` in the root directory of the project. Once it is installed, try `poetry shell` to activate the environment. This should enable the `poe` command.

Note: Ensure that the .env file, containing the database URL, password, and username, is placed in the root directory of the project. The current format of the .env file should be as follows (Replace the placeholders with your actual database credentials):
DATABASE_URL='postgres://[username]:[password]@[host]:[port]/[database]?sslmode=require'

VS Code should also prompt you to install the recommended extensions upon opening the project. They include the Python extension, the Black formatter, and iSort formatter. When you save a file, the formatters will automatically run. 

## Running the Project
To run the project, run `poe start-dev` in the root directory of the project. This will start the streamlit server. You can then access the app at `localhost:8501`.

To enable a smoother developer experience, visit the website on `localhost:8501`, click the three dots in the top right corner, and enable "Run on Save". This will automatically reload the app when you save a file.

## Running Tests
To run the tests, run `poe test` in the root directory of the project.

## Formatting
To format files, run `poe format` in the root directory of the project.

## Utility Scripts
To clean up the project, run `poe clean` in the root directory of the project. This will remove all of the generated `__pycache__` folders and `*.pyc` files.

To format the project, run `poe format` in the root directory of the project. This will run `black` on the project.

## Virtual Environment
When you run the `poe` scripts or `poetry` scripts, it should automatically use a virtual environment. If you want to manually activate the virtual environment, run `poetry shell` in the root directory of the project.

## Group Demo Video
We created a video for how to setup this project and run our application. See this [video](https://youtu.be/2Uk9yU0pOgk).
