FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
WORKDIR /opt/aeris
RUN groupadd --gid 10001 aeris && useradd --uid 10001 --gid 10001 --create-home aeris
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY --chown=aeris:aeris app.py VERSION LICENSE ./
COPY --chown=aeris:aeris src/ src/
COPY --chown=aeris:aeris research/ research/
COPY --chown=aeris:aeris .streamlit/ .streamlit/
RUN mkdir -p data && chown aeris:aeris data
USER aeris
EXPOSE 8501 8080
CMD ["python","-m","streamlit","run","app.py","--server.address=0.0.0.0","--server.headless=true"]
