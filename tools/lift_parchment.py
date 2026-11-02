"""Make a scan's parchment transparent (color-to-alpha) so paint and ink sit on the page.

    python3 tools/lift_parchment.py <scan.png> <out.png> <bg_r> <bg_g> <bg_b>
"""
import sys
from PIL import Image
import numpy as np
src,dst,br,bg,bb=sys.argv[1],sys.argv[2],*map(float,sys.argv[3:6])
im=np.asarray(Image.open(src).convert('RGBA')).astype(np.float32)
rgb=im[...,:3]; a0=im[...,3]/255
bgc=np.array([br,bg,bb],dtype=np.float32)
d=rgb-bgc
den=np.where(d<0,bgc,255-bgc)
a=np.max(np.abs(d)/den,axis=-1)
lo,hi=0.10,0.45   # ignore faint parchment mottling, firm up paint
a=np.clip((a-lo)/(hi-lo),0,1)
safe=np.maximum(a,1e-3)[...,None]
fg=np.clip(bgc+d/np.maximum(np.max(np.abs(d)/den,axis=-1),1e-3)[...,None],0,255)
out=np.dstack([fg,(a*a0*255)]).astype(np.uint8)
Image.fromarray(out,'RGBA').save(dst)
