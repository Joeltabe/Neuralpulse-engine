#!/usr/bin/env python3
"""Generate a simplified fsaverage5-like brain mesh as JSON for Three.js."""
import json
import numpy as np
from scipy.spatial import Delaunay

np.random.seed(42)

# Use icosphere subdivision approach for a brain-like shape
# Start with an icosahedron and subdivide

def icosahedron():
    t = (1.0 + np.sqrt(5.0)) / 2.0
    verts = np.array([
        [-1,  t,  0], [ 1,  t,  0], [-1, -t,  0], [ 1, -t,  0],
        [ 0, -1,  t], [ 0,  1,  t], [ 0, -1, -t], [ 0,  1, -t],
        [ t,  0, -1], [ t,  0,  1], [-t,  0, -1], [-t,  0,  1]
    ], dtype=float)
    faces = np.array([
        [0,11,5],[0,5,1],[0,1,7],[0,7,10],[0,10,11],
        [1,5,9],[5,11,4],[11,10,2],[10,7,6],[7,1,8],
        [3,9,4],[3,4,2],[3,2,6],[3,6,8],[3,8,9],
        [4,9,5],[2,4,11],[6,2,10],[8,6,7],[9,8,1]
    ], dtype=int)
    return verts, faces

def subdivide(verts, faces):
    new_verts = list(verts)
    mid_cache = {}
    
    def get_mid(i, j):
        key = (min(i, j), max(i, j))
        if key not in mid_cache:
            p = (new_verts[i] + new_verts[j]) / 2.0
            p = p / np.linalg.norm(p)
            mid_cache[key] = len(new_verts)
            new_verts.append(p)
        return mid_cache[key]
    
    new_faces = []
    for f in faces:
        a, b, c = f
        ab = get_mid(a, b)
        bc = get_mid(b, c)
        ca = get_mid(c, a)
        new_faces.append([a, ab, ca])
        new_faces.append([b, bc, ab])
        new_faces.append([c, ca, bc])
        new_faces.append([ab, bc, ca])
    
    return np.array(new_verts), np.array(new_faces)

# Generate brain mesh
verts, faces = icosahedron()
for _ in range(3):
    verts, faces = subdivide(verts, faces)

verts = np.array(verts)
faces = np.array(faces)

# Deform sphere into brain shape
theta = np.arctan2(verts[:, 2], verts[:, 0])
phi = np.arcsin(np.clip(verts[:, 1], -1, 1))

# Brain-like deformation
R = 1.0
# Make it elongated front-back (anterior-posterior)
ap_stretch = 1.2 - 0.2 * np.sin(theta)  # Wider at back
# Add asymmetry for hemispheres
hemi = np.sign(verts[:, 2])
# Sulci/gyri patterns
sulci = 0.03 * np.sin(5 * theta + 3 * phi) + 0.02 * np.cos(7 * phi)
# Temporal lobe bulge
temporal = 0.08 * np.exp(-((phi - 0.3)**2) / 0.1) * (1 - np.abs(hemi) * 0.3)
# Frontal pole
frontal = 0.06 * np.exp(-((theta + np.pi/2)**2) / 0.3) * np.exp(-(phi**2) / 0.2)
# Occipital pole  
occipital = 0.05 * np.exp(-((theta - np.pi/2)**2) / 0.2) * np.exp(-(phi**2) / 0.15)

rx = R * np.cos(phi) * np.cos(theta)
ry = R * np.sin(phi)
rz = R * np.cos(phi) * np.sin(theta)

# Apply deformations
scale_x = 1.15 + 0.02 * np.sin(theta)  # Slightly wider
scale_y = 1.0 + 0.05 * np.cos(2 * phi)
scale_z = ap_stretch

deformed = np.column_stack([
    rx * scale_x + temporal * np.cos(theta) + frontal * np.cos(theta + np.pi/2),
    ry * scale_y + sulci + temporal * np.sin(phi),
    rz * scale_z + temporal * np.sin(theta) + occipital * np.sin(theta - np.pi/2)
])

# Normalize to unit size
deformed = deformed / np.max(np.linalg.norm(deformed, axis=1))

# Compute vertex normals
def compute_normals(v, f):
    normals = np.zeros_like(v)
    for tri in f:
        v0, v1, v2 = v[tri]
        n = np.cross(v1 - v0, v2 - v0)
        n /= np.linalg.norm(n) + 1e-10
        normals[tri] += n
    norms = np.linalg.norm(normals, axis=1)
    norms[norms == 0] = 1
    normals /= norms[:, None]
    return normals

normals = compute_normals(deformed, faces)

# Assign ROI labels based on vertex position
# fsaverage5 parcellation-inspired regions
def assign_roi(v):
    x, y, z = v
    # Lateral/medial
    hemi = "L" if z < 0 else "R"
    
    # Visual cortex (occipital) - posterior (negative x)
    if x < -0.3 and abs(y) < 0.4:
        return f"{hemi}_V1" if np.random.random() < 0.3 else f"{hemi}_V2"
    
    # Motor/sensory (central)
    if abs(x) < 0.2 and abs(y) > 0.3:
        return f"{hemi}_M1" if y > 0 else f"{hemi}_S1"
    
    # Prefrontal (anterior)
    if x > 0.3 and abs(y) < 0.5:
        return f"{hemi}_DLPFC" if np.random.random() < 0.5 else f"{hemi}_VMPFC"
    
    # Temporal
    if abs(y) < -0.2 and abs(z) > 0.3:
        return f"{hemi}_STG" if z > 0 else f"{hemi}_MTG"
    
    # Parietal
    if abs(x) < 0.3 and y < -0.2:
        return f"{hemi}_IPS" if np.random.random() < 0.5 else f"{hemi}_SPL"
    
    # Default assignment
    return f"{hemi}_PCC" if y < -0.1 else f"{hemi}_Precuneus"

roi_labels = [assign_roi(v) for v in deformed]

# Simplify: assign to broader ROIs for cleaner visualization
roi_to_group = {
    "V1": "Visual Cortex", "V2": "Visual Cortex",
    "M1": "Motor/Somatosensory", "S1": "Motor/Somatosensory",
    "DLPFC": "Prefrontal", "VMPFC": "Prefrontal",
    "STG": "Temporal", "MTG": "Temporal",
    "IPS": "Parietal", "SPL": "Parietal",
    "PCC": "Default Mode", "Precuneus": "Default Mode",
}

roi_groups = []
for label in roi_labels:
    hemi = label[0]
    core = label[2:]
    for key, group in roi_to_group.items():
        if core.startswith(key):
            roi_groups.append(f"{hemi}_{group}")
            break
    else:
        roi_groups.append(f"{hemi}_Other")

# Unique group IDs
unique_groups = sorted(set(roi_groups))
group_to_id = {g: i for i, g in enumerate(unique_groups)}
group_ids = [group_to_id[g] for g in roi_groups]

# Build output
mesh_data = {
    "vertices": deformed.tolist(),
    "faces": faces.tolist(),
    "normals": normals.tolist(),
    "roi_groups": roi_groups,
    "group_ids": group_ids,
    "unique_groups": unique_groups,
    "n_vertices": len(deformed),
    "n_faces": len(faces),
}

output_path = "../frontend/js/brain_mesh.json"
with open(output_path, "w") as f:
    json.dump(mesh_data, f)

print(f"Generated brain mesh: {len(deformed)} vertices, {len(faces)} faces")
print(f"Groups: {len(unique_groups)}")
print(f"File: {output_path}")
