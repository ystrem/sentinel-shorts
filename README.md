# Sentinel Shorts

Automatický generátor vertikálních Shorts videí se space fakty.

Formát inspirovaný **UNIVERSIA** — krátká videa (15–20s) s NASA/Kosmonautikou tématikou.

## Rychlý start

```bash
# Náhodný fact + dnešní APOD
./bin/generate-short.py

# Specifický fact
./bin/generate-short.py --fact-id carrington-event

# Filtrovat podle kategorie
./bin/generate-short.py --category planets

# Vypsat dostupné fakty
./bin/generate-short.py --list-facts

# Vygenerovat a poslat na Telegram
./bin/generate-short.py --deliver
```

## Struktura

```
sentinel-shorts/
├── bin/
│   ├── generate-short.py     # Hlavní orchestrátor
│   ├── render-short.py       # FFmpeg renderer (1080×1920)
│   ├── fetch-image.py        # NASA APOD image fetcher
│   └── space-facts.py        # Space facts engine
├── data/
│   ├── facts/
│   │   └── space_facts.json  # 30+ předpřipravených faktů
│   ├── images/               # Cache APOD obrázků
│   └── music/                # Background ambient
├── output/                   # Hotová videa
├── config.yaml               # Konfigurace
└── README.md
```

## Konfigurace

V `config.yaml`:
- Rozlišení (výchozí 1080×1920)
- Délka videa (20s)
- Styl textu (velikost, barva, pozice)
- Ambience hudba
- Telegram delivery

## Formát Shorts

| Prvek | Spec |
|-------|------|
| Rozlišení | 1080×1920 (vertikála) |
| Délka | 20s |
| Titulek | 48px CENTERED |
| Rok | 64px ZLATÝ (pokud je) |
| Podtitul | 24px CENTERED |
| Pozadí | NASA APOD (Ken Burns zoom) |
| Hudba | Ambient space (FFmpeg generovaná) |
| Narace | Žádná (jen text) |

## Fakty

Databáze 30+ space faktů v `data/facts/space_facts.json`.
Kategorie: planets, history, cosmology, stars, spacecraft, moons, astronomy, black-holes, solar-storms, comets, physics, dwarf-planets

## Integrace se Sentinel

Až bude hotovo, můžeme propojit:
- Cron joby na pravidelné generování
- Telegram kanál
- YouTube Shorts upload

## Požadavky

- Python 3.10+
- FFmpeg (s libx264)
- Přístup k NASA APOD API
- Volitelně: AI model na aicore:4000 pro generování faktů z APOD
