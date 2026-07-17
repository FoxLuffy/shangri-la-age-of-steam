# Shangri-la: Age of Steam

A text-driven RPG powered by vLLM backends.

## Project Overview
This project implements a text-driven RPG where players interact with a dynamic world. The core experience is driven by a vLLM-powered backend that handles NPC logic, environment descriptions, and state management.

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
For a production-ready deployment, it is recommended to build the images using the provided Dockerfiles or host the frontend as a static site:

**Backend Container:**
- Image: `shangri-la-backend:latest`
- Ports: `8000:8000`
- Volume: `/data`

**Frontend Container:**
- Image: `shangri-la-frontend:latest`
- Ports: `5173:5173`
- Volume: `/data`

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
