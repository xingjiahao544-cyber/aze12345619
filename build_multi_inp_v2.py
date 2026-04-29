"""
build_multi_inp_v2.py - 正确的 3道×3层 多道搭接 INP 生成器
"""
import os

DIR = r"/mnt/d/temp/duoceng3"
os.makedirs(DIR, exist_ok=True)

# === 几何与网格 ===
sub_w, sub_d, sub_l = 0.018, 0.0048, 0.024
pow_w, pow_d, pow_l = 0.0018, 0.0018, 0.024
ms_sub = 0.0012
ms_pow = 0.0003
num_tracks = 3
track_sp = pow_w * 0.70    # 1.26mm
tx_start = (sub_w - (pow_w + (num_tracks-1)*track_sp)) / 2.0

nx_sub, ny_sub, nz_sub = int(sub_w/ms_sub), int(sub_d/ms_sub), int(sub_l/ms_sub)
nx_pow, ny_pow, nz_pow = int(pow_w/ms_pow), int(pow_d/ms_pow), int(pow_l/ms_pow)

lines = []
def L(s): lines.append(s)
def nL(s): lines.append(s.rstrip())

# === HEADER ===
L("*Heading")
L("** 3-Track x 3-Layer Laser Cladding (30% overlap)")
L("*Preprint, echo=NO, model=NO, history=NO, contact=NO")

# === SUBSTRATE PART ===
L("*Part, name=Substrate")
# Nodes
nid = 1
for k in range(nz_sub+1):
    for j in range(ny_sub+1):
        for i in range(nx_sub+1):
            L(f"{nid:>8d}, {i*ms_sub:.10f}, {j*ms_sub:.10f}, {k*ms_sub:.10f}")
            nid += 1
n_nodes_sub = nid - 1

# Elements
eid = 1
for k in range(nz_sub):
    for j in range(ny_sub):
        for i in range(nx_sub):
            n0 = 1 + k*(nx_sub+1)*(ny_sub+1) + j*(nx_sub+1) + i
            n1 = n0+1; n2 = n0+(nx_sub+1); n3 = n2+1
            n4 = n0+(nx_sub+1)*(ny_sub+1); n5 = n4+1; n6 = n4+(nx_sub+1); n7 = n6+1
            L(f"{eid:>8d}, {n0:>8d}, {n1:>8d}, {n3:>8d}, {n2:>8d}, {n4:>8d}, {n5:>8d}, {n7:>8d}, {n6:>8d}")
            eid += 1
n_elems_sub = eid - 1

L("*Nset, nset=All-Substrate, generate")
L(f"    1, {n_nodes_sub}, 1")
L("*Elset, elset=All-Substrate, generate")
L(f"    1, {n_elems_sub}, 1")
# Top face for contact
top_elems = list(range(n_elems_sub-nx_sub+1, n_elems_sub+1))
L(f"*Elset, elset=_Substrate-Top")
for i in range(0, len(top_elems), 16):
    chunk = top_elems[i:i+16]
    L("  " + ", ".join(str(e) for e in chunk) + ",")
nL(lines[-1].rstrip(","))
L("*Surface, type=ELEMENT, name=Top")
L("_Substrate-Top, S2")
L("*Solid Section, elset=All-Substrate, material=Material-1")
L(",")
L("*End Part")

# === POWDER PART ===
L("*Part, name=Powder")
# Nodes (Part内部编号 1~n_nodes_pow)
nid = 1
for k in range(nz_pow+1):
    for j in range(ny_pow+1):
        for i in range(nx_pow+1):
            L(f"{nid:>8d}, {i*ms_pow:.10f}, {j*ms_pow:.10f}, {k*ms_pow:.10f}")
            nid += 1
n_nodes_pow = nid - 1

# Elements (1~n_elems_pow)
eid = 1
for k in range(nz_pow):
    for j in range(ny_pow):
        for i in range(nx_pow):
            n0 = 1 + k*(nx_pow+1)*(ny_pow+1) + j*(nx_pow+1) + i
            n1 = n0+1; n2 = n0+(nx_pow+1); n3 = n2+1
            n4 = n0+(nx_pow+1)*(ny_pow+1); n5 = n4+1; n6 = n4+(nx_pow+1); n7 = n6+1
            L(f"{eid:>8d}, {n0:>8d}, {n1:>8d}, {n3:>8d}, {n2:>8d}, {n4:>8d}, {n5:>8d}, {n7:>8d}, {n6:>8d}")
            eid += 1
n_elems_pow = eid - 1

# Bottom face elements (j=0 for all k,i)
bot_elems = []
for k in range(nz_pow):
    for j in range(ny_pow):
        for i in range(nx_pow):
            if j == 0:
                bot_elems.append(1 + k*nx_pow*ny_pow + j*nx_pow + i)

L("*Elset, elset=_Powder-Bot")
for i in range(0, len(bot_elems), 16):
    chunk = bot_elems[i:i+16]
    L("  " + ", ".join(str(e) for e in chunk) + ",")
nL(lines[-1].rstrip(","))
L("*Surface, type=ELEMENT, name=Bottom")
L("_Powder-Bot, S3")

# All-Elements set
L("*Nset, nset=All-Elements, generate")
L(f"    1, {n_nodes_pow}, 1")
L("*Elset, elset=All-Elements, generate")
L(f"    1, {n_elems_pow}, 1")
L("*Solid Section, elset=All-Elements, material=Material-1")
L(",")

# Activation sets: 3 layers x 40 Z-groups
elems_per_layer = n_elems_pow // 3
elems_per_zg = elems_per_layer // 40
set_counter = 1
for ly in range(3):
    for zi in range(40):
        zs = 1 + ly*elems_per_layer + zi*elems_per_zg
        ze = zs + elems_per_zg - 1
        L(f"*Elset, elset=Set-{set_counter:03d}, generate")
        L(f"    {zs:>6d}, {ze:>6d}, 1")
        set_counter += 1

L("*End Part")

# === MATERIAL ===
L("*Material, name=Material-1")
L("*Conductivity\n 13.1,  10.\n  14., 100.\n  23., 300.\n  36., 500.\n  38., 800.\n  35.,1200.\n  70.,1350.\n 100.,1450.\n 130.,1800.\n 170.,3000.")
L("*Density\n7740.,  10.\n7710., 100.\n7680., 300.\n7580., 500.\n7470., 800.\n7350.,1200.\n7000.,1500.\n6900.,1600.\n6900.,3000.")
L("*Latent Heat\n270000., 1384.85, 1446.85")
L("*Specific Heat\n450.,  10.\n500., 100.\n650., 300.\n750., 500.\n850., 800.\n780.,1200.\n920.,1500.\n800.,1600.\n800.,3000.")
L("*Physical Constants, absolute zero=-273.15, stefan boltzmann=5.67037e-08")

# === ASSEMBLY ===
L("*Assembly, name=Assembly")
L("*Instance, name=Substrate-1, part=Substrate")
L("*End Instance")

track_x = [tx_start + t*track_sp for t in range(num_tracks)]
for t in range(num_tracks):
    L(f"*Instance, name=Powder-{t+1}, part=Powder")
    L(f"      {track_x[t]:.10f},       {sub_d:.10f},            0.")
    L("*End Instance")

# Surface references for Contact (Part-level surfaces through instances)
# Substrate-1.Top and Powder-1.Bottom etc are already defined in parts

# Activation sets per track
for t in range(num_tracks):
    for s in range(120):
        L(f"*Elset, elset=Track{t+1}-Set-{s+1:03d}, instance=Powder-{t+1}, generate")
        L(f"    {1+s*elems_per_zg:>6d}, {1+(s+1)*elems_per_zg-1:>6d}, 1")

L("*End Assembly")

# === CONTACT ===
for t in range(num_tracks):
    L(f"*Surface Interaction, name=Contact-Thermal-{t+1}")
    L("*Gap Conductance")
    L("1e7, 0.0")
    L("1e7, 1.0")
    L(f"*Contact Pair, interaction=Contact-Thermal-{t+1}")
    L(f"Substrate-1.Top, Powder-{t+1}.Bottom")

# === STEPS ===
L("** STEP: Step-1")
L("*Step, name=Step-1, nlgeom=NO, inc=1000000")
L("*Heat Transfer, end=PERIOD, deltmx=500.")
L("10.0, 0.1, 1e-10, 1.0,")
for t in range(num_tracks):
    L(f"*Model Change, remove")
    L(f"Powder-{t+1}.Track{t+1}-Set-001")
L("*End Step")

step_num = 2
for t in range(num_tracks):
    for ly in range(3):
        for zi in range(40):
            sid = ly*40 + zi + 1
            L(f"** STEP: Step-{step_num}")
            L(f"*Step, name=Step-{step_num}, nlgeom=NO, inc=1000000")
            L(f"*Heat Transfer, end=PERIOD, deltmx=50.")
            L("0.012, 0.12, 1.2e-05, 0.12,")
            L(f"*Model Change, add")
            L(f"Powder-{t+1}.Track{t+1}-Set-{sid:03d}")
            L(f"*Dflux")
            L(f"Powder-{t+1}.All-Elements, BFNU, 1.")
            L("*End Step")
            step_num += 1
        # Cooling step (except after last layer of last track)
        if ly < 2 or t < num_tracks - 1:
            L(f"** STEP: Step-{step_num} (Cool)")
            L(f"*Step, name=Step-{step_num}, nlgeom=NO, inc=5000000")
            L(f"*Heat Transfer, end=PERIOD, deltmx=200.")
            L("0.0012, 10., 1.2e-05, 1.,")
            L("*End Step")
            step_num += 1

# === WRITE ===
out = os.path.join(DIR, "multi_track.inp")
with open(out, 'w') as f:
    f.write('\n'.join(lines))

print(f"Written: {out}")
print(f"Steps: {step_num-1}")
print(f"Substrate: {n_elems_sub} elems, Powder: {n_elems_pow} elems/track")
print(f"Total: {n_elems_sub + num_tracks*n_elems_pow} elems")
print(f"Bot face: {len(bot_elems)} elems")
