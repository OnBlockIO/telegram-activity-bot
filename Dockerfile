FROM python:3.8

RUN apt-get update

RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

COPY requirements.txt .
COPY gm_bot.py .

RUN pip install -r requirements.txt

CMD python gm_bot.py
