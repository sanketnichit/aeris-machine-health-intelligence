# Mathematical audit — shared relative error projection

Let P,S,R be strictly positive primary indication, secondary indication, and unknown reference. Model P=R(1+c+e1), S=R(1+c+e2), with deterministic bounds |c|<=C, |e1|<=A, |e2|<=B. Assume nonnegative bounds and A+C<1, B+C<1. Write t=R/P>0 and q=S/P>0.

For fixed t the allowed c values are three closed intervals:

- [-C,C]
- [1/t-1-A,1/t-1+A]
- [q/t-1-B,q/t-1+B]

Three intervals on the real line have a common point if and only if every pair intersects (the largest lower endpoint cannot exceed the smallest upper endpoint). Pairwise overlap with the first interval gives L=max(1/(1+A+C), q/(1+B+C)), U=min(1/(1-A-C),q/(1-B-C)). Overlap of the two channel intervals gives |q-1| <= (A+B)t. Thus the exact real-arithmetic reference set is [max(L, |q-1|/(A+B)), U] if A+B>0 and the lower endpoint does not exceed U; otherwise empty. If A+B=0, q must equal 1 and the set is [L,U] when nonempty. Necessity and sufficiency follow directly, not from the experiment.

### Consequences

1. Conditional containment: if the true errors obey the declared model and bounds, R/P lies in the set. Feasibility does not prove that those assumptions hold.
2. Agreement non-identifiability: P=S=1530 rpm can mean R=1530 with c=0 or R=1500 with c=.02, both e1=e2=0. When common error is unknown, agreement does not identify reference speed.
3. With A=B=.005, C=.01, P=S=1530 gives an interval [1530/1.015,1530/.985], which excludes 1500. The measurements are compatible under an invalid assumed bound. C=.02 includes that reference. These are illustrative scenarios, not measured sensor data.
4. For fixed A,B,q the feasible set is nested as C increases; empty sets may become nonempty. A diagnostic rule that accepts only a common non-abstaining point decision over a nonempty set can lose decisions as the set expands, but globally monotone acceptance counts are not guaranteed because previously empty sets may become feasible. Invariance concerns the chosen rule, not true fault correctness.
5. The archived implementation (src/common_mode.py) uses floating-point slack and outward rounding, and restricts the ratio domain; the proof concerns exact real arithmetic, not a machine-certified implementation.

### Independent check

Use y=t*c, then the feasible polygon in (t,y) has inequalities (1-A)t+y<=1<=(1+A)t+y, (1-B)t+y<=q<=(1+B)t+y and -Ct<=y<=Ct, t>=0. Enumerating every pair of constraint boundaries with exact BigInt rational comparisons produces the projection independently of the three-interval derivation. The included Node.js script checks 3060 parameter combinations: 1658 feasible, 1402 empty, 0 discrepancies. This is an algebraic cross-check, not independent human review or sensor validation. It does not execute or certify the archived floating-point implementation. No changes to archived experiments.
