FROM python:3.9


COPY ./BIA_api/requirements.txt /BIA_api/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /BIA_api/requirements.txt

RUN apt-get update && apt-get -y install python3-pandas
RUN apt-get update && apt-get -y install python3-numpy



COPY BIA_api/app /BIA_api/app
COPY BIA_api/model /BIA_api/model

RUN mkdir /BIA_api/savedRequests

COPY /BIA_api/defaultModel.json /BIA_api/savedRequests

COPY BIA_gui /BIA_gui

COPY docker_start.sh docker_start.sh
RUN chmod +x docker_start.sh



EXPOSE 80
EXPOSE 8000

CMD ./docker_start.sh
