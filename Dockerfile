# 🐍 Imagem base slim (leve)
FROM python:3.12-slim

# 📂 Define diretório de trabalho
WORKDIR /app

# 🔧 Instala git
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# 📦 Copia primeiro requirements para cache de camada
COPY requirements.txt .

# ✅ Atualiza pip e instala dependências
RUN python -m pip install --root-user-action=ignore --no-cache-dir --upgrade pip && \
    pip install --root-user-action=ignore --no-cache-dir -r requirements.txt

# 🌐 Expõe a porta Flask
EXPOSE 5000

# 📂 Copia a aplicação
COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]