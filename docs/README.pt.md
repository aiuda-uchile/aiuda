# ALUDA

**ALUDA** e uma plataforma com IA, implantada localmente, projetada para apoiar o trabalho academico sem substitui-lo, melhorando a acessibilidade, a inclusao e a qualidade do conteudo.

Ela fornece ferramentas para **transcrever, legendar, traduzir e analisar materiais audiovisuais e escritos**, garantindo que todos os dados sejam processados com seguranca dentro da infraestrutura institucional.

---

## ✨ Funcionalidades

- 🎧 **Processamento de Audio e Video**

  - Transcricao e legendagem automaticas
  - Traducao de conteudo multimidia
- 📄 **Analise de Documentos e Apresentacoes**

  - Detecta problemas de legibilidade (por exemplo, tamanhos de fonte pequenos, texto muito longo)
  - Identifica problemas de acessibilidade (por exemplo, contraste de cores para pessoas daltonicas)
  - Destaca problemas basicos de escrita e sugere melhorias
- 🔒 **Foco em Privacidade**

  - Todo o processamento acontece localmente em servidores institucionais
  - Nenhum dado e enviado para plataformas comerciais externas
- ♿ **Acessibilidade e Inclusao**

  - Projetada para apoiar diversas necessidades de aprendizagem
  - Ajuda a criar materiais academicos mais inclusivos
- 🧩 **Aberta e Replicavel**

  - Construida com ferramentas e modelos de codigo aberto
  - Pode ser implantada em universidades, faculdades ou centros de pesquisa
  - Utilizavel por usuarios nao especialistas

---

## 🏗️ Arquitetura

- **Backend:** FastAPI
- **Frontend:** React (Vite)
- **Implantacao:** Docker

---

## 🐳 Instalacao do Docker

### Windows

1. Baixe o Docker Desktop: [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Execute o instalador e habilite o WSL 2 (recomendado)
3. Reinicie o computador
4. Verifique a instalacao:

```bash
docker --version
docker compose version
```

---

### Linux (Ubuntu/Debian)

1. Adicione o repositorio do Docker:

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

2. Edite o `.env` e configure as variaveis obrigatorias:

```bash
ALUDA_SMTP_PASSWORD=sua_senha_aqui
```

3. Inicie a aplicacao:

```bash
docker compose up --build
```

---

## 🌐 Servicos Disponiveis

- Saude do backend: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- Documentacao da API: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Frontend: [http://localhost:5173](http://127.0.0.1:8000/docs)

---

## 🛑 Parando a Aplicacao

```bash
docker compose down
```

---

## 📁 Estrutura do Projeto

```
src/
  backend/
    aluda_backend_fastapi.py	# API principal
    scripts/			# Logica de processamento
  frontend/			# Aplicacao React
jobs/				# Dados e saidas de tarefas
logs/				# Logs por tarefa
```

---

## ⚡ Comandos Rapidos

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
