# TechPulse AI — Fase 1: Coleta e Padronização de Notícias

## Descrição do projeto

TechPulse AI é um projeto de portfólio cujo objetivo final é ser um agente
inteligente capaz de coletar notícias de tecnologia, resumi-las com IA,
identificar tendências, responder perguntas via RAG e disponibilizar tudo
isso por API e dashboard.

**Esta primeira etapa** foca exclusivamente na construção de uma base
sólida de coleta: buscar notícias de múltiplas fontes e padronizá-las em
um único modelo de domínio (`Article`). Não há IA, banco de dados, API
web, dashboard, autenticação ou qualquer forma de persistência nesta fase.

## Arquitetura

O fluxo de dados segue um pipeline linear e desacoplado:

```
Fonte → Collector → Normalizer → Article → NewsCollectorService → Lista única → Terminal
```

- **Collectors**: buscam dados brutos na fonte (RSS ou API). Não limpam,
  não resumem, não classificam — apenas coletam.
- **Normalizers**: convertem os dados brutos de cada fonte no modelo
  único `Article`. Toda lógica de transformação vive aqui.
- **Article** (`app/models/article.py`): modelo Pydantic único que
  representa qualquer notícia, independentemente da origem.
- **NewsCollectorService**: orquestra a execução de todos os coletores e
  normalizadores, sem conhecer detalhes internos de nenhum deles.
- **utils**: funções puras e reutilizáveis (limpeza de texto, remoção de
  HTML, parsing de datas).

Essa separação garante baixo acoplamento: novas fontes podem ser
adicionadas criando apenas um novo collector + normalizer, sem alterar o
restante do sistema.

## Estrutura de pastas

```text
techpulse-ai/
├── app/
│   ├── collectors/
│   │   ├── base.py               # Contrato abstrato BaseCollector
│   │   ├── rss_collector.py      # Coletor genérico de RSS (TechCrunch)
│   │   ├── github_collector.py   # Coletor do GitHub Blog (herda RSSCollector)
│   │   ├── hackernews_collector.py
│   │   └── devto_collector.py
│   ├── models/
│   │   └── article.py            # Modelo de domínio único
│   ├── normalizers/
│   │   ├── rss_normalizer.py
│   │   ├── github_normalizer.py
│   │   ├── hackernews_normalizer.py
│   │   └── devto_normalizer.py
│   ├── services/
│   │   └── news_collector_service.py
│   ├── utils/
│   │   ├── dates.py
│   │   └── text.py
│   └── main.py
├── tests/
├── requirements.txt
├── .env.example
├── pytest.ini
└── README.md
```

## Tecnologias

- Python 3.13+
- Pydantic — validação e tipagem do modelo `Article`
- feedparser — leitura de feeds RSS/Atom
- requests — chamadas HTTP às APIs (Hacker News, Dev.to)
- BeautifulSoup4 — remoção de HTML dos textos coletados
- python-dotenv — configuração via variáveis de ambiente
- pytest — testes unitários

## Instalação

```bash
git clone <repositorio>
cd techpulse-ai
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Como executar

```bash
python -m app.main
```

A saída no terminal mostra, para cada artigo coletado: título, fonte,
data de publicação e URL.

## Como rodar os testes

```bash
pytest
```

Os testes cobrem o modelo `Article`, o contrato `BaseCollector`, todos os
normalizadores e o `NewsCollectorService` — usando fontes falsas (fakes),
sem necessidade de acesso à rede.

## Escopo desta etapa

**Incluído:** coleta de TechCrunch, Hacker News, GitHub Blog e Dev.to;
padronização em `Article`; impressão no terminal para validação.

**Fora de escopo (propositalmente):** banco de dados, SQLAlchemy, Alembic,
FastAPI, Streamlit, Docker, IA, embeddings, RAG, autenticação, cache,
filas, notificações. Esses itens serão tratados em etapas futuras do
projeto.
