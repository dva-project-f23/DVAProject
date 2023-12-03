# Amazon Product Review Visualizer

## Introduction

Team 21 - DVA Project

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

## Dataset

### Dataset Link

The dataset used was the [Amazon product data](https://cseweb.ucsd.edu/~jmcauley/datasets/amazon/links.html) dataset from UCSD. The [5-core electronics reviews](http://snap.stanford.edu/data/amazon/productGraph/categoryFiles/reviews_Electronics_5.json.gz) (9 GB) were used for our application. Product [metadata](http://snap.stanford.edu/data/amazon/productGraph/metadata.json.gz) (11 GB) was also included in the application.

### Populating Database

A script was used to populate a PostgreSQL database with the dataset from UCSD in order for the application to run smoothly as well as be deployable to the cloud. The steps to accomplish this are outlined below:

1. Install [Poetry](#setup) and install dependencies
2. If required, change the database provider in `schema.prisma` file. The default is PostgreSQL. However, any of the providers listed [here](https://www.prisma.io/docs/reference/database-reference/supported-databases) should work. Please note that some of the configuration options may need to be changed in the `schema.prisma` file. For example, a `GIN` index is used in the `schema.prisma` file. This is only supported by PostgreSQL. Other providers may require a different index type.
3. Set `DATABASE_URL` environment variable to the URL of the database. This can be done by either:
   1. running `export DATABASE_URL='postgres://[username]:[password]@[host]:[port]/[database]'` in the terminal
   2. adding `DATABASE_URL='postgres://[username]:[password]@[host]:[port]/[database]'` to a `.env` file
4. Run `poetry run prisma db push` to create the tables in the database and generate the Prisma client. Alternatively, you can run `poetry run prisma generate` to only generate the Prisma client without pushing the database.
5. Download the dataset from UCSD and place it in the `scripts` directory.
6. Run `poetry run python3 scripts/seed_db.py` to seed the database. This will take a while to run. The script will print out the progress as it runs.

## Group Demo Video

We created a video for how to setup this project and run our application. See this [video](https://youtu.be/2Uk9yU0pOgk).
