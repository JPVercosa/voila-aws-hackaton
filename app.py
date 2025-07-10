import streamlit as st
import boto3
import os
from dotenv import load_dotenv

# Para vetores
import faiss
import numpy as np

# ====== Carregar variáveis de ambiente ======
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION, S3_BUCKET_NAME]):
    st.error("Por favor, configure suas variáveis de ambiente no arquivo .env.")
    st.stop()

# ====== Inicializar cliente S3 ======
s3_client = boto3.client(
    's3',
    region_name=AWS_DEFAULT_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# ====== Função para salvar índice FAISS no S3 ======
def save_index_to_s3(index, s3_key):
    faiss.write_index(index, "temp.index")
    s3_client.upload_file("temp.index", S3_BUCKET_NAME, s3_key)
    os.remove("temp.index")

# ====== Função para carregar índice FAISS do S3 ======
def load_index_from_s3(s3_key):
    s3_client.download_file(S3_BUCKET_NAME, s3_key, "temp.index")
    index = faiss.read_index("temp.index")
    os.remove("temp.index")
    return index

# ====== Streamlit App ======
st.title("Hackathon Vetor DB + S3")

option = st.selectbox("O que você quer fazer?", ["Criar índice", "Consultar índice"])

if option == "Criar índice":
    uploaded_files = st.file_uploader("Envie arquivos de texto", accept_multiple_files=True)
    if st.button("Criar índice"):
        vectors = []
        for file in uploaded_files:
            # content = file.read().decode("utf-8")
            # Cria vetores dummy: cada documento vira um vetor aleatório (só exemplo)
            vector = np.random.rand(512).astype('float32')
            vectors.append(vector)

        xb = np.vstack(vectors)
        index = faiss.IndexFlatL2(512)
        index.add(xb)

        save_index_to_s3(index, "vector.index")
        st.success("Índice criado e salvo no S3!")

elif option == "Consultar índice":
    query = st.text_input("Digite uma query (dummy)")
    if st.button("Buscar"):
        index = load_index_from_s3("vector.index")
        # Vetor de consulta dummy
        xq = np.random.rand(1, 512).astype('float32')
        D, I = index.search(xq, k=5)
        st.write("Documentos mais próximos:", I)
