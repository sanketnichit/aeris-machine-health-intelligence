function verifyProjection(){
 const frac=(n,d)=>{if(d<0n){n=-n;d=-d}return [n,d]};
 const cmp=(a,b)=>{const x=a[0]*b[1]-b[0]*a[1];return x<0n?-1:x>0n?1:0};
 const max=(a,b)=>cmp(a,b)>=0?a:b,min=(a,b)=>cmp(a,b)<=0?a:b;
 const L=1000n;let cases=0,feasible=0,empty=0,failures=0;
 for(const a of [0n,1n,5n,11n,51n,100n])for(const b of [0n,1n,5n,11n,51n,100n])for(const c of [0n,1n,10n,50n,100n])for(const q of [500n,850n,900n,950n,980n,990n,995n,999n,1000n,1001n,1005n,1010n,1020n,1050n,1100n,1150n,1500n]){
  cases++;
  // x=R/P, y=x*shared error. Independent polygon constraints, all integer coefficients.
  const rows=[[L-a,L,L],[-L-a,-L,-L],[L-b,L,q],[-L-b,-L,-q],[-c,L,0n],[-c,-L,0n],[-1n,0n,0n]];
  const vs=[];
  for(let i=0;i<rows.length;i++)for(let j=i+1;j<rows.length;j++){
    const [u,v,w]=rows[i],[p,s,t]=rows[j];let den=u*s-v*p;if(den===0n)continue;let xn=w*s-v*t,yn=u*t-w*p;if(den<0n){den=-den;xn=-xn;yn=-yn}if(rows.every(([aa,bb,cc])=>aa*xn+bb*yn<=cc*den))vs.push([xn,den]);
  }
  let lo=max(frac(L,L+a+c),frac(q,L+b+c)),hi=min(frac(L,L-a-c),frac(q,L-b-c));let formulaEmpty=false;
  const diff=q>=L?q-L:L-q;if(a+b===0n){if(diff!==0n)formulaEmpty=true;}else lo=max(lo,frac(diff,a+b));if(cmp(lo,hi)>0)formulaEmpty=true;
  if(vs.length===0){empty++;if(!formulaEmpty)failures++;}else{feasible++;const vlo=vs.reduce(min),vhi=vs.reduce(max);if(formulaEmpty||cmp(vlo,lo)!==0||cmp(vhi,hi)!==0)failures++;}
 }
 return {cases,feasible,empty,failures};
}
const result = verifyProjection();
console.log(JSON.stringify(result, null, 2));
if(result.failures) process.exitCode = 1;
