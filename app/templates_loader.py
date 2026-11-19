import os
import fnmatch
from pathlib import Path
import yaml

TEMPLATES_DIR = Path(os.environ.get("TEMPLATES_DIR", "templates"))
_cache: dict = {}

def load_templates():
    global _cache
    result = {}
    for f in sorted(TEMPLATES_DIR.glob("*.yaml")):
        with open(f, encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        tid = data.get("id") or f.stem
        result[tid] = data
    _cache = result
    return result

def get_templates():
    if not _cache:
        load_templates()
    return _cache

def match_template(container, env, image):
    """
    Wählt das spezifischste Template:
    - env-Regel erfüllt  -> +10
    - image_pattern trifft -> +1
    Templates, die eine env-Regel haben, die NICHT erfüllt ist, werden verworfen.
    generic wird nur als Fallback genutzt.
    """
    templates = get_templates()
    best = None
    best_score = 0
    for tid, tpl in templates.items():
        if tid == "generic":
            continue
        detect = tpl.get("detect") or {}
        score = 0

        env_rules = detect.get("env") or {}
        if env_rules:
            if all(env.get(k) == v for k, v in env_rules.items()):
                score += 10
            else:
                continue  # env-Regel da, aber nicht erfüllt -> disqualifiziert

        patterns = detect.get("image_patterns") or []
        if patterns:
            if not image or not any(fnmatch.fnmatch(image, p) for p in patterns):
                continue  # image_patterns vorhanden, aber keins trifft -> disqualifiziert
            score += 1

        if score > best_score:
            best_score = score
            best = tpl

    return best or templates.get("generic", {})