FROM python:3.10

RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    xfonts-75dpi \
    xfonts-base \
    fontconfig \
    libjpeg62-turbo \
    libxrender1 \
    libxext6 \
    libssl-dev \
    libx11-6 \
    && apt-get clean

RUN ln -s /usr/bin/wkhtmltopdf /usr/local/bin/wkhtmltopdf

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
