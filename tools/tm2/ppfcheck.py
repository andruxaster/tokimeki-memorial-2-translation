import sys,struct,shutil,filecmp
orig,ppf,ref=sys.argv[1:4]
d=bytearray(open(orig,'rb').read()); p=open(ppf,'rb').read(); i=60
while i<len(p):
    o,n=struct.unpack_from('<QB',p,i); i+=9; d[o:o+n]=p[i:i+n]; i+=n
print(ppf, bytes(d)==open(ref,'rb').read())
