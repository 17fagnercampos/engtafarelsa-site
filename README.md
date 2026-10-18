# Site engtafarelsa.com.br

Site do Eng. Tafarel Sá. Os textos e as fotos ficam em arquivos simples e o site é gerado a cada mudança.

## Como editar (sem programar)

1. Entre em **https://app.pagescms.org** com a conta do GitHub.
2. Abra este repositório.
3. No menu da esquerda:
   - **Blog (artigos)**: editar um artigo ou clicar em *Add an entry* para escrever um novo.
   - **Fotos do site**: trocar cada foto do site (envie fotos na horizontal, perto de 1600 px de largura).
   - **Página Sobre**: sua trajetória.
   - **Configurações**: números de WhatsApp, redes sociais e o Pixel da Meta.
4. Clique em **Save**. Em 1 a 2 minutos a Cloudflare publica a mudança no ar.

Para guardar um artigo sem publicar, marque **Rascunho**.

## Onde fica cada coisa

| Pasta | O que tem |
|---|---|
| `conteudo/blog/` | Um arquivo `.md` por artigo. O nome do arquivo vira o endereço da página. |
| `conteudo/fotos.yml` | Qual foto aparece em cada espaço do site. |
| `conteudo/paginas/sobre.md` | Texto da página Sobre. |
| `conteudo/config.yml` | WhatsApp, YouTube, Instagram, Facebook, Pixel. |
| `fotos/` | As imagens enviadas pelo painel. |
| `build.py` | O gerador do site (páginas de produto, calculadora, layout). |
| `assets/site.css` | Cores e visual. |
| `vendor/` | Bibliotecas Markdown e YAML (puro Python), para o build não depender de instalação. |

## Publicação (Cloudflare Pages)

- Comando de build: `python3 build.py`
- Pasta de saída: `dist`

## Fotos novas mais leves
Depois de subir fotos pelo painel, rode `python3 otimizar_imagens.py` para gerar as versões .webp (o site usa sozinho).
