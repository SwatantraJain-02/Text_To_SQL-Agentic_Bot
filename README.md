# Text to SQL Agentic Bot

A project that provides an AI-powered agentic chatbot for supervised workflows, including a Text-to-SQL agent, RAG workflows, and a Streamlit frontend.

## Features

- Interactive Streamlit UI for multi-agent chat.
- Text-to-SQL agent that converts natural language queries into SQL and executes against a SQLite database.
- Retriever-Augmented Generation (RAG) workflows for knowledge-based QA.
- Jupyter notebooks for data ingestion and experimentation.

## Prerequisites

- Python 3.8 or higher (Preferrable - Python 3.12.0)  
- `git`  
- Recommended: [`virtualenv`](https://pypi.org/project/virtualenv/) or built-in `venv`  
- (Optional) [Streamlit](https://streamlit.io/) for the UI  
- (Optional) [Jupyter](https://jupyter.org/) for notebooks  

## Installation

1. Clone the repository  
   ```bash
   git clone https://github.com/SwatantraJain-02/Text_To_SQL-Agentic_Bot.git
   cd Text_To_SQL-Agentic_Bot
   ```

2. Create and activate a virtual environment  
   Windows (Command Prompt):  
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```  
   macOS/Linux:  
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install Python dependencies  
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Copy and configure environment variables  
   ```bash
   cp .env.example .env
   ```  
   Edit `.env` and fill in your API keys and settings:  
   - `LANGSMITH_TRACING_V2`, `LANGSMITH_ENDPOINT`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`  
   - `GROQ_API_KEY`, `GROQ_MODEL_NAME`  
   - `PDF_DIRECTORY` (relative path to your PDF documents)  
   - `DB_DIRECTORY` (relative path to your Database), `DB_NAME`, `COLLECTION_NAME`,
   - `EMBEDDING_MODEL`

5. Prepare data directories  
   The project will auto-create the following on first run:  
   - `logs/` 
   - PDF directory (from `PDF_DIRECTORY`)  
   - Database directory (from `DB_DIRECTORY`)  

## Usage

### 1. Streamlit Frontend

Launch the interactive UI for the multi-agent chatbot:

```bash
streamlit run frontend/app.py
```

- Navigate to `http://localhost:8501/` in your browser.
- Use the sidebar to select and configure agents.
- Chat through the main interface; toggle “Show AI Thinking Process” to inspect internal reasoning.

### 2. Jupyter Notebooks

- Data ingestion for RAG: `src/Notebooks/RAG_ingestion.ipynb`  
- Text-to-SQL experimentation: `src/Notebooks/Text_To_SQL.ipynb`  

Start Jupyter:

```bash
jupyter notebook src/Notebooks
```

## Project Structure

```
.
├── .env.example        # Sample environment variables
├── main.py             # (Optional) Top-level launch script
├── requirements.txt
├── setup.py
├── frontend/           # Streamlit application
│   ├── app.py
│   └── components/
│   └── config/
│   └── utils/
├── src/
│   ├── agents/         # Workflows and agents
│   ├── data/           # PDF documents & prompts
│   ├── db/             # SQLite database (auto-created)
│   └── utils/          # Configuration, logging, LLM adapter
├── logs/               # Log output (auto-created)
└── text_to_sql_agentic_bot.egg-info
```

## Troubleshooting

- Ensure your `.env` file is populated before running.  
- If Streamlit fails to start, verify installation with `streamlit --version`.  
- For database errors, confirm the SQLite file exists or the path is correct.  
- Review logs under `logs/` for detailed error messages.

## License

MIT License
