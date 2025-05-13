FROM python:3.12 AS base
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN mkdir /code
WORKDIR /code


FROM base AS dependency
RUN pip3 install --no-cache-dir fastapi==0.103.1
RUN pip3 install --no-cache-dir uvicorn==0.23.2
RUN pip3 install --no-cache-dir jinja2==3.1.2
RUN pip3 install --no-cache-dir python-multipart==0.0.6
RUN pip3 install --no-cache-dir python-dotenv==1.0.0 
RUN pip3 install --no-cache-dir aiohttp
RUN pip3 install --no-cache-dir joblib
RUN pip3 install --no-cache-dir pandas
RUN pip3 install --no-cache-dir catboost
RUN pip3 install --no-cache-dir xgboost
RUN pip3 install --no-cache-dir scikit-learn

FROM dependency
COPY app/ .

EXPOSE 8000
ENTRYPOINT [ "python",  "main.py" ]