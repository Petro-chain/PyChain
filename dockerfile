# Use a imagem base oficial do Python
FROM python:3.9-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de requisitos para o container
COPY requirements.txt .

# Instala as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Copia todos os arquivos do projeto para o diretório de trabalho
COPY . .

# Define a porta padrão para o Flask
ENV FLASK_APP app.py
ENV PYTHONUNBUFFERED 1

# Comando para aceitar argumentos dinamicamente
ENTRYPOINT ["python", "app.py"]
