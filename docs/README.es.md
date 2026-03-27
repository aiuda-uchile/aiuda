# ALUDA

**ALUDA** es una plataforma impulsada por IA, desplegada localmente, diseñada para apoyar el trabajo académico sin reemplazarlo, mejorando la accesibilidad, la inclusión y la calidad del contenido.

Proporciona herramientas para **transcribir, subtitular, traducir y analizar materiales audiovisuales y escritos**, garantizando que todos los datos se procesen de forma segura dentro de la infraestructura institucional.

---

## ✨ Funcionalidades

- 🎧 **Procesamiento de Audio y Video**

  - Transcripción y subtitulado automáticos
  - Traducción de contenido multimedia
- 📄 **Análisis de Documentos y Presentaciones**

  - Detecta problemas de legibilidad (p. ej., tamaños de fuente pequeños, texto demasiado largo)
  - Identifica problemas de accesibilidad (p. ej., contraste de color para personas daltónicas)
  - Señala problemas básicos de escritura y sugiere mejoras
- 🔒 **Enfoque en la Privacidad**

  - Todo el procesamiento ocurre localmente en servidores institucionales
  - No se envían datos a plataformas comerciales externas
- ♿ **Accesibilidad e Inclusión**

  - Diseñado para apoyar diversas necesidades de aprendizaje
  - Ayuda a crear materiales académicos más inclusivos
- 🧩 **Abierto y Replicable**

  - Construido con herramientas y modelos de código abierto
  - Puede desplegarse en universidades, facultades o centros de investigación
  - Utilizable por usuarios no expertos

---

## 🏗️ Arquitectura

- **Backend:** FastAPI
- **Frontend:** React (Vite)
- **Despliegue:** Docker

---

## 🐳 Instalación de Docker

### Windows

1. Descarga Docker Desktop: [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Ejecuta el instalador y habilita WSL 2 (recomendado)
3. Reinicia tu equipo
4. Verifica la instalación:

```bash
docker --version
docker compose version
```

---

### Linux (Ubuntu/Debian)

1. Añade el repositorio de Docker:

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
2. Instala y abre Docker
3. Verifica:

```bash
docker --version
docker compose version
```

---

## ⚙️ Requisitos

- Docker Desktop **o** Docker Engine + plugin de Docker Compose

---

## 🚀 Ejecución del Proyecto

Desde la raíz del proyecto:

1. Crea el archivo de entorno:

```bash
cp .env.example .env
```

2. Edita `.env` y configura las variables requeridas:

```bash
ALUDA_SMTP_PASSWORD=tu_contrasena_aqui
```

3. Inicia la aplicación:

```bash
docker compose up --build
```

---

## 🌐 Servicios Disponibles

- Salud del backend: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- Documentación API: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Frontend: [http://localhost:5173](http://127.0.0.1:8000/docs)

---

## 🛑 Detener la Aplicación

```bash
docker compose down
```

---

## 📁 Estructura del Proyecto

```
src/
  backend/
    aluda_backend_fastapi.py	# API principal
    scripts/			# Lógica de procesamiento
  frontend/			# Aplicación React
jobs/				# Datos y salidas de tareas
logs/				# Registros por tarea
```

---

## ⚡ Comandos Rápidos

```bash
# Construir e iniciar
docker compose up --build

# Detener
docker compose down

# Logs del backend
docker compose logs -f backend

# Logs del frontend
docker compose logs -f frontend
```
