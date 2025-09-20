bl_info = {
    "name": "Game Crater Generator",
    "author": "Game Asset Developer",
    "version": (1, 0, 1),
    "blender": (4, 2, 0),
    "location": "View3D > Add > Mesh > Game Crater",
    "description": "Generate clean game-ready crater meshes with dual materials and optimized UV mapping",
    "category": "Add Mesh",
    "doc_url": "",
    "tracker_url": "",
}

import bpy
import bmesh
import mathutils
import math
import random
from mathutils import Vector, noise
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import (
    FloatProperty, IntProperty, BoolProperty, 
    EnumProperty, PointerProperty
)

class CraterProperties(PropertyGroup):
    """Properties for crater generation based on real crater analysis"""
    
    outer_radius: FloatProperty(
        name="Outer Radius",
        description="Outer radius of crater (base/ground level)",
        default=2.6,
        min=0.5,
        max=100.0,
        unit='LENGTH',
        step=10
    )
    
    inner_radius: FloatProperty(
        name="Inner Radius", 
        description="Inner radius of crater (rim/lip)",
        default=1.3,
        min=0.1,
        max=50.0,
        unit='LENGTH',
        step=10
    )
    
    depth: FloatProperty(
        name="Crater Depth", 
        description="Maximum crater depth",
        default=0.5,
        min=0.1,
        max=100.0,
        unit='LENGTH',
        step=10
    )
    
    rim_height: FloatProperty(
        name="Rim Height",
        description="Height of crater rim above ground level",
        default=0.58,
        min=0.0,
        max=100.0,
        unit='LENGTH',
        step=10
    )
    
    resolution: IntProperty(
        name="Resolution",
        description="Crater mesh resolution (higher = more detail)",
        default=24,
        min=8,
        max=500,
        step=4
    )
    
    noise_strength: FloatProperty(
        name="Inside Surface Noise",
        description="Surface detail noise strength inside crater rim",
        default=0.05,
        min=0.0,
        max=30.0,
        step=1
    )
    
    outside_noise_strength: FloatProperty(
        name="Outside Surface Noise", 
        description="Surface detail noise strength outside crater rim",
        default=0.02,
        min=0.0,
        max=30.0,
        step=1
    )
    
    create_materials: BoolProperty(
        name="Create Materials",
        description="Generate dual-zone crater materials",
        default=True
    )
    
    auto_uv: BoolProperty(
        name="Auto UV Mapping",
        description="Generate optimized UV mapping",
        default=True
    )
    
    optimize_for_games: BoolProperty(
        name="Game Optimization",
        description="Apply game-ready mesh optimizations",
        default=True
    )
    
    close_bottom: BoolProperty(
        name="Close Bottom",
        description="Create a closed bottom for the crater (solid geometry)",
        default=True
    )
    
    bottom_thickness: FloatProperty(
        name="Bottom Thickness",
        description="Thickness of the crater bottom (how deep below ground level)",
        default=1.0,
        min=0.1,
        max=10.0,
        unit='LENGTH',
        step=10
    )
    
    outer_wall_angle: FloatProperty(
        name="Outer Wall Angle",
        description="Angle of the outer bottom walls (0 = vertical, positive = slanted outward)",
        default=0.0,
        min=-89.0,
        max=89.0,
        unit='ROTATION',
        step=100
    )
    
    inner_wall_angle: FloatProperty(
        name="Inner Wall Angle",
        description="Angle of the inner crater walls (0 = vertical, positive = slanted outward)",
        default=0.0,
        min=-89.0,
        max=89.0,
        unit='ROTATION',
        step=100
    )
    
    blast_asymmetry: FloatProperty(
        name="Blast Asymmetry",
        description="How asymmetric the explosion was (0 = perfect circle)",
        default=0.0,
        min=0.0,
        max=1.0,
        step=1
    )
    
    edge_fragmentation: FloatProperty(
        name="Edge Fragmentation",
        description="How broken/jagged the crater rim is",
        default=0.0,
        min=0.0,
        max=100.0,
        step=1
    )
    
    rim_height_variation: FloatProperty(
        name="Rim Height Variation",
        description="Random height variation across the rim (0 = uniform)",
        default=0.0,
        min=0.0,
        max=1.0,
        step=1
    )
    
    rim_noise_scale: FloatProperty(
        name="Rim Noise Scale",
        description="Scale of the noise pattern on rim",
        default=3.0,
        min=0.5,
        max=10.0
    )
    
    # Random range controls for all parameters
    random_outer_radius_min: FloatProperty(
        name="Random Outer Radius Min",
        description="Minimum outer radius for random generation",
        default=1.0,
        min=0.1,
        max=99.0,
        unit='LENGTH'
    )
    
    random_outer_radius_max: FloatProperty(
        name="Random Outer Radius Max", 
        description="Maximum outer radius for random generation",
        default=20.0,
        min=1.0,
        max=200.0,
        unit='LENGTH'
    )
    
    random_inner_radius_min: FloatProperty(
        name="Random Inner Radius Min",
        description="Minimum inner radius for random generation",
        default=0.5,
        min=0.1,
        max=99.0,
        unit='LENGTH'
    )
    
    random_inner_radius_max: FloatProperty(
        name="Random Inner Radius Max", 
        description="Maximum inner radius for random generation",
        default=10.0,
        min=1.0,
        max=200.0,
        unit='LENGTH'
    )
    
    random_depth_min: FloatProperty(
        name="Random Depth Min",
        default=0.1, min=0.1, max=99.0, unit='LENGTH'
    )
    random_depth_max: FloatProperty(
        name="Random Depth Max", 
        default=10.0, min=1.0, max=100.0, unit='LENGTH'
    )
    
    random_rim_height_min: FloatProperty(
        name="Random Rim Height Min",
        default=0.0, min=0.0, max=99.0, unit='LENGTH'
    )
    random_rim_height_max: FloatProperty(
        name="Random Rim Height Max",
        default=5.0, min=1.0, max=100.0, unit='LENGTH'
    )
    
    random_resolution_min: IntProperty(
        name="Random Resolution Min",
        default=8, min=8, max=499
    )
    random_resolution_max: IntProperty(
        name="Random Resolution Max",
        default=64, min=9, max=500
    )
    
    random_noise_min: FloatProperty(
        name="Random Noise Min",
        default=0.0, min=0.0, max=29.9
    )
    random_noise_max: FloatProperty(
        name="Random Noise Max",
        default=1.0, min=0.01, max=30.0
    )
    
    # Random ranges for explosion realism
    random_blast_asymmetry_min: FloatProperty(
        name="Random Blast Asymmetry Min",
        default=0.0, min=0.0, max=0.99
    )
    random_blast_asymmetry_max: FloatProperty(
        name="Random Blast Asymmetry Max",
        default=0.5, min=0.01, max=1.0
    )
    
    random_edge_fragmentation_min: FloatProperty(
        name="Random Edge Fragmentation Min", 
        default=0.0, min=0.0, max=99.9
    )
    random_edge_fragmentation_max: FloatProperty(
        name="Random Edge Fragmentation Max",
        default=5.0, min=0.01, max=100.0
    )
    
    random_rim_variation_min: FloatProperty(
        name="Random Rim Variation Min",
        default=0.0, min=0.0, max=0.99
    )
    random_rim_variation_max: FloatProperty(
        name="Random Rim Variation Max",
        default=0.3, min=0.01, max=1.0
    )


class MESH_OT_add_crater(Operator):
    """Generate clean game-ready crater mesh based on real crater analysis"""
    bl_idname = "mesh.add_crater"
    bl_label = "Add Game Crater"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    
    # Operator properties for undo panel - MUST MATCH PropertyGroup names exactly
    outer_radius: FloatProperty(name="Outer Radius", default=2.6, min=0.5, max=100.0)
    inner_radius: FloatProperty(name="Inner Radius", default=1.3, min=0.1, max=50.0)
    depth: FloatProperty(name="Depth", default=0.5, min=0.1, max=100.0)
    rim_height: FloatProperty(name="Rim Height", default=0.58, min=0.0, max=100.0)
    resolution: IntProperty(name="Resolution", default=24, min=8, max=500)
    noise_strength: FloatProperty(name="Inside Noise", default=0.05, min=0.0, max=30.0)
    outside_noise_strength: FloatProperty(name="Outside Noise", default=0.02, min=0.0, max=30.0)
    create_materials: BoolProperty(name="Materials", default=True)
    auto_uv: BoolProperty(name="Auto UV", default=True)
    optimize_for_games: BoolProperty(name="Game Optimization", default=True)
    close_bottom: BoolProperty(name="Close Bottom", default=True)
    bottom_thickness: FloatProperty(name="Bottom Thickness", default=1.0, min=0.1, max=10.0)
    outer_wall_angle: FloatProperty(name="Outer Wall Angle", default=0.0, min=-89.0, max=89.0)
    inner_wall_angle: FloatProperty(name="Inner Wall Angle", default=0.0, min=-89.0, max=89.0)
    rim_height_variation: FloatProperty(name="Rim Variation", default=0.0, min=0.0, max=1.0)
    rim_noise_scale: FloatProperty(name="Rim Noise Scale", default=3.0, min=0.5, max=10.0)
    blast_asymmetry: FloatProperty(name="Blast Asymmetry", default=0.0, min=0.0, max=1.0)
    edge_fragmentation: FloatProperty(name="Edge Fragmentation", default=0.0, min=0.0, max=100.0)
    
    def execute(self, context):
        try:
            # Generate clean crater mesh
            crater_data = self.generate_clean_crater()
            if not crater_data:
                self.report({'ERROR'}, "Failed to generate crater mesh")
                return {'CANCELLED'}
            
            # Create mesh object
            mesh = bpy.data.meshes.new("GameCrater")
            obj = bpy.data.objects.new("GameCrater", mesh)
            obj.location = context.scene.cursor.location
            
            # Apply mesh data
            mesh.from_pydata(crater_data['vertices'], [], crater_data['faces'])
            mesh.update()
            
            # Apply game optimizations
            if self.optimize_for_games:
                self.optimize_mesh_for_games(mesh)
            
            # Link to scene and select
            context.collection.objects.link(obj)
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj
            
            # Apply materials and UVs
            if self.create_materials:
                self.setup_clean_materials(obj)
            if self.auto_uv:
                self.generate_crater_uvs(obj)
            
            # Report results
            tri_count = len(mesh.polygons)
            vertex_count = len(mesh.vertices)
            
            self.report({'INFO'}, f"Crater: {tri_count} triangles, {vertex_count} vertices")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Crater generation failed: {str(e)}")
            return {'CANCELLED'}
    
    def generate_clean_crater(self):
        """Generate clean crater based on analysis data"""
        bm = bmesh.new()
        
        try:
            # Generate clean base geometry
            self.create_clean_crater_geometry(bm)
            
            # Add minimal surface detail
            self.apply_minimal_detail(bm)
            
            # Optimize topology
            if self.optimize_for_games:
                self.optimize_crater_topology(bm)
            
            # Extract mesh data
            vertices = [[v.co.x, v.co.y, v.co.z] for v in bm.verts]
            faces = [[v.index for v in f.verts] for f in bm.faces]
            
            return {'vertices': vertices, 'faces': faces}
            
        finally:
            bm.free()
    
    def create_clean_crater_geometry(self, bm):
        """Create clean crater geometry based on real crater analysis"""
        all_ring_verts = []
        
        # Use new dual radius system
        base_radius = self.outer_radius
        rim_radius = self.inner_radius
        
        # Calculate random asymmetry direction if asymmetric
        if self.blast_asymmetry > 0:
            blast_angle_rad = random.uniform(0, 2 * math.pi)  # Random direction each time
        else:
            blast_angle_rad = 0.0
        
        # Create outer ground-level base ring
        base_verts = []
        for i in range(self.resolution):
            angle = 2 * math.pi * i / self.resolution
            
            # Apply blast asymmetry - crater extends further in blast direction
            # Calculate how aligned this point is with the blast direction
            point_direction = angle - blast_angle_rad
            alignment = math.cos(point_direction)  # -1 to 1, where 1 is perfectly aligned
            
            # Much stronger asymmetry factor for visible effect
            asymmetry_factor = 1.0 + self.blast_asymmetry * alignment * 1.0  # Increased from 0.5 to 1.0
            
            x = base_radius * math.cos(angle) * asymmetry_factor
            y = base_radius * math.sin(angle) * asymmetry_factor
            z = 0.0  # Ground level
            
            base_verts.append(bm.verts.new((x, y, z)))
        all_ring_verts.append(base_verts)
        
        # Create slope rings - minimal for clean geometry
        slope_rings = max(2, min(3, self.resolution // 16))
        
        for slope_ring in range(1, slope_rings + 1):
            ring_factor = slope_ring / slope_rings
            # Linear radius reduction from outer to inner radius
            ring_radius = base_radius - (base_radius - rim_radius) * ring_factor
            
            # Gentle slope rise (24° average from analysis)
            slope_height = self.rim_height * (ring_factor ** 0.8)
            
            ring_verts = []
            for i in range(self.resolution):
                angle = 2 * math.pi * i / self.resolution
                
                # Apply blast asymmetry to slope rings too
                point_direction = angle - blast_angle_rad
                alignment = math.cos(point_direction)
                asymmetry_factor = 1.0 + self.blast_asymmetry * alignment * 0.8  # Increased from 0.3 to 0.8
                
                x = ring_radius * math.cos(angle) * asymmetry_factor
                y = ring_radius * math.sin(angle) * asymmetry_factor
                z = slope_height
                
                ring_verts.append(bm.verts.new((x, y, z)))
            all_ring_verts.append(ring_verts)
        
        # Create crater rim with variation and fragmentation
        rim_verts = []
        for i in range(self.resolution):
            angle = 2 * math.pi * i / self.resolution
            
            # Apply blast asymmetry to rim
            point_direction = angle - blast_angle_rad
            alignment = math.cos(point_direction)
            asymmetry_factor = 1.0 + self.blast_asymmetry * alignment * 0.6  # Increased from 0.2 to 0.6
            
            x = rim_radius * math.cos(angle) * asymmetry_factor
            y = rim_radius * math.sin(angle) * asymmetry_factor
            
            # Add rim height variation
            height_variation = 0.0
            if self.rim_height_variation > 0:
                # Use noise for natural variation
                noise_input = Vector((x, y, 0)) * (self.rim_noise_scale * 0.1)
                height_variation = noise.noise(noise_input) * self.rim_height_variation * self.rim_height
            
            # Add edge fragmentation - random chunks missing from rim
            fragmentation_factor = 1.0
            if self.edge_fragmentation > 0:
                # Use multiple noise octaves for smoother fragmentation
                frag_noise = (
                    noise.noise(Vector((x, y, 0)) * 0.5) * 0.6 +     # Large chunks
                    noise.noise(Vector((x, y, 0)) * 2.0) * 0.4       # Smaller detail
                )
                
                # Much more aggressive fragmentation - scale the parameter properly
                frag_threshold = 0.1 - (self.edge_fragmentation / 100.0) * 0.6  # Updated for 0-100 range
                if frag_noise > frag_threshold:
                    # More dramatic reduction
                    reduction = ((frag_noise - frag_threshold) / (1.0 - frag_threshold)) * (self.edge_fragmentation / 100.0)
                    fragmentation_factor = max(0.1, 1.0 - reduction * 2.0)  # Much stronger effect
            
            z = (self.rim_height + height_variation) * fragmentation_factor
            
            rim_verts.append(bm.verts.new((x, y, z)))
        all_ring_verts.append(rim_verts)
        
        # Create inner crater bowl with inner wall angle support
        inner_rings = max(1, min(2, self.resolution // 20))
        
        # Calculate inner wall angle offset
        inner_wall_angle_rad = math.radians(self.inner_wall_angle)
        inner_wall_offset_factor = math.tan(inner_wall_angle_rad) * 2.0  # Multiplier for effect
        
        for ring in range(1, inner_rings + 1):
            ring_factor = ring / inner_rings
            base_ring_radius = rim_radius * (1.0 - ring_factor * 0.7)
            
            # Apply inner wall angle - affects how the crater walls slope inward
            # Positive angle = walls slope outward (wider at bottom)
            # Negative angle = walls slope inward (narrower at bottom)
            depth_factor = (self.rim_height + self.depth) * ring_factor
            wall_radius_adjustment = depth_factor * inner_wall_offset_factor
            ring_radius = base_ring_radius + wall_radius_adjustment
            
            # Crater depth is now independent - goes from rim height down to crater depth below ground
            z = self.rim_height - depth_factor
            
            ring_verts = []
            for i in range(self.resolution):
                angle = 2 * math.pi * i / self.resolution
                
                # Apply asymmetry to inner crater too
                point_direction = angle - blast_angle_rad
                alignment = math.cos(point_direction)
                asymmetry_factor = 1.0 + self.blast_asymmetry * alignment * 0.4  # Increased from 0.1 to 0.4
                
                x = ring_radius * math.cos(angle) * asymmetry_factor
                y = ring_radius * math.sin(angle) * asymmetry_factor
                
                ring_verts.append(bm.verts.new((x, y, z)))
            all_ring_verts.append(ring_verts)
        
        # Create center point at the bottom of the crater with inner wall angle consideration
        center_height = -self.depth  # Center is at full crater depth below ground
        
        # Apply inner wall angle to center position
        total_depth = self.rim_height + self.depth
        center_radius_adjustment = total_depth * inner_wall_offset_factor
        center_x = center_radius_adjustment * 0.1  # Small offset for realistic effect
        center_y = center_radius_adjustment * 0.1
        
        center_vert = bm.verts.new((center_x, center_y, center_height))
        all_ring_verts.append([center_vert])
        
        # Connect rings with quads
        for ring_idx in range(len(all_ring_verts) - 1):
            current_ring = all_ring_verts[ring_idx]
            next_ring = all_ring_verts[ring_idx + 1]
            
            if len(next_ring) == 1:  # Connect to center
                for i in range(len(current_ring)):
                    next_i = (i + 1) % len(current_ring)
                    tri_verts = [current_ring[i], current_ring[next_i], next_ring[0]]
                    bm.faces.new(tri_verts)
            else:  # Connect rings
                for i in range(len(current_ring)):
                    next_i = (i + 1) % len(current_ring)
                    quad_verts = [
                        current_ring[i], current_ring[next_i],
                        next_ring[next_i], next_ring[i]
                    ]
                    try:
                        bm.faces.new(quad_verts)
                    except:
                        pass
        
        # Close the bottom if requested
        if self.close_bottom:
            self.create_crater_bottom(bm, all_ring_verts)
        
        bm.normal_update()
        bm.faces.ensure_lookup_table()
    
    def create_crater_bottom(self, bm, all_ring_verts):
        """Create a closed bottom for the crater with slanted outer walls"""
        # Get the outermost ring (base ring)
        base_ring = all_ring_verts[0]
        
        # Create bottom vertices at a depth below the crater
        bottom_depth = -self.bottom_thickness
        bottom_verts = []
        
        # Calculate outer wall offset based on outer wall angle
        outer_wall_angle_rad = math.radians(self.outer_wall_angle)
        # Increased multiplier for more visible effect
        wall_offset = self.bottom_thickness * math.tan(outer_wall_angle_rad) * 3.0
        
        # Create intermediate rings for slanted walls - more rings for smoother effect
        wall_rings = 5  # Increased from 3 to 5 for smoother slant
        all_wall_rings = []
        
        # Add the base ring as first wall ring
        all_wall_rings.append(base_ring)
        
        # Create intermediate rings with progressive offset
        for ring_idx in range(1, wall_rings):
            ring_factor = ring_idx / wall_rings
            ring_depth = -self.bottom_thickness * ring_factor
            # Use exponential curve for more dramatic effect
            ring_offset = wall_offset * (ring_factor ** 1.5)
            
            ring_verts = []
            for vert in base_ring:
                # Calculate direction from center for offset
                direction_x = vert.co.x
                direction_y = vert.co.y
                distance = math.sqrt(direction_x**2 + direction_y**2)
                
                if distance > 0:
                    # Normalize direction and apply progressive offset
                    norm_x = direction_x / distance
                    norm_y = direction_y / distance
                    
                    new_x = vert.co.x + norm_x * ring_offset
                    new_y = vert.co.y + norm_y * ring_offset
                else:
                    new_x = vert.co.x
                    new_y = vert.co.y
                
                ring_verts.append(bm.verts.new((new_x, new_y, ring_depth)))
            
            all_wall_rings.append(ring_verts)
        
        # Create final bottom ring with full offset
        for vert in base_ring:
            # Calculate direction from center for offset
            direction_x = vert.co.x
            direction_y = vert.co.y
            distance = math.sqrt(direction_x**2 + direction_y**2)
            
            if distance > 0:
                # Normalize direction and apply full offset
                norm_x = direction_x / distance
                norm_y = direction_y / distance
                
                bottom_x = vert.co.x + norm_x * wall_offset
                bottom_y = vert.co.y + norm_y * wall_offset
            else:
                bottom_x = vert.co.x
                bottom_y = vert.co.y
            
            bottom_z = bottom_depth
            bottom_verts.append(bm.verts.new((bottom_x, bottom_y, bottom_z)))
        
        all_wall_rings.append(bottom_verts)
        
        # Create center bottom vertex - also offset it based on outer wall angle
        center_offset_x = 0
        center_offset_y = 0
        if abs(self.outer_wall_angle) > 1:  # Only offset if significant angle
            # Create slight center offset for more realistic slanted bottom
            center_offset_x = wall_offset * 0.1
            center_offset_y = wall_offset * 0.1
        
        center_bottom = bm.verts.new((center_offset_x, center_offset_y, bottom_depth))
        
        # Connect wall rings to create slanted walls
        for ring_idx in range(len(all_wall_rings) - 1):
            current_ring = all_wall_rings[ring_idx]
            next_ring = all_wall_rings[ring_idx + 1]
            
            for i in range(len(current_ring)):
                next_i = (i + 1) % len(current_ring)
                try:
                    # Create quad connecting current ring to next ring
                    quad_face = bm.faces.new([
                        current_ring[i], current_ring[next_i],
                        next_ring[next_i], next_ring[i]
                    ])
                    # Don't set material here - let material assignment function handle it
                except:
                    pass
        
        # Create bottom faces (close the bottom)
        for i in range(len(bottom_verts)):
            next_i = (i + 1) % len(bottom_verts)
            try:
                # Create triangular faces from outer bottom ring to center
                tri_face = bm.faces.new([bottom_verts[i], bottom_verts[next_i], center_bottom])
                # Don't set material here - let material assignment function handle it
            except:
                pass
    
    def apply_minimal_detail(self, bm):
        """Apply surface noise with different levels inside vs outside rim"""
        if self.noise_strength <= 0 and self.outside_noise_strength <= 0:
            return
            
        for vert in bm.verts:
            # Multiple octave noise for smoother result
            pos = vert.co
            noise_val = (
                noise.noise(pos * 1.0) * 0.5 +      # Large features
                noise.noise(pos * 3.0) * 0.3 +      # Medium features  
                noise.noise(pos * 8.0) * 0.2        # Fine detail
            )
            
            # Determine if vertex is inside or outside crater rim with transition zone
            distance_from_center = math.sqrt(vert.co.x**2 + vert.co.y**2)
            rim_radius = self.inner_radius  # FIXED: use inner_radius consistently
            transition_width = rim_radius * 0.3  # 30% transition zone
            
            # Create smooth transition between inside and outside
            if distance_from_center < rim_radius - transition_width:
                # Clearly inside
                noise_strength = self.noise_strength
            elif distance_from_center > rim_radius + transition_width:
                # Clearly outside  
                noise_strength = self.outside_noise_strength
            else:
                # Transition zone - blend between inside and outside
                blend_factor = (distance_from_center - (rim_radius - transition_width)) / (2 * transition_width)
                blend_factor = max(0, min(1, blend_factor))  # Clamp to 0-1
                noise_strength = self.noise_strength * (1 - blend_factor) + self.outside_noise_strength * blend_factor
            
            # Apply noise with much gentler scaling
            final_noise = noise_val * noise_strength * 0.1  # Reduced from 0.3 to 0.1
            
            # Apply with falloff and clamping to prevent spikes
            base_radius = self.outer_radius * 2.0  # FIXED: use outer_radius
            if distance_from_center < base_radius:
                falloff = 1.0 - (distance_from_center / base_radius)
                noise_offset = final_noise * falloff * 0.3  # Reduced from 0.5 to 0.3
                
                # Clamp noise to prevent extreme spikes
                max_noise = min(self.rim_height * 0.2, 0.5)  # Max 20% of rim height or 0.5m
                noise_offset = max(-max_noise, min(max_noise, noise_offset))
                
                vert.co.z += noise_offset
    
    def optimize_crater_topology(self, bm):
        """Clean up topology for games"""
        # Remove duplicate vertices
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
        
        # Remove degenerate geometry
        bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.0001)
        
        # Recalculate normals
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        
        # Triangulate for game engines
        bmesh.ops.triangulate(
            bm, 
            faces=bm.faces,
            quad_method='BEAUTY',
            ngon_method='BEAUTY'
        )
    
    def optimize_mesh_for_games(self, mesh):
        """Final game optimizations"""
        mesh.validate(verbose=False, clean_customdata=True)
        mesh.calc_loop_triangles()
        mesh.update()
        
        # Set smooth shading
        for poly in mesh.polygons:
            poly.use_smooth = True
    
    def setup_clean_materials(self, obj):
        """Create clean materials for crater"""
        try:
            obj.data.materials.clear()
            
            # Inner crater material
            inner_mat = self.create_inner_material()
            obj.data.materials.append(inner_mat)
            
            # Outer slope material
            outer_mat = self.create_outer_material()
            obj.data.materials.append(outer_mat)
            
            # Assign materials
            self.assign_materials_clean(obj)
            
        except Exception as e:
            print(f"Material setup error: {e}")
    
    def create_inner_material(self):
        """Create inner crater material"""
        mat = bpy.data.materials.new(name="Crater_Inner")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        
        # Simple material setup
        output = nodes.new('ShaderNodeOutputMaterial')
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        
        # Dark crater color
        principled.inputs['Base Color'].default_value = (0.15, 0.1, 0.08, 1.0)
        principled.inputs['Roughness'].default_value = 0.9
        
        links.new(principled.outputs['BSDF'], output.inputs['Surface'])
        return mat
    
    def create_outer_material(self):
        """Create outer slope material"""
        mat = bpy.data.materials.new(name="Crater_Outer")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        
        # Simple material setup
        output = nodes.new('ShaderNodeOutputMaterial')
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        
        # Earth color
        principled.inputs['Base Color'].default_value = (0.5, 0.4, 0.3, 1.0)
        principled.inputs['Roughness'].default_value = 0.8
        
        links.new(principled.outputs['BSDF'], output.inputs['Surface'])
        return mat
    
    def assign_materials_clean(self, obj):
        """Assign materials based on analyzed crater geometry"""
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        
        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        
        # Based on your analysis: rim peak at distance 1.622, base at 2.575
        # Scale these proportionally to the current crater size
        rim_distance = self.inner_radius
        base_distance = self.outer_radius
        
        for face in bm.faces:
            face_center = face.calc_center_median()
            distance_from_center = math.sqrt(face_center.x**2 + face_center.y**2)
            
            # Special handling for bottom closure geometry
            if self.close_bottom:
                # Flat bottom: at the bottom thickness level (regardless of distance)
                if face_center.z <= (-self.bottom_thickness + 0.05):
                    face.material_index = 1  # Outer material for flat bottom
                    continue
                    
                # Side walls: below ground AND outside the main crater area
                if (face_center.z < -0.05 and  # Below ground
                    distance_from_center > self.outer_radius * 0.8):  # Outside main crater
                    face.material_index = 1  # Outer material for side walls
                    continue
            
            # Normal crater material assignment
            # Inner material: rim area and inner crater (steep areas)
            # Outer material: gentle outer slopes
            is_inner = (
                # Around rim peak area
                distance_from_center < rim_distance * 1.2 or
                # High elevation areas (above 40% of rim height)
                face_center.z > self.rim_height * 0.4 or
                # Steep slopes (your analysis showed steep inner areas)
                face.normal.z < 0.4
            )
            
            face.material_index = 0 if is_inner else 1
        
        bmesh.update_edit_mesh(obj.data)
        bpy.ops.object.mode_set(mode='OBJECT')
    
    def generate_crater_uvs(self, obj):
        """Generate clean UV mapping"""
        try:
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            
            if not obj.data.uv_layers:
                bpy.ops.mesh.uv_texture_add()
            
            # Clean UV projection
            bpy.ops.uv.smart_project(
                angle_limit=math.radians(30),
                island_margin=0.02,
                area_weight=0.0,
                correct_aspect=True
            )
            
            bpy.ops.uv.pack_islands(
                rotate=True,
                margin=0.02
            )
            
            bpy.ops.object.mode_set(mode='OBJECT')
            return True
            
        except Exception as e:
            print(f"UV mapping error: {e}")
            bpy.ops.object.mode_set(mode='OBJECT')
            return False
    
    def invoke(self, context, event):
        """Called when the operator is invoked from the panel"""
        # Copy values from scene properties to operator properties
        if hasattr(context.scene, 'crater_properties'):
            props = context.scene.crater_properties
            self.outer_radius = props.outer_radius
            self.inner_radius = props.inner_radius
            self.depth = props.depth
            self.rim_height = props.rim_height
            self.resolution = props.resolution
            self.noise_strength = props.noise_strength
            self.outside_noise_strength = props.outside_noise_strength
            self.create_materials = props.create_materials
            self.auto_uv = props.auto_uv
            self.optimize_for_games = props.optimize_for_games
            self.close_bottom = props.close_bottom
            self.bottom_thickness = props.bottom_thickness
            self.outer_wall_angle = props.outer_wall_angle
            self.inner_wall_angle = props.inner_wall_angle
            self.rim_height_variation = props.rim_height_variation
            self.rim_noise_scale = props.rim_noise_scale
            self.blast_asymmetry = props.blast_asymmetry
            self.edge_fragmentation = props.edge_fragmentation
        
        return self.execute(context)


class MESH_OT_add_random_crater(Operator):
    """Generate randomized crater with varied parameters"""
    bl_idname = "mesh.add_random_crater"
    bl_label = "Add Random Crater"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Randomize crater parameters using user-defined ranges
        scene = context.scene
        props = scene.crater_properties
        
        # Random values using user-defined ranges - now separate for inner and outer
        props.outer_radius = random.uniform(props.random_outer_radius_min, props.random_outer_radius_max)
        props.inner_radius = random.uniform(props.random_inner_radius_min, props.random_inner_radius_max)
        
        # Ensure inner radius is smaller than outer radius
        if props.inner_radius >= props.outer_radius:
            props.inner_radius = props.outer_radius * 0.7
        
        props.depth = random.uniform(props.random_depth_min, props.random_depth_max)
        props.rim_height = random.uniform(props.random_rim_height_min, props.random_rim_height_max)
        props.resolution = random.randint(props.random_resolution_min, props.random_resolution_max)
        props.noise_strength = random.uniform(props.random_noise_min, props.random_noise_max)
        props.outside_noise_strength = random.uniform(props.random_noise_min, props.random_noise_max)
        
        # Randomize explosion realism features
        props.blast_asymmetry = random.uniform(props.random_blast_asymmetry_min, props.random_blast_asymmetry_max)
        props.edge_fragmentation = random.uniform(props.random_edge_fragmentation_min, props.random_edge_fragmentation_max)
        
        # Randomize rim variation 
        props.rim_height_variation = random.uniform(props.random_rim_variation_min, props.random_rim_variation_max)
        props.rim_noise_scale = random.uniform(1.0, 8.0)
        
        # Always keep these true for working results
        props.create_materials = True
        props.auto_uv = True  
        props.optimize_for_games = True
        
        # Generate single crater
        bpy.ops.mesh.add_crater(
            outer_radius=props.outer_radius,
            inner_radius=props.inner_radius,
            depth=props.depth, 
            rim_height=props.rim_height,
            resolution=props.resolution,
            noise_strength=props.noise_strength,
            outside_noise_strength=props.outside_noise_strength,
            create_materials=props.create_materials,
            auto_uv=props.auto_uv,
            optimize_for_games=props.optimize_for_games,
            rim_height_variation=props.rim_height_variation,
            rim_noise_scale=props.rim_noise_scale,
            blast_asymmetry=props.blast_asymmetry,
            edge_fragmentation=props.edge_fragmentation,
            close_bottom=props.close_bottom,
            bottom_thickness=props.bottom_thickness,
            outer_wall_angle=props.outer_wall_angle,
            inner_wall_angle=props.inner_wall_angle
        )
        
        self.report({'INFO'}, f"Random: Outer={props.outer_radius:.1f} Inner={props.inner_radius:.1f} H={props.rim_height:.1f} Res={props.resolution}")
        
        return {'FINISHED'}


class MESH_OT_reset_crater_settings(Operator):
    """Reset all crater settings to defaults"""
    bl_idname = "mesh.reset_crater_settings"
    bl_label = "Reset to Defaults"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.crater_properties
        
        # Reset main parameters
        props.outer_radius = 2.6
        props.inner_radius = 1.3
        props.depth = 0.5
        props.rim_height = 0.58
        props.resolution = 24
        props.noise_strength = 0.05
        props.outside_noise_strength = 0.02
        props.create_materials = True
        props.auto_uv = True
        props.optimize_for_games = True
        props.close_bottom = True
        props.bottom_thickness = 1.0
        props.outer_wall_angle = 0.0
        props.inner_wall_angle = 0.0
        
        # Reset random ranges
        props.random_outer_radius_min = 1.0
        props.random_outer_radius_max = 20.0
        props.random_inner_radius_min = 0.5
        props.random_inner_radius_max = 10.0
        props.random_depth_min = 0.1
        props.random_depth_max = 10.0
        props.random_rim_height_min = 0.0
        props.random_rim_height_max = 5.0
        props.random_resolution_min = 8
        props.random_resolution_max = 64
        props.random_noise_min = 0.0
        props.random_noise_max = 1.0
        
        # Reset explosion realism features
        props.blast_asymmetry = 0.0
        props.edge_fragmentation = 0.0
        
        # Reset random ranges for explosion features
        props.random_blast_asymmetry_min = 0.0
        props.random_blast_asymmetry_max = 0.5
        props.random_edge_fragmentation_min = 0.0
        props.random_edge_fragmentation_max = 5.0
        props.random_rim_variation_min = 0.0
        props.random_rim_variation_max = 0.3
        
        # Reset rim variation
        props.rim_height_variation = 0.0
        props.rim_noise_scale = 3.0
        
        self.report({'INFO'}, "Settings reset to defaults")
        return {'FINISHED'}


class VIEW3D_PT_crater_generator(Panel):
    """Main crater generator panel"""
    bl_label = "Game Crater Generator"
    bl_idname = "VIEW3D_PT_crater_generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Create"
    bl_context = "objectmode"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.crater_properties
        
        # Main generation buttons
        col = layout.column(align=True)
        
        # Regular crater button
        row = col.row()
        row.scale_y = 1.8
        op = row.operator(
            "mesh.add_crater", 
            text="Generate Clean Crater", 
            icon='OUTLINER_OB_META'
        )
        # Pass current property values to the operator
        op.outer_radius = props.outer_radius
        op.inner_radius = props.inner_radius
        op.depth = props.depth
        op.rim_height = props.rim_height
        op.resolution = props.resolution
        op.noise_strength = props.noise_strength
        op.outside_noise_strength = props.outside_noise_strength
        op.create_materials = props.create_materials
        op.auto_uv = props.auto_uv
        op.optimize_for_games = props.optimize_for_games
        op.close_bottom = props.close_bottom
        op.bottom_thickness = props.bottom_thickness
        op.outer_wall_angle = props.outer_wall_angle
        op.inner_wall_angle = props.inner_wall_angle
        op.rim_height_variation = props.rim_height_variation
        op.rim_noise_scale = props.rim_noise_scale
        op.blast_asymmetry = props.blast_asymmetry
        op.edge_fragmentation = props.edge_fragmentation
        
        # Random crater button
        row = col.row()
        row.scale_y = 1.5
        row.operator(
            "mesh.add_random_crater", 
            text="Random Crater", 
            icon='FILE_REFRESH'
        )
        
        # Reset button
        row = col.row()
        row.scale_y = 1.2
        row.operator(
            "mesh.reset_crater_settings",
            text="Reset to Defaults",
            icon='LOOP_BACK'
        )
        
        # Add separator
        layout.separator()
        
        # Parameters
        box = layout.box()
        box.label(text="Crater Parameters", icon='SETTINGS')
        
        col = box.column(align=True)
        col.prop(props, "outer_radius")
        col.prop(props, "inner_radius")
        col.prop(props, "rim_height")
        col.prop(props, "depth")
        
        col = box.column(align=True)
        col.prop(props, "resolution")
        col.prop(props, "noise_strength")
        col.prop(props, "outside_noise_strength")
        
        # Rim variation controls
        col = box.column(align=True)
        col.prop(props, "rim_height_variation")
        if props.rim_height_variation > 0:
            col.prop(props, "rim_noise_scale")
        
        # Explosion realism controls
        box2 = layout.box()
        box2.label(text="Explosion Realism", icon='FORCE_TURBULENCE')
        
        col = box2.column(align=True)
        col.prop(props, "blast_asymmetry")
        col.prop(props, "edge_fragmentation")
        
        # Performance info
        estimated_tris = props.resolution * 4
        if estimated_tris > 800:
            box.label(text="Medium poly count", icon='INFO')
        else:
            box.label(text="Game-ready poly count", icon='CHECKMARK')
        
        # Materials and optimization
        box = layout.box()
        box.label(text="Output Options", icon='TOOL_SETTINGS')
        
        col = box.column(align=True)
        col.prop(props, "create_materials")
        col.prop(props, "auto_uv")
        col.prop(props, "optimize_for_games")
        col.prop(props, "close_bottom")
        if props.close_bottom:
            col.prop(props, "bottom_thickness")
            col.prop(props, "outer_wall_angle")
            col.prop(props, "inner_wall_angle")
        
        # Random range controls
        box = layout.box()
        box.label(text="Random Generation Ranges", icon='SETTINGS')
        
        # Outer radius range
        row = box.row(align=True)
        row.prop(props, "random_outer_radius_min", text="Outer Radius Min")
        row.prop(props, "random_outer_radius_max", text="Max")
        
        # Inner radius range
        row = box.row(align=True)
        row.prop(props, "random_inner_radius_min", text="Inner Radius Min")
        row.prop(props, "random_inner_radius_max", text="Max")
        
        # Depth range  
        row = box.row(align=True)
        row.prop(props, "random_depth_min", text="Depth Min")
        row.prop(props, "random_depth_max", text="Max")
        
        # Rim height range
        row = box.row(align=True) 
        row.prop(props, "random_rim_height_min", text="Rim Min")
        row.prop(props, "random_rim_height_max", text="Max")
        
        # Resolution range
        row = box.row(align=True)
        row.prop(props, "random_resolution_min", text="Resolution Min")
        row.prop(props, "random_resolution_max", text="Max")
        
        # Noise range
        row = box.row(align=True)
        row.prop(props, "random_noise_min", text="Noise Min")
        row.prop(props, "random_noise_max", text="Max")
        
        # Blast asymmetry range
        row = box.row(align=True)
        row.prop(props, "random_blast_asymmetry_min", text="Asymmetry Min")
        row.prop(props, "random_blast_asymmetry_max", text="Max")
        
        # Edge fragmentation range
        row = box.row(align=True)
        row.prop(props, "random_edge_fragmentation_min", text="Fragmentation Min") 
        row.prop(props, "random_edge_fragmentation_max", text="Max")
        
        # Rim variation range
        row = box.row(align=True)
        row.prop(props, "random_rim_variation_min", text="Rim Variation Min")
        row.prop(props, "random_rim_variation_max", text="Max")


def menu_func(self, context):
    """Add crater to the Add > Mesh menu"""
    self.layout.operator("mesh.add_crater", text="Game Crater", icon='OUTLINER_OB_META')


# Registration
classes = (
    CraterProperties,
    MESH_OT_add_crater,
    MESH_OT_add_random_crater,
    MESH_OT_reset_crater_settings,
    VIEW3D_PT_crater_generator,
)

def register():
    """Register all classes"""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.crater_properties = PointerProperty(type=CraterProperties)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)

def unregister():
    """Unregister classes"""
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    if hasattr(bpy.types.Scene, 'crater_properties'):
        del bpy.types.Scene.crater_properties
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
    print("Game Crater Generator loaded successfully!")
    print("Access via: Add > Mesh > Game Crater")