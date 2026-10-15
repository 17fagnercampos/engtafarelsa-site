# Site engtafarelsa.com.br

Site estático (HTML + CSS), sem dependências. Gerado por `build.py`.

## Como editar
- Textos e páginas: `build.py` (cada página é uma função).
- Visual: `assets/site.css`.
- Trechos destacados em amarelo no site (função `pend(...)`) são informações a confirmar antes de divulgar.

## Como gerar
    python3 build.py
O site pronto fica na pasta `dist/`.

## Como publicar na Cloudflare Pages
1. Suba esta pasta num repositório do GitHub.
2. Cloudflare → Workers & Pages → Create → Pages → conectar o repositório.
3. Build command: `python3 build.py` · Output directory: `dist`.
4. Em Custom domains, adicione engtafarelsa.com.br.
