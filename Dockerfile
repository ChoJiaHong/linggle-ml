FROM python:3.8 as fastapi-ml-base

WORKDIR /

RUN apt-get update && \
    apt-get install -y vim 

COPY ./requirements.txt /requirements.txt

RUN pip install --no-cache-dir --upgrade -r /requirements.txt
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y

RUN python -m nltk.downloader punkt
# Add .cargo/bin to PATH
ENV PATH="/root/.cargo/bin:${PATH}"




FROM fastapi-ml-base
WORKDIR /
COPY ./geclec_project-ml /geclec_project-ml

EXPOSE 80
CMD ["uvicorn", "geclec_project-ml.main:app", "--host", "0.0.0.0", "--port", "80"]


