# Development Environment Setup

This document provides instructions for setting up the development environment for this project.


### Health Checks

- `Postgres`: Uses `pg_isready` to ensure the database is ready.
- `App`: Uses `curl` to check if the application is running on port 8000.

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
│   ├
│   └── app.cfg
├── install.sh
├── dockerfile & docker-compose.yml
├── requirements.txt
└── ... (other project files)
```
This setup ensures that all necessary services are properly configured and managed using Docker Compose, facilitating a smooth development and testing process.
