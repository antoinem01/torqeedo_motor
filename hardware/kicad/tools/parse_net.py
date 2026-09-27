import re, sys, json
src = open(sys.argv[1]).read()
# tokenize s-expr
def parse(s):
    toks = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', s)
    stack=[[]]
    for t in toks:
        if t=='(': stack.append([])
        elif t==')':
            top=stack.pop(); stack[-1].append(top)
        else:
            if t.startswith('"'): t=t[1:-1]
            stack[-1].append(t)
    return stack[0][0]
tree=parse(src)
def find(node,name):
    return [x for x in node if isinstance(x,list) and x and x[0]==name]
comps={}
for c in find(find(tree,'components')[0],'comp'):
    ref=find(c,'ref')[0][1]
    val=find(c,'value')[0][1]
    fp=find(c,'footprint')
    # symbol UUID: lets KiCad match board footprints back to schematic symbols,
    # so "Update PCB from Schematic" keeps placement instead of duplicating parts
    ts=[x[1] for x in find(c,'tstamps') if len(x)>1 and x[1]!='/']
    comps[ref]={'value':val,'fp':fp[0][1] if fp else None,'uuid':ts[0] if ts else None}
nets={}
for n in find(find(tree,'nets')[0],'net'):
    name=find(n,'name')[0][1]
    nodes=[(find(x,'ref')[0][1], find(x,'pin')[0][1]) for x in find(n,'node')]
    nets[name]=nodes
json.dump({'comps':comps,'nets':nets}, open(sys.argv[2],'w'), indent=1)
missing=[r for r,d in comps.items() if not d['uuid']]
if missing: print("WARNING: no UUID for", missing)
for ref,d in sorted(comps.items()): print(f"{ref:9s} {d['value']:32s} {d['fp']}")
print("="*70)
for name,nodes in nets.items():
    if name.startswith('unconnected'): continue
    print(f"{name:12s} ({len(nodes)}) " + " ".join(f"{r}.{p}" for r,p in nodes))
