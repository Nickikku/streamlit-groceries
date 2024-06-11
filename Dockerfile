FROM python:3.8
LABEL Maintainer="nico.brand@bqa.nl"

RUN mkdir /app
WORKDIR /Users/nicobrand/AanvragenMynTyd
COPY . . 
RUN apt-get update
RUN apt purge tesseract* libtesseract*
RUN apt autoremove --purge
RUN pip install -r requirements.txt

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=80", "--server.address=0.0.0.0"]

CMD ["app.py", "credentials.py", "login.py"]
