# 🐍 Imagem base slim (leve)
FROM python:3.12-slim

# 📂 Define diretório de trabalho
WORKDIR /app

# 📦 Copia primeiro requirements para cache de camada
COPY requirements.txt .

# ✅ Atualiza pip e instala dependências
RUN python -m pip install --root-user-action=ignore --upgrade pip && \
    pip install --root-user-action=ignore --no-cache-dir -r requirements.txt

# 📂 Copia código da aplicação
#COPY app/ app/
#COPY config/ config/
#COPY data/ data/
#COPY logs/ logs/
#COPY wsgi.py wsgi.py

# 🌐 Expõe a porta Flask
EXPOSE 5000

# ▶️ Comando para iniciar o servidor (modo local/wsgi)
#CMD ["python", "-m", "app"]
#CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "wsgi:app"]
