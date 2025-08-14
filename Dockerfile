# 🐍 Imagem base slim (leve)
FROM python:3.12-slim
#FROM python:3.12-alpine

# 📂 Define diretório de trabalho
WORKDIR /app

# 📦 Copia primeiro requirements para cache de camada
COPY requirements.txt .

# ✅ Atualiza pip e instala dependências
RUN python -m pip install --root-user-action=ignore --upgrade pip && \
    pip install --root-user-action=ignore --no-cache-dir -r requirements.txt
#RUN apk add --no-cache python3-dev build-base && \
#    python3 -m pip install --no-cache-dir -r requirements.txt && \
#    apk del python3-dev build-base

# 📂 Copia código da aplicação
COPY app/ app/
COPY config/ config/
COPY wsgi.py wsgi.py

# wait for it
#COPY wait-for-it.sh app/
#RUN chmod +x app/wait-for-it.sh


# 🌐 Expõe a porta Flask
EXPOSE 5000

# ▶️ Comando para iniciar o servidor (modo simples)
#CMD ["python", "-m", "app"]
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "wsgi:app"]