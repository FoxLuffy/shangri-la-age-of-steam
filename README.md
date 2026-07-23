# Shangri-la: Age of Steam

A text-driven RPG powered by vLLM backends.

## Architecture & Key Features
This project uses a modern, production-ready architecture designed for low-latency, persistent AI narrative interactions:

- **vLLM Integration:** The backend leverages vLLM for high-throughput, scalable inference, enabling the system to handle multiple concurrent NPC interactions efficiently.
- **Persistent NPC Memories:** A new persistent memory system allows NPCs to retain information across sessions. Each NPC has a unique set of "memories" stored in a database, updated dynamically based on player interactions.
- **State-Aware Environment:** The world state is managed as a core JSON schema, synchronized across the backend and frontend to ensure a consistent narrative experience.
- **Real-time React Frontend:** A responsive terminal-style UI built with React and Vite, optimized for low-latency interaction with the AI backend.

- **Global Asynchronous World:** The backend synchronizes a global ledger and resource market, simulating an evolving world shaped by players.
- **Account & Session Management:** Integrated login authentication with a Session Control Plane supporting Solo and Synchronous Multiplayer lobbies.

## Tech Stack
- **Backend:** Python, FastAPI, vLLM, SQLite
- **Frontend:** React, Vite, Tailwind CSS

## Building and Running locally

### Building Docker Images
Build commands must be executed from the root repository directory (`.`):

- **Frontend Image:**
  ```bash
  docker build -t shangri-la-frontend:latest -f Dockerfile.frontend .
  ```
- **Backend Image:**
  ```bash
  docker build -t shangri-la-backend:latest -f Dockerfile.backend .
  ```

### Running with Docker Compose
```bash
docker-compose up --build
```

## Deployment (TrueNAS SCALE)

To deploy this project on TrueNAS SCALE as a Custom App, create a `dataset` for your config and use the following structure in the "Deployment Configuration":

### Environment Variables
| Name | Value |
| :---|---|
| `BACKEND_PORT` | `8003` |
| `FRONTEND_PORT` | `5173` |
| `VITE_BACKEND_URL` | *(Optional)* The full URL to your API backend (e.g., `https://api.yourdomain.com`). If not set, the frontend auto-routes based on the browser URL. |
| `SAOS_ADMIN_SECRET` | *(Optional)* The secret code to grant admin access on registration. |

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
      - "8003:8003"
    environment:
      - BACKEND_PORT=8003
      - VLLM_API_KEY=${VLLM_API_KEY}
      - SAOS_ADMIN_SECRET=${SAOS_ADMIN_SECRET}
    volumes:
      - /mnt/tank/saos_data:/data

  frontend:
    image: ghcr.io/<your-github-username>/shangri-la-frontend:latest
    container_name: shangri-la-frontend
    restart: unless-stopped
    ports:
      - "5173:80"
    environment:
      - FRONTEND_PORT=5173
      - VLLM_SERVER_URL=http://<YOUR_TRUENAS_HOST_IP>:<VLLM_PORT>
      - VITE_BACKEND_URL=https://api.yourdomain.com  # Set your custom domain here!
    volumes:
      - /mnt/tank/saos_data:/data
```

*Note: Ensure your vLLM server is accessible to these containers. You may need to use the host's local IP address in the frontend configuration.*

## Administrator Panel

This project includes a dedicated **Administrator Panel** to manage the server. The panel allows admins to:
- View all registered players (Callsigns).
- Delete (terminate) malicious or rule-breaking users.
- Inspect the narrative AI logs to monitor prompts for abuse.

**How to get Admin Access:**
1. Set the `SAOS_ADMIN_SECRET` environment variable in your backend deployment.
2. During account registration in the frontend UI, enter that exact secret into the "Admin Override Code" field.
3. Once logged in, an "Admin Panel" button will appear in the top-right corner of the interface.

## AI Integration & Roadmapping

The project supports centralized community roadmapping. When users submit Bug Reports or Feature Requests in the app, they are stored locally in the database.

- **Admin Export:** Within the Admin Panel, an "Export AI Roadmap" button triggers the `/admin/reports/export_roadmap` endpoint, which uses vLLM to read all reports and dynamically compile a prioritized markdown roadmap.
- **AI Tooling (`fetch_input` Skill):** The backend exposes `GET /admin/reports/fetch_and_clear` to allow AI agents (like Antigravity) to fetch and wipe all reports. The built-in `fetch_input` skill instructs the AI to log in, consume this data, and suggest tasks for implementation.

## CI/CD (GitHub Actions)
The following workflow provides a manual trigger to build and publish the artifacts.

`.github/workflows/publish.yml`
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

## Project Structure

```
├── Dockerfile.backend
├── Dockerfile.frontend
├── README.md
├── backend/
│   ├── client.py
│   ├── database.py
│   ├── database_init.py
│   ├── engine.py
│   ├── entrypoint.sh
│   ├── main.py
│   ├── models.py
│   ├── prompt_utils.py
│   ├── repository.py
│   ├── requirements.txt
│   └── tests/
├── docker-compose.yml
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── postcss.config.js
│   ├── public/
│   ├── src/
│   │   ├── App.css
│   │   ├── App.tsx
│   │   ├── api.ts
│   │   ├── components/
│   │   │   └── ChatInterface.tsx
│   │   ├── index.css
│   │   └── main.tsx
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
└── saos.db
```

## Project Status
- [x] Phase 1: Narrative-Driven Tactical Combat ⚔️
- [x] Phase 2: Industrialist Empire & City Management 🏭
- [x] Phase 3: The Asynchronous Shared World 🌐
- [x] Phase 4: Synchronous Multiplayer Sessions & Accounts 👥
- [ ] Phase 5: Community Modding Ecosystem 🛠️

Status: Multiplayer Session Control Plane & Accounts Integrated.
