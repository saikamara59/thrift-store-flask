FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install pipenv
RUN pipenv install --system --deploy

EXPOSE 5000

CMD ["python", "app.py"]