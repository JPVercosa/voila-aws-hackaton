import io
import json
import tempfile
import boto3
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from strands import Agent
from strands.models import BedrockModel
from pypdf import PdfReader
from tqdm import tqdm 

# ---------- Configuração do modelo LLM ----------
nova_model = BedrockModel(
    model_id="amazon.nova-pro-v1:0",
    region_name="us-east-1",
    temperature=0.2,
    top_p=0.9,
)

load_dotenv()

# ---------- Constantes ----------
AREAS = {
    "hr", "security", "privacy", "compliance", "operations",
    "finance", "legal", "risk_management", "it", "procurement",
    "health_safety", "ethics", "training", "customer_relations",
}
DATABASE_PREFIX = "database"
CLAUSE_FOLDER = f"{DATABASE_PREFIX}/clauses"
CATALOG_KEY = f"{DATABASE_PREFIX}/index.jsonl"

# ---------- Modelos ----------
class Clause(BaseModel):
    """Representa uma cláusula extraída de uma página PDF."""
    clause_text: str
    area: str = Field(..., description="Área em minúsculo, conforme enum AREAS")

class Clauses(BaseModel):
    """Wrapper para lista de cláusulas."""
    clauses: list[Clause]

class DBRow(BaseModel):
    """Representa uma linha no banco de dados de cláusulas."""
    doc_id: str
    doc_name: str
    vec_db_idx: int | None = None
    status: str = "pending"
    area: str
    clause_id: str
    clause_text: str
    created_at: str
    updated_at: str
    linked_docs: list[str] = []

# ---------- Ferramenta para separar PDFs ----------
# @tool
# def separate_pdfs(pdf_file: str) -> list[str]:
#     """Separa um arquivo PDF em páginas individuais.

#     Args:
#         pdf_file (str): Caminho ou chave do PDF.

#     Returns:
#         list[str]: Lista de páginas separadas.
#     """
#     print(f"Separating PDF: {pdf_file}")
#     pages = separate_pdf_pages(pdf_file)
#     print(f"Separated into {len(pages)} pages.")
#     return pages

# ---------- Agente de Ingestão ----------
class IngestionAgent(Agent):
    """Agente responsável por ingerir documentos PDF, extrair cláusulas
    e salvar no banco S3."""

    def __init__(self):
        super().__init__(model=nova_model)
        self.kb_id = os.getenv("STRANDS_KNOWLEDGE_BASE_ID")
        self.bucket = os.getenv("S3_BUCKET_NAME")
        self.s3 = boto3.client("s3")

    def _list_raw_files(self) -> list[str]:
        """Lista os arquivos brutos na pasta 'raw/' do bucket S3."""
        resp = self.s3.list_objects_v2(Bucket=self.bucket, Prefix="raw/")
        return [o["Key"] for o in resp.get("Contents", []) if not o["Key"].endswith("/")]

    def _object_exists(self, key: str) -> bool:
        """Verifica se um objeto existe no S3."""
        try:
            self.s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except self.s3.exceptions.ClientError:
            return False

    def _put_jsonl(self, key: str, lines: list[dict]):
        """Salva linhas JSONL em um objeto S3."""
        body = "\n".join(json.dumps(l, ensure_ascii=False) for l in lines).encode()
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=body)

    def _read_pdf_pages(self, key: str) -> list[str]:
        """Lê as páginas de um PDF armazenado no S3.

        Args:
            key (str): Caminho do arquivo PDF no bucket.

        Returns:
            list[str]: Texto de cada página.
        """
        obj = self.s3.get_object(Bucket=self.bucket, Key=key)
        data = obj["Body"].read()
        reader = PdfReader(io.BytesIO(data))
        return [p.extract_text() or "" for p in reader.pages]

    def _extract_clauses_from_page(self, page_text: str) -> list[Clause]:
        """Executa extração de cláusulas a partir do texto de uma página usando o LLM.

        Args:
            page_text (str): Texto da página.

        Returns:
            list[Clause]: Lista de cláusulas extraídas.
        """
        local_agent = Agent(model=nova_model)  # Novo agent sem histórico
        prompt = (
            "Você é um agente de extração de cláusulas. "
            "Leia o texto a seguir que é o conteúdo de **uma página** de um documento. "
            "Identifique e extraia **0, 1 ou mais** regras, cláusulas ou orientações operacionais "
            "que estejam embutidas no texto.\n\n"
            "Extraia todas as cláusulas detectadas e retorne tudo como UM ÚNICO objeto JSON "
            "no formato `{ \"clauses\": [...] }`. NÃO gere múltiplos ToolUse. "
            "Combine tudo em UM ToolUse."
            "Para cada cláusula encontrada, retorne um JSON com os campos: `clause_text` "
            "e `area` (uma das opções abaixo).\n\n"
            f"Áreas válidas: {', '.join(sorted(AREAS))}\n\n"
            f"Página:\n{page_text}"
        )

        try:
            response = local_agent.structured_output(Clauses, prompt)
            # print(response)

            if isinstance(response, Clauses):
                return response.clauses
            else:
                print("⚠️  Nenhuma cláusula extraída.")
                return []
        except Exception as e:
            print(f"❌ Erro ao extrair cláusula: {e}")
            return []

    def ingest_all(self):
        """Executa o processo completo de ingestão:
        1. Lista documentos novos.
        2. Lê páginas PDF.
        3. Extrai cláusulas página a página.
        4. Salva resultados parciais e atualiza catálogo.
        """
        processed_docs: set[str] = set()
        if self._object_exists(CATALOG_KEY):
            catalog_obj = self.s3.get_object(Bucket=self.bucket, Key=CATALOG_KEY)
            for line in catalog_obj["Body"].iter_lines():
                processed_docs.add(json.loads(line)["doc_name"])

        new_rows: list[dict] = []
        raw_files = self._list_raw_files()

        for raw_key in tqdm(raw_files, desc="📄 Processando documentos"):
            if raw_key in processed_docs:
                continue

            print(f"Ingerindo {raw_key}…")
            pages = self._read_pdf_pages(raw_key)
            if not pages:
                print(f"⚠️  Nenhuma página lida em {raw_key}")
                continue

            doc_id = str(uuid.uuid4())
            ts = datetime.now(timezone.utc).isoformat()

            for i, page_text in enumerate(pages):
                clauses = self._extract_clauses_from_page(page_text)
                print(f"Extraídas {len(clauses)} cláusulas da página {i + 1} do documento {raw_key}.")
                for cl in clauses:
                    row = DBRow(
                        doc_id=doc_id,
                        doc_name=raw_key,
                        area=cl.area,
                        clause_id=str(uuid.uuid4()),
                        clause_text=cl.clause_text,
                        created_at=ts,
                        updated_at=ts,
                    )
                    new_rows.append(row.model_dump())

            if new_rows:
                dated_folder = f"{CLAUSE_FOLDER}/{datetime.utcnow().date()}"
                clause_key = f"{dated_folder}/{doc_id}.jsonl"
                self._put_jsonl(clause_key, [r for r in new_rows if r["doc_id"] == doc_id])
                print(f"✔️  {clause_key} escrito.")

        if new_rows:
            if self._object_exists(CATALOG_KEY):
                cat_obj = self.s3.get_object(Bucket=self.bucket, Key=CATALOG_KEY)
                existing = cat_obj["Body"].read().decode()
                body = existing + "\n"
            else:
                body = ""
            body += "\n".join(json.dumps(r, ensure_ascii=False) for r in new_rows)
            self.s3.put_object(Bucket=self.bucket, Key=CATALOG_KEY, Body=body.encode())
            print(f"📚  {len(new_rows)} novas linhas adicionadas ao catálogo.")
        else:
            print("Nenhum documento novo para processar.")

# -------- CLI --------
if __name__ == "__main__":
    agent = IngestionAgent()
    agent.ingest_all()
