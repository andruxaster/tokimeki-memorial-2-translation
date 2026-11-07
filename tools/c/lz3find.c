#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned char out[1<<17];
long dec(unsigned char*s,long n,long pos,long maxo){
 if(pos+4>n) return 0; long size=s[pos]|s[pos+1]<<8|s[pos+2]<<16; if(s[pos+3]!=0||size<64||size>0x8000) return 0;
 pos+=4; long end=pos+size; if(end>n) return 0;
 unsigned char ring[1024]; memset(ring,0,1024); int r=0x3de; long o=0; unsigned fl=0;
 while(pos<end && o<maxo){ fl>>=1; if(!(fl&0x100)){ fl=s[pos++]|0xff00; if(pos>end) break;}
  if(!(fl&1)){ unsigned char c=s[pos++]; out[o++]=c; ring[r]=c; r=(r+1)&1023; continue; }
  int b=s[pos++];
  if(b<0x80){ int a=((b&3)<<8)|s[pos++]; int cnt=(b>>2)+3; for(int i=0;i<cnt&&o<maxo;i++){unsigned char c=ring[(a+i)&1023]; out[o++]=c; ring[r]=c; r=(r+1)&1023;} }
  else if(b<0xc0){ int d=b&15; int cnt=((b>>4)&3)+2; for(int i=0;i<cnt&&o<maxo;i++){unsigned char c=ring[(r-d)&1023]; out[o++]=c; ring[r]=c; r=(r+1)&1023;} }
  else { int cnt=(b&0x3f)+8; for(int i=0;i<cnt&&o<maxo&&pos<end;i++){unsigned char c=s[pos++]; out[o++]=c; ring[r]=c; r=(r+1)&1023;} }
 }
 return o;}
int main(int c,char**v){FILE*f=fopen(v[1],"rb");fseek(f,0,2);long n=ftell(f);rewind(f);unsigned char*s=malloc(n);if(fread(s,1,n,f)){};
 int nl=strlen(v[2])/2;unsigned char nd[256];for(int i=0;i<nl;i++)sscanf(v[2]+2*i,"%2hhx",&nd[i]);
 int step=atoi(v[3]);
 for(long p=0;p<n;p+=step){ long o=dec(s,n,p,1<<17); for(long i=0;i+nl<=o;i++) if(!memcmp(out+i,nd,nl)){printf("%lx out %ld at %ld\n",p,o,i);break;}}
}
