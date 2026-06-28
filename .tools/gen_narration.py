#!/usr/bin/env python3
"""Generate ElevenLabs narration + per-line highlight cues for one chapter.

Extracts readable elements in the SAME order book.js `ttsCollect()` highlights
them, normalizes the text the same way, sends it to ElevenLabs with timestamps,
and writes  story/audio/<cid>.mp3  +  story/audio/<cid>.cues.json (start seconds
per element).  Cue index N lines up with ttsItems[N] in the browser.
"""
import sys, os, re, json, base64, urllib.request
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_VOICE_ID = "auq43ws1oslv0tO4BDa7"   # Chapter 1; override per chapter via 3rd arg
MODEL = os.environ.get("ELEVEN_MODEL", "eleven_multilingual_v2")  # turbo/flash v2.5 = ~half the credits

# ----- read chapter file: front matter (title/subtitle) + body -----
def load_chapter(path):
    raw = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    fm, body = (m.group(1), m.group(2)) if m else ("", raw)
    def field(name):
        mm = re.search(r'^%s:\s*"?(.*?)"?\s*$' % name, fm, re.M)
        v = mm.group(1) if mm else ""
        return v.replace('\\"', '"')
    return field("title"), field("subtitle"), body

# ----- collect readable elements in document order (mirrors ttsCollect) -----
LABEL_SKIP = {"nlabel", "blabel", "badge", "nk", "cb-num", "suite-head", "page-marker"}

class Collector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []          # list of (tag, classes)
        self.items = []          # collected text strings, in order
        self.cap_depth = None    # depth at which capture started
        self.buf = []
        self.skip_depth = None   # depth of a label element to skip

    def _classes(self, attrs):
        for k, v in attrs:
            if k == "class":
                return set(v.split())
        return set()

    def _is_collector(self, tag, cls):
        parent_cls = self.stack[-1][1] if self.stack else set()
        anc = [c for (_, c) in self.stack]
        has = lambda name: any(name in c for c in anc)
        if "cb-title" in cls or "cb-sub" in cls: return True
        if tag == "p" and "page" in parent_cls: return True      # .page > p (incl big-quote)
        if "note" in cls: return True                             # .note
        if "bcap" in cls: return True                             # .bcap
        if tag == "p" and has("case"): return True                # .suite .case p
        if tag in ("h3", "p") and has("next"): return True        # .next h3, .next p
        return False

    def handle_starttag(self, tag, attrs):
        cls = self._classes(attrs)
        # decide using ancestors (current stack), THEN push self
        is_col = self.cap_depth is None and self._is_collector(tag, cls)
        self.stack.append((tag, cls))
        depth = len(self.stack)
        if self.cap_depth is not None:
            if self.skip_depth is None and (cls & LABEL_SKIP):
                self.skip_depth = depth
            return
        if is_col:
            self.cap_depth = depth
            self.buf = []
            self.skip_depth = None

    def handle_data(self, data):
        if self.cap_depth is not None and self.skip_depth is None:
            self.buf.append(data)

    def handle_endtag(self, tag):
        depth = len(self.stack)
        if self.skip_depth is not None and depth == self.skip_depth:
            self.skip_depth = None
        if self.cap_depth is not None and depth == self.cap_depth:
            text = re.sub(r"\s+", " ", "".join(self.buf)).strip()
            if len(text) > 1:
                self.items.append(text)
            self.cap_depth = None
            self.buf = []
        if self.stack:
            self.stack.pop()

# ----- normalize for natural speech (mirrors ttsNormalize) -----
def normalize(t):
    t = re.sub(r"£\s?([\d,]+(?:\.\d+)?)", lambda m: m.group(1).replace(",", "") + " pounds", t)
    reps = [
        (r"\bCI/CD\b", "C I, C D"), (r"\bAPIs\b", "A P Eyes"), (r"\bAPI\b", "A P I"),
        (r"\bUI\b", "U I"), (r"\bAI\b", "A.I."), (r"\bJSON\b", "Jason"),
        (r"\bSDET\b", "S D E T"), (r"\bQA\b", "Q A"), (r"\bCI\b", "C I"),
        (r"\bSEV-?1\b", "severity one"), (r"\bP1\b", "P one"), (r"\bSAST\b", "S A S T"),
        (r"\bDAST\b", "D A S T"), (r"\bK6\b", "K six"),
    ]
    for pat, sub in reps:
        flags = re.I if "SEV" in pat else 0
        t = re.sub(pat, sub, t, flags=flags)
    return re.sub(r"\s+", " ", t).strip()

def main():
    cid = sys.argv[1] if len(sys.argv) > 1 else "ch1"
    src = sys.argv[2]
    voice_id = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_VOICE_ID
    speed = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0   # 0.7 slow .. 1.2 fast
    outdir = sys.argv[5] if len(sys.argv) > 5 else os.path.join(ROOT, "story", "audio")
    key = open(os.path.join(ROOT, ".elevenlabs.key")).read().strip()

    title, subtitle, body = load_chapter(src)
    c = Collector(); c.feed(body)
    elems = [normalize(title), normalize(subtitle)] + [normalize(x) for x in c.items]
    elems = [e for e in elems if len(e) > 1]

    # join with newlines so ElevenLabs pauses between lines; track each line's offset
    joined, offsets, pos = "", [], 0
    sep = "\n\n"
    for i, e in enumerate(elems):
        line = e if re.search(r'[.!?…"”]$', e) else e + "."
        offsets.append(pos)
        joined += line
        pos = len(joined)
        if i < len(elems) - 1:
            joined += sep; pos = len(joined)

    print("elements: %d" % len(elems))
    for i, e in enumerate(elems):
        print("  [%2d] %s" % (i, (e[:64] + ("…" if len(e) > 64 else ""))))

    payload = json.dumps({"text": joined, "model_id": MODEL,
                          "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.0, "use_speaker_boost": True, "speed": speed}}).encode()
    url = "https://api.elevenlabs.io/v1/text-to-speech/%s/with-timestamps" % voice_id
    import time
    d = None
    for attempt in range(1, 7):   # ElevenLabs intermittently returns transient 401/429/5xx
        req = urllib.request.Request(url, data=payload,
                                     headers={"xi-api-key": key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as r:
                d = json.loads(r.read())
            break
        except urllib.error.HTTPError as e:
            body = ""
            try: body = e.read().decode()
            except Exception: pass
            if "quota_exceeded" in body:
                import sys as _s
                print("ERROR: ElevenLabs quota exceeded — top up credits and retry.\n  " + body[:300])
                _s.exit(2)   # not transient; don't retry
            if e.code in (429, 500, 502, 503) and attempt < 6:
                wait = 2 * attempt
                print("  attempt %d got HTTP %d — retrying in %ds…" % (attempt, e.code, wait))
                time.sleep(wait)
                continue
            print("ERROR: HTTP %d — %s" % (e.code, body[:300]))
            raise

    audio = base64.b64decode(d["audio_base64"])
    al = d["alignment"]
    starts = al["character_start_times_seconds"]
    nchars = len(starts)

    # map each line's char offset -> start time
    cues = []
    for off in offsets:
        off = min(off, nchars - 1)
        cues.append(round(starts[off], 3))

    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, cid + ".mp3"), "wb") as f:
        f.write(audio)
    with open(os.path.join(outdir, cid + ".cues.json"), "w") as f:
        json.dump(cues, f)

    print("duration ~%.1fs | cues: %d | audio: %d KB" %
          (al["character_end_times_seconds"][-1], len(cues), len(audio) // 1024))

if __name__ == "__main__":
    main()
