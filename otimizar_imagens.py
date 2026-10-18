"""Gera versões .webp (mais leves) das fotos do site.
Rode depois de subir fotos novas:  python3 otimizar_imagens.py
O build usa o .webp automaticamente quando ele existe."""
from pathlib import Path
from PIL import Image, ImageOps

RAIZ = Path(__file__).parent
LARGURA_MAX = 1200

for pasta in ["fotos", "assets/biotecnal"]:
    for f in (RAIZ / pasta).rglob("*"):
        if f.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            continue
        destino = f.with_suffix(".webp")
        if destino.exists() and destino.stat().st_mtime >= f.stat().st_mtime:
            continue
        im = ImageOps.exif_transpose(Image.open(f))
        im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
        if im.width > LARGURA_MAX:
            im = im.resize((LARGURA_MAX, round(im.height * LARGURA_MAX / im.width)), Image.LANCZOS)
        im.save(destino, "WEBP", quality=78, method=6)
        print(f"{f.relative_to(RAIZ)}: {f.stat().st_size // 1024} KB -> {destino.stat().st_size // 1024} KB")
