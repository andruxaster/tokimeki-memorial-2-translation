#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned char *out;
long dec(unsigned char*s,long n,long pos,long maxo){long o=0;int flags=0,mask=0x80;
 while(pos<n&&o<maxo){mask<<=1;if(mask==0x100){flags=s[pos++];mask=1;}
  if(flags&mask){if(pos+1>=n)break;int b0=s[pos],b1=s[pos+1];pos+=2;int off=(b0|(b1&15)<<8)+1;int ln=b1>>4;if(ln==15)ln=s[pos++]+15;ln+=2;if(off>o)return -o;for(int i=0;i<ln&&o<maxo;i++){out[o]=out[o-off];o++;}}
  else out[o++]=s[pos++];}
 return o;}
int main(int c,char**v){FILE*f=fopen(v[1],"rb");fseek(f,0,2);long n=ftell(f);rewind(f);unsigned char*s=malloc(n);fread(s,1,n,f);
 int nl=strlen(v[2])/2;unsigned char nd[256];for(int i=0;i<nl;i++)sscanf(v[2]+2*i,"%2hhx",&nd[i]);
 long skip=atol(v[3]); out=malloc(1<<22);
 for(long p=0;p+2<n;p+=2048){if(0)continue;
  long o=dec(s,n,p+skip,(1<<17)); if(o<0)o=-o;
  for(long i=0;i+nl<=o;i++) if(!memcmp(out+i,nd,nl)){printf("%lx %lx %ld\n",p,i,o);break;}}
}
