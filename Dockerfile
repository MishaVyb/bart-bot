FROM python:3.10-slim

LABEL author='misha.vybornyy@gmail.com'

WORKDIR /bart-bot

COPY requirements.txt .

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt --no-cache-dir

COPY . .

CMD ["python", "src/polling.py"]