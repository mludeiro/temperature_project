# Project Assignment: FastAPI + SQLModel + Pandas + Celery ETL API

## Objective

Build a small but complete Python backend application that demonstrates:

-   Loading an external CSV dataset
-   Triggering a background processing workflow using Celery
-   Performing data transformation using Pandas (including aggregations)
-   Storing processed data into a relational DB (Postgres) relational database using
    SQLModel
-   Exposing the processed data through an asynchronous FastAPI API
-   Ensuring high code quality and modern tooling: uv, ruff, mypy
-   Packaging the project in a clean repository with a professional
    structure

## Dataset

You will use the public global temperature dataset:

📄 **GlobalLandTemperaturesByCity.csv**\
Source:
https://www.kaggle.com/datasets/berkeleyearth/climate-change-earth-surface-temperature-data



## Project Overview

You will implement a small pipeline and API:

       +-----------------+          +-------------+         +---------------+         +----------------+
       | FastAPI Upload  | -------> | Local File  | ----->  | Celery Worker | ----->  | Postgres (DB)  |
       +-----------------+          +-------------+         +---------------+         +----------------+
                                                                       |
                                                                   uses Pandas

1.  FastAPI exposes a POST endpoint to trigger the ETL process. This
    will enqueue a Celery task.\
2.  Celery loads the dataset with Pandas, performs data cleaning and
    aggregation, and saves final data into Postgres via SQLModel.\
3.  FastAPI exposes GET endpoints to read the processed results.

## Detailed Requirements

### 1. Project Structure

Use a clean and professional layout:

    project/
    │── data/
    │     └── <USER UPLOADED CSV FILES...>
    │── app/
    │     ├── main.py
    │     ├── db.py
    │     ├── models.py
    │     ├── celery_app.py
    │     ├── tasks.py
    │     └── routers/
    │           └── weather.py
    │── requirements.txt (optional if using uv)
    │── pyproject.toml
    │── README.md

### 2. Tools & Quality Requirements

Your project must use:

#### ✔ uv

For installation and execution.\
Your README should include how to run FastAPI, Celery, and the worker.

#### ✔ ruff

-   Enforce linting\
-   Enforce formatting (`ruff format`)

#### ✔ mypy

-   Use type annotations
-   mypy should pass successfully

#### ✔ Celery

-   Use Redis or RabbitMQ (Redis recommended)
-   Implement a worker that runs the ETL transformation asynchronously

#### ✔ Pandas

Required for:
- Loading CSV
- Cleaning rows
- Extracting temperature statistics
- Grouping and aggregations

#### ✔ SQLModel

-   Store transformed data
-   Use async engine

#### ✔ FastAPI

-   Async endpoints
-   One POST to trigger ETL
-   One GET to query results

#### ✔ Linting and type checking automation

Provide a way to run ruff and mypy easily.

It can be a pre-commit hook, a shell script, makefile or whatever mean to run both tools with a single command.

### 3. ETL Requirements

The ETL should include:

#### Extract

-   Load the CSV file from a local filesystem directory

#### Transform (Celery task)

-   Use Pandas
-   Remove rows where temperature is null
-   Keep only records from after year 1900
-   Group records by year
-   Create new computed fields
       * Convert date to year
       * Normalize city names (e.g. strip whitespace)
-   Aggregation (mandatory)
    * Compute average temperature per city per year
    * Example Pandas operations can include for example:
        * df.dropna()
        * df.groupby([...]).agg({...})
        * reset_index()
-   Additional cleaning as needed

#### Load (Celery task)

-   Convert DataFrame rows into SQLModel objects
-   Insert them into relational DB (Postgres)

### 4. API Requirements

#### `POST /datasets`

Triggers the Celery ETL task
**Returns:**

``` json
{ "status": "enqueued", "task_id": "..." }
```

#### `GET /etl/status/{task_id}`

Query Celery for task state

Return: PENDING / STARTED / SUCCESS / FAILURE

#### `GET /temperatures?page=1&city="Buenos Aires"&year="1995"`

Returns paginated processed data.

Query parameters:
* page (optional page number, defaults to 1)
* city (optional filter)
* year (optional filter)

```json
{
    "page": 1,
    "total_pages": 1,
    "data": [
        {
            "id": 1,
            "city": "Buenos Aires",
            "year": 1995,
            "avg_temperature": 17.44
        }
    ]
}
```

#### `GET /temperatures/{id}`

Returns specific record data.

```json
{
    "id": 1,
    "city": "Buenos Aires",
    "year": 1995,
    "avg_temperature": 17.44
}
```

### 5. Database Requirements

``` python
class CityTemperature(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    city: str
    year: int
    avg_temperature: float
```

### 6. Celery Requirements

-   Celery instance
-   Redis backend
-   ETL task using Pandas + SQLModel

### 7. README Requirements

#### Run FastAPI:

``` sh
uvicorn app.main:app --reload
```

#### Run the Celery worker:

``` sh
celery -A app.celery_app.celery worker --loglevel=info
```

#### Start Redis as needed.

## Expected Outcome

-   Modern Python API
-   Async ETL pipeline
-   Pandas data transformation
-   SQLModel persistence
-   Clean, typed, linted code 
-   Professional project structure
