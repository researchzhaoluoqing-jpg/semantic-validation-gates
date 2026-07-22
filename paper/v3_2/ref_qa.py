"""QA for the manuscript bibliography: key/citation cross-check."""
import re, glob, io, os

os.chdir(r"C:\Users\AItra\machineL\Papers\Working_Paper_Gates\paper\v3_2")

bib = io.open('sections/bibliography.tex', encoding='utf-8').read()
keys = re.findall(r"\\bibitem\{([^}]+)\}", bib)

body = ""
for f in ['main.tex'] + sorted(glob.glob('sections/*.tex')):
    if 'bibliography' in f:
        continue
    body += io.open(f, encoding='utf-8').read()

cited = set()
for m in re.findall(r"\\cite\{([^}]+)\}", body):
    cited.update(k.strip() for k in m.split(','))

print(f"bibliography entries : {len(keys)}")
print(f"distinct keys cited  : {len(cited)}")
dupes = sorted({k for k in keys if keys.count(k) > 1})
print(f"duplicate keys       : {dupes or 'none'}")
uncited = [k for k in keys if k not in cited]
print(f"UNCITED entries      : {uncited or 'none'}")
undefined = sorted(c for c in cited if c not in keys)
print(f"UNDEFINED citations  : {undefined or 'none'}")

# year sanity: flag entries whose year looks implausible
for k in keys:
    entry = re.search(r"\\bibitem\{" + re.escape(k) + r"\}(.*?)(?=\\bibitem|\\end\{thebibliography\})",
                      bib, re.S).group(1)
    years = re.findall(r"\b(19|20)(\d\d)\b", entry)
    yrs = [int(a + b) for a, b in years]
    if not yrs:
        print(f"  ! no year found: {k}")
