#!/usr/bin/env python3
"""Gera o site estático engtafarelsa.com.br na pasta dist/.

Uso: python3 build.py
Para publicar: suba a pasta dist/ na Cloudflare Pages (ou qualquer hospedagem estática).

Trechos marcados com pend("...") aparecem destacados em amarelo no site:
são informações que o Tafarel precisa confirmar antes de divulgar.
"""
import html
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote

RAIZ = Path(__file__).parent
sys.path.insert(0, str(RAIZ / "vendor"))  # markdown e yaml, puro Python, sem instalar nada
import markdown  # noqa: E402
import yaml  # noqa: E402

CONTEUDO = RAIZ / "conteudo"


def ler_yaml(caminho):
    with open(caminho, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def ler_md(caminho):
    """Lê um arquivo .md com cabeçalho YAML (entre ---). Devolve (dados, corpo)."""
    texto = Path(caminho).read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", texto, re.S)
    if not m:
        return {}, texto
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def md_html(texto):
    """Markdown do painel para HTML do site (tabelas com rolagem no celular)."""
    h = markdown.markdown(texto or "", extensions=["markdown.extensions.tables", "markdown.extensions.sane_lists"])
    h = h.replace("<table>", '<div class="tabela-rolagem"><table class="tabela">').replace("</table>", "</table></div>")
    return h


CONFIG = ler_yaml(CONTEUDO / "config.yml")
FOTOS = ler_yaml(CONTEUDO / "fotos.yml")
DIST = RAIZ / "dist"
DOMINIO = "https://engtafarelsa.com.br"

ZAP = str(CONFIG.get("whatsapp_tafarel") or "5551999365993")
ZAP_LEGIVEL = CONFIG.get("whatsapp_tafarel_legivel") or "(51) 99936-5993"
# Brasil Estufas (representação): vendas de estufas vão para este número
ZAP_ESTUFAS = str(CONFIG.get("whatsapp_vendas") or "5548998508182")
ZAP_ESTUFAS_LEGIVEL = CONFIG.get("whatsapp_vendas_legivel") or "(48) 99850-8182"
YOUTUBE = CONFIG.get("youtube") or "https://www.youtube.com/@engtafarelsa"

# Loja AKSO: links de parceiro 7766 (Piscicultura Lucrativa), testados em 15/10/2026.
# Preços de referência da loja nessa data ("a partir de"); a loja pode mudar.
AKSO_DATA = "15/10/2026"
AKSO_KITS = [
    ("Oxigênio dissolvido", "Grandes produções e tanque-rede: falta de oxigênio de madrugada.",
     [("AK121 Medidor de oxigênio dissolvido e temperatura (sonda óptica)", "R$ 4.379,00",
       "https://loja.akso.com.br/produtos/medidores-de-oxigenio-dissolvido/ak121-od-max-com-eletrodo-otico?parceiro=7766")]),
    ("pH completo", "Para quem está começando e ainda não sabe se a água está boa.",
     [("AK90 Agro Medidor de pH de bolso", "R$ 321,90",
       "https://loja.akso.com.br/produtos/medidores-de-ph-e-orp/medidor-de-ph-de-bolso-phmetro-ak90-new-agro?parceiro=7766"),
      ("Solução pH 4 (250 mL)", "R$ 24,24", "https://loja.akso.com.br/solucao-de-ph-4-250ml?parceiro=7766"),
      ("Solução pH 7 (250 mL)", "R$ 25,35", "https://loja.akso.com.br/solucao-de-ph-7-250ml?parceiro=7766"),
      ("Solução pH 10 (250 mL)", "R$ 20,61", "https://loja.akso.com.br/solucao-de-ph-10-250ml?parceiro=7766"),
      ("Solução KCl 3M para guardar o eletrodo", "R$ 36,88", "https://loja.akso.com.br/solucao-kcl-3m-cloreto-de-potassio-250ml?parceiro=7766"),
      ("Pepsina para limpar o eletrodo", "R$ 31,78", "https://loja.akso.com.br/solucao-de-pepsina-para-limpeza-de-eletrodos-de-ph-250ml?parceiro=7766")]),
    ("Kit Nitrito", "Mortalidade que aparece depois de aumentar a ração.",
     [("AK45 Medidor de nitrito", "R$ 581,38", "https://loja.akso.com.br/ak45-nitrito-tester-medidor?parceiro=7766"),
      ("AK4045 Reagente para nitrito (50 testes)", "R$ 166,32", "https://loja.akso.com.br/depois-da-compra/ak4045-reagente-em-po-nitrito-50-testes?parceiro=7766"),
      ("AK4215 Padrões de verificação", "R$ 168,11", "https://loja.akso.com.br/produtos/ak4215-kit-padroes-de-verificacao-nitrito?parceiro=7766")]),
    ("Kit Amônia", "Peixe comendo bem e mesmo assim sem crescer.",
     [("AK43 Medidor de amônia", "R$ 581,38", "https://loja.akso.com.br/amonia-tester-medidor-de-amonia?parceiro=7766"),
      ("AK4043 Reagente para amônia (50 testes)", "R$ 141,68", "https://loja.akso.com.br/reagente-liquido-para-amonia-faixa-media-50-testes?parceiro=7766"),
      ("AK4205 Padrões de verificação", "R$ 169,00", "https://loja.akso.com.br/produtos/ak4205-kit-padroes-de-verificacao-amonia?parceiro=7766")]),
    ("Kit Alcalinidade", "pH que oscila e filtro biológico que não estabiliza.",
     [("AK44 Medidor de alcalinidade", "R$ 635,59", "https://loja.akso.com.br/ak44-alcalinidade-tester-akso?parceiro=7766"),
      ("AK4044 Reagente para alcalinidade (50 testes)", "R$ 131,45", "https://loja.akso.com.br/depois-da-compra/reagentes-e-solucoes/ak4044-reagente-para-alcalinidade-50-testes?parceiro=7766"),
      ("AK4220 Padrões de verificação", "R$ 150,04", "https://loja.akso.com.br/analise-de-agua/ak4220-kit-padroes-de-verificacao-alcalinidade-tester-ak44?parceiro=7766")]),
    ("Multiparâmetro", "Técnicos, consultores e cooperativas que medem várias fazendas.",
     [("AK88+ pH, condutividade, OD, TDS, salinidade e temperatura", "R$ 4.866,40",
       "https://loja.akso.com.br/produtos/medidores-de-condutividadetds-e-salinidade/ak88-medidor-multiparametro-com-sonda-optica-de-od?parceiro=7766")]),
    ("Salinidade", "Camarão e água salobra.",
     [("AK58 Medidor de salinidade de bolso", "R$ 264,60", "https://loja.akso.com.br/medidor-de-salinidade-de-bolso-ak58?parceiro=7766"),
      ("Solução NaCl 80 ppt (250 mL)", "R$ 147,12", "https://loja.akso.com.br/solucao-nacl-80-ppt-para-ak58-250-ml?parceiro=7766")]),
]
INSTAGRAM = CONFIG.get("instagram") or "https://instagram.com/engtafarelsa"
FACEBOOK = CONFIG.get("facebook") or ""
BENFICA_URL = "https://benficaagroengenharia.com.br"
CNPJ = "40.342.113/0001-90"
ENDERECO = "BR-386, km 407 — Triunfo/RS"


def pend(texto):
    """Informação provisória, destacada para revisão."""
    return f'<mark class="pendente" title="Confirmar antes de publicar">{texto}</mark>'


def foto(nome, alt, prof=0, classe="foto"):
    """Foto real do site (assets/fotos/<nome>.jpg)."""
    return (f'<img class="{classe}" src="{"../" * prof}assets/fotos/{nome}.jpg" alt="{alt}" '
            f'loading="lazy" decoding="async">')


def foto_slot(slot, provisorio, prof=0, classe="foto-provisoria"):
    """Foto editável pelo painel (conteudo/fotos.yml). Sem imagem: mostra o espaço reservado."""
    f = FOTOS.get(slot) or {}
    img = (f.get("imagem") or "").lstrip("/")
    if not img:
        return f'<div class="{classe}">{provisorio}</div>'
    extra = " foto-larga" if "foto-larga" in classe else ""
    return (f'<img class="foto{extra}" src="{"../" * prof}{img}" alt="{html.escape(f.get("descricao") or "")}" '
            f'loading="lazy" decoding="async">')


CARTAO_AUTOR = (
    '<span class="cartao-mono" aria-hidden="true">TS</span>'
    '<span class="cartao-nome">Eng. Tafarel Sá</span>'
    '<span class="cartao-cargo">Engenheiro · Benfica AgroEngenharia</span>'
    '<span class="cartao-local">Triunfo/RS · @engtafarelsa</span>'
)


def zap_link(msg, numero=None):
    return f"https://wa.me/{numero or ZAP}?text={quote(msg)}"


ICONE_ZAP = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.2-.4.2-.4.7-1.3.1-.1 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.7 11.8 11.8 0 0 0 4.5 4c1.7.7 2.3.8 3.2.6.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.1-1.2l-.5-.3Z"/></svg>'
)


def botao_zap(texto, msg, extra="", numero=None):
    return (
        f'<a class="botao botao-zap {extra}" href="{zap_link(msg, numero)}" '
        f'target="_blank" rel="noopener">{ICONE_ZAP}{texto}</a>'
    )


# ---------------------------------------------------------------- navegação
MENU = [
    ("blog/", "Água Boa Dá Lucro"),
    ("qualidade-da-agua", "Qualidade da água"),
    ("biotecnal", "Biotecnal"),
    ("piscicultura", "Piscicultura"),
    ("aquaponia-comercial", "Aquaponia"),
    ("hidroponia", "Hidroponia"),
    ("estufas", "Estufas"),
    ("loja-akso", "Loja AKSO"),
    ("sobre", "Sobre"),
]


def href(alvo, prof):
    """Link relativo a partir da profundidade da página atual."""
    prefixo = "../" * prof
    if alvo == "":
        return prefixo + "index.html"
    if alvo.endswith("/"):
        return prefixo + alvo + "index.html"
    return prefixo + alvo + ".html"


# Meta Pixel: cole aqui o ID quando criar o Pixel no Gerenciador de Eventos (deixe vazio para não carregar).
META_PIXEL_ID = str(CONFIG.get("meta_pixel_id") or "")

# Origem do contato: lê ?utm_source / ?utm_campaign (ou ?origem) da URL, guarda na sessão e
# acrescenta no fim da mensagem de qualquer link de WhatsApp. Assim você sabe no próprio WhatsApp
# se o cliente veio do anúncio, do YouTube ou do Google.
ORIGEM_JS = r"""
<script>
(function(){
  var K='eng_origem', o=null;
  try{var q=new URLSearchParams(location.search);
    var src=(q.get('utm_source')||q.get('origem')||'').toLowerCase(), camp=q.get('utm_campaign')||'';
    if(src){var nome=/fb|facebook|ig|insta|meta/.test(src)?'anúncio Facebook/Instagram':/youtube|yt/.test(src)?'YouTube':/google/.test(src)?'Google':src;
      o=nome+(camp?' · '+camp:''); sessionStorage.setItem(K,o);}
    else{o=sessionStorage.getItem(K);}
  }catch(e){}
  document.addEventListener('click',function(e){
    var a=e.target.closest&&e.target.closest('a[href*="wa.me/"]'); if(!a) return;
    if(o&&a.href.indexOf('Origem%3A')<0){
      var u=new URL(a.href), t=u.searchParams.get('text')||'';
      u.searchParams.set('text',t+'\n\n(Origem: '+o+')'); a.href=u.toString();
    }
    if(window.fbq){try{fbq('track','Contact');}catch(err){}}
  },true);
})();
</script>"""


def pixel_html():
    if not META_PIXEL_ID:
        return ""
    return ("<script>!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?"
            "n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;"
            "n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];"
            "s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');"
            f"fbq('init','{META_PIXEL_ID}');fbq('track','PageView');</script>")



_PALAVRAS_SOLTAS = {"para", "e", "de", "do", "da", "dos", "das", "no", "na", "com", "o", "a", "em", "por"}


def desc_curta(d, limite=158):
    """Meta description com até ~158 caracteres, cortada no fim de frase ou de palavra."""
    d = " ".join(d.split())
    if len(d) <= limite:
        return d
    corte = d[:limite]
    ponto = corte.rfind(". ")
    if ponto >= 90:
        return corte[:ponto + 1]
    return corte[:corte.rfind(" ")].rstrip(",;:-–") + "…"


def titulo_tag(t, limite=65):
    """Título curto para o Google/Bing (até ~65 caracteres). O título completo continua no og:title."""
    if len(t) <= limite:
        return t
    base = t.rsplit(" | ", 1)[0] if t.endswith("| Eng. Tafarel Sá") else t
    if len(base) <= 70:  # sem o sufixo, aceita até 70 (limite do Bing) para não cortar a frase
        return base
    palavras = base.split()
    while palavras and (len(" ".join(palavras)) > limite or palavras[-1].lower() in _PALAVRAS_SOLTAS):
        palavras.pop()
    return " ".join(palavras).rstrip(":,;-–")


def pagina(*, slug, titulo, descricao, corpo, prof=0, msg_zap, ld=None, ativo=None, zap_numero=None):
    canonico = DOMINIO + "/" + (slug.removesuffix("index") if slug else "")
    css = "../" * prof + "assets/site.css"
    itens_menu = "".join(
        f'<a href="{href(a, prof)}"{" class=\"menu-destaque\"" if a == "blog/" else ""}{" aria-current=\"page\"" if a == ativo else ""}>{n}</a>'
        for a, n in MENU
    )
    ld_html = ""
    if ld:
        ld_html = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titulo_tag(titulo))}</title>
<meta name="description" content="{html.escape(desc_curta(descricao))}">
<link rel="canonical" href="{canonico}">
<meta property="og:type" content="website">
<meta property="og:locale" content="pt_BR">
<meta property="og:title" content="{html.escape(titulo)}">
<meta property="og:description" content="{html.escape(descricao)}">
<meta property="og:url" content="{canonico}">
<meta property="og:site_name" content="Eng. Tafarel Sá">
<meta property="og:image" content="{DOMINIO}/assets/og-capa.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Eng. Tafarel Sá: qualidade da água na piscicultura">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0c1416">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,700..800&family=Atkinson+Hyperlegible:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{css}">
<link rel="alternate" type="application/rss+xml" title="Blog Eng. Tafarel Sá" href="{DOMINIO}/blog/feed.xml">
{ld_html}
{pixel_html()}
</head>
<body>
<a class="skip" href="#conteudo">Pular para o conteúdo</a>
<header class="topo">
  <div class="wrap">
    <a class="marca" href="{href('', prof)}">Eng. Tafarel Sá<small>Qualidade da água e piscicultura</small></a>
    <a class="topo-cta" href="{href('projeto', prof)}">Contar meu projeto</a>
    <button class="menu-botao" aria-expanded="false" aria-controls="menu">Menu</button>
    <nav class="menu" id="menu" aria-label="Principal">{itens_menu}</nav>
  </div>
</header>
<main id="conteudo">
{corpo}
</main>
<footer class="rodape">
  <div class="wrap rodape-grade">
    <div>
      <h3>Eng. Tafarel Sá</h3>
      <p>Engenheiro responsável pela <a href="{BENFICA_URL}">Benfica AgroEngenharia</a>.<br>
      CNPJ {CNPJ}</p>
      <p>{ENDERECO}<br>Atendimento no Rio Grande do Sul e em outros estados, conforme o projeto.</p>
    </div>
    <div>
      <h3>Produtos e serviços</h3>
      <ul>
        <li><a href="{href('estufas', prof)}">Estufas Brasil Estufas</a></li>
        <li><a href="{href('piscicultura', prof)}">Consultoria em piscicultura</a></li>
        <li><a href="{href('aquaponia-comercial', prof)}">Consultoria em aquaponia</a></li>
        <li><a href="{href('hidroponia', prof)}">Hidroponia Hortivinyl</a></li>
        <li><a href="{href('qualidade-da-agua', prof)}">Qualidade da água</a></li>
        <li><a href="{href('biotecnal', prof)}">Linha Aqua Biotecnal</a></li>
        <li><a href="{href('calculadora', prof)}">Calculadora de manejo</a></li>
        <li><a href="{href('loja-akso', prof)}">Loja AKSO</a></li>
        <li><a href="{href('tanques-de-geomembrana', prof)}">Tanques de geomembrana</a></li>
        <li><a href="{href('traira-e-trairao', prof)}">Traíra e trairão</a></li>
        <li><a href="{href('cursos', prof)}">Cursos</a></li>
      </ul>
    </div>
    <div>
      <h3>Contato</h3>
      <ul>
        <li><a href="{zap_link('Olá, Tafarel! Vim pelo site.')}" target="_blank" rel="noopener">WhatsApp {ZAP_LEGIVEL}</a></li>
        <li><a href="{zap_link('Olá! Vim pelo site do Eng. Tafarel e quero orçamento de estufa.', ZAP_ESTUFAS)}" target="_blank" rel="noopener">Estufas: {ZAP_ESTUFAS_LEGIVEL}</a></li>
        <li><a href="{YOUTUBE}" target="_blank" rel="noopener">YouTube Engenheiro Tafarel Sá</a></li>
        <li><a href="{INSTAGRAM}" target="_blank" rel="noopener">Instagram @engtafarelsa</a></li>
      </ul>
    </div>
  </div>
</footer>
{botao_zap("Falar no WhatsApp", msg_zap, "zap-fixo", zap_numero)}
<script>
  (function () {{
    var b = document.querySelector('.menu-botao'), m = document.getElementById('menu');
    if (!b || !m) return;
    b.addEventListener('click', function () {{
      var aberto = m.classList.toggle('aberto');
      b.setAttribute('aria-expanded', aberto ? 'true' : 'false');
    }});
  }})();
</script>
{ORIGEM_JS}
</body>
</html>
"""


# ---------------------------------------------------------------- blocos comuns
def perguntas(lista):
    itens = "".join(
        f"<details><summary>{p}</summary><div><p>{r}</p></div></details>" for p, r in lista
    )
    return f'<div class="perguntas">{itens}</div>'


def faq_ld(lista):
    import re
    limpa = lambda s: re.sub(r"<[^>]+>", "", s)
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": limpa(p),
             "acceptedAnswer": {"@type": "Answer", "text": limpa(r)}}
            for p, r in lista
        ],
    }


def etapas(lista, claro=False):
    itens = "".join(f"<li><div><strong>{t}</strong><p>{d}</p></div></li>" for t, d in lista)
    return f'<ol class="etapas{" claro" if claro else ""}">{itens}</ol>'


def chamada(titulo, texto, botao, msg, numero=None):
    return f"""<section class="chamada"><div class="wrap">
<h2>{titulo}</h2><p>{texto}</p>{botao_zap(botao, msg, numero=numero)}
</div></section>"""


ETAPAS_PADRAO = [
    ("Você me chama no WhatsApp",
     "Conta o que quer produzir, onde fica a área e qual o tamanho que imagina. Fotos e vídeos do terreno ajudam muito."),
    ("Avaliamos juntos",
     "Por vídeo ou em visita técnica, vejo terreno, fonte de água e acesso, e entendo sua meta de produção."),
    ("Projeto e orçamento por escrito",
     "Você recebe o que vai ser feito, materiais, prazo e valor. Sem surpresa no meio da obra."),
    ("Execução com responsabilidade técnica",
     "Instalação com equipe própria e ART, a Anotação de Responsabilidade Técnica do engenheiro."),
    ("Acompanhamento depois da entrega",
     "Oriento a operação nos primeiros ciclos para a estrutura render o que foi planejado."),
]


def pagina_produto(*, slug, titulo_seo, descricao, h1, promessa, foto, para_quem,
                   inclui, faq, msg, chamada_titulo, extra="", numero=None,
                   passos=None, botao="Pedir orçamento no WhatsApp",
                   chamada_texto="Mande fotos da área e o que você quer produzir. Eu respondo pessoalmente."):
    corpo = f"""
<section class="cabeca-pagina"><div class="wrap cabeca-grade">
  <div>
    <p class="trilha"><a href="index.html">Início</a> / {h1}</p>
    <h1>{h1}</h1>
    <p class="promessa">{promessa}</p>
    <div class="hero-acoes">{botao_zap(botao, msg, numero=numero)}</div>
  </div>
  {foto if foto.startswith(("<img", "<div")) else f'<div class="foto-provisoria">{foto}</div>'}
</div></section>

<section class="secao"><div class="wrap duas-colunas">
  <div>
    <h2>Para quem é</h2>
    <ul class="lista-check">{"".join(f"<li>{i}</li>" for i in para_quem)}</ul>
  </div>
  <div>
    <h2>O que está incluído</h2>
    <ul class="lista-check">{"".join(f"<li>{i}</li>" for i in inclui)}</ul>
  </div>
</div></section>
{extra}
<section class="secao secao-escura"><div class="wrap">
  <h2>Como funciona</h2>
  {etapas(passos or ETAPAS_PADRAO)}
</div></section>

<section class="secao secao-branca"><div class="wrap">
  <h2>Perguntas comuns</h2>
  {perguntas(faq)}
</div></section>
{chamada(chamada_titulo, chamada_texto, botao, msg, numero)}
"""
    ld = [
        {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": h1,
            "description": descricao,
            "areaServed": "BR-RS",
            "provider": {"@id": DOMINIO + "/#tafarel"},
        },
        faq_ld(faq),
    ]
    return pagina(slug=slug, titulo=titulo_seo, descricao=descricao, corpo=corpo,
                  msg_zap=msg, ld=ld, ativo=slug, zap_numero=numero)


# ---------------------------------------------------------------- home
CORTE_SVG = """
<svg class="corte" viewBox="0 0 1100 300" role="img" aria-labelledby="corte-t">
  <title id="corte-t">Desenho em corte de um tanque escavado revestido com geomembrana e de uma estufa ao lado</title>
  <rect class="terra" x="0" y="170" width="1100" height="130"/>
  <path class="terra-risco" d="M0 210 H1100 M0 250 H1100 M0 285 H1100"/>
  <polygon points="70,170 170,285 520,285 620,170" fill="#e6ddc9"/>
  <polygon class="agua" points="88,186 175,276 515,276 602,186"/>
  <path class="onda" d="M120 200 q20 -8 40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0"/>
  <polyline class="manta" points="62,170 170,288 520,288 628,170"/>
  <line class="chao" x1="0" y1="170" x2="1100" y2="170"/>
  <g>
    <path class="estufa" d="M720 170 V105 Q855 25 990 105 V170 Z"/>
    <path class="costela" d="M765 170 V82 M810 170 V64 M855 170 V58 M900 170 V64 M945 170 V82"/>
    <g class="planta">
      <ellipse cx="760" cy="160" rx="14" ry="10"/><ellipse cx="805" cy="160" rx="14" ry="10"/>
      <ellipse cx="850" cy="160" rx="14" ry="10"/><ellipse cx="895" cy="160" rx="14" ry="10"/>
      <ellipse cx="940" cy="160" rx="14" ry="10"/>
    </g>
  </g>
  <path class="cota" d="M628 170 L668 130 H770"/>
  <text x="676" y="124">geomembrana</text>
  <path class="cota" d="M345 186 V140 M330 140 H360 M345 276 V296"/>
  <text x="240" y="132">lâmina d'água</text>
  <path class="cota" d="M990 105 L1030 70"/>
  <text x="980" y="62">estufa</text>
</svg>"""

OFERTAS = [
    ("qualidade-da-agua", "Qualidade da água",
     "Valores de referência, como medir e como corrigir oxigênio, amônia, nitrito, pH e lodo."),
    ("biotecnal", "Linha Aqua Biotecnal",
     "Oxitrat, Bactrat P, Bactrat Aquanitro e Nutrat Aqua Plus, com protocolo para o seu viveiro."),
    ("estufas", "Estufas",
     "Representante Brasil Estufas. Estrutura para hortaliças, mudas e flores, com orçamento direto com a fábrica."),
    ("piscicultura", "Consultoria em piscicultura",
     "Do dimensionamento dos viveiros ao manejo da água, para produzir mais peixe por metro quadrado."),
    ("aquaponia-comercial", "Consultoria em aquaponia",
     "Peixe e hortaliça no mesmo sistema, projetado para vender, não para hobby."),
    ("hidroponia", "Hidroponia Hortivinyl",
     "Torre, mini bancada e bancadas para iniciantes, com garantia de 10 anos do fabricante."),
    ("tanques-de-geomembrana", "Tanques de geomembrana",
     "Viveiros e reservatórios que não perdem água, com manta Geotop."),
    ("traira-e-trairao", "Traíra e trairão",
     "Criação de peixe nativo para pesca esportiva e pesque-pague."),
    ("loja-akso", "Loja AKSO",
     "Medidores de oxigênio, pH e amônia que eu uso e recomendo. Compra direto pelo link."),
]

FAQ_HOME = [
    ("Você atende só no Rio Grande do Sul?",
     "A base fica em Triunfo/RS. Atendo o estado inteiro e outros estados quando o porte do projeto justifica o deslocamento. A consultoria também pode ser feita por vídeo."),
    ("Preciso ter o projeto pronto para pedir orçamento?",
     "Não. Você me conta o que quer produzir e o tamanho da área, e eu monto o projeto junto com o orçamento."),
    ("Quem emite a nota fiscal?",
     f"Nos serviços de engenharia e consultoria, a Benfica AgroEngenharia, CNPJ {CNPJ}. Nas estufas, a própria Brasil Estufas. Nos medidores, a loja AKSO."),
    ("Dá para financiar?",
     "Muitos produtores usam linhas de crédito rural. Eu preparo o projeto e o orçamento no formato que o banco ou a cooperativa pedir."),
]

SERIE = [
    ("Amônia e crescimento", "Por que o peixe para de crescer mesmo comendo bem."),
    ("Oxigênio dissolvido ao amanhecer", "Nunca meça oxigênio ao meio-dia. A hora certa salva o lote."),
    ("Alcalinidade", "A base que segura o pH e mantém o filtro biológico vivo."),
    ("Nitrito", "O veneno silencioso que aparece depois da amônia."),
    ("Matéria orgânica e decantação", "Como tirar a sujeira da água sem trocar o tanque inteiro."),
    ("Filtragem biológica", "As bactérias que trabalham de graça para você."),
]


def bloco_youtube(prof=0, titulo="Água Boa Dá Lucro", intro=None):
    intro = intro or ("A minha série no YouTube sobre qualidade de água na piscicultura. "
                      "Um parâmetro por episódio, explicado com estudo e com o que eu vejo no campo.")
    eps = "".join(f"<li><strong>{t}</strong><span>{d}</span></li>" for t, d in SERIE)
    return f"""<section class="secao secao-escura" id="youtube"><div class="wrap yt">
  <div>
    <h2>{titulo}</h2>
    <p class="intro">{intro}</p>
    <div class="hero-acoes">
      <a class="botao botao-zap" href="{YOUTUBE}" target="_blank" rel="noopener">Assistir no YouTube</a>
      <a class="botao botao-linha botao-claro" href="{href('blog/', prof)}">Ver vídeos e artigos</a>
    </div>
  </div>
  <ol class="serie">{eps}</ol>
</div></section>"""


def home():
    linhas = "".join(
        f'<li class="oferta"><h3>{n}</h3><p>{d}</p><a href="{href(s, 0)}">Ver detalhes</a></li>'
        for s, n, d in OFERTAS
    )
    linhas += (
        f'<li class="oferta oferta-curso"><h3>Cursos</h3>'
        f"<p>Aquaponia e piscicultura, online e presencial, com quem projeta e instala esses sistemas.</p>"
        f'<a href="{href("cursos", 0)}">Ver cursos</a></li>'
    )
    clientes = ["GE Vernova", "GKN Automotive", "SENAR", "Grupo Brasanitas", "Taurus", "Supra",
                "Colégio São Luís Guanella"]
    msg = "Olá, Tafarel! Vim pelo site e quero conversar sobre o meu projeto."
    corpo = f"""
<section class="portal-hero home-portal"><div class="wrap portal-grade">
  <div>
    <p class="card-cat">Portal de qualidade de água na piscicultura</p>
    <h1>Água Boa Dá Lucro</h1>
    <p class="promessa">Guias práticos, produtos Biotecnal, cases e mercado, com o Eng. Tafarel Sá. Para a ração virar peixe e não prejuízo.</p>
    <div class="hero-acoes">
      <a class="botao botao-zap" href="{href('blog/', 0)}">Ler os guias</a>
      <a class="botao botao-linha botao-claro" href="#cadastro">Receber no WhatsApp</a>
    </div>
    <nav class="cat-chips" aria-label="Categorias">{"".join(f'<a class="cat-chip" href="{href("blog/categoria/" + c, 0)}">{n}</a>' for c, n, _ in CATEGORIAS)}</nav>
  </div>
  <div class="hero-destaque"><p class="card-cat">Em destaque</p>{card_artigo(ARTIGOS[0], 0, 2).replace('loading="lazy"', 'fetchpriority="high"', 1)}</div>
</div></section>

<section class="secao"><div class="wrap">
  <div class="sec-topo"><h2>Últimos conteúdos</h2><a href="{href('blog/', 0)}">Ver todos</a></div>
  <div class="cards">{"".join(card_artigo(a, 0) for a in ARTIGOS[1:7])}</div>
</div></section>

<section class="secao"><div class="wrap">
  <h2>Qual é o problema da sua água?</h2>
  <p class="intro">Escolha o que você está vendo no viveiro. Cada linha leva para o guia e para o produto que resolve.</p>
  {tabela_matriz(0)}
  <p style="margin-top:20px"><a class="botao botao-linha" href="{href('calculadora', 0)}#diagnostico">Fazer o diagnóstico da água</a> <a class="botao botao-linha" href="{href('projeto', 0)}">Contar meu projeto</a></p>
</div></section>

{bloco_cadastro(0)}
{CADASTRO_JS}

<section class="secao" id="o-que-eu-faco"><div class="wrap">
  <h2>O que eu faço</h2>
  <p class="intro">Escolha o que você precisa. Cada caminho leva direto para quem resolve.</p>
  <ul class="ofertas">{linhas}</ul>
</div></section>

{bloco_youtube(0)}

<section class="secao secao-branca" id="quem-assina"><div class="wrap assina">
  <div class="assina-lado">
    {foto_slot("inicio_tafarel", CARTAO_AUTOR, classe="cartao-autor")}
    <ul class="assina-fatos">
      <li><strong>Desde 2020</strong><span>Benfica AgroEngenharia</span></li>
      <li><strong>RS e SC</strong><span>Representante Biotecnal</span></li>
      <li><strong>4 marcas</strong><span>de fabricante, com procedência</span></li>
    </ul>
  </div>
  <div>
    <p class="sobretitulo">Quem assina o projeto</p>
    <h2>Eng. Tafarel Sá</h2>
    <p class="assina-lead">Sou engenheiro e responsável técnico pela Benfica AgroEngenharia, empresa de engenharia com sede em Triunfo/RS desde 2020.</p>
    <p>Represento a Brasil Estufas, a Biotecnal e a Geotop, vendo a linha de hidroponia Hortivinyl e indico os equipamentos AKSO. Isso quer dizer material de fabricante, com procedência, e alguém que responde por ele depois da entrega.</p>
    <p>No canal, apresento a série <a href="{href('blog/', 0)}">Água Boa Dá Lucro</a>: manejo da água explicado com números, para o produtor decidir com segurança.</p>
    <p class="assina-clientes-titulo">Pela Benfica, já atendemos empresas como:</p>
    <ul class="clientes">{"".join(f"<li>{c}</li>" for c in clientes)}</ul>
    <div class="assina-acoes">
      {botao_zap("Falar com o Tafarel", "Olá, Tafarel! Vi o seu site e quero conversar sobre um projeto.")}
      <a class="botao botao-linha" href="{href('sobre', 0)}">Conheça minha trajetória</a>
    </div>
  </div>
</div></section>

<section class="secao"><div class="wrap">
  <h2>Perguntas comuns</h2>
  {perguntas(FAQ_HOME)}
</div></section>
{chamada("Me conte o que você quer produzir.", "Mande fotos da área pelo WhatsApp. Eu respondo pessoalmente com o próximo passo.", "Falar com o Tafarel no WhatsApp", msg)}
"""
    ld = [
        {
            "@context": "https://schema.org",
            "@type": "Person",
            "@id": DOMINIO + "/#tafarel",
            "name": "Tafarel Sá",
            "jobTitle": "Engenheiro ambiental",
            "knowsAbout": ["Qualidade da água na piscicultura", "Oxigênio dissolvido", "Amônia e nitrito em viveiros",
                           "Aquaponia", "Hidroponia", "Biotecnologia aplicada à aquicultura"],
            "affiliation": {"@type": "Organization", "name": "Biotecnal", "url": "https://www.biotecnal.ind.br"},
            "url": DOMINIO + "/",
            "sameAs": [INSTAGRAM, YOUTUBE],
            "worksFor": {
                "@type": "Organization",
                "name": "Benfica AgroEngenharia",
                "url": BENFICA_URL,
                "taxID": CNPJ,
                "address": {"@type": "PostalAddress", "streetAddress": "BR 386 KM 407",
                            "addressLocality": "Triunfo", "addressRegion": "RS", "addressCountry": "BR"},
                "telephone": "+" + ZAP,
            },
        },
        faq_ld(FAQ_HOME),
    ]
    return pagina(slug="", titulo="Piscicultura e qualidade da água no RS e SC | Eng. Tafarel Sá",
                  descricao="Qualidade da água na piscicultura: oxigênio, amônia, nitrito e lodo. Produtos Biotecnal com protocolo do Eng. Tafarel Sá, representante no RS e SC. Consultoria, aquaponia, hidroponia e estufas.",
                  corpo=corpo, msg_zap=msg, ld=ld)


# ---------------------------------------------------------------- produtos
PASSOS_ESTUFA = [
    ("Você chama no WhatsApp da Brasil Estufas",
     "Conta a cultura, as medidas da área e a cidade. Fotos do terreno ajudam muito."),
    ("Escolha do modelo",
     "Definimos juntos o modelo e o tamanho certos para a sua cultura e o vento da sua região."),
    ("Orçamento por escrito",
     "Você recebe estrutura, filme, prazo de entrega e valor."),
    ("Entrega e montagem",
     "A estufa sai de fábrica e a montagem é combinada no orçamento."),
]


def estufas():
    return pagina_produto(
        slug="estufas",
        titulo_seo="Estufas agrícolas Brasil Estufas | Representante Eng. Tafarel Sá",
        descricao="Estufas agrícolas Brasil Estufas para hortaliças, mudas, flores e aquaponia. Orçamento direto pelo WhatsApp com o representante Eng. Tafarel Sá.",
        h1="Estufas agrícolas Brasil Estufas",
        promessa="Sou representante da Brasil Estufas. Estrutura de fábrica para produzir o ano todo, com orientação de engenheiro na escolha do modelo.",
        foto=foto_slot("estufas", "Foto de estufa<br>(substituir)"),
        para_quem=[
            "Produtores de hortaliças que querem produzir o ano todo",
            "Viveiros de mudas e produção de flores",
            "Quem vai montar aquaponia e precisa da estrutura para a parte vegetal",
            "Quem já tem estufa e precisa ampliar ou trocar",
        ],
        inclui=[
            "Orientação na escolha do modelo e do tamanho",
            "Estrutura e filme plástico de fábrica",
            "Orçamento por escrito com prazo de entrega",
            "Projeto de climatização, quando a cultura pede controle de temperatura",
            "Integração com o sistema de aquaponia, se for o seu caso",
        ],
        faq=[
            ("Quanto custa uma estufa?",
             "Depende do modelo, do tamanho e da cidade de entrega. Mande as medidas da área e a cultura pelo WhatsApp e você recebe o orçamento."),
            ("Vocês entregam fora do RS?",
             "A Brasil Estufas atende o Brasil todo. O frete entra no orçamento."),
            ("Dá para usar a estufa com aquaponia?",
             f"Sim. Se for montar aquaponia, veja também a <a href=\"{href('aquaponia-comercial', 0)}\">consultoria em aquaponia</a>, que dimensiona a estufa junto com os tanques."),
        ],
        msg="Olá! Vim pelo site do Eng. Tafarel e quero orçamento de estufa Brasil Estufas. A área tem __ x __ metros, na cidade de __, e quero plantar __.",
        chamada_titulo="Quer saber quanto fica a sua estufa?",
        chamada_texto="Mande as medidas da área, a cidade e a cultura. O orçamento sai pelo WhatsApp de vendas da Brasil Estufas.",
        botao="Pedir orçamento de estufa",
        numero=ZAP_ESTUFAS,
        passos=PASSOS_ESTUFA,
    )


def tanques():
    return pagina_produto(
        slug="tanques-de-geomembrana",
        titulo_seo="Tanque de geomembrana para piscicultura e reservatório | Eng. Tafarel Sá",
        descricao="Tanques e reservatórios impermeabilizados com geomembrana Geotop: projeto, fornecimento e instalação com equipe própria e responsabilidade técnica.",
        h1="Tanques de geomembrana",
        promessa="Tanque de peixe, reservatório ou lagoa impermeabilizados com geomembrana Geotop. Eu projeto, forneço a manta e instalo com equipe própria.",
        foto=foto_slot("tanques", "Foto de tanque com geomembrana<br>(substituir)"),
        para_quem=[
            "Piscicultores que perdem água por infiltração no viveiro",
            "Quem vai construir tanque novo e quer evitar vazamento desde o início",
            "Reservatórios de água para irrigação",
            "Lagoas e bacias que precisam de estanqueidade",
        ],
        inclui=[
            "Dimensionamento do tanque e escolha da espessura da manta",
            "Orientação para o preparo do solo antes da instalação",
            "Geomembrana Geotop com procedência de fabricante",
            "Instalação e soldagem das emendas por equipe própria",
            "Teste de estanqueidade na entrega",
            "ART do engenheiro responsável",
        ],
        faq=[
            ("Qual espessura de geomembrana eu preciso?",
             "Depende do uso, do tamanho do tanque e do terreno. A espessura certa sai no projeto. Manta mais grossa que o necessário encarece sem ganho, e mais fina reduz a vida útil."),
            ("Vocês instalam em tanque que já existe?",
             "Sim. O tanque precisa ser esvaziado e o solo regularizado antes da manta. Avalio por foto ou visita."),
            ("Quanto custa?",
             "O valor depende principalmente da área de manta, que inclui fundo, taludes e ancoragem. Me mande as medidas do tanque para eu calcular."),
            ("Quanto tempo dura a geomembrana?",
             f"{pend('Confirmar vida útil e garantia Geotop por espessura')} A durabilidade depende do material, da instalação e da exposição ao sol."),
        ],
        msg="Olá, Tafarel! Vim pelo site e quero orçamento de tanque com geomembrana. Medidas aproximadas: __ x __ m, profundidade __ m.",
        chamada_titulo="Mande as medidas do seu tanque.",
        chamada_texto="Mande as medidas e a cidade. Eu respondo pessoalmente com o orçamento.",
        numero=ZAP,
    )


def links_relacionados(itens, prof=0):
    li = "".join(f'<li class="oferta"><h3>{t}</h3><p>{d}</p><a href="{href(s, prof)}">{a}</a></li>'
                 for s, t, d, a in itens)
    return f"""<section class="secao secao-branca"><div class="wrap">
  <h2>Complete a sua produção</h2>
  <ul class="ofertas">{li}</ul>
</div></section>"""


def piscicultura():
    return pagina_produto(
        slug="piscicultura",
        titulo_seo="Consultoria em piscicultura no RS | Eng. Tafarel Sá",
        descricao="Consultoria em piscicultura: qualidade da água, dimensionamento de viveiros, aeração, manejo e adequação ambiental, com o Eng. Tafarel Sá. Presencial no RS ou por vídeo.",
        h1="Consultoria em piscicultura",
        promessa="Para quem quer começar a criar peixe do jeito certo ou já produz e quer mais resultado por tanque. Presencial no RS ou por vídeo em todo o Brasil.",
        foto=foto_slot("piscicultura", "Foto de viveiros em produção<br>(substituir)"),
        para_quem=[
            "Produtores começando na piscicultura que querem evitar erro de projeto",
            "Quem já produz e tem mortalidade, crescimento lento ou água ruim",
            "Propriedades que precisam de adequação ambiental",
            "Investidores avaliando a viabilidade de um empreendimento aquícola",
        ],
        inclui=[
            "Diagnóstico da propriedade, da fonte de água e da produção atual",
            "Dimensionamento e projeto de viveiros e tanques",
            "Plano de qualidade da água, aeração e recirculação",
            "Rotina de manejo e de arraçoamento para a equipe",
            "Orientação para adequação e licenciamento ambiental",
            "Acompanhamento técnico continuado, se você quiser",
        ],
        faq=[
            ("Como é cobrada a consultoria?",
             f"{pend('Definir: diagnóstico com valor fixo, abatido se fechar o projeto?')} O formato e o valor são combinados antes de começar."),
            ("Atende propriedade pequena?",
             "Sim. O tamanho do projeto muda, mas o cuidado com água e manejo é o mesmo."),
            ("Dá para fazer por vídeo?",
             "Sim. Com fotos, vídeos e as medições da sua água, boa parte do diagnóstico é feita a distância."),
        ],
        msg="Olá, Tafarel! Quero consultoria em piscicultura. Hoje eu crio __ em __ tanques/viveiros e o meu problema é __.",
        chamada_titulo="Vamos olhar a sua produção.",
        chamada_texto="Mande fotos dos tanques e, se tiver, as últimas medições da água. Eu respondo pessoalmente.",
        botao="Pedir consultoria no WhatsApp",
        extra=bloco_youtube(0, "Aprenda antes com a série Água Boa Dá Lucro")
        + links_relacionados([
            ("loja-akso", "Medidores AKSO", "Oxímetro, pH e amônia para medir em vez de adivinhar.", "Ver medidores"),
            ("tanques-de-geomembrana", "Tanques de geomembrana", "Viveiro que não perde água, com manta Geotop.", "Ver tanques"),
            ("biotecnal", "Tratamento Biotecnal", "Água limpa e dejeto tratado com sistema biológico.", "Ver Biotecnal"),
            ("traira-e-trairao", "Traíra e trairão", "Peixe nativo para pesca esportiva e pesque-pague.", "Ver criação"),
        ]),
    )


def aquaponia():
    return pagina_produto(
        slug="aquaponia-comercial",
        titulo_seo="Consultoria em aquaponia comercial | Eng. Tafarel Sá",
        descricao="Consultoria em aquaponia comercial: estudo de viabilidade, projeto, implantação e treinamento. Peixe e hortaliça no mesmo sistema, dimensionado para vender.",
        h1="Consultoria em aquaponia",
        promessa="Peixe e hortaliça no mesmo sistema, com a água circulando entre os dois. Projetado para produzir e vender, não para hobby de quintal.",
        foto=foto_slot("aquaponia", "Foto de sistema de aquaponia<br>(substituir)"),
        para_quem=[
            "Produtores que querem duas fontes de receita na mesma área",
            "Propriedades com pouca água disponível",
            "Investidores que querem um negócio de produção de alimentos",
            "Escolas e instituições que buscam um sistema produtivo e didático",
        ],
        inclui=[
            "Estudo de viabilidade e definição da escala de produção",
            "Projeto completo: tanques, filtragem, bombeamento e bancadas",
            "Indicação da estufa Brasil Estufas certa para a parte vegetal",
            "Plano de qualidade da água e de medições",
            "Acompanhamento da partida do sistema",
            "Treinamento da equipe que vai operar",
        ],
        faq=[
            ("Aquaponia dá lucro?",
             "Pode dar, se o sistema for dimensionado para a escala certa e a produção tiver para quem vender. Por isso a consultoria começa pelo estudo de viabilidade, antes de qualquer obra."),
            ("Qual a diferença para um sistema caseiro?",
             "Escala, controle e confiabilidade. Um sistema comercial tem filtragem, aeração e bombeamento dimensionados para operar todos os dias sem perder lote."),
            ("Quero aprender antes de investir. Tem curso?",
             f"Sim. Veja os <a href=\"{href('cursos', 0)}\">cursos online e presenciais</a>."),
        ],
        msg="Olá, Tafarel! Quero consultoria em aquaponia comercial. Quero produzir __ e tenho uma área de __.",
        chamada_titulo="Quer saber se a aquaponia fecha a conta para você?",
        chamada_texto="Me conte o que quer produzir, para quem vai vender e o tamanho da área. Eu respondo pessoalmente.",
        botao="Pedir consultoria no WhatsApp",
        extra=links_relacionados([
            ("estufas", "Estufas Brasil Estufas", "A estrutura para a parte vegetal do sistema.", "Ver estufas"),
            ("loja-akso", "Medidores AKSO", "O equilíbrio da aquaponia depende de medir a água.", "Ver medidores"),
            ("cursos", "Cursos", "Aprenda o sistema antes de investir.", "Ver cursos"),
        ]),
    )


# Hidroponia Hortivinyl: sistemas pequenos. Preço de referência quando houver
# (loja Bruno Palma Hidroponia, 15/10/2026); o resto é orçamento no WhatsApp de vendas.
HIDRO_SISTEMAS = [
    ("Torre de cultivo", "12 plantas", "1,50 m de altura, base de 42 x 42 cm",
     "Torre com base, 12 vasos, bomba submersa de 20 W, mangueira, timer bivolt e kit de nutrientes.", None),
    ("Mini Bancada", "29 plantas", "1,20 x 0,80 m, 0,90 m de altura",
     "3 perfis 80x40 mm, 1 perfil 60x30 mm, travessas, colunas, irrigação, bomba de 20 W, timer bivolt e kit de nutrientes.", None),
    ("Bancada Mista 1,5 m", "70 plantas", "1,5 m, fase final e berçário na mesma bancada",
     "6 perfis 80x40 mm, 2 perfis 60x30 mm, coletor, tampas de entrada e saída, injetores e cola. Cavaletes à parte (kit com 2 cavaletes 1,5 m: R$ 214,00).", "R$ 764,00"),
    ("Bancada para Iniciantes 3 m", "cerca de 165 plantas", "1,70 x 3 m",
     "9 perfis (7 de 80x40 mm e 2 de 60x30 mm), bomba, timer, coletores, colunas, presilhas, conexões, injetores e kit de nutrientes. Reservatório de 150 a 200 L e canos à parte.", None),
    ("Bancada para Iniciantes 6 m", "cerca de 330 plantas", "1,70 x 6 m",
     "9 perfis (7 de 80x40 mm e 2 de 60x30 mm), bomba, timer, coletores, colunas, presilhas, conexões, injetores e kit de nutrientes. Reservatório de 150 a 200 L e canos à parte.", None),
]


def hidroponia():
    cards = ""
    for nome, cap, med, inclui, preco in HIDRO_SISTEMAS:
        valor = (f'<p class="preco">A partir de {preco}<small>preço de referência</small></p>' if preco
                 else '<p class="preco preco-consulta">Preço no WhatsApp</p>')
        msg_item = f"Olá! Vim pelo site do Eng. Tafarel e quero orçamento da {nome} Hortivinyl. Minha cidade é __."
        cards += f"""<article class="kit sistema">
  <h3>{nome}</h3>
  <p class="cap">{cap} · {med}</p>
  <p>{inclui}</p>
  {valor}
  {botao_zap("Pedir este sistema", msg_item, numero=ZAP_ESTUFAS)}
</article>"""
    medidores = "".join(
        f'<li><a href="{l}" target="_blank" rel="noopener sponsored">{n}</a><span>{pr}</span></li>'
        for n, pr, l in AKSO_KITS[1][2])
    extra = f"""
<section class="secao" id="sistemas"><div class="wrap">
  <h2>Sistemas pequenos Hortivinyl</h2>
  <p class="intro">Para começar em casa, no sítio ou testar antes de crescer. Perfis de PVC Hortivinyl, com garantia de 10 anos do fabricante.</p>
  <div class="kits">{cards}</div>
  <p class="nota-afiliado">Preço de referência de mercado em {AKSO_DATA}. O valor final, o frete e o prazo vêm no orçamento pelo WhatsApp.</p>
</div></section>

<section class="secao"><div class="wrap">
  <h2>Do berçário à colheita</h2>
  <div class="galeria">
    {"".join(foto_slot(f"hidroponia_galeria_{i}", "Foto (substituir)", classe="foto-provisoria foto-larga") for i in range(1, 5))}
  </div>
</div></section>

<section class="secao secao-branca"><div class="wrap">
  <h2>Meça a solução nutritiva</h2>
  <p class="intro">Na hidroponia, pH fora da faixa trava a absorção de nutrientes. O medidor de pH AKSO com as soluções de calibração resolve isso.</p>
  <article class="kit"><h3>pH completo AKSO</h3><ul>{medidores}</ul></article>
  <p class="nota-afiliado">Links de parceiro AKSO: a loja me paga uma comissão quando você compra por eles, sem custo a mais para você.</p>
</div></section>"""
    return pagina_produto(
        slug="hidroponia",
        titulo_seo="Hidroponia Hortivinyl: torre, mini bancada e bancadas para iniciantes | Eng. Tafarel Sá",
        descricao="Sistemas pequenos de hidroponia Hortivinyl: torre de cultivo, mini bancada e bancadas de 1,5 m a 6 m, com garantia de 10 anos. Orçamento pelo WhatsApp.",
        h1="Hidroponia Hortivinyl",
        promessa="Sistemas pequenos para produzir alface, temperos e folhosas sem terra. Estrutura Hortivinyl com garantia de 10 anos e orientação de engenheiro para montar.",
        foto=foto_slot("hidroponia", "Foto de bancada Hortivinyl<br>(substituir)"),
        para_quem=[
            "Quem quer produzir hortaliça em casa ou no sítio",
            "Pequenos produtores testando a hidroponia antes de investir mais",
            "Escolas e projetos sociais",
            "Quem já tem aquaponia e quer ampliar a parte vegetal",
        ],
        inclui=[
            "Estrutura Hortivinyl de fábrica, em PVC sem metais pesados",
            "Garantia de 10 anos do fabricante",
            "Orientação para escolher o tamanho certo",
            "Indicação do medidor de pH e da estufa, se precisar",
        ],
        faq=[
            ("Qual sistema escolher para começar?",
             "Para casa, a torre (12 plantas) ou a mini bancada (29 plantas). Para vender a produção, a bancada de 3 m (cerca de 165 plantas) é o primeiro passo."),
            ("O sistema precisa de estufa?",
             f"Ao ar livre funciona, mas a estufa protege da chuva e do sol forte. Veja as <a href=\"{href('estufas', 0)}\">estufas Brasil Estufas</a>."),
            ("O que não vem no kit?",
             "Nas bancadas para iniciantes, o reservatório de 150 a 200 L e os canos. Na bancada mista de 1,5 m, os cavaletes."),
        ],
        msg="Olá! Vim pelo site do Eng. Tafarel e quero orçamento de hidroponia Hortivinyl. Quero produzir __ plantas, na cidade de __.",
        chamada_titulo="Qual sistema cabe no seu espaço?",
        chamada_texto="Mande o espaço disponível e a cidade. O orçamento sai pelo WhatsApp de vendas.",
        botao="Pedir orçamento de hidroponia",
        numero=ZAP_ESTUFAS,
        passos=[
            ("Você chama no WhatsApp de vendas", "Conta o espaço disponível, a cidade e o que quer produzir."),
            ("Escolha do sistema", "Definimos juntos o tamanho certo para o seu espaço e a sua meta de produção."),
            ("Orçamento por escrito", "Você recebe o sistema, o frete e o prazo de entrega."),
            ("Entrega e montagem", "O sistema chega com as peças de encaixe. Eu oriento a montagem e a partida."),
        ],
        extra=extra,
    )



def loja_akso():
    def kit(nome, dor, itens):
        linhas = "".join(
            f'<li><a href="{l}" target="_blank" rel="noopener sponsored">{n}</a><span>{pr}</span></li>'
            for n, pr, l in itens)
        return f'<article class="kit"><h3>{nome}</h3><p>{dor}</p><ul>{linhas}</ul></article>'
    itens = "".join(kit(*k) for k in AKSO_KITS)
    msg = "Olá, Tafarel! Estou em dúvida sobre qual medidor AKSO comprar para o meu tanque."
    corpo = f"""
<section class="cabeca-pagina"><div class="wrap">
  <p class="trilha"><a href="index.html">Início</a> / Loja AKSO</p>
  <h1>Medidores AKSO para piscicultura</h1>
  <p class="promessa">Os medidores que eu uso no campo e recomendo. Você compra direto na loja oficial da AKSO, com nota e garantia do fabricante.</p>
  <div class="hero-acoes">{botao_zap("Tirar dúvida antes de comprar", msg)}</div>
</div></section>

<section class="secao"><div class="wrap">
  <h2>O que medir primeiro</h2>
  <p class="intro">Se você só puder comprar um, comece pelo oxímetro. Oxigênio baixo ao amanhecer é a causa mais comum de mortalidade.</p>
  <div class="kits">{itens}</div>
  <p class="nota-afiliado">Preços de referência da loja AKSO em {AKSO_DATA}, valores "a partir de". O preço final aparece na loja. Os links desta página são de parceiro: a AKSO me paga uma comissão quando você compra por eles, sem custo a mais para você.</p>
</div></section>

{bloco_youtube(0, "Aprenda a usar cada medição", "Na série Água Boa Dá Lucro eu mostro o que cada número quer dizer e o que fazer quando ele sai da faixa.")}
{chamada("Não sabe qual medidor serve para você?", "Me diga a espécie, o tamanho dos tanques e o que você já mede. Eu indico o kit certo.", "Tirar dúvida no WhatsApp", msg)}
"""
    return pagina(slug="loja-akso", titulo="Medidores AKSO para piscicultura | Eng. Tafarel Sá",
                  descricao="Oxímetro, medidor de pH, amônia e alcalinidade AKSO para piscicultura e aquaponia, indicados pelo Eng. Tafarel Sá. Compra direta na loja oficial.",
                  corpo=corpo, msg_zap=msg, ativo="loja-akso")


SOBRE_DADOS, SOBRE_CORPO = ler_md(CONTEUDO / "paginas" / "sobre.md")


def sobre():
    msg = "Olá, Tafarel! Vim pela página Sobre e quero conversar."
    corpo = f"""
<section class="cabeca-pagina"><div class="wrap cabeca-grade">
  <div>
    <p class="trilha"><a href="index.html">Início</a> / Sobre</p>
    <h1>{SOBRE_DADOS.get("titulo") or "Eng. Tafarel Sá"}</h1>
    <p class="promessa">{SOBRE_DADOS.get("subtitulo") or ""}</p>
    {md_html(SOBRE_CORPO)}
    <div class="hero-acoes">
      {botao_zap("Falar comigo no WhatsApp", msg)}
      <a class="botao botao-linha" href="{BENFICA_URL}">Conhecer a Benfica</a>
    </div>
  </div>
  {foto_slot("sobre_retrato", "Retrato do Tafarel<br>(substituir)")}
</div></section>

<section class="secao"><div class="wrap">
  <h2>Marcas que represento</h2>
  <ul class="ofertas">
    <li class="oferta"><h3>Brasil Estufas</h3><p>Estufas agrícolas de fábrica, com atendimento em todo o Brasil.</p><a href="{href('estufas', 0)}">Ver estufas</a></li>
    <li class="oferta"><h3>Biotecnal</h3><p>Sistemas biológicos para tratamento de água e dejetos. Representação no RS e em SC.</p><a href="{href('biotecnal', 0)}">Ver Biotecnal</a></li>
    <li class="oferta"><h3>Geotop</h3><p>Geomembranas para tanques, reservatórios e lagoas. Representação no RS, SC e PR.</p><a href="{href('tanques-de-geomembrana', 0)}">Ver tanques</a></li>
    <li class="oferta"><h3>Hortivinyl</h3><p>Perfis e sistemas de hidroponia em PVC, com garantia de 10 anos do fabricante.</p><a href="{href('hidroponia', 0)}">Ver hidroponia</a></li>
    <li class="oferta"><h3>AKSO</h3><p>Medidores de qualidade da água que eu uso e indico.</p><a href="{href('loja-akso', 0)}">Ver medidores</a></li>
  </ul>
</div></section>
"""
    ld = {"@context": "https://schema.org", "@type": "ProfilePage", "mainEntity": {
        "@type": "Person", "@id": DOMINIO + "/#tafarel", "name": "Tafarel Sá", "jobTitle": "Engenheiro ambiental",
        "url": DOMINIO + "/sobre", "sameAs": [u for u in (INSTAGRAM, YOUTUBE, FACEBOOK) if u],
        "knowsAbout": ["Qualidade da água na piscicultura", "Piscicultura", "Aquaponia", "Hidroponia",
                       "Estufas agrícolas", "Tanques de geomembrana", "Tratamento biológico de água"],
        "worksFor": {"@type": "Organization", "name": "Benfica AgroEngenharia", "url": BENFICA_URL, "taxID": CNPJ}}}
    return pagina(ld=ld, slug="sobre", titulo="Sobre o Eng. Tafarel Sá | Benfica AgroEngenharia",
                  descricao="Conheça o Eng. Tafarel Sá, fundador e responsável técnico da Benfica AgroEngenharia, em Triunfo/RS, e representante Brasil Estufas, Biotecnal e Geotop.",
                  corpo=corpo, msg_zap=msg, ativo="sobre")


def nao_encontrada():
    corpo = f"""
<section class="secao"><div class="wrap">
  <h1>Página não encontrada</h1>
  <p>O endereço pode ter mudado. Volte para o início ou fale comigo direto pelo WhatsApp.</p>
  <div class="hero-acoes"><a class="botao botao-linha" href="/">Ir para o início</a></div>
</div></section>"""
    return pagina(slug="404", titulo="Página não encontrada | Eng. Tafarel Sá",
                  descricao="Página não encontrada.", corpo=corpo, msg_zap="Olá, Tafarel! Vim pelo site.")


# ================================================================ BLOG
DATA_SITE = "2026-10-15"
FONTE_BIOTECNAL = ("Biotecnal (2025): Guia Prático Aquicultura de Resultado e boletins técnicos da linha Aqua", "https://www.biotecnal.ind.br")
FONTE_EMERSON = ("Emerson, K. et al. (1975). Aqueous ammonia equilibrium calculations: effect of pH and temperature. Journal of the Fisheries Research Board of Canada, 32, 2379–2383",
                 "https://doi.org/10.1139/f75-274")
FONTE_PEIXEBR = ("Anuário Peixe BR 2025, via Notícias Agrícolas: piscicultura brasileira cresce 9,2% e alcança 968,7 mil toneladas",
                 "https://www.noticiasagricolas.com.br/noticia/395317")

def carregar_artigos():
    """Cada arquivo em conteudo/blog/*.md é um artigo. O nome do arquivo é o endereço (slug)."""
    artigos = []
    for arq in sorted((CONTEUDO / "blog").glob("*.md")):
        try:
            d, corpo = ler_md(arq)
        except Exception as erro:  # um artigo com erro não derruba o site inteiro
            print(f"AVISO: artigo {arq.name} ignorado por erro no cabeçalho: {erro}")
            continue
        if d.get("rascunho"):
            continue
        artigos.append({
            "slug": arq.stem,
            "titulo": d.get("titulo") or arq.stem,
            "descricao": d.get("descricao") or "",
            "data": str(d.get("data") or DATA_SITE),
            "resposta": d.get("resposta") or "",
            "ep": d.get("episodio") or None,
            "foto": (d.get("foto") or "").lstrip("/"),
            "foto_legenda": d.get("foto_legenda") or "",
            "whatsapp": d.get("whatsapp") or "vendas",
            "produtos": [p for p in (d.get("produtos") or []) if p in PROD or p in ROTULO_EXTRA],
            "faq": [(q.get("pergunta"), q.get("resposta")) for q in (d.get("perguntas") or []) if q.get("pergunta")],
            "fontes": [(f.get("texto"), f.get("link") or None) for f in (d.get("fontes") or []) if f.get("texto")],
            "corpo": md_html(corpo),
            "categoria": d.get("categoria") or "dicas-tecnicas",
            "leitura": max(1, round(len((corpo + " " + str(d.get("resposta") or "") + " " +
                                       " ".join(str(q.get("resposta") or "") for q in (d.get("perguntas") or []))).split()) / 180)),
        })
    artigos.sort(key=lambda a: (a["data"], a["categoria"] == "cases"), reverse=True)  # no mesmo dia, case vem primeiro
    return artigos


MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]


def rfc822(iso):
    from datetime import datetime, timezone, timedelta
    from email.utils import format_datetime
    try:
        d = datetime.fromisoformat(iso[:10]).replace(hour=12, tzinfo=timezone(timedelta(hours=-3)))
    except Exception:
        d = datetime.now(timezone.utc)
    return format_datetime(d)


def data_legivel(iso):
    try:
        a, m, d = (int(x) for x in iso[:10].split("-"))
        return f"{d} de {MESES[m - 1]} de {a}"
    except Exception:
        return iso


def post_page(a):
    numero = ZAP  # tudo no portal Água Boa Dá Lucro vai para o WhatsApp do Tafarel
    msg = f"Olá, Tafarel! Li no Água Boa Dá Lucro o artigo \"{a['titulo']}\" e quero conversar sobre o meu caso."
    def rotulo(s):
        info = PROD.get(s) or ROTULO_EXTRA[s]
        link = href("biotecnal-" + s, 1) if s in PROD else href("biotecnal", 1) + "#qualidade-agua"
        img = RAIZ / "assets" / "biotecnal" / f"{s}.jpg"
        foto = (f'<img src="../assets/biotecnal/{s}.jpg" alt="Embalagem do {info["nome"]} da Biotecnal" loading="lazy" decoding="async">'
                if img.exists() else f'<span class="rotulo-sem-foto" aria-hidden="true">{info["nome"]}</span>')
        msg_p = f"Olá, Tafarel! Li o artigo \"{a['titulo']}\" e quero saber sobre o {info['nome']}."
        return (f'<article class="rotulo"><a class="rotulo-img" href="{link}">{foto}</a>'
                f'<div class="rotulo-txt"><p class="card-cat">{info["tipo"]}</p><h3>{info["nome"]}</h3>'
                f'<p>{info["resumo"]}</p>'
                f'<p class="rotulo-acoes"><a href="{link}">Ver ficha</a>'
                f'<a href="{zap_link(msg_p, ZAP)}" target="_blank" rel="noopener">Pedir no WhatsApp</a></p></div></article>')
    prods = "".join(rotulo(s) for s in a["produtos"])
    titulo_prods = "Produtos usados neste case" if a["categoria"] == "cases" else "Produtos citados"
    rel = sorted((o for o in ARTIGOS if o["slug"] != a["slug"]),
                 key=lambda o: (o["categoria"] != a["categoria"], -len(set(o["produtos"]) & set(a["produtos"]))))[:3]
    outros = "".join(card_artigo(o, 1) for o in rel)
    fontes = "".join((f'<li><a href="{u}" target="_blank" rel="noopener">{n}</a></li>' if u else f'<li>{n}</li>')
                     for n, u in a["fontes"])
    ep = (f'<p class="post-meta">{a["ep"]} · <a href="{YOUTUBE}" target="_blank" rel="noopener">assistir no YouTube</a></p>'
          if a.get("ep") else "")
    corpo = f"""
<article class="secao secao-branca"><div class="wrap artigo">
  <p class="trilha"><a href="../index.html">Início</a> / <a href="index.html">{PORTAL}</a> / <a href="categoria/{a['categoria']}.html">{CAT.get(a['categoria'], ('Dicas técnicas',))[0]}</a></p>
  <h1>{a['titulo']}</h1>
  <p class="post-meta">Por <a href="../sobre.html">Eng. Tafarel Sá</a> · {data_legivel(a['data'])} · {a['leitura']} min de leitura</p>
  {ep}
  {f'<figure class="post-foto"><img src="../{a["foto"]}" alt="{html.escape(a["foto_legenda"] or a["titulo"])}" decoding="async">' + (f'<figcaption>{a["foto_legenda"]}</figcaption>' if a["foto_legenda"] else '') + '</figure>' if a["foto"] else ''}
  <div class="resposta-rapida"><p><strong>Resposta rápida:</strong> {a['resposta']}</p></div>
  {a['corpo']}
  {('<h2>Perguntas frequentes</h2>' + perguntas(a['faq'])) if a['faq'] else ''}
  {('<h2>Fontes</h2><ul class="fontes">' + fontes + '</ul>') if fontes else ''}
  {caixa_autor(1)}
  <div class="hero-acoes">{botao_zap("Falar sobre o meu caso no WhatsApp", msg, numero=numero)}
  <a class="botao botao-linha" href="../projeto.html">Contar meu projeto</a></div>
</div></article>

{f'''<section class="secao"><div class="wrap">
  <h2>{titulo_prods}</h2>
  <div class="rotulos">{prods}</div>
</div></section>''' if prods else ''}

<section class="secao secao-branca"><div class="wrap">
  <h2>Continue lendo</h2>
  <div class="cards">{outros}</div>
</div></section>
{bloco_cadastro(1)}
{CADASTRO_JS}
"""
    ld = [
        {"@context": "https://schema.org", "@type": "BlogPosting", "headline": a["titulo"],
         "description": a["descricao"], "datePublished": a["data"], "dateModified": a["data"],
         **({"image": f"{DOMINIO}/{a['foto']}"} if a["foto"] else {}),
         "inLanguage": "pt-BR", "mainEntityOfPage": f"{DOMINIO}/blog/{a['slug']}",
         "author": {"@type": "Person", "@id": DOMINIO + "/#tafarel", "name": "Tafarel Sá",
                    "jobTitle": "Engenheiro ambiental", "url": DOMINIO + "/sobre"},
         "publisher": {"@type": "Organization", "name": "Benfica AgroEngenharia", "url": BENFICA_URL},
         "citation": [u or n for n, u in a["fontes"]]},
        faq_ld(a["faq"]),
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Início", "item": DOMINIO + "/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": DOMINIO + "/blog/"},
            {"@type": "ListItem", "position": 3, "name": a["titulo"]}]},
    ]
    return pagina(slug="blog/" + a["slug"], titulo=a["titulo"] + " | Eng. Tafarel Sá",
                  descricao=a["descricao"], corpo=corpo, prof=1, msg_zap=msg, ld=ld, ativo="blog/", zap_numero=numero)


# ================================================================ QUALIDADE DA ÁGUA + BIOTECNAL
# Fonte técnica: fichas técnicas Biotecnal Agro (set/2026) e base técnica do Tafarel.
# Itens marcados "A CONFIRMAR" na base técnica (pH 8,5 no choque, alcalinidade 20 mg/L,
# tabela emergencial do Oxitrat, doses de choque) NÃO são publicados: ficam para o diagnóstico.

AUTOR_BIO = ("Engenheiro ambiental, fundador da Benfica AgroEngenharia e representante técnico-comercial "
             "da Biotecnal no Rio Grande do Sul e em Santa Catarina. Apresenta a série Água Boa Dá Lucro no YouTube.")

REFERENCIAS = [
    # parâmetro, faixa, frequência, link do artigo
    ("Oxigênio dissolvido", "3 a 6 mg/L", "Diária, ao amanhecer", "oxigenio-dissolvido-piscicultura"),
    ("Amônia total", "abaixo de 0,5 mg/L", "Diária", "amonia-na-piscicultura"),
    ("Nitrito", "abaixo de 0,5 mg/L", "Semanal", "nitrito-na-piscicultura"),
    ("pH", "6 a 9; ideal 7,5 a 8,0", "Diária", "alcalinidade-e-ph-na-piscicultura"),
    ("Alcalinidade total", "acima de 50 mg/L", "Semanal", "alcalinidade-e-ph-na-piscicultura"),
    ("Temperatura", "25 a 28 °C (tilápia)", "Diária", "chuva-forte-e-inversao-termica"),
]

BIO_PRODUTOS = [
    {"slug": "oxitrat", "nome": "OXITRAT", "tipo": "Oxigênio em pó",
     "resumo": "Fonte de oxigênio e estabilizador de pH para viveiros em hipóxia, no transporte de peixes e na manutenção da qualidade da água.",
     "ativo": "Percarbonato de sódio, bicarbonato de sódio e agente potencializador",
     "acao": "Libera oxigênio de forma gradual por toda a coluna d'água, do fundo à superfície, e ajusta alcalinidade e pH.",
     "indicacao": ["Hipóxia e oxigênio emergencial", "Madrugadas críticas, chuva forte e inversão térmica", "Oxigênio no transporte de peixes", "Manutenção da qualidade da água"],
     "dose": "0,25 a 1,0 g por m³ de água, conforme a demanda de oxigênio e a biomassa. Manutenção: 0,5 g por m³ ao dia, a lanço (num viveiro de 1 ha com 1,5 m de profundidade, cerca de 7,5 kg por dia). No transporte, a dose sai da biomassa transportada.",
     "apresentacao": "Blister metálico de 1 kg e baldes de 3, 5, 10 e 20 kg", "validade": "24 meses",
     "registro": "Uso profissional, industrial (CRQ/PR 09.200.672)",
     "dica": "A asfixia em massa acontece de madrugada, quando não dá tempo de comprar. O Oxitrat tem que estar estocado no barracão antes da crise."},
    {"slug": "bactrat-p", "nome": "BACTRAT P", "tipo": "Modulador biológico",
     "resumo": "Consórcio de Bacillus e bactéria láctica que degrada a matéria orgânica e o lodo do fundo e mantém a água estável no ciclo inteiro.",
     "ativo": "Bacillus subtilis, B. licheniformis, B. amyloliquefaciens, B. cereus e Lactococcus lactis, com mais de 1 bilhão de microrganismos por grama",
     "acao": "As bactérias benéficas consomem o lodo e os resíduos orgânicos, o que evita a formação de amônia e reduz a necessidade de renovar água.",
     "indicacao": ["Excesso de lodo no fundo", "Água turva", "Água verde (eutrofização)", "Prevenção de amônia ao longo do ciclo"],
     "dose": "0,2 g por kg de ração fornecida ao viveiro, diariamente, a lanço sobre a maior área possível.",
     "apresentacao": "Baldes de 2 kg e 10 kg (em pacotes de 1 kg) e pouch de 1 kg e 2,5 kg, com copos dosadores de 5 g e 30 g", "validade": "18 meses",
     "registro": "Cadastrado no MAPA sob o nº 341/13 SEFIP/DDA/SFA-PR",
     "dica": "Deixe o aerador ligado pelo menos 2 horas antes e 2 horas depois da aplicação."},
    {"slug": "nutrat-aqua-plus", "nome": "NUTRAT AQUA PLUS", "tipo": "Bioestimulador e biossurfactante",
     "resumo": "Líquido à base de extrato de levedura que dispersa a matéria orgânica, gera microbolhas e acelera a oxidação de amônia e nitrito.",
     "ativo": "Extrato de levedura Saccharomyces cerevisiae livre de células, fitotensoativo e adjuvantes",
     "acao": "Reduz a tensão superficial da água, o que forma microbolhas e melhora a entrada de oxigênio. Também estimula a microbiota benéfica a decompor a matéria orgânica.",
     "indicacao": ["Amônia e nitrito altos", "Oxigênio baixo", "Carga orgânica elevada", "Água verde (eutrofização)"],
     "dose": "Manutenção em tanques escavados: 500 a 1.000 mL por hectare de lâmina d'água (ou por 10.000 m³), uma vez por semana. Amônia e nitrito altos, carga orgânica elevada ou eutrofização: 1 L por hectare, durante uma semana ou até regularizar. Diluir em água e aplicar perto dos aeradores.",
     "apresentacao": "Frasco de 1 L, galão de 5 L e bombona de 20 L", "validade": "18 meses",
     "registro": "Resolução Conama nº 463/2014",
     "dica": "Dilua sempre em água e aplique perto dos aeradores. Dose grande de uma vez pode soltar matéria orgânica do fundo: divida em aplicações menores."},
    {"slug": "bactrat-aquanitro", "nome": "BACTRAT AQUANITRO", "tipo": "Modulador biológico nitrificante",
     "resumo": "Consórcio de bactérias nitrificantes que oxida a amônia e o nitrito em viveiros e tanques aerados.",
     "ativo": "Bactérias nitrificantes selecionadas e enzimas auxiliares do metabolismo do nitrogênio",
     "acao": "Forma um biofilme nitrificante que transforma amônia em nitrito e nitrito em nitrato, a forma menos tóxica para o peixe.",
     "indicacao": ["Amônia alta em tanque aerado", "Acúmulo de nitrito", "Partida de sistemas de recirculação e aquaponia"],
     "dose": "Choque: 1,0 kg por 1.000 m² de lâmina d'água. Manutenção: 500 g por 1.000 m², uma vez por semana, ou conforme balanço de massa.",
     "apresentacao": "Baldes de 2 kg e 30 kg", "validade": "18 meses",
     "registro": "Ibama Portaria nº 241; Resolução Conama nº 463",
     "dica": "Bactéria nitrificante precisa de oxigênio e alcalinidade para trabalhar. Sem aeração, o produto não rende."},
    {"slug": "bactrat-aquatech", "nome": "BACTRAT AQUATECH", "tipo": "Modulador biológico de lodo",
     "resumo": "Consórcio de microrganismos e enzimas que estabiliza o lodo e o sedimento de tanques escavados, viveiros sem geomembrana e sistemas de recirculação.",
     "ativo": "Bacillus spp. selecionados, actinomicetos e bactérias oxidantes de enxofre, com enzimas hidrolíticas; mais de 1 bilhão de microrganismos por grama",
     "acao": "As enzimas quebram a matéria orgânica acumulada no fundo e as bactérias consomem o que sobra. O lodo para de crescer e o fundo deixa de soltar gases.",
     "indicacao": ["Tanque escavado com muito lodo", "Viveiro sem geomembrana", "Recirculação (RAS) e reprodutores com carga orgânica alta", "Cheiro de ovo podre no fundo (gás sulfídrico)"],
     "dose": "Aclimatação: 50 g por 1.000 m² por semana, nas 2 primeiras semanas. Manutenção: 5 g por saca de 25 kg de ração. Choque: 100 g por 1.000 m² e depois 0,5 g por kg de ração por 10 dias. A lanço, de manhã e com aeração, nas zonas de maior acúmulo de lodo.",
     "apresentacao": "Baldes de 2 kg e 10 kg e bombona de 30 kg", "validade": "18 meses",
     "registro": "Ficha técnica Biotecnal Agro (setembro de 2026)",
     "dica": "Aplique onde o lodo se acumula: perto do comedouro e do dreno. O aerador ligado é o que leva o oxigênio para as bactérias trabalharem no fundo."},
    {"slug": "bioflow-aqua", "nome": "BIOFLOW AQUA", "tipo": "Floculante e adensador de bioflocos",
     "resumo": "Floculante à base de lignossulfonatos que clarifica a água e adensa os flocos microbianos em sistemas de bioflocos (BFT).",
     "ativo": "Lignossulfonatos, adjuvantes e veículo; sólidos entre 6% e 9%",
     "acao": "Junta as partículas em suspensão em flocos maiores, que descem para o fundo. A água clareia e, no bioflocos, os flocos ficam mais firmes e fáceis de controlar.",
     "indicacao": ["Água turva por sólidos em suspensão", "Bioflocos com flocos soltos ou excesso de sólidos", "Clarificação antes de despesca ou transferência"],
     "dose": "Definida pelo técnico responsável: na clarificação, pela turbidez e pelos sólidos suspensos totais; nos bioflocos, pelos sólidos sedimentáveis medidos em cone Imhoff.",
     "apresentacao": "Galão de 5 kg, bombona de 25 kg e contentor IBC de 1.100 kg", "validade": "24 meses",
     "registro": "Anvisa INF-022/2016 e Resolução Conama nº 463/2014",
     "dica": "No bioflocos, meça os sólidos sedimentáveis no cone Imhoff antes de aplicar. A dose sai desse número, não do olho."},
]

BIO_LINHA_COMPLEMENTAR = [
    ("Bicarbonato de sódio", "Alcalinizante", "Grau alimentício, origem mineral, pureza mínima de 99%. Corrige a alcalinidade e estabiliza o pH do viveiro. Saco de 25 kg."),
    ("Algitrat", "Controle de algas", "Sulfato de cobre a 25% para algas e cianofíceas, até 3 mL por m³. Cobre é sensível em água de baixa alcalinidade: só com orientação técnica."),
    ("Bacsteril", "Desinfetante", "Quaternário de amônio de amplo espectro para instalações, tanques, veículos e utensílios. 1 L rende 2.000 L de solução."),
    ("Aqua-Clean", "Saneante e removedor de biofilme", "Peróxido de hidrogênio a 50% com prata. Remove biofilme de tubulações e desinfeta sistemas de água. Registro Anvisa."),
    ("Sanibel e Clim 90 (TCCA)", "Desinfecção com cloro", "Ácido tricloroisocianúrico com 90% de cloro ativo, em tabletes de 20 g e 200 g, para reservatórios, tanques e caixas d'água."),
    ("Tiossulfato de sódio", "Neutralizador de cloro", "Elimina o cloro residual antes do povoamento: 5 mg de tiossulfato para cada mg de cloro livre."),
]

# Portfólio completo Biotecnal Agro (Fichas Técnicas, setembro de 2026)
BIO_DIVISOES = [
    ("Sanidade e ambiência", "Moduladores biológicos que estabilizam camas e dejetos e reduzem amônia, moscas e patógenos nas criações.",
     [("Bactrat BC", "bovinos de corte em confinamento"), ("Bactrat BL", "bovinos de leite em Compost Barn e Free Stall"),
      ("Bactrat AP", "aves de postura"), ("Bactrat S", "suinocultura, todas as fases"), ("Bactrat CA", "camas de equinos, ovinos e caprinos")]),
    ("Resíduos e efluentes", "Bioestimuladores, enzimas e adsorventes para estações de tratamento, biodigestores e compostagem.",
     [("Enzipro WP", "lagoas e biorreatores"), ("Enzipro Anaero", "biodigestores e reatores anaeróbios"),
      ("Nutrat S", "efluentes com óleos e gorduras"), ("Nutrat HB", "metais pesados e efluentes tóxicos"),
      ("Bactrat Compostrat", "compostagem de resíduos e carcaças")]),
    ("Água potável e de processo", "Coagulante, sequestrante e corretivos para estações de tratamento de água e efluentes.",
     [("Organotrat 100", "coagulante orgânico de origem vegetal"), ("Econox", "sequestrante e anti-incrustante para água potável")]),
]

# Matriz problema → solução. Só as indicações "altamente indicado" da base técnica.
MATRIZ = [
    ("Amônia alta", "amonia-na-piscicultura", ["nutrat-aqua-plus", "bactrat-aquanitro"]),
    ("Nitrito alto", "nitrito-na-piscicultura", ["bactrat-aquanitro", "nutrat-aqua-plus"]),
    ("Oxigênio baixo ao amanhecer", "oxigenio-dissolvido-piscicultura", ["oxitrat", "nutrat-aqua-plus"]),
    ("Peixe boquejando ou morrendo", "chuva-forte-e-inversao-termica", ["oxitrat"]),
    ("Excesso de lodo no fundo", "lodo-e-materia-organica", ["bactrat-p", "bactrat-aquatech"]),
    ("Água turva", "lodo-e-materia-organica", ["bactrat-p", "bioflow-aqua"]),
    ("Água verde demais", "lodo-e-materia-organica", ["bactrat-p", "nutrat-aqua-plus"]),
]

PROD = {p["slug"]: p for p in BIO_PRODUTOS}
# Insumos sem página própria que podem aparecer como rótulo nos artigos e cases
ROTULO_EXTRA = {
    "bicarbonato-de-sodio": {"nome": "BICARBONATO DE SÓDIO", "tipo": "Insumo alcalinizante",
        "resumo": "Grau alimentício, origem mineral, pureza mínima de 99%. Eleva e estabiliza a alcalinidade e o pH da água de cultivo. Saco de 25 kg.",
    },
}
ARTIGOS = carregar_artigos()


def link_prod(slug, prof=0):
    return f'<a href="{href("biotecnal-" + slug, prof)}">{PROD[slug]["nome"]}</a>'


def tabela_referencia(prof=0):
    linhas = "".join(
        f'<tr><td><a href="{href("blog/" + a, prof)}">{p}</a></td><td>{f}</td><td>{q}</td></tr>'
        for p, f, q, a in REFERENCIAS)
    return f"""<div class="tabela-rolagem"><table class="tabela">
<caption>Valores de referência para tilápia em viveiro escavado</caption>
<thead><tr><th scope="col">Parâmetro</th><th scope="col">Faixa ideal</th><th scope="col">Quando medir</th></tr></thead>
<tbody>{linhas}</tbody></table></div>"""


def tabela_matriz(prof=0):
    linhas = "".join(
        f'<tr><td><a href="{href("blog/" + a, prof)}">{prob}</a></td>'
        f'<td>{", ".join(link_prod(s, prof) for s in prods)}</td></tr>'
        for prob, a, prods in MATRIZ)
    return f"""<div class="tabela-rolagem"><table class="tabela">
<caption>Qual produto Biotecnal resolve cada problema</caption>
<thead><tr><th scope="col">O que você está vendo</th><th scope="col">Produto mais indicado</th></tr></thead>
<tbody>{linhas}</tbody></table></div>"""


def caixa_autor(prof=0):
    return f"""<aside class="autor">
  <div class="autor-sigla" aria-hidden="true">TS</div>
  <div><p class="autor-nome">Eng. Tafarel Sá</p><p>{AUTOR_BIO}</p>
  <p><a href="{href('sobre', prof)}">Sobre o autor</a> · <a href="{YOUTUBE}" target="_blank" rel="noopener">Canal no YouTube</a></p></div>
</aside>"""


MSG_BIO = "Olá, Tafarel! Vim pelo site e quero um protocolo Biotecnal para a minha água. Problema: __. Área do viveiro: __ m²."


def qualidade_agua():
    cards = "".join(
        f'<li class="oferta"><h3>{p["nome"]}</h3><p>{p["tipo"]}. {p["resumo"]}</p>'
        f'<a href="{href("biotecnal-" + p["slug"], 0)}">Ver produto</a></li>' for p in BIO_PRODUTOS)
    artigos = "".join(
        f'<li><a href="{href("blog/" + a["slug"], 0)}">{a["titulo"]}</a></li>' for a in ARTIGOS)
    faq = [
        ("Quais parâmetros da água devo medir na piscicultura?",
         "Oxigênio dissolvido, pH e temperatura todos os dias; amônia diariamente em sistemas intensivos; nitrito e alcalinidade uma vez por semana. O oxigênio deve ser medido ao amanhecer, quando está no ponto mais baixo."),
        ("Qual o oxigênio ideal para tilápia?",
         "Entre 3 e 6 mg/L. Abaixo de 3 mg/L o peixe come menos, cresce menos e fica mais sujeito a doença."),
        ("Qual o nível máximo de amônia?",
         "A amônia total deve ficar abaixo de 0,5 mg/L. A parte tóxica (amônia não ionizada) aumenta quando o pH e a temperatura sobem."),
        ("Como melhorar a qualidade da água do viveiro?",
         "Medindo primeiro e corrigindo a causa: aeração bem posicionada, ração na medida, controle do lodo com bactérias benéficas e oxigênio de reserva para emergências."),
    ]
    corpo = f"""
<section class="cabeca-pagina"><div class="wrap">
  <p class="trilha"><a href="index.html">Início</a> / Qualidade da água</p>
  <h1>Qualidade da água na piscicultura</h1>
  <p class="promessa">Água boa dá lucro. Peixe em água ruim come, mas não converte: a ração vira amônia, o lote cresce devagar e a mortalidade aparece de madrugada.</p>
  <div class="resposta-rapida"><p><strong>Resumo:</strong> meça oxigênio, pH e temperatura todos os dias, amônia e nitrito com frequência e alcalinidade toda semana. Mantenha o oxigênio entre 3 e 6 mg/L, a amônia e o nitrito abaixo de 0,5 mg/L e a alcalinidade acima de 50 mg/L. Quando algum número sair da faixa, corrija a causa antes que vire mortalidade.</p></div>
  <div class="hero-acoes">
    <a class="botao botao-zap" href="{href('calculadora', 0)}#diagnostico">Fazer o diagnóstico da minha água</a>
    {botao_zap("Pedir protocolo no WhatsApp", MSG_BIO, extra="botao-linha", numero=ZAP)}
  </div>
</div></section>

<section class="secao"><div class="wrap">
  <h2>Os números que importam</h2>
  <p class="intro">Faixas de trabalho que eu uso em campo para tilápia em viveiro escavado no Sul do Brasil. Clique em cada parâmetro para entender o que ele causa e como corrigir.</p>
  {tabela_referencia(0)}
</div></section>

<section class="secao secao-branca"><div class="wrap">
  <h2>Medir: o primeiro passo</h2>
  <div class="duas-colunas">
    <div>
      <p>Sem medir, todo manejo é chute. O mínimo é um oxímetro e um medidor de pH. Para sistemas intensivos, entram os testes de amônia, nitrito e alcalinidade.</p>
      <p>Uso e indico os medidores AKSO, com calibração e suporte no Brasil.</p>
      <p><a class="botao botao-linha" href="{href('loja-akso', 0)}">Ver os medidores AKSO</a></p>
    </div>
    <ol class="etapas claro">
      <li><div><strong>Oxigênio ao amanhecer</strong><p>É a hora em que ele está no ponto mais baixo do dia.</p></div></li>
      <li><div><strong>pH e temperatura junto</strong><p>Os dois definem quanto da amônia é tóxica.</p></div></li>
      <li><div><strong>Anote tudo</strong><p>Uma planilha simples mostra a tendência antes da crise.</p></div></li>
    </ol>
  </div>
</div></section>

<section class="secao"><div class="wrap">
  <h2>Corrigir: problema e solução</h2>
  <p class="intro">Produtos da linha Aqua da Biotecnal, empresa de biotecnologia de Toledo/PR, com fabricação própria desde 2007. Sou representante técnico da Biotecnal no RS e em SC.</p>
  {tabela_matriz(0)}
  <ul class="ofertas" style="margin-top:32px">{cards}</ul>
</div></section>

<section class="secao secao-branca"><div class="wrap">
  <h2>Guias completos</h2>
  <ul class="lista-artigos">{artigos}</ul>
</div></section>

{bloco_youtube(0)}

<section class="secao"><div class="wrap">
  <h2>Perguntas comuns</h2>
  {perguntas(faq)}
  {caixa_autor(0)}
</div></section>
{chamada("Sua água está fora da faixa?", "Mande as medições e a área do viveiro. Eu monto o protocolo Biotecnal para o seu caso.", "Pedir protocolo no WhatsApp", MSG_BIO, ZAP)}
"""
    ld = [faq_ld(faq), {
        "@context": "https://schema.org", "@type": "Article",
        "headline": "Qualidade da água na piscicultura: valores de referência, como medir e como corrigir",
        "author": {"@id": DOMINIO + "/#tafarel"}, "inLanguage": "pt-BR",
        "dateModified": DATA_SITE, "about": "Qualidade da água em viveiros de piscicultura"}]
    return pagina(slug="qualidade-da-agua",
                  titulo="Qualidade da água na piscicultura: valores ideais e como corrigir | Eng. Tafarel Sá",
                  descricao="Oxigênio, amônia, nitrito, pH e alcalinidade: valores de referência para tilápia, como medir e como corrigir com produtos Biotecnal. Guia do Eng. Tafarel Sá.",
                  corpo=corpo, msg_zap=MSG_BIO, ld=ld, ativo="qualidade-da-agua", zap_numero=ZAP)



def biotecnal():
    cards = "".join(
        f'<article class="kit produto-bio"><p class="tipo">{p["tipo"]}</p><h3>{p["nome"]}</h3><p>{p["resumo"]}</p>\n'
        f'<ul class="lista-check">{"".join(f"<li>{i}</li>" for i in p["indicacao"])}</ul>\n'
        f'<a class="botao botao-linha" href="{href("biotecnal-" + p["slug"], 0)}">Ver ficha e uso</a></article>'
        for p in BIO_PRODUTOS)
    comp = "".join(
        f'<li class="oferta"><h3>{n}</h3><p><strong>{t}.</strong> {d}</p>'
        f'<a href="{zap_link("Olá, Tafarel! Vim pelo site e quero saber sobre o " + n + " da Biotecnal.", ZAP)}" target="_blank" rel="noopener">Perguntar</a></li>'
        for n, t, d in BIO_LINHA_COMPLEMENTAR)
    divs = "".join(
        f'<article class="divisao"><h3>{n}</h3><p>{d}</p><ul>'
        + "".join(f"<li><strong>{pn}</strong>: {pu}</li>" for pn, pu in itens)
        + f'</ul><a href="{zap_link("Olá, Tafarel! Vim pelo site e quero saber sobre a linha " + n.lower() + " da Biotecnal.", ZAP)}" target="_blank" rel="noopener">Perguntar sobre esta linha</a></article>'
        for n, d, itens in BIO_DIVISOES)
    faq = [
        ("O que é a Biotecnal?",
         "Uma indústria de biotecnologia de Toledo/PR, ativa desde 2007, que fabrica produtos biológicos e químicos para aquicultura, produção animal e tratamento de água e efluentes."),
        ("Os produtos biológicos fazem mal ao peixe?",
         "Não. O Bactrat P e o Bactrat Aquanitro são bactérias benéficas que já existem na natureza, selecionadas e concentradas. Eles competem com as bactérias ruins e consomem a matéria orgânica que vira amônia."),
        ("Qual produto usar primeiro?",
         "Depende do problema. Para prevenção ao longo do ciclo, o Bactrat P na ração. Para oxigênio baixo ou emergência, o Oxitrat. Para amônia e nitrito, o Nutrat Aqua Plus e o Bactrat Aquanitro. O certo é medir a água e montar o protocolo."),
        ("Vocês atendem fora do RS e SC?",
         "Sou representante técnico no RS e em SC. Para outros estados, eu te coloco em contato com a equipe da Biotecnal da sua região."),
    ]
    corpo = f"""
<section class="cabeca-pagina"><div class="wrap">
  <p class="trilha"><a href="index.html">Início</a> / Biotecnal</p>
  <h1>Biotecnal no RS e em SC</h1>
  <p class="promessa">Biotecnologia para a água da piscicultura: bactérias benéficas, bioestimulador, floculante e oxigênio em pó para prevenir e resolver amônia, nitrito, lodo e falta de oxigênio. E o portfólio completo Biotecnal Agro para criação animal e efluentes. Representante técnico no RS e em SC.</p>
  <div class="hero-acoes">
    {botao_zap("Pedir protocolo para o meu viveiro", MSG_BIO, numero=ZAP)}
    <a class="botao botao-linha" href="{href('calculadora', 0)}">Calcular as doses de manutenção</a>
  </div>
</div></section>

<section class="secao"><div class="wrap">
  <h2>Qual produto para cada problema</h2>
  <p class="intro">O diagnóstico vem da medição. Com o número na mão, a escolha é direta.</p>
  {tabela_matriz(0)}
</div></section>

<section class="secao secao-branca"><div class="wrap">
  <h2>Linha Aqua: aquicultura</h2>
  <div class="kits">{cards}</div>
</div></section>

<section class="secao"><div class="wrap cabeca-grade">
  <div>
    <h2>Por dentro da Biotecnal</h2>
    <p>Indústria de biotecnologia em Toledo/PR desde 2007, com registros no IBAMA, na ANVISA e no Ministério da Agricultura. A linha Aqua parte de uma ideia simples: tratar a água é tão importante quanto tratar os animais.</p>
    <ul class="selos">
      <li><strong>ISO 9001:2015</strong><span>Gestão da qualidade</span></li>
      <li><strong>ISO 14001</strong><span>Gestão ambiental</span></li>
      <li><strong>CRQ 9ª Região</strong><span>Responsável técnico (ART)</span></li>
      <li><strong>Licença sanitária</strong><span>Em dia</span></li>
    </ul>
    <div class="hero-acoes">
      <a class="botao botao-linha" href="{href('blog/biotecnal-quem-fabrica-a-linha-aqua', 0)}">Conhecer a Biotecnal</a>
      <a class="botao botao-linha" href="{href('seja-revenda-biotecnal', 0)}">Seja revenda no RS e SC</a>
    </div>
  </div>
  <img class="foto" src="assets/biotecnal/produtos-linha-aqua.jpg" alt="Linha Aqua Biotecnal: Nutrat Aqua Plus, Bactrat P e Oxitrat" loading="lazy" decoding="async">
</div></section>

<section class="secao" id="qualidade-agua"><div class="wrap">
  <h2>Qualidade de água e biosseguridade</h2>
  <p class="intro">Alcalinidade, algas, desinfecção e cloro. Uso conforme orientação técnica.</p>
  <ul class="ofertas">{comp}</ul>
</div></section>

<section class="secao secao-branca" id="portfolio"><div class="wrap">
  <h2>Portfólio completo Biotecnal Agro</h2>
  <p class="intro">Além da aquicultura, a Biotecnal tem linhas para criação animal, efluentes e tratamento de água. Também atendo essas linhas no RS e em SC.</p>
  <div class="divisoes">{divs}</div>
  <p class="nota-afiliado">Fonte: Fichas Técnicas Biotecnal Agro, setembro de 2026. Dose e aplicação definidas com o técnico para cada caso.</p>
</div></section>

<section class="secao secao-escura"><div class="wrap">
  <h2>Como funciona o atendimento</h2>
  {etapas([
      ("Você manda as medições", "Oxigênio, pH, amônia, nitrito, temperatura, a área e a profundidade do viveiro. Fotos da água ajudam."),
      ("Eu monto o protocolo", "Produto, dose, horário de aplicação e o que medir nos dias seguintes, por escrito."),
      ("Pedido e entrega", "O produto sai da Biotecnal, em Toledo/PR, direto para a sua propriedade."),
      ("Acompanhamento", "Conferimos juntos as medições até a água voltar para a faixa."),
  ])}
</div></section>

<section class="secao"><div class="wrap">
  <h2>Perguntas comuns</h2>
  {perguntas(faq)}
  {caixa_autor(0)}
</div></section>
{chamada("Vamos tratar a sua água?", "Mande as medições e o problema. O protocolo sai pelo WhatsApp.", "Pedir protocolo no WhatsApp", MSG_BIO, ZAP)}
"""
    ld = [faq_ld(faq), {
        "@context": "https://schema.org", "@type": "ItemList", "name": "Linha Aqua Biotecnal",
        "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{DOMINIO}/biotecnal-{p['slug']}", "name": p["nome"]}
                            for i, p in enumerate(BIO_PRODUTOS)]}]
    return pagina(slug="biotecnal",
                  titulo="Biotecnal no RS e SC: linha Aqua e portfólio Biotecnal Agro",
                  descricao="Produtos Biotecnal para piscicultura no RS e SC: Oxitrat, Bactrat P, Aquanitro, Aquatech, Bioflow e Nutrat Aqua Plus. Protocolo e venda com o Eng. Tafarel Sá.",
                  corpo=corpo, msg_zap=MSG_BIO, ld=ld, ativo="biotecnal", zap_numero=ZAP)

def produto_bio(p):
    msg = f"Olá, Tafarel! Vim pelo site e quero comprar {p['nome']} da Biotecnal. Área do viveiro: __ m². Problema: __."
    artigos_rel = [a for a in ARTIGOS if p["slug"] in a.get("produtos", [])]
    rel = "".join(f'<li><a href="{href("blog/" + a["slug"], 0)}">{a["titulo"]}</a></li>' for a in artigos_rel)
    faq = [
        (f"Para que serve o {p['nome']}?", f"{p['resumo']} {p['acao']}"),
        (f"Qual a dose do {p['nome']}?", f"Pela ficha técnica: {p['dose']} Em situação de crise, o protocolo é definido a partir das medições da água."),
        (f"Onde comprar {p['nome']} no RS e em SC?", "Com o Eng. Tafarel Sá, representante técnico da Biotecnal. O pedido é feito pelo WhatsApp e sai de fábrica para a sua propriedade."),
    ]
    corpo = f"""
<section class="cabeca-pagina"><div class="wrap">
  <p class="trilha"><a href="index.html">Início</a> / <a href="{href('biotecnal', 0)}">Biotecnal</a> / {p['nome']}</p>
  <p class="tipo">{p['tipo']}</p>
  <h1>{p['nome']}</h1>
  <p class="promessa">{p['resumo']}</p>
  <div class="hero-acoes">{botao_zap(f"Comprar {p['nome']}", msg, numero=ZAP)}</div>
  {f'<img class="produto-img" src="assets/biotecnal/{p["slug"]}.jpg" alt="Embalagem do {p["nome"]} da Biotecnal" decoding="async">' if (RAIZ / "assets" / "biotecnal" / (p["slug"] + ".jpg")).exists() else ""}
</div></section>

<section class="secao"><div class="wrap duas-colunas">
  <div>
    <h2>Como age</h2>
    <p>{p['acao']}</p>
    <h3>Quando usar</h3>
    <ul class="lista-check">{"".join(f"<li>{i}</li>" for i in p['indicacao'])}</ul>
    <div class="resposta-rapida"><p><strong>Dica de campo:</strong> {p['dica']}</p></div>
  </div>
  <div>
    <h2>Ficha técnica</h2>
    <dl class="ficha">
      <dt>Composição</dt><dd>{p['ativo']}</dd>
      <dt>Dose de uso (ficha)</dt><dd>{p['dose']}</dd>
      <dt>Apresentações</dt><dd>{p['apresentacao']}</dd>
      <dt>Validade</dt><dd>{p['validade']} a partir da fabricação</dd>
      <dt>Registro</dt><dd>{p['registro']}</dd>
      <dt>Fabricante</dt><dd>Biotecnal Ltda., Toledo/PR</dd>
    </dl>
    <p class="nota-afiliado">Doses do Guia Prático Aquicultura de Resultado e das Fichas Técnicas Biotecnal Agro (setembro de 2026). Protocolo de choque só com diagnóstico da água.</p>
  </div>
</div></section>

{f'<section class="secao secao-branca"><div class="wrap"><h2>Leia antes de aplicar</h2><ul class="lista-artigos">{rel}</ul></div></section>' if rel else ''}

<section class="secao"><div class="wrap">
  <h2>Perguntas comuns</h2>
  {perguntas(faq)}
</div></section>
{chamada(f"Quer {p['nome']} com o protocolo certo?", "Mande a área do viveiro e as últimas medições. Eu indico a dose e a forma de aplicar.", f"Comprar {p['nome']}", msg, ZAP)}
"""
    ld = [faq_ld(faq), {
        "@context": "https://schema.org", "@type": "Product", "name": p["nome"],
        "description": p["resumo"], "category": p["tipo"],
        "brand": {"@type": "Brand", "name": "Biotecnal"},
        "manufacturer": {"@type": "Organization", "name": "Biotecnal Ltda.", "url": "https://www.biotecnal.ind.br"}}]
    return pagina(slug="biotecnal-" + p["slug"],
                  titulo=f"{p['nome']} Biotecnal: {p['tipo'].lower()} para piscicultura | Eng. Tafarel Sá",
                  descricao=f"{p['nome']} da Biotecnal: {p['resumo']} Dose, apresentações e onde comprar no RS e SC.",
                  corpo=corpo, msg_zap=msg, ld=ld, ativo="biotecnal", zap_numero=ZAP)


CALC_JS = r"""
<script>
(function () {
  var f = document.getElementById('calc');
  if (!f) return;
  var fmt = function (n, d) { return n.toLocaleString('pt-BR', {maximumFractionDigits: d === undefined ? 1 : d}); };
  function calcular() {
    var area = parseFloat(f.area.value.replace(',', '.')) || 0;
    var prof = parseFloat(f.prof.value.replace(',', '.')) || 0;
    var racao = parseFloat(f.racao.value.replace(',', '.')) || 0;
    var prob = f.problema.value;
    var vol = area * prof;
    var ha = area / 10000;
    var bactrat = racao * 0.2;               // g/dia (0,2 g por kg de ração)
    var nutMin = ha * 500, nutMax = ha * 1000; // mL/semana (500 a 1.000 mL por ha, ficha set/26)
    var oxi = vol * 0.5 / 1000; // kg/dia (0,5 g por m³ ao dia, ficha set/26)
    var aquanitro = area / 1000 * 500;       // g/semana
    document.getElementById('r-vol').textContent = fmt(vol, 0) + ' m³';
    document.getElementById('r-bac').textContent = racao ? fmt(bactrat) + ' g por dia' : 'informe a ração diária';
    document.getElementById('r-nut').textContent = area ? fmt(nutMin, 0) + ' a ' + fmt(nutMax, 0) + ' mL por semana' : 'informe a área';
    document.getElementById('r-oxi').textContent = vol ? (oxi >= 1 ? fmt(oxi) + ' kg' : fmt(oxi * 1000, 0) + ' g') + ' por dia' : 'informe área e profundidade';
    document.getElementById('r-aqn').textContent = (aquanitro >= 1000 ? fmt(aquanitro / 1000) + ' kg' : fmt(aquanitro, 0) + ' g') + ' por semana';
    var ind = f.problema.selectedOptions[0].getAttribute('data-ind') || '';
    var box = document.getElementById('r-prob');
    box.hidden = !ind;
    box.querySelector('span').textContent = ind;
    var msg = 'Olá, Tafarel! Usei a calculadora do site. Viveiro de ' + fmt(area, 0) + ' m², ' + fmt(prof) +
      ' m de profundidade (' + fmt(vol, 0) + ' m³), ' + fmt(racao) + ' kg de ração por dia.' +
      (prob ? ' Problema: ' + prob + '.' : '') + ' Quero o protocolo Biotecnal.';
    document.getElementById('r-zap').href = 'https://wa.me/' + f.getAttribute('data-zap') + '?text=' + encodeURIComponent(msg);
  }
  f.addEventListener('input', calcular);
  f.addEventListener('submit', function (e) { e.preventDefault(); calcular(); });
  calcular();
})();
</script>"""

DIAG_JS = r"""
<script>
(function(){
  var f=document.getElementById('diag'); if(!f) return;
  var out=document.getElementById('diag-res'), btn=document.getElementById('diag-zap');
  function v(id){var x=document.getElementById(id).value.replace(',','.').trim();return x===''?null:parseFloat(x);}
  function nh3(tan,ph,t){var pka=0.09018+2729.92/(t+273.15);return tan/(1+Math.pow(10,pka-ph));}
  function fmt(n,d){return n.toFixed(d).replace('.',',');}
  function item(n,t,x){return '<li class="d-'+n+'"><strong>'+t+'</strong><span>'+x+'</span></li>';}
  function calc(e){
    if(e) e.preventDefault();
    var od=v('d-od'),ph=v('d-ph'),t=v('d-t'),tan=v('d-tan'),no2=v('d-no2'),alc=v('d-alc');
    var L=[],prod={},res=[];
    if(od!==null){res.push('oxigênio '+fmt(od,1)+' mg/L');
      if(od<2){L.push(item('ruim','Oxigênio crítico ('+fmt(od,1)+' mg/L)','Risco de mortalidade nas próximas horas. Ligue toda a aeração e suspenda a ração.'));prod['OXITRAT']=1;}
      else if(od<3){L.push(item('alerta','Oxigênio baixo ('+fmt(od,1)+' mg/L)','Abaixo de 3 mg/L o peixe come menos e cresce menos.'));prod['OXITRAT']=1;prod['NUTRAT AQUA PLUS']=1;}
      else L.push(item('ok','Oxigênio na faixa ('+fmt(od,1)+' mg/L)','Se não mediu ao amanhecer, repita nesse horário: é quando ele fica mais baixo.'));}
    if(ph!==null){res.push('pH '+fmt(ph,1));
      if(ph<6||ph>9)L.push(item('alerta','pH fora da faixa ('+fmt(ph,1)+')','A faixa é 6 a 9, ideal 7,5 a 8,0. pH alto aumenta a amônia tóxica; pH baixo costuma vir com alcalinidade baixa.'));
      else L.push(item('ok','pH na faixa ('+fmt(ph,1)+')','Dentro de 6 a 9.'));}
    if(t!==null){res.push(fmt(t,0)+' °C');}
    if(tan!==null){res.push('amônia total '+fmt(tan,2)+' mg/L');
      var txt='';
      if(ph!==null){var tt=(t===null?27:t),x=nh3(tan,ph,tt);
        txt=' Com pH '+fmt(ph,1)+' e '+fmt(tt,0)+' °C'+(t===null?' (temperatura estimada)':'')+', cerca de '+fmt(x,3)+' mg/L está na forma tóxica (NH₃)'+(x>=0.05?', acima do limite de 0,05 mg/L.':'.');}
      if(tan>=2){L.push(item('ruim','Amônia muito alta ('+fmt(tan,2)+' mg/L)','Corte a ração e fale comigo antes de aplicar qualquer produto.'+txt));prod['NUTRAT AQUA PLUS']=1;prod['BACTRAT AQUANITRO']=1;}
      else if(tan>=0.5){L.push(item('alerta','Amônia acima da faixa ('+fmt(tan,2)+' mg/L)','A amônia total deve ficar abaixo de 0,5 mg/L.'+txt));prod['NUTRAT AQUA PLUS']=1;prod['BACTRAT AQUANITRO']=1;prod['BACTRAT P']=1;}
      else L.push(item((txt.indexOf('acima')>0)?'alerta':'ok','Amônia total na faixa ('+fmt(tan,2)+' mg/L)','Abaixo de 0,5 mg/L.'+txt));}
    if(no2!==null){res.push('nitrito '+fmt(no2,2)+' mg/L');
      if(no2>=0.5){L.push(item('ruim','Nitrito alto ('+fmt(no2,2)+' mg/L)','Risco de doença do sangue marrom. Sinal de nitrificação incompleta, quase sempre com oxigênio baixo.'));prod['BACTRAT AQUANITRO']=1;prod['NUTRAT AQUA PLUS']=1;}
      else L.push(item('ok','Nitrito na faixa ('+fmt(no2,2)+' mg/L)','Abaixo de 0,5 mg/L.'));}
    if(alc!==null){res.push('alcalinidade '+fmt(alc,0)+' mg/L');
      if(alc<20)L.push(item('ruim','Alcalinidade muito baixa ('+fmt(alc,0)+' mg/L)','O pH fica instável e as bactérias nitrificantes perdem força. Corrija antes do resto.'));
      else if(alc<50)L.push(item('alerta','Alcalinidade baixa ('+fmt(alc,0)+' mg/L)','A referência é acima de 50 mg/L. A nitrificação consome cerca de 7 mg/L de alcalinidade por mg/L de amônia.'));
      else L.push(item('ok','Alcalinidade boa ('+fmt(alc,0)+' mg/L)','Acima de 50 mg/L.'));}
    if(!L.length){out.innerHTML='<p>Preencha pelo menos um valor.</p>';btn.hidden=true;return;}
    var p=Object.keys(prod), h='<ul class="d-lista">'+L.join('')+'</ul>';
    if(p.length) h+='<div class="resposta-rapida"><p><strong>Produtos Biotecnal para esse quadro:</strong> '+p.join(', ')+'. A dose depende do volume e da biomassa: eu monto o protocolo com você.</p></div>';
    out.innerHTML=h;
    btn.href='https://wa.me/'+btn.getAttribute('data-num')+'?text='+encodeURIComponent('Olá, Tafarel! Fiz o diagnóstico da água no site. Meus números: '+res.join('; ')+'. Quero o protocolo Biotecnal.');
    btn.hidden=false;
  }
  f.addEventListener('submit',calc);
})();
</script>"""


def bloco_diagnostico():
    campos = [("d-od", "Oxigênio dissolvido", "mg/L", "3,5"), ("d-ph", "pH", "", "8,2"),
              ("d-t", "Temperatura", "°C", "27"), ("d-tan", "Amônia total", "mg/L", "1,0"),
              ("d-no2", "Nitrito", "mg/L", "0,1"), ("d-alc", "Alcalinidade", "mg/L", "40")]
    inputs = "".join(
        f'<div><label for="{i}">{n}{(" <small>" + u + "</small>") if u else ""}</label>'
        f'<input id="{i}" inputmode="decimal" autocomplete="off" placeholder="ex.: {ph}"></div>'
        for i, n, u, ph in campos)
    return f"""<section class="secao secao-branca" id="diagnostico"><div class="wrap">
  <h2>Diagnóstico rápido da água</h2>
  <p class="intro">Digite as medições que você tem, mesmo que sejam só algumas. O diagnóstico compara com as faixas de referência e calcula quanto da amônia está na forma tóxica, pelo pH e pela temperatura (equação de Emerson, 1975). Nada é salvo: os números só saem daqui se você enviar pelo WhatsApp.</p>
  <div class="calc-grade">
    <form id="diag" class="calc" novalidate>
      <div class="diag-campos">{inputs}</div>
      <button class="botao botao-linha" type="submit">Ver diagnóstico</button>
    </form>
    <div class="calc-resultado" aria-live="polite">
      <div id="diag-res"><p>O resultado aparece aqui. Sem medidor? Veja os <a href="loja-akso.html">kits AKSO</a>.</p></div>
      <a id="diag-zap" class="botao botao-zap" href="#" data-num="{ZAP}" target="_blank" rel="noopener" hidden>{ICONE_ZAP}Enviar o diagnóstico e pedir o protocolo</a>
    </div>
  </div>
</div></section>{DIAG_JS}"""


def calculadora():
    opcoes = '<option value="">Só manutenção, sem problema agora</option>' + "".join(
        f'<option value="{prob}" data-ind="{", ".join(PROD[s]["nome"] for s in prods)}">{prob}</option>'
        for prob, _, prods in MATRIZ)
    corpo = f"""
<section class="cabeca-pagina"><div class="wrap">
  <p class="trilha"><a href="index.html">Início</a> / Calculadora</p>
  <h1>Calculadora de manejo da água</h1>
  <p class="promessa">Informe o tamanho do viveiro e a ração do dia para ver as doses de manutenção da linha Biotecnal. Tem medições da água? <a href="#diagnostico">Faça o diagnóstico rápido</a> logo abaixo.</p>
</div></section>

<section class="secao"><div class="wrap calc-grade">
  <form id="calc" class="calc" data-zap="{ZAP}" novalidate>
    <label for="area">Área de lâmina d'água (m²)</label>
    <input id="area" name="area" inputmode="decimal" value="5000">
    <label for="prof">Profundidade média (m)</label>
    <input id="prof" name="prof" inputmode="decimal" value="1,5">
    <label for="racao">Ração fornecida por dia (kg)</label>
    <input id="racao" name="racao" inputmode="decimal" value="100">
    <label for="problema">Algum problema agora?</label>
    <select id="problema" name="problema">{opcoes}</select>
  </form>
  <div class="calc-resultado" aria-live="polite">
    <p class="calc-vol">Volume de água: <strong id="r-vol"></strong></p>
    <dl class="ficha">
      <dt>{link_prod('bactrat-p')} · prevenção de amônia e lodo</dt><dd id="r-bac"></dd>
      <dt>{link_prod('nutrat-aqua-plus')} · manutenção</dt><dd id="r-nut"></dd>
      <dt>{link_prod('oxitrat')} · manutenção</dt><dd id="r-oxi"></dd>
      <dt>{link_prod('bactrat-aquanitro')} · manutenção</dt><dd id="r-aqn"></dd>
    </dl>
    <div class="resposta-rapida" id="r-prob" hidden><p><strong>Mais indicado para o seu problema:</strong> <span></span>. A dose de correção depende das medições: peça o protocolo.</p></div>
    <p class="nota-afiliado">Doses de manutenção da ficha técnica Biotecnal. Não usar para crise: em emergência de oxigênio, amônia ou nitrito, o protocolo é feito a partir das medições.</p>
    <a id="r-zap" class="botao botao-zap" href="#" target="_blank" rel="noopener">{ICONE_ZAP}Enviar meus números e pedir o protocolo</a>
  </div>
</div></section>

{bloco_diagnostico()}

<section class="secao"><div class="wrap">
  <h2>Faixas de referência</h2>
  {tabela_referencia(0)}
</div></section>
{CALC_JS}
"""
    return pagina(slug="calculadora",
                  titulo="Calculadora de manejo e diagnóstico da água para piscicultura | Eng. Tafarel Sá",
                  descricao="Calcule as doses de manutenção Biotecnal pela área e pela ração, e faça o diagnóstico da água: oxigênio, pH, amônia tóxica (NH3), nitrito e alcalinidade.",
                  corpo=corpo, msg_zap=MSG_BIO, ativo="calculadora", zap_numero=ZAP,
                  ld={"@context": "https://schema.org", "@type": "WebApplication", "name": "Calculadora de manejo e diagnóstico da água",
                      "applicationCategory": "UtilitiesApplication", "operatingSystem": "Web", "inLanguage": "pt-BR",
                      "offers": {"@type": "Offer", "price": "0", "priceCurrency": "BRL"},
                      "author": {"@id": DOMINIO + "/#tafarel"}})


def traira():
    msg = "Olá, Tafarel! Quero criar traíra/trairão. Objetivo: __ (pesca esportiva, pesque-pague ou venda). Área disponível: __. Cidade: __."
    msg_guia = "Olá, Tafarel! Quero receber o guia de criação de traíra e trairão."
    faq = [
        ("Dá para criar traíra em viveiro?",
         "Dá. O ponto crítico é a alimentação: traíra e trairão são carnívoros e precisam ser condicionados a comer ração ainda alevinos. Com isso resolvido, a criação segue a lógica de qualquer viveiro: água, densidade e manejo."),
        ("Traíra come ração?",
         f"Come, se for condicionada no berçário. No estudo de Luz e colegas (2002), o condicionamento levou a sobrevivência dos alevinos de trairão de 27,5% para 96,7%. Veja o <a href=\"{href('blog/condicionamento-alimentar-do-trairao', 0)}\">artigo completo</a>."),
        ("Qual a diferença entre traíra e trairão?",
         "Os dois são do gênero Hoplias. A traíra é menor e muito comum nos açudes e rios do Sul. O trairão cresce bem mais, o que o torna o preferido de quem busca peixe grande para a pesca esportiva."),
        ("Precisa de licença para criar traíra?",
         "A piscicultura precisa de regularização ambiental, como qualquer criação de peixe. As exigências mudam por estado e por porte. Na consultoria eu oriento o caminho."),
    ]
    corpo = f"""
<section class="cabeca-pagina"><div class="wrap">
  <p class="trilha"><a href="index.html">Início</a> / <a href="{href('piscicultura', 0)}">Piscicultura</a> / Traíra e trairão</p>
  <h1>Criação de traíra e trairão</h1>
  <p class="promessa">Peixe nativo, valorizado na pesca esportiva e nos pesque-pague. Pouca gente sabe criar, e é aí que está a oportunidade.</p>
  <div class="resposta-rapida"><p><strong>Resumo:</strong> traíra e trairão são predadores. O segredo da criação é o condicionamento alimentar no berçário, que ensina o alevino a comer ração. Depois disso, o que define o resultado é a classificação por tamanho, contra o canibalismo, e a qualidade da água.</p></div>
  <div class="hero-acoes">
    {botao_zap("Quero criar traíra ou trairão", msg)}
    {botao_zap("Receber o guia de criação", msg_guia, extra="botao-linha")}
  </div>
</div></section>

<section class="secao"><div class="wrap">
  <h2>Para quem é</h2>
  <ul class="ofertas">
    <li class="oferta"><h3>Pesque-pague e pesca esportiva</h3><p>Trairão grande no lago atrai o pescador esportivo, que paga pela experiência e volta.</p></li>
    <li class="oferta"><h3>Produtor que quer diversificar</h3><p>Um peixe nativo, com mercado próprio e pouca concorrência, ao lado da tilápia.</p></li>
    <li class="oferta"><h3>Açude e lazer na propriedade</h3><p>Repovoar o açude e ter peixe esportivo para a família e os amigos.</p></li>
  </ul>
</div></section>

<section class="secao secao-branca"><div class="wrap duas-colunas">
  <div>
    <h2>O que muda em relação à tilápia</h2>
    <ul class="lista-check">
      <li><strong>Alimentação:</strong> carnívoro, precisa de condicionamento para aceitar ração.</li>
      <li><strong>Canibalismo:</strong> lote desuniforme vira lote menor. Classificar por tamanho é rotina.</li>
      <li><strong>Berçário:</strong> a fase que decide o negócio. Ambiente controlado, pouca luz e água limpa.</li>
      <li><strong>Água:</strong> a traíra tolera melhor água ruim que muitos peixes, mas alevino em condicionamento não. Oxigênio alto e fundo limpo fazem diferença na sobrevivência.</li>
    </ul>
  </div>
  <div>
    <h2>Como eu ajudo</h2>
    {etapas([
        ("Projeto do berçário e dos viveiros", "Dimensionamento, tanques de geomembrana e aeração para a escala que você quer."),
        ("Protocolo de condicionamento", "Da ração úmida para a seca, com classificação e rotina de manejo."),
        ("Plano de água", "Medições, Biotecnal para o fundo e oxigênio de reserva para o transporte."),
        ("Acompanhamento", "Do primeiro lote até a rotina andar sozinha."),
    ], claro=True)}
  </div>
</div></section>

<section class="secao"><div class="wrap">
  <h2>Produtos e serviços que entram na criação</h2>
  <ul class="ofertas">
    <li class="oferta"><h3>Tanques de geomembrana</h3><p>Berçário e viveiro que não perdem água.</p><a href="{href('tanques-de-geomembrana', 0)}">Ver tanques</a></li>
    <li class="oferta"><h3>BACTRAT P</h3><p>Fundo limpo e menos amônia, com dose pela ração do dia.</p><a href="{href('biotecnal-bactrat-p', 0)}">Ver produto</a></li>
    <li class="oferta"><h3>OXITRAT</h3><p>Oxigênio em pó para o transporte de alevinos e para emergências.</p><a href="{href('biotecnal-oxitrat', 0)}">Ver produto</a></li>
    <li class="oferta"><h3>Medidores AKSO</h3><p>Oxigênio, pH e amônia medidos, e não adivinhados.</p><a href="{href('loja-akso', 0)}">Ver medidores</a></li>
  </ul>
</div></section>

<section class="secao secao-branca"><div class="wrap">
  <h2>Perguntas comuns</h2>
  {perguntas(faq)}
  {caixa_autor(0)}
</div></section>
{chamada("Quer começar a sua criação de traíra?", "Me conte o objetivo, a área e a cidade. Eu respondo pessoalmente com o próximo passo.", "Falar com o Tafarel no WhatsApp", msg)}
"""
    ld = [faq_ld(faq)]
    return pagina(slug="traira-e-trairao",
                  titulo="Criação de traíra e trairão: condicionamento, berçário e manejo | Eng. Tafarel Sá",
                  descricao="Como criar traíra e trairão para pesca esportiva e pesque-pague: condicionamento alimentar, berçário, canibalismo e qualidade da água. Consultoria do Eng. Tafarel Sá.",
                  corpo=corpo, msg_zap=msg, ld=ld, ativo="piscicultura")


CURSO_MODULOS = [
    ("Introdução à aquaponia", "A história da técnica, o que ela é, as vantagens, para quem serve e para quem não serve."),
    ("Aquaponia amadora e comercial", "Os tipos de sistema e por que o sistema de quintal não escala para vender."),
    ("Módulo 1: Método AquaHortis", "A visão geral do método de aquaponia lucrativa que eu uso nos projetos."),
    ("O que plantar para vender", "Foco em hortaliças com possibilidade de processamento, como os temperos, e nichos de mercado: alfaces gourmet e mini hortaliças."),
    ("Peixes e juvenis", "A opção de produzir os próprios juvenis com mais controle."),
    ("Qualidade da água no sistema", "O que medir, com que frequência e como corrigir sem matar as plantas nem os peixes."),
]


def cursos():
    msg = "Olá, Tafarel! Quero entrar na lista de espera do curso Aquaponia Comercial."
    mods = "".join(f"<li><div><strong>{t}</strong><p>{d}</p></div></li>" for t, d in CURSO_MODULOS)
    faq = [
        ("Preciso saber hidroponia ou piscicultura antes?", "Não. O curso começa do conceito e vai até o sistema comercial."),
        ("O curso serve para quem quer só um sistema em casa?", "O foco é aquaponia comercial, para vender. Quem quer começar pequeno também aproveita, mas o método é pensado para dar lucro."),
        ("Quando abrem as turmas?", "As turmas estão sendo montadas. Quem está na lista de espera é avisado primeiro e tem condição de lançamento."),
    ]
    corpo = f"""
<section class="cabeca-pagina"><div class="wrap">
  <p class="trilha"><a href="index.html">Início</a> / Cursos</p>
  <h1>Curso Aquaponia Comercial</h1>
  <p class="promessa">Método AquaHortis: aquaponia pensada para vender, com quem projeta e instala esses sistemas no campo. Online e presencial.</p>
  <div class="resposta-rapida"><p><strong>Aquaponia</strong> é a produção que integra o cultivo de plantas sem solo (hidroponia) com a criação de peixes em um sistema de recirculação de água, como define James Rakocy, referência mundial no tema. O peixe aduba a planta e a planta limpa a água do peixe.</p></div>
  <div class="hero-acoes">{botao_zap("Entrar na lista de espera", msg)}</div>
</div></section>

<section class="secao"><div class="wrap duas-colunas">
  <div>
    <h2>Por que este curso existe</h2>
    <p>A maioria dos cursos de aquaponia ensina a montar um sistema de quintal. Bonito, mas não paga a conta. Este curso nasceu dos projetos comerciais que eu faço: o que plantar para vender, como dimensionar e como operar sem perder lote.</p>
    <h3>Para quem é</h3>
    <ul class="lista-check">
      <li>Produtor que quer duas receitas na mesma área</li>
      <li>Quem tem pouca água ou pouca terra</li>
      <li>Quem vai investir em aquaponia e quer errar no papel, não na obra</li>
      <li>Técnicos e estudantes que querem trabalhar com o tema</li>
    </ul>
  </div>
  <div>
    <h2>O que você vai aprender</h2>
    <ol class="etapas claro">{mods}</ol>
  </div>
</div></section>

<section class="secao secao-branca"><div class="wrap duas-colunas">
  <div class="curso">
    <h2>Online</h2>
    <p>Aulas gravadas para assistir no seu ritmo, de qualquer lugar do Brasil.</p>
    <div class="hero-acoes">{botao_zap("Quero o curso online", "Olá, Tafarel! Quero entrar na lista de espera do curso Aquaponia Comercial ONLINE.")}</div>
  </div>
  <div class="curso">
    <h2>Presencial</h2>
    <p>Prática em sistema funcionando, no RS: montagem, medições de água, manejo e colheita.</p>
    <div class="hero-acoes">{botao_zap("Quero o curso presencial", "Olá, Tafarel! Quero entrar na lista de espera do curso Aquaponia Comercial PRESENCIAL. Sou da cidade de __.")}</div>
  </div>
</div></section>

<section class="secao"><div class="wrap">
  <h2>Perguntas comuns</h2>
  {perguntas(faq)}
  {caixa_autor(0)}
</div></section>

{bloco_youtube(0, "Enquanto isso, comece pelo YouTube", "A série Água Boa Dá Lucro é gratuita e cobre a base de qualidade de água que o curso aprofunda.")}
"""
    ld = [faq_ld(faq), {
        "@context": "https://schema.org", "@type": "Course", "name": "Aquaponia Comercial: Método AquaHortis",
        "description": "Curso de aquaponia comercial online e presencial com o Eng. Tafarel Sá.",
        "inLanguage": "pt-BR",
        "provider": {"@type": "Organization", "name": "Benfica AgroEngenharia", "url": BENFICA_URL}}]
    return pagina(slug="cursos", titulo="Curso Aquaponia Comercial: Método AquaHortis | Eng. Tafarel Sá",
                  descricao="Curso de aquaponia comercial online e presencial com o Eng. Tafarel Sá: o que plantar para vender, dimensionamento, peixes e qualidade da água. Entre na lista de espera.",
                  corpo=corpo, msg_zap=msg, ld=ld, ativo="cursos")


# ---------------------------------------------------------------- contar meu projeto
# Cada tipo: rótulo, descrição, para qual WhatsApp vai (venda = Brasil, consultoria = Tafarel), perguntas.
# Pergunta: (id, rótulo, tipo, opções ou placeholder)
PROJETO_TIPOS = [
    ("agua", "Água do viveiro", "Amônia, oxigênio, lodo, mortalidade. Protocolo Biotecnal.", "consultoria", [
        ("area", "Área de lâmina d'água (m²)", "texto", "ex.: 5000"),
        ("especie", "Peixe", "opcoes", ["Tilápia", "Peixe nativo", "Traíra/trairão", "Outro"]),
        ("problema", "O que está acontecendo?", "opcoes", ["Amônia ou nitrito alto", "Oxigênio baixo / peixe boquejando", "Lodo, água turva ou verde demais", "Mortalidade", "Só quero prevenir"]),
        ("medicoes", "Medições que você tem (opcional)", "texto", "ex.: OD 2,5; pH 8,4; amônia 1,0"),
    ]),
    ("estufa", "Estufa", "Brasil Estufas para hortaliças, mudas, flores ou aquaponia.", "venda", [
        ("medidas", "Medidas da área (m x m)", "texto", "ex.: 8 x 30"),
        ("cultura", "O que vai plantar?", "texto", "ex.: alface, morango, mudas"),
        ("ja_tem", "Já tem estufa?", "opcoes", ["Não, é a primeira", "Sim, quero ampliar", "Sim, quero trocar"]),
    ]),
    ("hidroponia", "Hidroponia", "Sistemas Hortivinyl, da torre à bancada de 6 m.", "venda", [
        ("plantas", "Quantas plantas quer produzir?", "opcoes", ["Até 30 (casa)", "30 a 200", "200 a 1.000", "Mais de 1.000"]),
        ("objetivo", "Para quê?", "opcoes", ["Consumo próprio", "Vender a produção", "Escola ou projeto"]),
    ]),
    ("tanque", "Tanque de geomembrana", "Viveiro, reservatório ou revestimento de tanque que perde água.", "consultoria", [
        ("medidas", "Medidas (comprimento x largura x profundidade)", "texto", "ex.: 20 x 10 x 1,5 m"),
        ("uso", "Uso", "opcoes", ["Peixe", "Reservatório de água", "Efluente/lagoa", "Outro"]),
        ("existe", "O tanque já está escavado?", "opcoes", ["Sim", "Não", "Existe e perde água"]),
    ]),
    ("piscicultura", "Projeto de piscicultura", "Começar a criar peixe ou melhorar a produção.", "consultoria", [
        ("fase", "Em que fase você está?", "opcoes", ["Ainda vou começar", "Já produzo e quero melhorar", "Tenho problema agora"]),
        ("tamanho", "Tamanho (viveiros, área ou produção)", "texto", "ex.: 3 viveiros de 2.000 m²"),
        ("especie", "Peixe", "opcoes", ["Tilápia", "Peixe nativo", "Traíra/trairão", "Ainda não sei"]),
    ]),
    ("aquaponia", "Aquaponia comercial", "Peixe e hortaliça no mesmo sistema, para vender.", "consultoria", [
        ("area", "Área disponível (m²)", "texto", "ex.: 300"),
        ("vender", "Já sabe para quem vai vender?", "opcoes", ["Sim, já tenho clientes", "Tenho uma ideia", "Ainda não"]),
    ]),
    ("traira", "Traíra e trairão", "Criação para pesca esportiva, pesque-pague ou venda.", "consultoria", [
        ("objetivo", "Objetivo", "opcoes", ["Pesque-pague / pesca esportiva", "Vender peixe", "Açude da propriedade"]),
        ("estrutura", "Estrutura que você tem", "texto", "ex.: 1 açude de 1 ha"),
    ]),
    ("curso", "Curso", "Aquaponia comercial, online ou presencial.", "consultoria", [
        ("formato", "Formato", "opcoes", ["Online", "Presencial", "Tanto faz"]),
    ]),
]

PROJETO_JS = r"""
<script>
(function(){
  var f=document.getElementById('projeto'); if(!f) return;
  var cfg=JSON.parse(document.getElementById('projeto-cfg').textContent);
  var saida=document.getElementById('p-msg'), btn=document.getElementById('p-enviar'), dest=document.getElementById('p-destino');
  function tipo(){var r=f.querySelector('input[name=tipo]:checked');return r?r.value:null;}
  function val(el){if(el.type==='radio'){return el.checked?el.value:null;}return el.value.trim()||null;}
  function montar(){
    var t=tipo();
    f.querySelectorAll('.p-grupo').forEach(function(g){g.hidden=(g.getAttribute('data-tipo')!==t);});
    document.getElementById('p-comum').hidden=!t;
    if(!t){saida.textContent='Escolha acima o que você quer fazer.';btn.setAttribute('aria-disabled','true');btn.removeAttribute('href');dest.textContent='';return;}
    var c=cfg[t], linhas=[c.saudacao,'','*'+c.rotulo+'*'];
    var g=f.querySelector('.p-grupo[data-tipo="'+t+'"]');
    c.perguntas.forEach(function(p){
      var v=null;
      g.querySelectorAll('[name="'+t+'-'+p[0]+'"]').forEach(function(el){var x=val(el);if(x)v=x;});
      if(v) linhas.push('• '+p[1].replace(/ \(opcional\)/,'')+': '+v);
    });
    ['nome','cidade','prazo','detalhe'].forEach(function(k){
      var v=null; f.querySelectorAll('[name="c-'+k+'"]').forEach(function(el){var x=val(el);if(x)v=x;});
      var rot={nome:'Nome',cidade:'Cidade',prazo:'Quando quer começar',detalhe:'Mais detalhes'}[k];
      if(v) linhas.push('• '+rot+': '+v);
    });
    linhas.push('','Posso mandar fotos e vídeos da área aqui na conversa.');
    var msg=linhas.join('\n');
    saida.textContent=msg;
    btn.href='https://wa.me/'+c.numero+'?text='+encodeURIComponent(msg);
    btn.removeAttribute('aria-disabled');
    dest.textContent=c.destino;
  }
  f.addEventListener('input',montar); f.addEventListener('change',montar);
  f.querySelectorAll('input[name=tipo]').forEach(function(r){r.addEventListener('change',function(){
    var g=f.querySelector('.p-grupo[data-tipo="'+r.value+'"]'); if(g) setTimeout(function(){g.scrollIntoView({behavior:'smooth',block:'start'});},50);});});
  btn.addEventListener('click',function(e){if(btn.getAttribute('aria-disabled')){e.preventDefault();f.querySelector('input[name=tipo]').focus();}});
  var pre=(location.hash||'').replace('#','');
  var alvo=f.querySelector('input[name=tipo][value="'+pre+'"]'); if(alvo) alvo.checked=true;
  montar();
})();
</script>"""


def projeto():
    cfg = {}
    cards, grupos = "", ""
    for t, rot, desc, canal, perguntas in PROJETO_TIPOS:
        numero = ZAP_ESTUFAS if canal == "venda" else ZAP
        cfg[t] = {"rotulo": rot, "numero": numero,
                  "saudacao": ("Olá! Vim pelo site do Eng. Tafarel e quero contar meu projeto." if canal == "venda"
                               else "Olá, Tafarel! Vim pelo site e quero contar meu projeto."), "perguntas": [[p[0], p[1]] for p in perguntas],
                  "destino": ("Vai para o WhatsApp de vendas de estufas " + ZAP_ESTUFAS_LEGIVEL) if canal == "venda"
                  else ("Vai direto para o WhatsApp do Tafarel " + ZAP_LEGIVEL)}
        cards += (f'<label class="p-card"><input type="radio" name="tipo" value="{t}">'
                  f'<span><strong>{rot}</strong><small>{desc}</small></span></label>')
        campos = ""
        for pid, prot, ptipo, extra in perguntas:
            nome = f"{t}-{pid}"
            if ptipo == "opcoes":
                ops = "".join(f'<label class="p-chip"><input type="radio" name="{nome}" value="{html.escape(o)}"><span>{o}</span></label>' for o in extra)
                campos += f'<fieldset class="p-campo"><legend>{prot}</legend><div class="p-chips">{ops}</div></fieldset>'
            else:
                campos += (f'<div class="p-campo"><label for="{nome}">{prot}</label>'
                           f'<input id="{nome}" name="{nome}" autocomplete="off" placeholder="{html.escape(extra)}"></div>')
        grupos += f'<div class="p-grupo" data-tipo="{t}" hidden><h2 class="p-passo">2. Conte um pouco mais</h2>{campos}</div>'
    prazos = "".join(f'<label class="p-chip"><input type="radio" name="c-prazo" value="{o}"><span>{o}</span></label>'
                     for o in ["Agora", "Em até 3 meses", "Em 6 meses ou mais", "Só pesquisando"])
    corpo = f"""
<style>.zap-fixo{{display:none}}</style>
<section class="cabeca-pagina"><div class="wrap">
  <p class="trilha"><a href="index.html">Início</a> / Contar meu projeto</p>
  <h1>Conte o seu projeto</h1>
  <p class="promessa">Responda em 1 minuto. A mensagem chega pronta no WhatsApp certo, e eu já respondo com o próximo passo, sem você ter que explicar tudo de novo.</p>
</div></section>

<section class="secao"><div class="wrap p-grade">
  <form id="projeto" class="p-form" novalidate onsubmit="return false">
    <fieldset class="p-campo"><legend class="p-passo">1. O que você quer fazer?</legend>
      <div class="p-cards">{cards}</div>
    </fieldset>
    {grupos}
    <div id="p-comum" hidden>
      <h2 class="p-passo">3. Sobre você</h2>
      <div class="p-duas">
        <div class="p-campo"><label for="c-nome">Seu nome</label><input id="c-nome" name="c-nome" autocomplete="name"></div>
        <div class="p-campo"><label for="c-cidade">Cidade e estado</label><input id="c-cidade" name="c-cidade" autocomplete="address-level2" placeholder="ex.: Triunfo/RS"></div>
      </div>
      <fieldset class="p-campo"><legend>Quando quer começar?</legend><div class="p-chips">{prazos}</div></fieldset>
      <div class="p-campo"><label for="c-detalhe">Quer contar mais alguma coisa? (opcional)</label><textarea id="c-detalhe" name="c-detalhe" rows="3"></textarea></div>
    </div>
  </form>
  <aside class="p-resumo" aria-live="polite">
    <h2 class="p-passo">Sua mensagem</h2>
    <pre id="p-msg" class="p-msg"></pre>
    <a id="p-enviar" class="botao botao-zap" target="_blank" rel="noopener" aria-disabled="true">{ICONE_ZAP}Enviar no WhatsApp</a>
    <p id="p-destino" class="nota-afiliado"></p>
    <p class="nota-afiliado">Nada fica salvo no site. A mensagem só sai quando você toca em enviar, e você ainda pode editar no WhatsApp.</p>
  </aside>
</div></section>
<script type="application/json" id="projeto-cfg">{json.dumps(cfg, ensure_ascii=False)}</script>
{PROJETO_JS}
"""
    return pagina(slug="projeto", titulo="Conte o seu projeto | Eng. Tafarel Sá",
                  descricao="Conte em 1 minuto o que você quer fazer: estufa, hidroponia, água do viveiro, tanque, piscicultura, aquaponia ou curso. A mensagem chega pronta no WhatsApp.",
                  corpo=corpo, msg_zap="Olá, Tafarel! Vim pelo site.", ativo="projeto")


# ---------------------------------------------------------------- portal Água Boa Dá Lucro
PORTAL = "Água Boa Dá Lucro"
CATEGORIAS = [
    ("dicas-tecnicas", "Dicas técnicas", "Oxigênio, amônia, nitrito, pH, lodo, alimentação e manejo, explicados com estudo e com o que eu vejo no campo."),
    ("produtos", "Produtos Biotecnal", "Como e quando usar cada produto da linha Aqua, com dose da ficha técnica e protocolo."),
    ("cases", "Cases", "Resultados reais de produtores que trataram a água: o problema, o protocolo e os números."),
    ("por-dentro-da-biotecnal", "Por dentro da Biotecnal", "A fábrica, as certificações, a pesquisa e as pessoas por trás da linha Aqua."),
    ("mercado", "Mercado e tendências", "Números da piscicultura no Brasil e no Sul, preços, mercado e o que muda para o produtor."),
    ("vida-no-campo", "Vida no campo", "Histórias de produtores, eventos, dias de campo e o dia a dia da piscicultura."),
]
CAT = {s: (n, d) for s, n, d in CATEGORIAS}

AREAS_ATUACAO = ["Piscicultor", "Carcinicultor (camarão)", "Pesque-pague", "Aquaponia", "Alevinocultor",
                 "Técnico, zootecnista ou engenheiro de pesca", "Veterinário", "Agrônomo",
                 "Cooperativa ou associação", "Revenda agropecuária", "Emater ou prefeitura",
                 "Indústria de ração ou frigorífico", "Estudante ou professor", "Outro"]
UFS = ["RS", "SC", "PR", "SP", "MG", "MS", "MT", "GO", "DF", "RJ", "ES", "BA", "SE", "AL", "PE", "PB", "RN",
       "CE", "PI", "MA", "PA", "AP", "AM", "RR", "RO", "AC", "TO"]
INTERESSES = ["Qualidade da água", "Produtos Biotecnal", "Cursos", "Novos vídeos", "Ser revenda Biotecnal"]


def card_artigo(a, prof, nivel=3):
    nome_cat = CAT.get(a["categoria"], ("", ""))[0]
    foto = a["foto"]
    if not foto:  # sem foto própria: usa a embalagem do primeiro produto Biotecnal citado
        for pr in a["produtos"]:
            if (RAIZ / "assets" / "biotecnal" / f"{pr}.jpg").exists():
                foto = f"assets/biotecnal/{pr}.jpg"
                break
    img = (f'<img src="{"../" * prof}{foto}" alt="{html.escape(a.get("foto_legenda") or a["titulo"])}" loading="lazy" decoding="async">' if foto
           else f'<span class="card-sem-foto" aria-hidden="true">{nome_cat}</span>')
    return (f'<article class="card-post"><a class="card-link" href="{href("blog/" + a["slug"], prof)}">'
            f'<div class="card-img">{img}</div>'
            f'<div class="card-txt"><p class="card-cat">{nome_cat} · {a["leitura"]} min de leitura</p>'
            f'<h{nivel}>{a["titulo"]}</h{nivel}><p>{a["descricao"]}</p></div></a></article>')


def bloco_cadastro(prof=0, titulo="Receba o Água Boa Dá Lucro no WhatsApp", intro=None):
    intro = intro or ("Um conteúdo por semana sobre qualidade de água, os episódios novos do canal e avisos de "
                      "cursos e dias de campo. Escolha o seu perfil para receber o que interessa a você.")
    areas = "".join(f'<option>{x}</option>' for x in AREAS_ATUACAO)
    ufs = "".join(f'<option{" selected" if u == "RS" else ""}>{u}</option>' for u in UFS)
    ints = "".join(f'<label class="p-chip"><input type="checkbox" name="cad-int" value="{x}"><span>{x}</span></label>' for x in INTERESSES)
    return f"""<section class="secao secao-cadastro" id="cadastro"><div class="wrap cad-grade">
  <div>
    <p class="card-cat">{PORTAL}</p>
    <h2>{titulo}</h2>
    <p>{intro}</p>
    <p class="nota-afiliado">Você entra na lista do Eng. Tafarel Sá. Para sair, é só responder "sair". Nada fica salvo neste site.</p>
  </div>
  <form class="calc cad-form" data-zap="{ZAP}" novalidate onsubmit="return false">
    <label for="cad-nome">Seu nome</label><input id="cad-nome" autocomplete="name">
    <div class="p-duas">
      <div class="p-campo"><label for="cad-area">Área de atuação</label><select id="cad-area"><option value="">Escolha</option>{areas}</select></div>
      <div class="p-campo"><label for="cad-uf">Estado</label><select id="cad-uf">{ufs}</select></div>
    </div>
    <label for="cad-cidade">Cidade</label><input id="cad-cidade" autocomplete="address-level2">
    <label for="cad-prod">O que você produz ou faz? (opcional)</label><input id="cad-prod" placeholder="ex.: tilápia, 3 viveiros de 2.000 m²">
    <fieldset class="p-campo"><legend>Quero receber sobre</legend><div class="p-chips">{ints}</div></fieldset>
    <a class="botao botao-zap cad-enviar" href="#" target="_blank" rel="noopener">{ICONE_ZAP}Quero receber no WhatsApp</a>
  </form>
</div></section>"""


CADASTRO_JS = r"""
<script>
(function(){
  document.querySelectorAll('.cad-form').forEach(function(f){
    var b=f.querySelector('.cad-enviar');
    function v(id){var e=f.querySelector('#'+id);return e&&e.value.trim();}
    function montar(){
      var ints=[].slice.call(f.querySelectorAll('input[name=cad-int]:checked')).map(function(i){return i.value;});
      var l=['Olá, Tafarel! Quero receber o Água Boa Dá Lucro.',''];
      if(v('cad-nome')) l.push('• Nome: '+v('cad-nome'));
      if(v('cad-area')) l.push('• Área de atuação: '+v('cad-area'));
      l.push('• Cidade/UF: '+[v('cad-cidade'),v('cad-uf')].filter(Boolean).join('/'));
      if(v('cad-prod')) l.push('• O que faço: '+v('cad-prod'));
      if(ints.length) l.push('• Quero receber: '+ints.join(', '));
      b.href='https://wa.me/'+f.getAttribute('data-zap')+'?text='+encodeURIComponent(l.join('\n'));
    }
    f.addEventListener('input',montar); f.addEventListener('change',montar); montar();
  });
})();
</script>"""


def portal_index():
    destaque = ARTIGOS[0]
    resto = ARTIGOS[1:]
    chips = "".join(f'<a class="cat-chip" href="{href("blog/categoria/" + s, 1)}">{n}</a>' for s, n, _ in CATEGORIAS)
    secoes = ""
    for s, n, d in CATEGORIAS:
        lista = [a for a in resto if a["categoria"] == s][:6]
        if not lista:
            continue
        secoes += f"""<section class="secao"><div class="wrap">
  <div class="sec-topo"><h2>{n}</h2><a href="{href("blog/categoria/" + s, 1)}">Ver tudo</a></div>
  <p class="intro">{d}</p>
  <div class="cards">{"".join(card_artigo(a, 1) for a in lista)}</div>
</div></section>"""
    corpo = f"""
<section class="portal-hero"><div class="wrap portal-grade">
  <div>
    <p class="trilha"><a href="../index.html">Início</a> / {PORTAL}</p>
    <h1>{PORTAL}</h1>
    <p class="promessa">O portal de qualidade de água na piscicultura do Eng. Tafarel Sá, com a tecnologia da Biotecnal. Dicas técnicas, produtos, cases e mercado, para a ração virar peixe e não prejuízo.</p>
    <nav class="cat-chips" aria-label="Categorias">{chips}</nav>
  </div>
  <img class="portal-img" src="../assets/biotecnal/produtos-linha-aqua.jpg" alt="Linha Aqua Biotecnal: Nutrat Aqua Plus, Bactrat P e Oxitrat" decoding="async">
</div></section>

<section class="secao"><div class="wrap">
  <p class="card-cat">Em destaque</p>
  <div class="destaque">{card_artigo(destaque, 1, 2)}</div>
</div></section>
{secoes}
{bloco_cadastro(1)}
{bloco_youtube(1)}
<section class="secao"><div class="wrap">
  <div class="sec-topo"><h2>Ferramentas grátis</h2></div>
  <ul class="ofertas">
    <li class="oferta"><h3>Diagnóstico da água</h3><p>Digite oxigênio, pH, amônia e nitrito e veja o que está fora da faixa, com a amônia tóxica calculada.</p><a href="../calculadora.html#diagnostico">Fazer o diagnóstico</a></li>
    <li class="oferta"><h3>Calculadora de doses</h3><p>Doses de manutenção da linha Aqua pela área do viveiro e pela ração do dia.</p><a href="../calculadora.html">Calcular</a></li>
    <li class="oferta"><h3>Valores de referência</h3><p>A tabela de oxigênio, amônia, nitrito, pH, alcalinidade e temperatura para tilápia.</p><a href="../qualidade-da-agua.html">Ver a tabela</a></li>
  </ul>
</div></section>
{CADASTRO_JS}
"""
    ld = {"@context": "https://schema.org", "@type": "Blog", "name": PORTAL, "url": DOMINIO + "/blog/",
          "inLanguage": "pt-BR", "author": {"@id": DOMINIO + "/#tafarel"},
          "blogPost": [{"@type": "BlogPosting", "headline": a["titulo"], "url": f"{DOMINIO}/blog/{a['slug']}"} for a in ARTIGOS]}
    return pagina(slug="blog/", titulo=f"{PORTAL}: portal de qualidade de água na piscicultura | Eng. Tafarel Sá",
                  descricao="Dicas técnicas, produtos Biotecnal, cases e mercado da piscicultura. O portal Água Boa Dá Lucro do Eng. Tafarel Sá, com a tecnologia da Biotecnal.",
                  corpo=corpo, prof=1, msg_zap="Olá, Tafarel! Vim pelo portal Água Boa Dá Lucro.", ativo="blog/", ld=ld)


def categoria_page(s, n, d):
    lista = [a for a in ARTIGOS if a["categoria"] == s]
    chips = "".join(f'<a class="cat-chip{" ativo" if c == s else ""}" href="{href("blog/categoria/" + c, 2)}">{nn}</a>' for c, nn, _ in CATEGORIAS)
    if lista:
        conteudo = f'<div class="cards">{"".join(card_artigo(a, 2, 2) for a in lista)}</div>'
    elif s == "cases":
        msg = "Olá, Tafarel! Usei a linha Biotecnal e quero contar o meu resultado para virar um case no Água Boa Dá Lucro."
        conteudo = f"""<div class="resposta-rapida"><p><strong>Os primeiros cases estão sendo preparados.</strong> Usou a linha Aqua e mediu o antes e o depois? Seu resultado pode virar um case aqui, com o seu nome e a sua propriedade, se você quiser.</p></div>
<div class="hero-acoes">{botao_zap("Quero contar o meu resultado", msg)}</div>"""
    else:
        conteudo = '<p class="intro">Os primeiros conteúdos desta seção estão sendo preparados. Cadastre-se abaixo para ser avisado.</p>'
    corpo = f"""
<section class="cabeca-pagina"><div class="wrap">
  <p class="trilha"><a href="../../index.html">Início</a> / <a href="../index.html">{PORTAL}</a> / {n}</p>
  <h1>{n}</h1>
  <p class="promessa">{d}</p>
  <nav class="cat-chips" aria-label="Categorias">{chips}</nav>
</div></section>
<section class="secao"><div class="wrap">{conteudo}</div></section>
{bloco_cadastro(2)}
{CADASTRO_JS}
"""
    return pagina(slug=f"blog/categoria/{s}", titulo=f"{n} | {PORTAL} | Eng. Tafarel Sá", descricao=d,
                  corpo=corpo, prof=2, msg_zap="Olá, Tafarel! Vim pelo portal Água Boa Dá Lucro.", ativo="blog/")


def cadastro_page():
    corpo = f"""
<section class="cabeca-pagina"><div class="wrap">
  <p class="trilha"><a href="index.html">Início</a> / Cadastro</p>
  <h1>Receba o {PORTAL}</h1>
  <p class="promessa">Conteúdo de qualidade de água direto no seu WhatsApp, separado pelo seu perfil.</p>
</div></section>
{bloco_cadastro(0, titulo="Seu cadastro em 30 segundos")}
{CADASTRO_JS}
"""
    return pagina(slug="cadastro", titulo=f"Receba o {PORTAL} no WhatsApp | Eng. Tafarel Sá",
                  descricao="Cadastre-se para receber dicas de qualidade de água, episódios novos e avisos de cursos e dias de campo pelo WhatsApp.",
                  corpo=corpo, msg_zap="Olá, Tafarel! Quero receber o Água Boa Dá Lucro.", ativo="blog/")


def revenda_page():
    msg = ("Olá, Tafarel! Tenho interesse em revender a linha Biotecnal.\n• Empresa: __\n• Tipo: agropecuária / cooperativa / técnico\n"
           "• Cidade/UF: __\n• Atendo produtores de: __")
    faq = [
        ("Quem pode revender a linha Aqua Biotecnal?",
         "Agropecuárias, cooperativas, associações de produtores e técnicos que atendem piscicultores no Rio Grande do Sul e em Santa Catarina."),
        ("Preciso entender de qualidade de água?",
         "Ajuda, mas não é obrigatório. O suporte técnico e os protocolos ficam comigo, e o conteúdo do Água Boa Dá Lucro serve de material para os seus clientes."),
        ("Como funciona o pedido?",
         "As condições comerciais, o pedido mínimo e o frete são combinados direto, conforme a sua região e o volume."),
    ]
    corpo = f"""
<section class="cabeca-pagina"><div class="wrap cabeca-grade">
  <div>
    <p class="trilha"><a href="index.html">Início</a> / <a href="{href('biotecnal', 0)}">Biotecnal</a> / Seja revenda</p>
    <h1>Seja revenda Biotecnal no RS e em SC</h1>
    <p class="promessa">Para agropecuárias, cooperativas e técnicos que atendem piscicultores. Produto de fábrica certificada, suporte técnico de engenheiro e conteúdo pronto para os seus clientes.</p>
    <div class="hero-acoes">{botao_zap("Quero ser revenda", msg)}</div>
  </div>
  <img class="foto" src="assets/biotecnal/produtos-linha-aqua.jpg" alt="Linha Aqua Biotecnal" decoding="async">
</div></section>
<section class="secao"><div class="wrap">
  <h2>O que a revenda recebe</h2>
  <ul class="ofertas">
    <li class="oferta"><h3>Linha Aqua completa</h3><p>Bactrat P, Nutrat Aqua Plus, Oxitrat e Bactrat Aquanitro, fabricados em Toledo/PR por indústria com ISO 9001 e ISO 14001.</p><a href="{href('biotecnal', 0)}">Ver produtos</a></li>
    <li class="oferta"><h3>Suporte técnico</h3><p>Seu cliente com problema de água? Eu ajudo a montar o protocolo a partir das medições.</p><a href="{href('calculadora', 0)}#diagnostico">Ver o diagnóstico</a></li>
    <li class="oferta"><h3>Conteúdo que vende</h3><p>Os artigos e vídeos do Água Boa Dá Lucro explicam o problema e o produto. Você compartilha com os seus clientes.</p><a href="{href('blog/', 0)}">Ver o portal</a></li>
  </ul>
</div></section>
<section class="secao secao-branca"><div class="wrap">
  <h2>Perguntas comuns</h2>
  {perguntas(faq)}
</div></section>
{chamada("Vamos conversar sobre a sua região?", "Me conte onde você atua e quantos piscicultores atende. Eu respondo pessoalmente.", "Quero ser revenda", msg)}
"""
    return pagina(slug="seja-revenda-biotecnal", titulo="Seja revenda Biotecnal no RS e SC | Eng. Tafarel Sá",
                  descricao="Agropecuárias, cooperativas e técnicos: revenda a linha Aqua Biotecnal no Rio Grande do Sul e em Santa Catarina, com suporte técnico e conteúdo pronto.",
                  corpo=corpo, msg_zap=msg, ld=faq_ld(faq), ativo="biotecnal")


# ---------------------------------------------------------------- build
def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "blog").mkdir(parents=True)
    shutil.copytree(RAIZ / "assets", DIST / "assets")
    if (RAIZ / "fotos").exists():
        shutil.copytree(RAIZ / "fotos", DIST / "fotos")

    paginas = {
        "index.html": home(),
        "estufas.html": estufas(),
        "tanques-de-geomembrana.html": tanques(),
        "piscicultura.html": piscicultura(),
        "aquaponia-comercial.html": aquaponia(),
        "loja-akso.html": loja_akso(),
        "biotecnal.html": biotecnal(),
        "qualidade-da-agua.html": qualidade_agua(),
        "calculadora.html": calculadora(),
        "hidroponia.html": hidroponia(),
        "cursos.html": cursos(),
        "traira-e-trairao.html": traira(),
        "projeto.html": projeto(),
        "sobre.html": sobre(),
        "blog/index.html": portal_index(),
        "cadastro.html": cadastro_page(),
        "seja-revenda-biotecnal.html": revenda_page(),
        "404.html": nao_encontrada(),
    }
    for p in BIO_PRODUTOS:
        paginas[f"biotecnal-{p['slug']}.html"] = produto_bio(p)
    for a in ARTIGOS:
        paginas[f"blog/{a['slug']}.html"] = post_page(a)
    (DIST / "blog" / "categoria").mkdir(parents=True, exist_ok=True)
    for c, n, d in CATEGORIAS:
        paginas[f"blog/categoria/{c}.html"] = categoria_page(c, n, d)
    for nome, conteudo in paginas.items():
        (DIST / nome).write_text(conteudo, encoding="utf-8")

    urls = []
    for nome in paginas:
        if nome == "404.html":
            continue
        caminho = nome.removesuffix("index.html").removesuffix(".html")
        urls.append(f"  <url><loc>{DOMINIO}/{caminho}</loc></url>")
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls) + "\n</urlset>\n", encoding="utf-8")
    # GEO: resumo para buscadores de IA
    linhas = [f"# Eng. Tafarel Sá", "",
              "> Site do Eng. Tafarel Sá, engenheiro ambiental e representante técnico da Biotecnal no RS e em SC. "
              "Conteúdo sobre qualidade da água na piscicultura (oxigênio dissolvido, amônia, nitrito, pH, alcalinidade, lodo) "
              "e produtos da linha Aqua Biotecnal (Oxitrat, Bactrat P, Bactrat Aquanitro, Bactrat Aquatech, Bioflow Aqua, Nutrat Aqua Plus). "
              "Inclui cases reais com análises de água, como o de Rolante/RS, onde o nitrito caiu de 5 mg/L a zero em 8 dias. "
              "Para comprar produtos Biotecnal no Rio Grande do Sul e em Santa Catarina, o contato é o WhatsApp do Tafarel abaixo.", "",
              "## Valores de referência (tilápia, viveiro escavado)"]
    linhas += [f"- {pp}: {fx} ({fq})" for pp, fx, fq, _ in REFERENCIAS]
    linhas += ["", "## Guias", f"- [Qualidade da água na piscicultura]({DOMINIO}/qualidade-da-agua)"]
    linhas += [f"- [{a['titulo']}]({DOMINIO}/blog/{a['slug']}): {a['resposta']}" for a in ARTIGOS]
    linhas += ["", "## Outras páginas",
               f"- [Portal Água Boa Dá Lucro]({DOMINIO}/blog/): dicas técnicas, produtos Biotecnal, cases, por dentro da Biotecnal e mercado da piscicultura.",
               f"- [Seja revenda Biotecnal no RS e SC]({DOMINIO}/seja-revenda-biotecnal): para agropecuárias, cooperativas e técnicos.",
               f"- [Cadastro]({DOMINIO}/cadastro): receber o Água Boa Dá Lucro pelo WhatsApp.",
               f"- [Criação de traíra e trairão]({DOMINIO}/traira-e-trairao): condicionamento alimentar, berçário e manejo para pesca esportiva e pesque-pague.",
               f"- [Curso Aquaponia Comercial]({DOMINIO}/cursos): Método AquaHortis, online e presencial.",
               f"- [Calculadora e diagnóstico da água]({DOMINIO}/calculadora): doses Biotecnal pela ração e diagnóstico com cálculo de amônia tóxica."]
    linhas += ["", "## Produtos Biotecnal"]
    linhas += [f"- [{p['nome']}]({DOMINIO}/biotecnal-{p['slug']}): {p['tipo']}. {p['resumo']}" for p in BIO_PRODUTOS]
    linhas += ["", "## Contato", f"- Contar um projeto (formulário que gera a mensagem de WhatsApp): {DOMINIO}/projeto",
               f"- WhatsApp do Tafarel (Biotecnal, Água Boa Dá Lucro, consultoria, tanques e cursos): +{ZAP}", f"- WhatsApp de vendas de estufas e hidroponia (Brasil Estufas): +{ZAP_ESTUFAS}", f"- YouTube: {YOUTUBE}", f"- Instagram: {INSTAGRAM}"]
    (DIST / "llms.txt").write_text("\n".join(linhas) + "\n", encoding="utf-8")

    itens = "".join(
        f"<item><title>{html.escape(a['titulo'])}</title><link>{DOMINIO}/blog/{a['slug']}</link>"
        f"<description>{html.escape(a['descricao'])}</description><pubDate>{rfc822(a['data'])}</pubDate>"
        f"<guid>{DOMINIO}/blog/{a['slug']}</guid></item>" for a in ARTIGOS)
    (DIST / "blog" / "feed.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
        f"<title>Blog Eng. Tafarel Sá</title><link>{DOMINIO}/blog/</link>"
        "<description>Qualidade da água na piscicultura</description><language>pt-BR</language>"
        + itens + "</channel></rss>", encoding="utf-8")

    (DIST / "robots.txt").write_text(
        "".join(f"User-agent: {b}\nAllow: /\n\n" for b in ["*", "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User", "PerplexityBot", "Google-Extended", "Bingbot"]) + f"Sitemap: {DOMINIO}/sitemap.xml\n", encoding="utf-8")
    print(f"{len(paginas)} páginas geradas em {DIST}")


if __name__ == "__main__":
    main()
