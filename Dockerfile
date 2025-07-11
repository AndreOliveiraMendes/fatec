# 🐍 Imagem base slim (leve)
FROM python:3.12-slim
#FROM python:3.12-alpine

# 📌 Informações de autoria
LABEL maintainer="ao_mendes@hotmail.com"

# 📂 Define diretório de trabalho
WORKDIR /app

# 📦 Copia primeiro requirements para cache de camada
COPY requirements.txt .

# ✅ Atualiza pip e instala dependências
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
#RUN apk add --no-cache python3-dev build-base && \
#    python3 -m pip install --no-cache-dir -r requirements.txt && \
#    apk del python3-dev build-base

# 📂 Copia código da aplicação
COPY app/ app/
COPY config.py ./

# 🌐 Expõe a porta Flask
EXPOSE 5000

# ▶️ Comando para iniciar o servidor (modo simples)
CMD ["python", "-m", "app.main"]
#CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app.main:create_app()"]
