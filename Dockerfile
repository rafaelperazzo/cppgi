FROM python:3.10-bullseye
ENV TZ=America/Fortaleza
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update
RUN apt-get install -y build-essential g++ libmariadb-dev-compat libmariadb-dev wkhtmltopdf
COPY requirements.txt ./
RUN pip install setuptools_scm==5.0.2 --upgrade
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 80
CMD python /home/perazzo/cppgi/pesquisa.py
