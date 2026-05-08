# AIUDA

**AIUDA** é uma plataforma com IA, implantada localmente, projetada para apoiar o trabalho acadêmico sem substituí-lo, melhorando a acessibilidade, a inclusão e a qualidade do conteúdo.

Ela fornece ferramentas para **transcrever, legendar, traduzir e analisar materiais audiovisuais e escritos**, garantindo que todos os dados sejam processados com segurança dentro da infraestrutura institucional.

---

## ✨ Funcionalidades

- 🎧 **Processamento de Áudio e Vídeo**

  - Transcrição e legendagem automáticas
  - Tradução de conteúdo multimídia
- 📄 **Análise de Documentos e Apresentações**

  - Detecta problemas de legibilidade (por exemplo, tamanhos de fonte pequenos, texto muito longo)
  - Identifica problemas de acessibilidade (por exemplo, contraste de cores para pessoas daltônicas)
  - Destaca problemas básicos de escrita e sugere melhorias
- 🔒 **Foco em Privacidade**

  - Todo o processamento acontece localmente em servidores institucionais
  - Nenhum dado e enviado para plataformas comerciais externas
- ♿ **Acessibilidade e Inclusão**

  - Projetada para apoiar diversas necessidades de aprendizagem
  - Ajuda a criar materiais acadêmicos mais inclusivos
- 🧩 **Aberta e Replicável**

  - Construída com ferramentas e modelos de código aberto
  - Pode ser implantada em universidades, faculdades ou centros de pesquisa
  - Utilizável por usuários não especialistas

---

## 🏗️ Arquitetura

- **Backend:** FastAPI
- **Frontend:** React (Vite)
- **Implantação:** Docker

---

## 🐳 Instalação do Docker

### Windows

1. Baixe o Docker Desktop: [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Execute o instalador e habilite o WSL 2 (recomendado)
3. Reinicie o computador
4. Verifique a instalação:

```bash
docker --version
docker compose version
```

---

### Linux (Ubuntu/Debian)

1. Adicione o repositório do Docker:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

2. Instale o Docker:

```bash
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

sudo usermod -aG docker $USER
newgrp docker
```

3. Verifique:

```bash
docker --version
docker compose version
```

---

### macOS

1. Baixe o Docker Desktop: [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Instale e inicie o Docker
3. Verifique:

```bash
docker --version
docker compose version
```

---

## ⚙️ Requisitos

- Docker Desktop **ou** Docker Engine + plugin Docker Compose

---

## 🚀 Executando o Projeto

Na raiz do projeto:

1. Crie o arquivo de ambiente:

```bash
cp .env.example .env
```

2. Edite o `.env` e configure as variáveis obrigatórias:

```bash
AIUDA_SMTP_PASSWORD=sua_senha_aqui
```

3. Inicie a aplicação:

```bash
docker compose up --build
```

---

## 🌐 Serviços Disponíveis

- Saude do backend: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- Documentacao da API: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Frontend: [http://localhost:5173](http://127.0.0.1:8000/docs)

---

## 🛑 Parando a Aplicação

```bash
docker compose down
```

---

## 📁 Estrutura do Projeto

```
src/
  backend/
    aiuda_backend_fastapi.py	# API principal
    scripts/			# Lógica de processamento
  frontend/			# Aplicação React
jobs/				# Dados e saídas de tarefas
logs/				# Logs por tarefa
```

---

## ⚡ Comandos Rápidos

```bash
# Build e start
docker compose up --build

# Stop
docker compose down

# Logs do backend
docker compose logs -f backend

# Logs do frontend
docker compose logs -f frontend
```
