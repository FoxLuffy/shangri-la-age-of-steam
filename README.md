# Shangri-la: Age of Steam

A text-driven RPG powered by vLLM backends.

## Architecture & Key Features
This project uses a modern, production-ready architecture designed for low-latency, persistent AI narrative interactions:

- **vLLM Integration:** The backend leverages vLLM for high-throughput, scalable inference, enabling the system to handle multiple concurrent NPC interactions efficiently.
- **Persistent NPC Memories:** A new persistent memory system allows NPCs to retain information across sessions. Each NPC has a unique set of "memories" stored in a database, updated dynamically based on player interactions.
- **State-Aware Environment:** The world state is managed as a core JSON schema, synchronized across the backend and frontend to ensure a consistent narrative experience.
- **Real-time React Frontend:** A responsive terminal-style UI built with React and Vite, optimized for low-latency interaction with the AI backend.

## Tech Stack
- **Backend:** Python, FastAPI, vLLM
- **Frontend:** React, Vite, Tailwind CSS
- **Data:** JSON/SQLite for world state

## Deployment (TrueNAS SCALE)

To deploy this project on TrueNAS SCALE as a Custom App, create a `dataset` for your config and use the following structure in the "Deployment Configuration":

### Environment Variables
| Name | Value |
| :---32|---|
| `BACKEND_PORT` | `8000` |
| `FRONTEND_PORT` | `5173` |

### Storage (Host Path)
| Name | Host Path | Mount Path |
| :---|---|---|
| `saos_data` | `/mnt/tank/saos_data` | `/data` |

### Dockerfile / Image Configuration
For a production-ready deployment, use the following `docker-compose.yml` configuration:

```yaml
version: "3.8"

services:
  backend:
    image: ghcr.io/<your-github-username>/shangri-la-backend:latest
    container_name: shangri-la-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - BACKEND_PORT=8000
      - VLLM_API_KEY=${VLLM_API_KEY}
    volumes:
      - /mnt/tank/saos_data:/data

  frontend:
    image: ghcr.io/<your-github-username>/shangri-la-frontend:latest
    container_name: shangri-la-frontend
    restart: unless-stopped
    ports:
      - "5173:5173"
    environment:
      - FRONTEND_PORT=5173
      - VLLM_SERVER_URL=http://<YOUR_TRUENAS_HOST_IP>:<VLLM_PORT>
    volumes:
      - /mnt/tank/saos_data:/data
```

*Note: Ensure your vLLM server is accessible to these containers. You may need to use the host's local IP address in the frontend configuration.*

## CI/CD (GitHub Actions)
The following workflow provides a manual trigger to build and publish the artifacts.

.github/workflows/publish.yml
```yaml
name: Publish Artifacts

on:
  workflow_dispatch:
    description: "Publish project artifacts"

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install Dependencies
        run: |
          python -m venv .venv
          source .venv/bin/activate
          pip install -r backend/requirements.txt

      - name: Build Backend Docker Image
        run: |
          docker build -t shangri-la-backend:latest -f Dockerfile.backend .

      - name: Build Frontend Docker Image
        run: |
          docker build -t shangri-la-frontend:latest -f Dockerfile.frontend .

      - name: Push to Registry
        # Replace with your actual registry credentials
        run: |
          echo "${{ secrets.REGISTRY_PASSWORD }}" | docker login -u ${{ secrets.REGISTRY_USERNAME }} --password-stdin
          docker push shangri-la-backend:latest
          docker push shangri-la-frontend:latest
```
--- Project Structure Complete ---

## Project Status
- [x] Phase 1: Foundation & Core API
- [x] Phase 2: Frontend Shell
- [x] Phase 3: AI Narrative Logic
- [x] Phase 4: Polish & Deployment (Initial)

Status: Core foundations complete.
