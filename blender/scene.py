"""
Last Soul — scene builder (headless Blender).

Metaball-based faceless silhouette figure + single window light + volumetric haze.
Metaballs blend into ONE continuous surface, so the figure reads as a designed
silhouette instead of floating primitives (the v2 failure mode).

usage:
  blender -b --factory-startup -P blender/scene.py -- <variant> <res_x> <res_y> <samples> <frames> <outdir>
  variants: wide | close | low | anim
"""
import bpy, math, sys, mathutils

a = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
VARIANT = a[0] if a else "wide"
RX, RY  = (int(a[1]), int(a[2])) if len(a) > 2 else (960, 540)
SAMP    = int(a[3]) if len(a) > 3 else 32
FRAMES  = int(a[4]) if len(a) > 4 else 1
OUT     = a[5] if len(a) > 5 else "/tmp/out"

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ───────────────────────── materials ─────────────────────────
def mat(name, col, rough=0.6, metal=0.0, emit=None, es=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit is not None:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = es
    return m

BLACK  = mat("Figure", (0.004,0.004,0.006), 0.42)
WALL   = mat("Wall",   (0.028,0.032,0.040), 0.94)
DESK   = mat("Desk",   (0.050,0.041,0.034), 0.68)
PAPER  = mat("Paper",  (0.58,0.56,0.52),    0.88)
WOOD   = mat("Pencil", (0.30,0.15,0.05),    0.55)
GLASS  = mat("WinGlass",(0.9,0.75,0.55), 1.0, emit=(1.0,0.79,0.56), es=9.0)
MFRAME = mat("WinFrame",(0.018,0.018,0.022), 0.72)

def link(o): bpy.context.collection.objects.link(o); return o

# ───────────────────────── room ─────────────────────────
bpy.ops.mesh.primitive_plane_add(size=24, location=(0,0,0))
bpy.context.object.data.materials.append(WALL)
bpy.ops.mesh.primitive_plane_add(size=24, location=(0,4.2,2.6), rotation=(math.radians(90),0,0))
bpy.context.object.data.materials.append(WALL)

# ───────────────────────── window = THE single source ─────────────────────────
WX, WY, WZ = 1.02, 4.16, 1.66
bpy.ops.mesh.primitive_plane_add(size=1, location=(WX, WY-0.02, WZ), rotation=(math.radians(-90),0,0))
w = bpy.context.object; w.scale = (0.70, 0.50, 1); w.data.materials.append(GLASS)

def bar(loc, scale):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.scale = scale; o.data.materials.append(MFRAME); return o
for dx in (-0.70, -0.233, 0.233, 0.70):
    bar((WX + dx*0.5, WY-0.05, WZ), (0.024, 0.035, 1.02))
bar((WX, WY-0.05, WZ), (0.70, 0.035, 0.026))
bar((WX, WY-0.05, WZ+0.48), (0.76, 0.045, 0.032))
bar((WX, WY-0.05, WZ-0.48), (0.76, 0.045, 0.032))

bpy.ops.object.light_add(type='AREA', location=(WX, WY-0.30, WZ))
key = bpy.context.object
key.data.energy = 240; key.data.size = 1.3; key.data.color = (1.0,0.77,0.53)
key.rotation_euler = (math.radians(-90), 0, 0)

# ───────────────────────── desk ─────────────────────────
bpy.ops.mesh.primitive_cube_add(size=1, location=(0.26, 1.34, 0.755))
d = bpy.context.object; d.scale = (1.10, 0.60, 0.045); d.data.materials.append(DESK)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0.02, 1.34, 0.37))
bpy.context.object.scale = (0.055, 0.55, 0.74); bpy.context.object.data.materials.append(DESK)

bpy.ops.mesh.primitive_plane_add(size=1, location=(0.14, 1.22, 0.800), rotation=(0,0,math.radians(11)))
p = bpy.context.object; p.scale = (0.32, 0.22, 1); p.data.materials.append(PAPER)
for dx in (-0.05, 0.0, 0.05):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0058, depth=0.20, location=(0.56+dx, 1.16, 0.818),
                                        rotation=(math.radians(90), 0, math.radians(7)))
    bpy.context.object.data.materials.append(WOOD)

# ───────────────────────── figure: primitives → join → voxel remesh ─────────────────────────
# (metaballs would not merge reliably; voxel remesh gives ONE continuous surface)
PARTS = []

def ball(co, r, scl=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=co, segments=32, ring_count=16)
    o = bpy.context.object; o.scale = scl
    o.data.materials.append(BLACK); PARTS.append(o); return o

def limb(p0, p1, r0, r1):
    """یک استوانهٔ مخروطی بین دو نقطه"""
    p0, p1 = mathutils.Vector(p0), mathutils.Vector(p1)
    v = p1 - p0; L = v.length
    bpy.ops.mesh.primitive_cone_add(radius1=r0, radius2=r1, depth=L,
                                   location=(p0 + p1) / 2, vertices=24)
    o = bpy.context.object
    o.rotation_euler = v.to_track_quat('Z', 'Y').to_euler()
    o.data.materials.append(BLACK); PARTS.append(o); return o

CX = 0.26                       # وسط میز
SEAT_Y = 1.82                   # نشسته، پشت میز
# ستون فقرات: لگن → کمر → قفسهٔ سینه (کمی به جلو خم)
ball((CX, SEAT_Y,        0.455), 0.150, (1.15, 0.95, 0.80))   # لگن
ball((CX, SEAT_Y-0.045,  0.600), 0.145, (1.10, 0.92, 0.90))   # شکم
ball((CX, SEAT_Y-0.095,  0.760), 0.150, (1.12, 0.88, 0.95))   # کمر
ball((CX, SEAT_Y-0.135,  0.900), 0.148, (1.10, 0.86, 0.92))   # قفسهٔ سینه
ball((CX, SEAT_Y-0.165,  1.010), 0.120, (1.00, 0.90, 0.80))   # شانه‌ها
ball((CX, SEAT_Y-0.180,  1.105), 0.055)                        # گردن
head = ball((CX, SEAT_Y-0.190, 1.245), 0.108, (1.0, 1.06, 1.14))  # سر بی‌چهره

for s_ in (-1, 1):
    ball((CX + s_*0.155, SEAT_Y-0.165, 1.030), 0.088)                     # سرشانه
    limb((CX + s_*0.170, SEAT_Y-0.170, 1.020), (CX + s_*0.200, SEAT_Y-0.320, 0.860), 0.058, 0.050)
    limb((CX + s_*0.200, SEAT_Y-0.320, 0.860), (CX + s_*0.145, SEAT_Y-0.560, 0.805), 0.050, 0.040)
    ball((CX + s_*0.140, SEAT_Y-0.575, 0.800), 0.045, (1.3, 1.0, 0.85))   # دست روی کاغذ
limb((CX-0.135, SEAT_Y-0.020, 0.450), (CX-0.130, SEAT_Y-0.330, 0.505), 0.120, 0.100)  # ران
limb((CX+0.135, SEAT_Y-0.020, 0.450), (CX+0.130, SEAT_Y-0.330, 0.505), 0.120, 0.100)

bpy.ops.object.select_all(action='DESELECT')
for o in PARTS: o.select_set(True)
bpy.context.view_layer.objects.active = PARTS[0]
bpy.ops.object.join()
fig = bpy.context.object
fig.name = "Figure"

rm = fig.modifiers.new("Remesh", 'REMESH')
rm.mode = 'VOXEL'; rm.voxel_size = 0.016; rm.use_smooth_shade = True
sm = fig.modifiers.new("Smooth", 'SMOOTH'); sm.factor = 0.75; sm.iterations = 12
bpy.ops.object.modifier_apply(modifier="Remesh")
bpy.ops.object.modifier_apply(modifier="Smooth")
bpy.ops.object.shade_smooth()

# ───────────────────────── haze ─────────────────────────
bpy.ops.mesh.primitive_cube_add(size=1, location=(0.1, 2.2, 1.4))
vol = bpy.context.object; vol.scale = (3.4, 3.6, 2.8)
vm = bpy.data.materials.new("Haze"); vm.use_nodes = True
nt = vm.node_tree; nt.nodes.clear()
o_ = nt.nodes.new("ShaderNodeOutputMaterial"); pv = nt.nodes.new("ShaderNodeVolumePrincipled")
pv.inputs["Density"].default_value = 0.020
pv.inputs["Anisotropy"].default_value = 0.62
pv.inputs["Color"].default_value = (1.0,0.93,0.84,1)
nt.links.new(pv.outputs[0], o_.inputs["Volume"])
vol.data.materials.append(vm)

# ───────────────────────── camera per variant ─────────────────────────
CAM = {
    #            location              target                   lens  fstop  push
    "wide":  ((-2.30, -0.95, 1.30), (0.26, 1.72, 1.00),  46,  3.2, 0.20),
    "close": ((-0.62, -0.10, 1.36), (0.26, 1.60, 1.22),  85,  1.8, 0.05),
    "low":   (( 0.26, -1.15, 0.38), (0.26, 1.70, 1.18),  35,  4.0, 0.14),
    "anim":  ((-2.30, -0.95, 1.30), (0.26, 1.72, 1.00),  46,  3.2, 0.34),
}
loc, tgt, lens, fstop, push = CAM.get(VARIANT, CAM["wide"])

bpy.ops.object.camera_add(location=loc)
cam = bpy.context.object; sc.camera = cam
cam.data.lens = lens
cam.data.dof.use_dof = True
cam.data.dof.focus_object = fig
cam.data.dof.aperture_fstop = fstop
tv = mathutils.Vector(tgt) - mathutils.Vector(loc)
rot = tv.to_track_quat('-Z', 'Y').to_euler()

f0, f1 = 1, max(FRAMES, 1)
for fr, k in ((f0, 0.0), (f1, 1.0)):
    p_ = mathutils.Vector(loc) + (mathutils.Vector(tgt) - mathutils.Vector(loc)).normalized() * (push * k)
    cam.location = p_; cam.rotation_euler = rot
    cam.keyframe_insert("location", frame=fr)
    cam.keyframe_insert("rotation_euler", frame=fr)

# ───────────────────────── render ─────────────────────────
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = SAMP
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 6
sc.cycles.volume_bounces = 1
sc.render.resolution_x, sc.render.resolution_y = RX, RY
sc.render.resolution_percentage = 100
sc.render.fps = 24
sc.frame_start, sc.frame_end = 1, f1
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.image_settings.file_format = 'PNG'

if FRAMES <= 1:
    sc.frame_set(max(1, f1))
    sc.render.filepath = f"{OUT}/{VARIANT}.png"
    bpy.ops.render.render(write_still=True)
else:
    sc.render.filepath = f"{OUT}/{VARIANT}_"
    bpy.ops.render.render(animation=True)
