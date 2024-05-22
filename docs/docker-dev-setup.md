# Development Environment Setup

This document provides instructions for setting up the development environment for this project.

## Environment Variables

The application requires several environment variables to be set for proper configuration. These variables should be defined in a `.env` file in the .docker directory of this project.

### Example `.env` File

Here is an example of what your `.env` file should look like:

# Postgres configuration 
```
POSTGRES_DB=db_prod
POSTGRES_USER=postgres
POSTGRES_PASSWORD=example_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
```

# Any other environment variables your application needs
API_ENDPOINT=https://prod--gateway.elifesciences.org

- Notes: Ensure to add `.docker/.env` file you just created to `.gitignore` and `.dockerignore` file

### Health Checks

- `Postgres`: Uses `pg_isready` to ensure the database is ready.
- `App`: Uses `curl` to check if the application is running on port 8000.

### Volumes

- `db_data`: Stores `PostgreSQL` data.
- `./.docker/data`: Maps to the `/data `directory inside the Postgres container.
- `./install.sh`: Maps the install.sh script to the `/app` directory inside the app container.

#### 3rd Party credentials for local development

The service has dependencies on the following 3rd party services:  

[`crossref`](https://www.crossref.org)
[`scopus`](https://www.scopus.com/home.uri)
[`Google Analytics`](https://developers.google.com/analytics/devguides/collection/ga4)

Each of these require credentials to be set in the environment. You will need to set these up in your local environment 
in order to ingest/generate metrics data locally.

In the `.docker/app.cfg` file, you will need to set the following variables with real values:

```
[scopus]
apikey: <scopus api key>

[crossref]
user: <crossref user>
pass: <crossref pass>
```
For Google Analytics, you will need to provide a `client_secrets.json` file in the root of the project.

Example `client-secrets.json` file:
```json
{
  "private_key_id": "<private_key_id>",
  "private_key": "<private_key>",
  "client_id": "<client_id>",
  "client_email": "<client_email>",
  "type": "service_account"
}
```

#### TODO: AWS Section
...
### Running the Project

#### Build the services:
```
docker-compose build
```
#### Start the service
```
docker-compose up --wait
```
#### Access the application:

The application will be available at http://localhost:8000.

#### Stopping the services:
```
docker-compose down
```
Notes
Ensure that the install.sh script has execute permissions before running the services:


```
chmod +x install.sh
```

The Postgres service will be checked for health every 10 seconds, and the application will wait until both Postgres and Localstack are healthy before starting.

Troubleshooting
If you encounter a permission denied error for any script, make sure it has execute permissions.

Check the logs of individual services using:

```
docker-compose logs <service_name>
```
Replace <service_name> with postgres, localstack, or app as needed.

### Directory Structure
The project expects the following directory structure:
```
.
├── .docker
│   ├── .env.dev
│   └── data
├── install.sh
├── docker-compose.yml
├── requirements.txt
└── ... (other project files)
```
This setup ensures that all necessary services are properly configured and managed using Docker Compose, facilitating a smooth development and testing process.
