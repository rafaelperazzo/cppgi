FROM python:2
ENV TZ=America/Fortaleza
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update
#RUN apt-get install -y python python-pip python-dev build-essential g++ python-bs4 python-soupsieve libmariadbclient-dev libmariadb-dev-compat libmariadb-dev wkhtmltopdf
RUN apt-get install -y build-essential g++ libmariadbclient-dev libmariadb-dev-compat libmariadb-dev wkhtmltopdf
RUN pip install unidecode==1.1.1
RUN pip install numpy pandas sympy matplotlib werkzeug==0.16.1 Flask lxml mysqlclient requests Flask-HTTPAuth Flask-Mail Flask-Uploads pdfkit waitress
RUN pip install ezodf
RUN pip install opencv-python==4.2.0.32
RUN pip install Pillow
RUN pip install Flask-WTF
RUN pip install bs4
#RUN apt-get install -y curl unoconv
EXPOSE 80
CMD python /home/perazzo/cppgi/pesquisa.py
