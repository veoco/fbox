FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN rm -rf www \
    && mkdir -p www \
    && wget https://github.com/veoco/dbox/releases/latest/download/dbox.tar.gz -O www/dbox.tar.gz \
    && tar -xf www/dbox.tar.gz -C www \
    && rm www/dbox.tar.gz

EXPOSE 8000
ENTRYPOINT ["uvicorn", "fbox.main:app", "--host", "0.0.0.0"]