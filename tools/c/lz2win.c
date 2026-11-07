#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned char out[1<<16];
long dec(unsigned char*s,long n,long pos,long maxo){long o=0;unsigned bits=0;int cnt=1;
#define GB() ({ if(--cnt==0){ if(pos>=n) return o; bits=s[pos++]; cnt=8;} int _b=bits&1; bits>>=1; _b; })
 while(o<maxo){ int b=GB(); if(!b){ if(pos>=n) return o; out[o++]=s[pos++]; continue;}
  int b2=GB(); long len,dist;
  if(!b2){ if(pos+1>=n) return o; unsigned w=(s[pos]<<8)|s[pos+1]; pos+=2; if(!w) return o; len=w&15; if(len) len+=2; else { len=s[pos++]+1;} dist=w>>4; }
  else { int a=GB(); int c=GB(); len=(a<<1|c)+2; dist=s[pos++]; if(!dist) dist=0x100; }
  for(long i=0;i<len&&o<maxo;i++){ out[o]= (dist>o)?0:out[o-dist];o++;}
 }
 return o;}
int main(int c,char**v){FILE*f=fopen(v[1],"rb");fseek(f,0,2);long n=ftell(f);rewind(f);unsigned char*s=malloc(n);if(fread(s,1,n,f)){};
 FILE*g=fopen(v[2],"rb"); unsigned char ref[8192]; if(fread(ref,1,8192,g)){};
 long lo=strtol(v[3],0,0), hi=strtol(v[4],0,0);
 long best=0,bp=0;
 for(long p=lo;p<hi;p++){ long o=dec(s,n,p,8192); long m=0; for(long i=0;i<o;i++) if(out[i]==ref[i]) m++; if(m>best){best=m;bp=p;} }
 printf("best %lx match %ld\n",bp,best);
}
