# AIUDA

**AIUDA** é unha plataforma impulsada por IA, despregada localmente, deseñada para apoiar o traballo académico sen substituilo, mellorando a accesibilidade, a inclusión e a calidade do contido.

Ofrece ferramentas para **transcribir, subtitular, traducir e analizar materiais audiovisuais e escritos**, garantindo que todos os datos se procesen de forma segura dentro da infraestrutura institucional.

---

## ✨ Funcionalidades

- 🎧 **Procesamento de Audio e Video**

  - Transcrición e subtitulado automáticos
  - Traducióon de contido multimedia
- 📄 **Análise de Documentos e Presentacións**

  - Detecta problemas de lexibilidade (por exemplo, tamaños de letra pequenos, texto demasiado longo)
  - Identifica problemas de accesibilidade (por exemplo, contraste de cor para persoas daltónicas)
  - Sinala problemas básicos de redacción e suxire melloras
- 🔒 **Enfoque na Privacidade**

  - Todo o procesamento ocorre localmente en servidores institucionais
  - Non se envian datos a plataformas comerciais externas
- ♿ **Accesibilidade e Inclusión**

  - Deseñada para apoiar diversas necesidades de aprendizaxe
  - Axuda a crear materiais académicos méis inclusivos
- 🧩 **Aberta e Replicable**

  - Construida con ferramentas e modelos de código aberto
  - Pode despregarse en universidades, facultades ou centros de investigación
  - Utilizable por persoas non expertas

---

## 🏗️ Arquitectura

- **Backend:** FastAPI
- **Frontend:** React (Vite)
- **Despregamento:** Docker

---

## 🐳 Instalación de Docker

### Windows

1. Descarga Docker Desktop: [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Executa o instalador e habilita WSL 2 (recomendado)
3. Reinicia o equipo
4. Verifica a instalación:

```bash
docker --version
docker compose version
```

---

### Linux (Ubuntu/Debian)

1. Engade o repositorio de Docker:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

2. Instala Docker:

```bash
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

sudo usermod -aG docker $USER
newgrp docker
```

3. Verifica:

```bash
docker --version
docker compose version
```

---

### macOS

1. Descarga Docker Desktop: [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Instala e inicia Docker
3. Verifica:

```bash
docker --version
docker compose version
```

---

## ⚙️ Requisitos

- Docker Desktop **ou** Docker Engine + plugin de Docker Compose

---

## 🚀 Execución do Proxecto

Dende a raíz do proxecto:

1. Crea o ficheiro de entorno:

```bash
cp .env.example .env
```

2. Edita `.env` e configura as variables requiridas:

```bash
AIUDA_SMTP_PASSWORD=o_teu_contrasinal_aqui
```

3. Inicia a aplicación:

```bash
docker compose up --build
```

---

## 🌐 Servizos Dispoñibles

- Estado do backend: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- Documentacion da API: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Frontend: [http://localhost:5173](http://127.0.0.1:8000/docs)

---

## 🛑 Deter a Aplicación

```bash
docker compose down
```

---

## 📁 Estrutura do Proxecto

```
src/
  backend/
    aiuda_backend_fastapi.py	# API principal
    scripts/			# Lóxica de procesamento
  frontend/			# Aplicación React
jobs/				# Datos e saídas de tarefas
logs/				# Rexistros por tarefa
```

---

## ⚡ Comandos Rápidos

```bash
# Construir e iniciar
docker compose up --build

# Deter
docker compose down

# Logs do backend
docker compose logs -f backend

# Logs do frontend
docker compose logs -f frontend
```
