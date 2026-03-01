import bpy
import math

class CelestialBody:
    def __init__(self, name, radius, location=(0,0,0)):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location)
        self.obj = bpy.context.view_layer.objects.active
        self.obj.name = name
        
        # Smooth shade
        bpy.ops.object.shade_smooth()
        self.material = bpy.data.materials.new(name=f"{name}_Mat")
        self.material.use_nodes = True
        self.obj.data.materials.append(self.material)

    def set_emission(self, color=(1, 1, 0.8, 1), strength=10.0):
        nodes = self.material.node_tree.nodes
        links = self.material.node_tree.links
        nodes.clear()
        
        emission = nodes.new(type='ShaderNodeEmission')
        emission.inputs['Color'].default_value = color
        emission.inputs['Strength'].default_value = strength
        
        output = nodes.new(type='ShaderNodeOutputMaterial')
        link = links.new(emission.outputs['Emission'], output.inputs['Surface'])
        
        # Prevent the Sun sphere from casting shadows and blocking the internal point light
        if hasattr(self.obj, 'visible_shadow'):
            self.obj.visible_shadow = False
        
        # Add a point light inside for illumination
        bpy.ops.object.light_add(type='POINT', location=self.obj.location)
        light = bpy.context.view_layer.objects.active
        light.data.energy = 500000.0  # Extra high energy for the planets to receive light
        light.data.shadow_soft_size = 2.0 # Softer shadows
        light.data.color = (1.0, 0.9, 0.8) # Slightly warm light
        
        # Optional: Add a second light type (Sun lamp) just to guarantee illumination
        bpy.ops.object.light_add(type='SUN', location=self.obj.location)
        sun_lamp = bpy.context.view_layer.objects.active
        sun_lamp.data.energy = 5.0

    def set_procedural_texture(self, planet_type='rocky', color_palette=None):
        """
        planet_type: 'rocky' (noise texture) or 'gas' (wave texture)
        color_palette: list of tuples like [(position, (r, g, b, a)), ...]
        """
        nodes = self.material.node_tree.nodes
        links = self.material.node_tree.links
        
        bsdf = nodes.get("Principled BSDF")
        if not bsdf:
            bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
            output = nodes.get('Material Output')
            if output: links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
            
        colorramp = nodes.new(type='ShaderNodeValToRGB')
        
        if color_palette:
            colorramp.color_ramp.elements.remove(colorramp.color_ramp.elements[0])
            for idx, (pos, col) in enumerate(color_palette):
                if idx < len(colorramp.color_ramp.elements):
                    elem = colorramp.color_ramp.elements[idx]
                else:
                    elem = colorramp.color_ramp.elements.new(pos)
                elem.position = pos
                elem.color = col
        
        if planet_type == 'rocky':
            noise = nodes.new(type='ShaderNodeTexNoise')
            noise.inputs['Scale'].default_value = 5.0
            noise.inputs['Detail'].default_value = 15.0
            
            links.new(noise.outputs['Fac'], colorramp.inputs['Fac'])
            
            # Bump map for rocky surfaces
            bump = nodes.new(type='ShaderNodeBump')
            bump.inputs['Distance'].default_value = 0.5
            links.new(noise.outputs['Fac'], bump.inputs['Height'])
            links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
            
            bsdf.inputs['Roughness'].default_value = 0.7
            
        elif planet_type == 'gas':
            wave = nodes.new(type='ShaderNodeTexWave')
            wave.wave_type = 'BANDS'
            wave.bands_direction = 'Z'
            wave.inputs['Scale'].default_value = 3.0
            wave.inputs['Distortion'].default_value = 4.0
            wave.inputs['Detail'].default_value = 10.0
            
            links.new(wave.outputs['Fac'], colorramp.inputs['Fac'])
            bsdf.inputs['Roughness'].default_value = 0.4
            
        links.new(colorramp.outputs['Color'], bsdf.inputs['Base Color'])

    def animate_orbit(self, center_obj, distance, speed, frames):
        # Set default interpolation type for new keyframes
        bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
        
        # Create an Empty at the center object to act as the pivot
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=center_obj.location)
        pivot = bpy.context.view_layer.objects.active
        pivot.name = f"{self.obj.name}_Pivot"
        
        # Parent the object to the pivot
        self.obj.parent = pivot
        self.obj.location = (distance, 0, 0)
        
        # Animate the pivot's rotation
        pivot.rotation_euler = (0, 0, 0)
        pivot.keyframe_insert(data_path="rotation_euler", frame=1)
        
        pivot.rotation_euler = (0, 0, math.radians(speed * frames))
        pivot.keyframe_insert(data_path="rotation_euler", frame=frames)
        
        # Also rotate the object itself
        self.obj.rotation_euler = (0, 0, 0)
        self.obj.keyframe_insert(data_path="rotation_euler", frame=1)
        self.obj.rotation_euler = (0, 0, math.radians(speed * frames * 5)) # Rotate 5x faster than orbit
        self.obj.keyframe_insert(data_path="rotation_euler", frame=frames)
        
        return pivot

