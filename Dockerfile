FROM python:3.12.3

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY .env .

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "main.py"]