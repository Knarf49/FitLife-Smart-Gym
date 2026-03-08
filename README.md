## Getting Started (Docker)

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed

### Steps

1. **Extract the zip file** and open a terminal in the project folder

   ```bash
   cd FitLife-Smart-Gym

   ```

2. **Build the Docker image**

   ```bash
   docker build -t fitlife .

   ```

3. **Run the container**

   ```bash
   docker run -p 8000:8000 fitlife

   ```

4. **Open the API docs in your browser**
   ```bash
   http://localhost:8000/docs
   ```
