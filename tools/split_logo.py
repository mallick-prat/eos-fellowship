"""Split the one-path logo SVG into sun_sil.d (outline), sun_ink.d (linework) and word.d (wordmark).

    python3 tools/split_logo.py <eos-logo.svg> <out_dir>
"""
import re,sys
d=re.search(r' d="([^"]+)"',open(sys.argv[1]).read()).group(1)
subs=[s.strip() for s in re.split(r'(?=M)',d) if s.strip()]
def bbox(s):
    n=list(map(int,map(float,re.findall(r'-?\d+\.?\d*',s)))); return min(n[0::2]),min(n[1::2]),max(n[0::2]),max(n[1::2])
def compact(s):
    s=re.sub(r'\s*L\s*',' ',s); s=re.sub(r'M\s*','M',s); return re.sub(r'\s*Z',"Z",s)
sun=[s for s in subs if bbox(s)[2]<800]; word=[s for s in subs if bbox(s)[0]>900]
sil=[s for s in sun if bbox(s)==(146,223,766,856)]
print(len(sun),len(word),len(sil),len(subs))
open(sys.argv[2]+'/sun_ink.d','w').write(''.join(compact(s) for s in sun))
open(sys.argv[2]+'/sun_sil.d','w').write(compact(sil[0]))
open(sys.argv[2]+'/word.d','w').write(''.join(compact(s) for s in word))
wb=[bbox(s) for s in word]; print('word bbox',min(b[0] for b in wb),min(b[1] for b in wb),max(b[2] for b in wb),max(b[3] for b in wb))
