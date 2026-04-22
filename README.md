# AIUDA

**AIUDA** is a locally deployed AI-powered platform designed to support academic work, without replacing it, by improving accessibility, inclusivity, and content quality.

It provides tools to **transcribe, subtitle, translate, and analyze audiovisual and written materials**, while ensuring that all data is processed securely within institutional infrastructure.

## 🌍 Languages

- English: [README.md](README.md)
- Español: [docs/README.es.md](docs/README.es.md)
- Português: [docs/README.pt.md](docs/README.pt.md)
- Galego: [docs/README.gl.md](docs/README.gl.md)

---

## ✨ Features

- 🎧 **Audio & Video Processing**

  - Automatic transcription and subtitling
  - Translation of multimedia content
- 📄 **Document & Presentation Analysis**

  - Detects readability issues (e.g., small font sizes, overly long text)
  - Identifies accessibility problems (e.g., color contrast for colorblind users)
  - Highlights basic writing issues and suggests improvements
- 🔒 **Privacy-Focused**

  - All processing happens locally on institutional servers
  - No data is sent to external commercial platforms
- ♿ **Accessibility & Inclusion**

  - Designed to support diverse learning needs
  - Helps create more inclusive academic materials
- 🧩 **Open & Replicable**

  - Built with open-source tools and models
  - Can be deployed in universities, faculties, or research centers
  - Usable by non-expert users

---

## 🏗️ Architecture

- **Backend:** FastAPI
- **Frontend:** React (Vite)
- **Deployment:** Docker

---

## 🐳 Docker Installation

### Windows

1. Download Docker Desktop: [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Run the installer and enable WSL 2 (recommended)
3. Restart your computer
4. Verify installation:

```bash
docker --version
docker compose version
```

---

### Linux (Ubuntu/Debian)

1. Add Docker repository:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

2. Install Docker:

```bash
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

sudo usermod -aG docker $USER
newgrp docker
```

3. Verify:

```bash
docker --version
docker compose version
```

---

### macOS

1. Download Docker Desktop: [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Install and launch Docker
3. Verify:

```bash
docker --version
docker compose version
```

---

## ⚙️ Requirements

- Docker Desktop **or** Docker Engine + Docker Compose plugin

---

## 🚀 Running the Project

From the project root:

1. Create environment file:

```bash
cp .env.example .env
```

2. Edit `.env` and configure required variables:

```bash
AIUDA_SMTP_PASSWORD=your_password_here
```

3. Start the application:

```bash
docker compose up --build
```

---

## 🌐 Available Services

- Backend health: [http://127.0.0.1:8010/api/health](http://127.0.0.1:8010/api/health)
- API docs: [http://127.0.0.1:8010/docs](http://127.0.0.1:8010/docs)
- Frontend: [http://localhost:5173](http://localhost:5173)

---

## 🛑 Stopping the Application

```bash
docker compose down
```

---

## 📁 Project Structure

```
src/
  backend/
    aiuda_backend_fastapi.py	# Main API
    scripts/			# Processing logic
  frontend/			# React App
jobs/				# Task data & Outputs
logs/				# Logs per task
```

---

## ⚡ Quick Commands

```bash
# Build and start
docker compose up --build

# Stop
docker compose down

# Backend logs
docker compose logs -f backend

# Frontend logs
docker compose logs -f frontend
```
