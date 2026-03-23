# 🐍 Imagem base slim (leve)
FROM python:3.12-slim

# 📂 Define diretório de trabalho
WORKDIR /app

# 🔧 Instala git
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && echo "172.16.0.200 academico.fatecourinhos.edu.br" >> /etc/hosts

# 📦 Copia primeiro requirements para cache de camada
COPY requirements.txt .

# ✅ Atualiza pip e instala dependências
RUN python -m pip install --root-user-action=ignore --no-cache-dir --upgrade pip && \
    pip install --root-user-action=ignore --no-cache-dir -r requirements.txt

# 🌐 Expõe a porta Flask
EXPOSE 5000

# ▶️ Comando para iniciar o servidor (modo local/wsgi)
#CMD ["python", "-m", "app"]
#CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "wsgi:app"]
