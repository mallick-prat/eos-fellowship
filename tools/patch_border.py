"""Clone ivy over the small red figure on the border's right edge so that edge can repeat.

    python3 tools/patch_border.py <border.png> <out.png>
"""
import sys
from PIL import Image
im=Image.open(sys.argv[1]).convert('RGBA')
# cover the little red figure on the right edge with ivy cloned from just above it
patch=im.crop((468,500,600,560))
for y in (584,620):
    im.alpha_composite(Image.new('RGBA',(132,60),(0,0,0,0)),(468,y))
im2=im.copy()
im2.paste(patch,(468,580))
im2.paste(im.crop((468,440,600,480)),(468,630))
im2.save(sys.argv[2])
