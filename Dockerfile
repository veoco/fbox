FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN rm -rf www \
    && mkdir -p www \
    && tar -xf dbox.tar.gz -C www \
    && rm dbox.tar.gz

EXPOSE 8000
ENTRYPOINT ["uvicorn", "fbox.main:app", "--host", "0.0.0.0"]