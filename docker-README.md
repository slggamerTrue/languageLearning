# AI English Tutor Docker Setup

This document provides instructions for running the AI English Tutor application using Docker.

## Prerequisites

- Docker and Docker Compose installed on your system
- Git (to clone the repository)

## Getting Started

### Building and Running with Docker Compose

1. Navigate to the project root directory:

```bash
cd ai-english-tutor
```

2. Build and start the containers:

```bash
docker-compose up -d
```

This will:
- Build the Docker image for the application
- Start the application container
- Start a MongoDB container
- Set up the necessary network connections between containers

3. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:9000

### Stopping the Application

To stop the running containers:

```bash
docker-compose down
```

To stop the containers and remove the volumes (this will delete the database data):

```bash
docker-compose down -v
```

## Docker Configuration Details

The setup includes:

- **Frontend**: React application running on port 3000
- **Backend**: FastAPI application running on port 9000
- **Database**: MongoDB running on port 27017

## Environment Variables

You can customize the application by modifying the environment variables in the `docker-compose.yml` file:

- `MONGODB_URI`: MongoDB connection string
- `JWT_SECRET`: Secret key for JWT token generation

## Building the Docker Image Manually

If you want to build the Docker image manually:

```bash
docker build -t ai-english-tutor .
```

To run the container manually:

```bash
docker run -p 3000:3000 -p 9000:9000 --env MONGODB_URI=mongodb://mongo:27017 --env JWT_SECRET=your-secret-key ai-english-tutor
```

## Troubleshooting

- If you encounter connection issues with MongoDB, ensure the MongoDB container is running:
  ```bash
  docker ps
  ```

- To view logs from the application:
  ```bash
  docker-compose logs app
  ```

- To view logs from MongoDB:
  ```bash
  docker-compose logs mongo
  ```
