"""Essai rapide de l'agent Diagnostic, sans interface web.

    uv run python scripts/essai_diagnostic.py "ma tente a un arceau cassé, je l'ai depuis 3 ans"
    uv run python scripts/essai_diagnostic.py "mon vélo fait un bruit" --photo chemin/vers/photo.jpg
"""

import argparse
import asyncio
import json
import mimetypes
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google.genai import types  # noqa: E402

from diagnostic.agent import root_agent  # noqa: E402
from shared.execution import executer_agent  # noqa: E402


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("message")
    parser.add_argument("--photo", type=Path)
    args = parser.parse_args()

    parts = [types.Part(text=args.message)]
    if args.photo:
        mime = mimetypes.guess_type(args.photo)[0] or "image/jpeg"
        parts.append(types.Part.from_bytes(data=args.photo.read_bytes(), mime_type=mime))

    r = await executer_agent(root_agent, parts)
    print(json.dumps(json.loads(r.texte), ensure_ascii=False, indent=2))
    print(f"\n{r.latence_s:.1f} s · {r.tokens_entree} tokens en entrée · {r.tokens_sortie} en sortie")


if __name__ == "__main__":
    asyncio.run(main())
