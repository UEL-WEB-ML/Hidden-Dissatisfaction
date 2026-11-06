import sys
from PIL import Image
ims=[Image.open(f) for f in sys.argv[2:]]
h=max(i.height for i in ims); W=sum(i.width for i in ims)+40*len(ims)
c=Image.new('RGB',(W,h),'white'); x=0
for i in ims: c.paste(i,(x,0)); x+=i.width+40
c.thumbnail((2400,2400)); c.save(sys.argv[1])
