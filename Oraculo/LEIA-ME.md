# 🔮 Oraculo

Assistente de Conhecimento com interface identica ao ChatGPT.

## Estrutura

```
Oraculo/
├── backend/          # API Python (FastAPI)
│   ├── main.py       # Servidor API
│   └── requirements.txt
├── frontend/         # Interface (Next.js + React)
│   ├── app/          # Paginas
│   └── components/   # Componentes React
├── core/             # Logica de RAG
├── loaders/          # Processamento de documentos
└── config.py         # Configuracoes
```

## Instalacao

### 1. Backend (Python)

```bash
cd backend
pip install -r requirements.txt
```

### 2. Frontend (Node.js)

```bash
cd frontend
npm install
```

## Configuracao

Edite o arquivo `.env` na raiz do projeto:

```
OPENAI_API_KEY=sua-chave-aqui
```

## Executando

### Terminal 1 - Backend

```bash
cd backend
python main.py
```

O servidor inicia em http://localhost:8000

### Terminal 2 - Frontend

```bash
cd frontend
npm run dev
```

A interface abre em http://localhost:3000

## Uso

1. Abra http://localhost:3000
2. Adicione documentos pelo menu lateral (PDF, Word, Excel, etc.)
3. Converse com o Oraculo!

## Formatos Suportados

- PDF, DOCX, XLSX, PPTX
- TXT, CSV, JSON
- Imagens (PNG, JPG) com OCR
- Sites e videos do YouTube
