"""Blender scene + camera shots for the 'Phantom Traffic Jam' Short.
Run:  xvfb-run -a blender -b --factory-startup -P scene.py -- START END RESX
Renders frames START..END (video frames at 30 fps) to frames/f_####.png
"""
import bpy, json, math, random, sys, os
from mathutils import Vector, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
F_START = int(argv[0]) if len(argv) > 0 else 1
F_END = int(argv[1]) if len(argv) > 1 else 1
RESX = int(argv[2]) if len(argv) > 2 else 1080
FPS = 30

SIM = json.load(open(os.path.join(HERE, 'sim.json')))
DT = SIM['dt']; N = SIM['N']
LANE_Y = -1.8
random.seed(7)

# ---------------------------------------------------------------- scene setup
sc = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = RESX
sc.render.resolution_y = int(RESX * 16 / 9)
sc.render.fps = FPS
sc.render.image_settings.file_format = 'PNG'
ee = sc.eevee
ee.taa_render_samples = 24
ee.use_bloom = True; ee.bloom_intensity = 0.06; ee.bloom_threshold = 1.2; ee.bloom_radius = 5
ee.use_gtao = True; ee.gtao_distance = 2.0
ee.use_soft_shadows = True
ee.shadow_cascade_size = '2048'
ee.use_ssr = False
sc.view_settings.view_transform = 'AgX'
try:
    sc.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass
sc.view_settings.exposure = 0.0


def mat(name, color, rough=0.5, metal=0.0, emit=None, estr=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = estr
    return m


def noise_mat(name, c1, c2, scale, rough=0.9):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale
    nz.inputs['Detail'].default_value = 6
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*c1, 1); ramp.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    return m


# World: Nishita sunset sky
world = bpy.data.worlds.new('W'); sc.world = world; world.use_nodes = True
wn = world.node_tree
sky = wn.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'NISHITA'
sky.sun_elevation = math.radians(7); sky.sun_rotation = math.radians(15)
sky.altitude = 200; sky.air_density = 1.4; sky.dust_density = 3.0
bg = wn.nodes['Background']; bg.inputs['Strength'].default_value = 0.35
wn.links.new(sky.outputs['Color'], bg.inputs['Color'])

# Sun
bpy.ops.object.light_add(type='SUN', location=(0, 0, 50))
sun = bpy.context.object; sun.data.energy = 4.2
sun.data.color = (1.0, 0.72, 0.45); sun.data.angle = math.radians(1.5)
sun.rotation_euler = Vector((-math.cos(math.radians(11)), 0.45, -math.sin(math.radians(11)))).to_track_quat('-Z', 'Y').to_euler()
sun.data.shadow_cascade_max_distance = 250

# Ground
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.02))
g = bpy.context.object; g.scale = (6000, 3000, 1)
g.data.materials.append(noise_mat('grass', (0.035, 0.055, 0.015), (0.11, 0.1, 0.03), 0.02))

# Road + shoulders + markings
X0, X1 = -1500, 1500
def strip(name, y, w, z, m, x0=X0, x1=X1):
    bpy.ops.mesh.primitive_plane_add(size=1, location=((x0 + x1) / 2, y, z))
    o = bpy.context.object; o.name = name; o.scale = (x1 - x0, w, 1)
    o.data.materials.append(m); return o
asphalt = noise_mat('asphalt', (0.025, 0.025, 0.028), (0.06, 0.06, 0.065), 1.5, rough=0.8)
strip('road', 0, 8.2, 0.0, asphalt)
strip('shoulderL', 5.2, 2.2, -0.005, noise_mat('gravel', (0.12, 0.1, 0.08), (0.22, 0.19, 0.15), 3))
strip('shoulderR', -5.2, 2.2, -0.005, bpy.data.materials['gravel'])
white = mat('paint', (0.85, 0.85, 0.8), 0.6)
yellow = mat('paintY', (0.9, 0.62, 0.05), 0.6)
strip('edgeR', -3.85, 0.15, 0.004, white); strip('edgeL', 3.85, 0.15, 0.004, white)
strip('centerA', 0.12, 0.12, 0.004, yellow); strip('centerB', -0.12, 0.12, 0.004, yellow)

# Trees (instanced low-poly pines)
tree_col = bpy.data.collections.new('TreeSrc'); sc.collection.children.link(tree_col)
bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=2.2, depth=6, location=(0, 0, 4.5))
crown = bpy.context.object; crown.data.materials.append(noise_mat('leaf', (0.02, 0.07, 0.025), (0.06, 0.14, 0.04), 1.2))
bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.3, depth=2, location=(0, 0, 1))
trunk = bpy.context.object; trunk.data.materials.append(mat('bark', (0.12, 0.07, 0.04), 0.9))
for o in (crown, trunk):
    for c in o.users_collection: c.objects.unlink(o)
    tree_col.objects.link(o)
tree_col.hide_render = False
sc.view_layers[0].layer_collection.children['TreeSrc'].exclude = True
for i in range(1400):
    x = random.uniform(X0, X1)
    side = random.choice((-1, 1))
    y = side * ((9 if side > 0 else 24) + random.expovariate(1 / 35))
    if abs(y) > 260: continue
    inst = bpy.data.objects.new('tree', None)
    inst.instance_type = 'COLLECTION'; inst.instance_collection = tree_col
    s = random.uniform(0.7, 1.6)
    inst.location = (x, y, 0); inst.scale = (s, s, s * random.uniform(0.9, 1.4))
    inst.rotation_euler.z = random.uniform(0, 6.28)
    sc.collection.objects.link(inst)

# ---------------------------------------------------------------- cars
PAINTS = [(0.8, 0.8, 0.82), (0.55, 0.56, 0.58), (0.03, 0.03, 0.035), (0.5, 0.03, 0.02),
          (0.04, 0.1, 0.32), (0.25, 0.27, 0.3), (0.7, 0.7, 0.72), (0.12, 0.2, 0.14)]
glass = mat('glass', (0.01, 0.012, 0.015), 0.08, 0.3)
tyre = mat('tyre', (0.015, 0.015, 0.015), 0.85)
headm = mat('head', (1, 1, 1), 0.2, emit=(1, 0.95, 0.85), estr=6)

def bevel_box(size, loc, w, segs=3):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    m = o.modifiers.new('b', 'BEVEL'); m.width = w; m.segments = segs
    o.modifiers.new('s', 'WEIGHTED_NORMAL') if False else None
    bpy.ops.object.modifier_apply(modifier='b')
    bpy.ops.object.shade_smooth()
    return o

# template meshes
body_t = bevel_box((4.5, 1.86, 0.62), (0, 0, 0.62), 0.22)
cab_t = bevel_box((2.5, 1.62, 0.62), (-0.25, 0, 1.18), 0.25)
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.36, depth=0.26, rotation=(math.pi / 2, 0, 0))
wheel_t = bpy.context.object; bpy.ops.object.shade_smooth()
for o in (body_t, cab_t, wheel_t):
    o.hide_render = True; o.hide_viewport = True

cars = []
def glow_mat(col, name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    o = nt.nodes.new('ShaderNodeOutputMaterial'); e = nt.nodes.new('ShaderNodeEmission'); e.name = 'Emission'
    e.inputs['Color'].default_value = (*col, 1); e.inputs['Strength'].default_value = 0
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    tc = nt.nodes.new('ShaderNodeTexCoord'); gr = nt.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'
    nt.links.new(tc.outputs['Object'], gr.inputs['Vector']); nt.links.new(gr.outputs['Fac'], mx.inputs['Fac'])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(e.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o.inputs[0])
    m.blend_method = 'BLEND'; m.shadow_method = 'NONE'
    return m
def make_car(i, paint):
    root = bpy.data.objects.new(f'car{i}', None); sc.collection.objects.link(root)
    pm = mat(f'paint{i}', paint, 0.28, 0.55)
    b = bpy.data.objects.new(f'body{i}', body_t.data.copy()); b.data.materials.append(pm)
    c = bpy.data.objects.new(f'cab{i}', cab_t.data); c.data.materials.clear() if False else None
    c.active_material = glass
    for o in (b, c):
        sc.collection.objects.link(o); o.parent = root
    wheels = []
    for wx in (1.45, -1.45):
        for wy in (0.86, -0.86):
            w = bpy.data.objects.new('w', wheel_t.data); w.active_material = tyre
            w.location = (wx, wy, 0.36); sc.collection.objects.link(w); w.parent = root
            wheels.append(w)
    bm = mat(f'brake{i}', (0.3, 0.0, 0.0), 0.3, emit=(1, 0.004, 0.0), estr=1.0)
    for ly in (0.62, -0.62):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(-2.26, ly, 0.86))
        l = bpy.context.object; l.scale = (0.06, 0.42, 0.13); l.active_material = bm; l.parent = root
        bpy.ops.mesh.primitive_cube_add(size=1, location=(2.26, ly, 0.78))
        h = bpy.context.object; h.scale = (0.06, 0.36, 0.11); h.active_material = headm; h.parent = root
    bpy.ops.mesh.primitive_circle_add(vertices=24, radius=1, fill_type='TRIFAN', location=(0, 0, 0.02))
    gl = bpy.context.object; gl.parent = root; gl.active_material = glow_mat((1, 0.03, 0.0), f'glow{i}')
    return dict(root=root, paint=pm, brake=bm, wheels=wheels, base=paint, glow=gl)

for i in range(N):
    paint = random.choice(PAINTS)
    cars.append(make_car(i, paint))
HERO = 0; CALM = 5
HERO_COL = (0.95, 0.55, 0.02); CALM_COL = (0.0, 0.45, 0.9)

# oncoming traffic (constant speed, other lane)
onc = []
for j in range(26):
    c = make_car(100 + j, random.choice(PAINTS))
    c['root'].rotation_euler.z = math.pi
    c['brake'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 1.2
    onc.append((c, random.uniform(X0, X1)))

# ---------------------------------------------------------------- sim lookup
def sim_state(scen, i, t):
    S = SIM[scen]; k = t / DT
    k0 = max(0, min(int(k), len(S['x']) - 2)); f = min(max(k - k0, 0), 1)
    x = S['x'][k0][i] * (1 - f) + S['x'][k0 + 1][i] * f
    a = S['a'][k0][i] * (1 - f) + S['a'][k0 + 1][i] * f
    v = S['v'][k0][i] * (1 - f) + S['v'][k0 + 1][i] * f
    return x, v, a

def carpos(scen, i, t):
    return sim_state(scen, i, t)[0]

def frac_car(scen, fi, t):
    i0 = int(fi); f = fi - i0
    return carpos(scen, i0, t) * (1 - f) + carpos(scen, min(i0 + 1, N - 1), t) * f

def lerp(a, b, u): return a + (b - a) * u
def smooth(u): u = max(0, min(1, u)); return u * u * (3 - 2 * u)

# ---------------------------------------------------------------- shots
# (video start, video end, scenario, sim start, cam function(u, st) -> (loc, target, lens))
def s_hook(u, st):
    xj = -95 + 0
    return (Vector((xj - 75 + 30 * u, -10, 34 - 6 * u)), Vector((xj + 25 + 25 * u, -1, 0)), 28)
def s_chase(u, st):
    x0 = carpos('A', 0, st)
    return (Vector((x0 - 13.5, 1.2, 3.6)), Vector((x0 + 8, LANE_Y, 0.9)), 26)
def s_track(u, st):
    fi = lerp(1.2, 7.8, smooth(u))
    xt = frac_car('A', fi, st)
    return (Vector((xt - 14, -14, 5.5)), Vector((xt + 4, LANE_Y, 0.8)), 30)
def s_aerial(u, st):
    fi = lerp(6, 12, u); xc = frac_car('A', fi, st)
    return (Vector((xc - 55, -4, 62)), Vector((xc + 30, LANE_Y, 0)), 30)
def s_stop(u, st):
    xs = -11
    return (Vector((xs - 26 - 4 * u, -6.5, 2.2)), Vector((xs + 20, LANE_Y + 0.5, 1.0)), 32)
def s_gone(u, st):
    x0 = carpos('A', 0, st)
    return (Vector((x0 + 16 - 4 * u, 5.5, 1.6)), Vector((x0 - 2, LANE_Y, 1.0)), 30)
def s_title(u, st):
    xj = -95
    return (Vector((xj - 30, -2, 60 + 30 * u)), Vector((xj + 10, LANE_Y, 0)), 26)
def s_fix(u, st):
    xc = carpos('B', CALM, st)
    return (Vector((xc - 38 + 6 * u, -16, 22)), Vector((xc + 22, LANE_Y, 0)), 28)

T = json.load(open(os.path.join(HERE, 'timing.json')))
st_ = [m['start'] for m in T]
END = T[-1]['end'] + 1.0
SHOTS = [
    (0.0,      st_[2] - 0.1, 'A', 27.0, s_hook),
    (st_[2] - 0.1, st_[3] - 0.1, 'A', 0.4, s_chase),
    (st_[3] - 0.1, st_[5] - 0.1, 'A', 4.0, s_track),
    (st_[5] - 0.1, st_[6] - 0.1, 'A', 9.8, s_aerial),
    (st_[6] - 0.1, st_[6] + 3.4, 'A', 13.6, s_stop),
    (st_[6] + 3.4, st_[7] - 0.1, 'A', 24.0, s_gone),
    (st_[7] - 0.1, st_[8] - 0.1, 'A', 29.0, s_title),
    (st_[8] - 0.1, END, 'B', 2.5, s_fix),
]

cam_data = bpy.data.cameras.new('cam'); cam_data.sensor_fit = 'VERTICAL'; cam_data.sensor_height = 24
cam_data.clip_end = 3000
cam = bpy.data.objects.new('cam', cam_data); sc.collection.objects.link(cam); sc.camera = cam

def update(vt):
    for (a, b, scen, s0, fn) in SHOTS:
        if a <= vt < b or (vt >= b and (a, b) == SHOTS[-1][:2]):
            break
    u = (vt - a) / (b - a); st = s0 + (vt - a)
    loc, tgt, lens = fn(u, st)
    cam.location = loc
    cam.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
    cam_data.lens = lens * 24 / 36 * 1.0
    for i, c in enumerate(cars):
        x, v, acc = sim_state(scen, i, st)
        c['root'].location = (x, LANE_Y, 0)
        for w in c['wheels']: w.rotation_euler = (math.pi / 2, x / 0.36, 0)
        braking = max(0.0, min(1.0, (-acc - 0.4) / 1.2))
        stopped = 1.0 if v < 0.5 else 0.0
        lvl = max(braking, stopped)
        e = 1.0 + 9 * lvl
        c['glow'].scale = (lvl * 3.2 + 0.001, lvl * 1.9 + 0.001, 1)
        gm = c['glow'].active_material.node_tree.nodes['Emission']
        gm.inputs['Strength'].default_value = 2.5 * lvl
        c['brake'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = e
        col = c['base']
        if i == HERO: col = HERO_COL
        if i == CALM and scen == 'B':
            col = CALM_COL
            c['glow'].scale = (3.4, 2.1, 1)
            n = c['glow'].active_material.node_tree.nodes['Emission']
            n.inputs['Color'].default_value = (0.0, 0.9, 0.35, 1); n.inputs['Strength'].default_value = 3
        elif i == CALM:
            c['glow'].active_material.node_tree.nodes['Emission'].inputs['Color'].default_value = (1, 0.03, 0, 1)
        c['paint'].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*col, 1)
    for c, ox in onc:
        x = ((ox - 22 * (vt + 40)) - X0) % (X1 - X0) + X0
        c['root'].location = (x, -LANE_Y, 0)
        for w in c['wheels']: w.rotation_euler = (math.pi / 2, -x / 0.36, 0)

out = os.path.join(HERE, 'frames'); os.makedirs(out, exist_ok=True)
print('TOTAL_FRAMES', int(END * FPS))
import time
FRAMES = [int(v) for v in argv[3].split(',')] if len(argv) > 3 else range(F_START, min(F_END, int(END * FPS)) + 1)
for f in FRAMES:
    t0 = time.time()
    update((f - 1) / FPS)
    sc.render.filepath = os.path.join(out, f'f_{f:04d}.png')
    bpy.ops.render.render(write_still=True)
    print('FRAME', f, round(time.time() - t0, 2), flush=True)
