"""Port complet du générateur de prescripts basé sur prescript.js.
Cette version vise à reproduire la logique de génération (RNG déterministe quotidiennement,
choix dans de larges listes, composition de la phrase, normalisation).

Exemple d'usage:
    rng = make_daily_rng(user_id)
    script = generate_prescript(rng)
"""
from __future__ import annotations
import datetime
import platform
import math
from typing import Callable, List, Optional
import json
from pathlib import Path


def xmur3(s: str) -> Callable[[], int]:
    """Hash déterministe (port JS xmur3) utilisé pour générer une seed 32-bit."""
    h = 1779033703 ^ len(s)
    for ch in s:
        h = (h ^ ord(ch)) * 3432918353 & 0xFFFFFFFF
        h = ((h << 13) | (h >> 19)) & 0xFFFFFFFF
    def fn():
        nonlocal h
        h = (h ^ (h >> 16)) * 2246822507 & 0xFFFFFFFF
        h = (h ^ (h >> 13)) * 3266489909 & 0xFFFFFFFF
        h ^= (h >> 16)
        return h & 0xFFFFFFFF
    return fn


def mulberry32(seed: int) -> Callable[[], float]:
    """PRNG léger (port JS mulberry32) qui retourne un float dans [0, 1)."""
    def rng():
        nonlocal seed
        seed = (seed + 0x6D2B79F5) & 0xFFFFFFFF
        t = seed
        t = (t ^ (t >> 15)) * (t | 1) & 0xFFFFFFFF
        t = t ^ (t + ((t ^ (t >> 7)) * (t | 61) & 0xFFFFFFFF)) & 0xFFFFFFFF
        val = (t ^ (t >> 14)) & 0xFFFFFFFF
        return val / 4294967296.0
    return rng


def rand_int(rng: Callable[[], float], max_exclusive: int) -> int:
    """Retourne un entier pseudo-aléatoire dans [0, max_exclusive)."""
    return int(math.floor(rng() * max_exclusive))


def pick(rng: Callable[[], float], arr: List[Optional[str]]) -> str:
    """Choisit un élément d'une liste via le RNG injecté.

    Convention projet:
    - liste vide => chaîne vide,
    - valeur `None` => chaîne vide.
    """
    if not arr:
        return ""
    v = arr[rand_int(rng, len(arr))]
    return "" if v is None else str(v)


def iso_day_local() -> str:
    """Date locale au format ISO (YYYY-MM-DD), utilisée pour seed quotidienne."""
    d = datetime.date.today()
    return d.strftime("%Y-%m-%d")


def make_daily_rng(user_id: str) -> Callable[[], float]:
    """Construit un RNG quotidien déterministe par utilisateur/environnement.

    Utilisé surtout pour tests / reproductibilité; le cog principal peut utiliser
    un RNG non déterministe selon la configuration UX souhaitée.
    """
    day = iso_day_local()
    ua = platform.platform() or ""
    seed_str = f"{user_id}|{day}|{ua}"
    seed = xmur3(seed_str)()
    return mulberry32(seed)


def ordinal_suffix(n: int) -> str:
    """Suffixe ordinal anglais (`st`, `nd`, `rd`, `th`)."""
    mod100 = n % 100
    if 11 <= mod100 <= 13:
        return "th"
    if n % 10 == 1:
        return "st"
    if n % 10 == 2:
        return "nd"
    if n % 10 == 3:
        return "rd"
    return "th"


def cap_first(s: str) -> str:
    """Met en majuscule la première lettre, sans modifier le reste."""
    if not s:
        return s
    return s[0].upper() + s[1:]


def lower_first(s: str) -> str:
    """Met en minuscule la première lettre, utile pour concaténer des fragments."""
    if not s:
        return s
    return s[0].lower() + s[1:]


def normalize_punctuation(text: str) -> str:
    """Nettoyage post-composition de ponctuation/espaces.

    Cette étape corrige les artefacts de concaténation de segments
    (espaces superflus, combinaisons invalides, etc.).
    """
    if not text:
        return text
    t = text
    # Réduction des doublons de ponctuation et des irrégularités d'espaces
    t = t.replace('\r', '')
    t = t.replace(' , .', '.')
    t = t.replace(' ,.', '.')
    t = t.replace(' . ,', '.')
    t = ' '.join(t.split())
    # Garantit un espace après la ponctuation si une lettre suit
    t = t.replace('!.', '!')
    return t.strip()


def fix_indefinite_articles(text: str) -> str:
    """Applique des corrections simples de grammaire anglaise.

    Inclut:
    - remplacements usuels (`1 times` -> `once`, `2 times` -> `twice`),
    - ajustements `a/an` basés sur règles heuristiques.
    """
    if not text:
        return text
    # Remplacements simples ('1 times', etc.)
    t = text.replace('1 times', 'once').replace('2 times', 'twice')
    # Correcteur simple de 'a/an' (non exhaustif mais pratique)
    import re
    def repl(m):
        a = m.group(1)
        word = m.group(2)
        w = word.lower()
        hard_vowel_sound = ["uni", "use", "user", "ufo", "euro", "one", "once", "ubiq"]
        for ex in hard_vowel_sound:
            if w.startswith(ex):
                return m.group(0)
        if w.startswith(('honest','hour','heir')):
            return 'an ' + word
        if re.match(r'^[AEFHILMNORSX]', word):
            return 'an ' + word
        if w[0] in 'aeiou':
            return 'an ' + word
        return m.group(0)
    t = re.sub(r'\b(a)\s+([A-Za-z][A-Za-z\-]*)', repl, t)
    return t


# --- content lists (fallback interne) ---
#
# Ces listes servent de valeurs par défaut.
# Elles peuvent être surchargées depuis `data/prescript.json` (section `en.pools`).
LOCATION_A = [
    "beach", "store", "house", "apartment complex", "ocean", "hotel", "motel",
    "place you cherish", "place you keep your family", "restaurant", "place to eat", "theater",
    "library", "school", "factory", "backstreet alleyway", "nest", "empty field", "graveyard",
    "basement", "alley", "parking lot", "abandoned lot", "office", "workshop", "place no one checks twice",
    "place people pass through quickly", "place that won't last forever", "place that smells like dust",
    "place that echoes", "place you were told not to enter", "public restroom", "train platform",
    "lighthouse", "secret location only you know about", "place you call home", "place they'd call home",
    "place you'd hide a body"
]

PREPRESCRIPT = [
    "Pack a lunchbox and consume it on top of a trash can in the streets of District 11 at 1 PM today.",
    "Bake dacquoise while the hour hand rests between 7 and 8, and eat it while watching a movie.",
    "Initiate a game of Never Have I Ever with the first five people you encounter. When one folds a finger, break it.",
    "Neatly clip the nails of the sixty-second person you come across.",
    "Pet quadrupedal animals five times.",
    "Spin a wheel and throw a cake at the person determined by the result.",
    "Consume eight crabs stored at room temperature and ripe persimmon at once.",
    "At the railing on the roof of a building, shout out the name of the person you dislike, then jump off.",
    "After a meal, discard all dishes that were used to serve it.",
    "On the morning after receiving the Prescript, drink three cups of water as soon as you get up.",
    "Race against residents that live in the same building as you to District 7. Measure the distance every twenty-three minutes and disqualify the one farthest away from the destination.",
    "Within three days, knit a scarf with a butterfly pattern.",
    "Dial any number. Give a New Year's greeting and words of blessing to whoever receives the call.",
    "See green from a white wall.",
    "When hungry, consume a Cheeki's cheeseburger with added onion.",
    "Fold thirty-nine paper cranes and throw them from the rooftop.",
    "When your eyes meet another person's, nod at them.",
    "Return to your home this instant. You may leave once a dog barks in front of your house one time.",
    "Wear light green clothing and take 10 steps in a triangle-shaped alley.",
    "Call the first person you meet a homosexual, then proceed to kiss them.",
    "Do not go home until you have finished reading the value of e.",
    "In 400,000 meters, turn right.",
    "Sleep for a total of 800 hours per day.",
    "Only eat and write with your right hand.",
    "Order something online you don't need.",
    "Submit to the city's prescripts.",
    "Waste your money on someone.",
    "Go to sleep. You must dream about a bird locked in a cage.",
    "Ensure that 2 plus 2 is equal to 5.",
]

PERSON_IDENTIFIER = [
    "ugly", "beautiful", "handsome", "cute", "pretty", "plain", "attractive", "unattractive",
    "young", "old", "middle-aged", "elderly", "youthful", "aged", "tall", "short",
    "small", "big", "thin", "fat", "skinny", "chubby", "lean", "muscular", "weak", "strong",
    "pale", "dark", "tan", "scarred", "freckled", "wrinkled", "smooth", "blonde", "brunette",
    "black-haired", "red-haired", "bald",
]

COLOR1 = [
    "blue", "black", "red", "brown", "velvet", "yellow", "pink", "white", "grey", "green",
    "light green", "light red", "dark red", "dark green", "cyan", "teal", "purple", "violet",
    "magenta", "orange", "amber", "gold", "silver", "beige", "tan", "ivory", "cream", "charcoal",
    "maroon", "navy", "indigo", "crimson", "scarlet", "lime", "mint", "olive", "peach", "lavender",
]

CLOTHING = [
    "hat", "cap", "hood", "hoodie", "cloak", "coat", "jacket", "vest", "shirt", "t-shirt",
    "sweater", "blouse", "dress", "skirt", "robe", "pants", "trousers", "jeans", "shorts", "leggings",
    "socks", "stockings", "tights", "shoes", "boots", "sandals", "slippers", "gloves", "mittens", "scarf",
    "shawl", "belt", "suspenders", "mask", "face covering", "veil", "glasses", "goggles",
]

MATERIAL_CONDITION = [
    "cloth", "fabric", "leather", "denim", "wool", "cotton", "linen", "silk", "velvet", "fur",
    "rubber", "plastic", "metal", "steel", "iron", "brass", "copper", "bronze", "rusted", "torn",
    "patched", "worn", "new", "stained", "dirty", "clean",
]

GAMES = [
    "Patty Cake", "Never Have I Ever", "Truth or Dare", "Tag", "Hide and Seek", "Peekaboo",
    "Hopscotch", "Simon Says", "Red Light Green Light", "Freeze Tag", "Marco Polo", "Chess", "Checkers",
    "Backgammon", "Dominoes", "Twister", "Charades", "Would You Rather", "Paintball", "Rock Paper Scissors",
]

OBJCS = [
    "pen and paper", "pencil", "eraser", "apples", "empty bottle", "glass cup", "ceramic mug",
    "notebook", "folder", "envelope", "plant with leaves", "dead plant", "potted plant",
    "duct tape", "roll of tape", "string", "rope", "charcoal", "chalk", "ash", "something plastic",
    "plastic container", "plastic bag", "wooden chair", "broken stool", "pack of playing cards", "single playing card",
    "dice", "spoon", "fork", "knife", "empty plate", "crayons", "paint", "paintbrush",
    "toilet paper", "paper towels", "tissues", "old photograph", "key", "keyring", "locked box",
    "backpack", "cardboard box", "flashlight", "battery", "clock", "broken clock", "mirror",
]

TOPIC = [
    "love", "lie", "death", "fear", "regret", "hope", "loneliness", "trust", "guilt", "desire",
    "your secrets", "your desires", "your fears", "your past", "your future", "memories", "forgotten memories",
    "dreams", "recurring dreams", "nightmares", "life", "gaming", "the city", "a movie",
]

ACTIVITIES = [
    "commit a felony", "steal money", "betray a friend", "become a proxy", "play games",
    "talk about your secrets", "shake someone's hand", "drink something", "sit on the train tracks",
    "travel somewhere new", "do a backflip", "do a frontflip", "roll a dice", "swing a baseball bat",
]

VERBS = [
    "touch", "hold", "push", "pull", "lift", "drop", "carry", "throw", "toss", "drag",
    "place", "move", "slide", "press", "tap", "knock on", "open", "close", "lock", "unlock",
    "bind", "insert into", "use as a weapon", "paint", "write on", "break",
]

STARTER = [
    "", "", "", "pause briefly, ", "wait a moment, ", "continue, ", "proceed, ", "then, ",
    "look around, ", "look forward, ", "take a step and ", "take another step and ", "stop moving and ",
]

ADDITIONAL_RANDOM = [
    "", " backwards", " on a rooftop", " at a ", " slowly", " carefully", " without stopping",
    " without speaking", " twice", " while being observed", " without looking back", " without making noise",
    " while hearing a sound that is not there", " until it feels wrong", " alone", " with others nearby",
]

TASK0_POOL = ["", "At noon, ", "When you breathe, "]
TRANSITION_POOL = [", then ", " and ", ". Next, ", ". Afterwards, "]
FOLLOWUP_POOL = [
    "make them a nice meal.",
    "ensure they never talk again.",
    "ignore them entirely.",
    "leave food outside their door.",
    "return home.",
]


# Tentative de surcharge depuis le JSON (non destructif).
# En cas d'erreur/clé manquante, on conserve automatiquement les fallbacks internes.
try:
    root = Path(__file__).resolve().parents[1]
    data_file = root / 'data' / 'prescript.json'
    if data_file.exists():
        with data_file.open('r', encoding='utf-8') as _f:
            _data = json.load(_f)
        _en = _data.get('en') or {}
        _pools = _en.get('pools') if isinstance(_en.get('pools'), dict) else {}

        def _coerce(name, default):
            # Priorité au nouveau schéma `en.pools`, repli vers l'ancien schéma `en.<KEY>`.
            v = _pools.get(name, _en.get(name))
            return v if isinstance(v, list) else default

        LOCATION_A = _coerce('LOCATION_A', LOCATION_A)
        PREPRESCRIPT = _coerce('PREPRESCRIPT', PREPRESCRIPT)
        PERSON_IDENTIFIER = _coerce('PERSON_IDENTIFIER', PERSON_IDENTIFIER)
        COLOR1 = _coerce('COLOR1', COLOR1)
        CLOTHING = _coerce('CLOTHING', CLOTHING)
        MATERIAL_CONDITION = _coerce('MATERIAL_CONDITION', MATERIAL_CONDITION)
        GAMES = _coerce('GAMES', GAMES)
        OBJCS = _coerce('OBJCS', OBJCS)
        TOPIC = _coerce('TOPIC', TOPIC)
        ACTIVITIES = _coerce('ACTIVITIES', ACTIVITIES)
        VERBS = _coerce('VERBS', VERBS)
        STARTER = _coerce('STARTER', STARTER)
        ADDITIONAL_RANDOM = _coerce('ADDITIONAL_RANDOM', ADDITIONAL_RANDOM)
except Exception:
    # En cas d'erreur, conserver silencieusement les valeurs par défaut.
    pass


def _choose_how_to_find_target(
    number5: int,
    number1: int,
    end1: str,
    number8: int,
    end8: str,
    finalpersonidentifier: str,
    finalcolor1: str,
    finalclothing: str,
) -> list[str]:
    """Construit les modèles de ciblage d'une personne.

    Le nombre `number5` influence le sous-ensemble utilisé, ce qui reproduit
    la logique de branchement historique du script source.
    """
    if number5 > 5:
        return [
            f"the last {number5} {finalpersonidentifier} people you see before you get home",
            f"the first {number5} {finalpersonidentifier} people you meet after receiving the prescript",
            f"someone in {finalcolor1} {finalclothing}",
            f"the {number1}{end1} person you come across",
        ]
    return [
        f"someone in {finalcolor1} {finalclothing}",
        f"the {number8}{end8} person you've had a crush on",
        "the first person that looks at you",
    ]


def _build_primary_task_pool(finalllocation: str, finalhowtofind: str, picked_verb: str, finalobjcs: str) -> list[str]:
    """Fabrique les templates de tâche principale (pool `task1`)."""
    return [
        f"Go to a {finalllocation} and observe {finalhowtofind}.",
        f"Find {finalhowtofind} and {picked_verb} them.",
        f"Leave a {finalobjcs} for {finalhowtofind}.",
    ]


def _build_followup_pool(number9: int) -> list[str]:
    """Fabrique les compléments finaux conditionnels (`follow2up`)."""
    return [
        " Your gender does not matter.",
        f" You must sleep {number9} hours tonight.",
        " You must not ask why.",
    ]


def generate_prescript(rng: Callable[[], float]) -> str:
    """Génère un prescript final à partir d'un RNG injecté.

    Pipeline:
    1) tirages initiaux (lieu, personne, objets, nombres),
    2) composition de fragments (préfixe, tâche, transition, followups),
    3) nettoyage de surface (ponctuation + grammaire simple).

    Note importante:
    l'ordre des appels RNG est volontairement conservé pour ne pas modifier
    la distribution ni la reproductibilité des résultats.
    """
    # Reproduit la structure logique JS: nombreux tirages intermédiaires et branches aléatoires.
    finalllocation = pick(rng, LOCATION_A)
    israndom = rand_int(rng, 150)
    if israndom == 4:
        # Branche rare: prescript préécrit direct
        return pick(rng, PREPRESCRIPT)

    finalpersonidentifier = pick(rng, PERSON_IDENTIFIER)
    finalcolor1 = pick(rng, COLOR1)
    finalclothing = pick(rng, CLOTHING)
    finalobjcs = pick(rng, OBJCS)
    finaltopic = pick(rng, TOPIC)
    finalactivities = pick(rng, ACTIVITIES)

    # Nombres utilisés pour paramétrer les templates.
    number1 = rand_int(rng, 150) + 1
    number7 = rand_int(rng, 100) + 1
    number2 = rand_int(rng, 400) + 1
    number4 = rand_int(rng, 1300) + 1
    number5 = rand_int(rng, 6) + 1
    number8 = rand_int(rng, 7) + 1
    number9 = rand_int(rng, 8) + 1

    end1 = ordinal_suffix(number1)
    end7 = ordinal_suffix(number7)
    end8 = ordinal_suffix(number8)

    # Garder ces variables évite d'altérer l'ordre des opérations/choix RNG
    # lors des refactors structurels.
    _ = (finaltopic, finalactivities, number2, number4, number7, end7)

    # Choix de la stratégie de ciblage.
    howtofind = _choose_how_to_find_target(
        number5=number5,
        number1=number1,
        end1=end1,
        number8=number8,
        end8=end8,
        finalpersonidentifier=finalpersonidentifier,
        finalcolor1=finalcolor1,
        finalclothing=finalclothing,
    )
    finalhowtofind = pick(rng, howtofind)

    # Construction de la tâche principale.
    finaltask0 = pick(rng, TASK0_POOL)
    finalstarter = pick(rng, STARTER)
    if finaltask0 == "":
        finalstarter = cap_first(finalstarter)

    # IMPORTANT: conserver ce tirage ici pour maintenir la parité RNG.
    picked_verb = pick(rng, VERBS)
    task1_pool = _build_primary_task_pool(
        finalllocation=finalllocation,
        finalhowtofind=finalhowtofind,
        picked_verb=picked_verb,
        finalobjcs=finalobjcs,
    )
    finaltask1 = pick(rng, task1_pool)
    # Si un préfixe est déjà présent, on met la tâche en minuscule initiale
    # pour améliorer la continuité grammaticale.
    if finaltask0 or finalstarter:
        finaltask1 = lower_first(finaltask1)

    # Branches conditionnelles de transition et compléments.
    followupChanceA = rand_int(rng, 3)
    followupChanceB = rand_int(rng, 4)

    finaltransition = pick(rng, TRANSITION_POOL) if followupChanceA == 2 else ""
    # Si transition inline (", then" / "and"), éviter les artefacts ". and".
    if finaltransition in (", then ", " and "):
        finaltask1 = finaltask1.rstrip()
        if finaltask1.endswith(('.', '!', '?')):
            finaltask1 = finaltask1[:-1]

    finalfollowup = pick(rng, FOLLOWUP_POOL) if finaltransition else ""

    follow2up = _build_followup_pool(number9)
    finalfollowup2 = pick(rng, follow2up) if followupChanceB == 2 else ""

    # Assemblage final puis normalisation grammaticale/syntaxique.
    finalscript = (finaltask0 + finalstarter + finaltask1 + finaltransition + finalfollowup + finalfollowup2).strip()
    finalscript = normalize_punctuation(finalscript)
    finalscript = fix_indefinite_articles(finalscript)
    return finalscript


if __name__ == "__main__":
    rng = make_daily_rng("u_test")
    for _ in range(10):
        print(generate_prescript(rng))
