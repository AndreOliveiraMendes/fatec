# 🐍 Imagem base slim (leve)
FROM python:3.12-slim

# 📌 Informações de autoria
LABEL maintainer="ao_mendes@hotmail.com"

# 📂 Define diretório de trabalho
WORKDIR /app

# 📦 Copia primeiro requirements para cache de camada
COPY requirements.txt .

# ✅ Atualiza pip e instala dependências
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 📂 Copia código da aplicação
COPY app/ app/
COPY config.py ./
COPY .env ./
COPY .env.* ./

# 🌐 Expõe a porta Flask
EXPOSE 5000

# ▶️ Comando para iniciar o servidor (modo simples)
CMD ["python", "-m", "app.main"]
#CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app.main:create_app()"]
