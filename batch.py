"""
batch.py — Procesa las 41 empresas de Toku en batch.
Genera 1 dossier MD por empresa en ./output/
Robusto: si falla una empresa, continúa con la siguiente.
"""
import csv
import os
import time
from pathlib import Path
from orchestrator import TokuDossierEngine

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

COMPANIES_CSV = Path(__file__).parent / "companies.csv"


def run_batch(limit: int = None, skip_existing: bool = True):
    engine = TokuDossierEngine()

    with open(COMPANIES_CSV, encoding="utf-8") as f:
        companies = list(csv.DictReader(f))

    if limit:
        companies = companies[:limit]

    total = len(companies)
    ok, failed = 0, 0

    print(f"\n[LAUNCH] TOKU GTM RADAR - Batch de {total} empresas")
    print("=" * 55)

    for i, row in enumerate(companies, 1):
        empresa = row["empresa"]
        sector = row["sector"]
        pitch = row["pitch_principal"]
        contexto = row.get("contexto", "")

        filename = OUTPUT_DIR / f"{engine.safe_filename(empresa)}.md"

        if skip_existing and filename.exists():
            print(f"[{i}/{total}] SKIP: {empresa} — ya existe, saltando.")
            ok += 1
            continue

        print(f"[{i}/{total}] RESEARCHING: {empresa} ({sector})")

        try:
            dossier = engine.generate_dossier(empresa, sector, pitch, contexto)
            filename.write_text(dossier, encoding="utf-8")
            print(f"         DONE: {filename.name}")
            ok += 1
        except Exception as e:
            print(f"         FAIL: {e}")
            failed += 1

        # Pausa entre empresas para respetar rate limits (incrementada a 12s para seguridad)
        if i < total:
            time.sleep(12)

    print("\n" + "=" * 55)
    print(f"COMPLETED: {ok} | FAILED: {failed} | Total: {total}")
    print(f"Dossiers en: {OUTPUT_DIR}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Toku GTM Radar - Batch Processor")
    parser.add_argument("--limit", type=int, default=None, help="Procesar solo N empresas (para test)")
    parser.add_argument("--force", action="store_true", help="Regenerar aunque ya exista el dossier")
    args = parser.parse_args()

    run_batch(limit=args.limit, skip_existing=not args.force)
