import bpy
import math

class SceneManager:
    def __init__(self):
        pass

    def clear_scene(self):
        bpy.ops.wm.read_factory_settings(use_empty=True)

    def setup_render_engine(self, output_filepath, frames=250):
        scene = bpy.context.scene
        try:
            scene.render.engine = 'BLENDER_EEVEE'
        except Exception:
            scene.render.engine = 'BLENDER_EEVEE_NEXT'
        
        # EEVEE Settings (Bloom is heavily dependent on blender version, try accessing it safely)
        if hasattr(scene.eevee, "use_bloom"):
            scene.eevee.use_bloom = True
            scene.eevee.bloom_intensity = 0.05
            
        scene.render.resolution_x = 1920
        scene.render.resolution_y = 1080
        scene.render.fps = 30
        
        scene.frame_start = 1
        scene.frame_end = frames
        
        # Output settings
        scene.render.image_settings.file_format = 'PNG'
        scene.render.filepath = output_filepath

    def setup_world_background(self):
        world = bpy.context.scene.world
        if not world:
            world = bpy.data.worlds.new("World")
            bpy.context.scene.world = world
            
        world.use_nodes = True
        nodes = world.node_tree.nodes
        links = world.node_tree.links
        
        nodes.clear()
        
        bg_node = nodes.new(type='ShaderNodeBackground')
        output_node = nodes.new(type='ShaderNodeOutputWorld')
        
        # Procedural stars
        noise_node = nodes.new(type='ShaderNodeTexNoise')
        noise_node.inputs['Scale'].default_value = 200.0
        
        colorramp_node = nodes.new(type='ShaderNodeValToRGB')
        colorramp_node.color_ramp.elements[0].position = 0.6
        colorramp_node.color_ramp.elements[0].color = (0, 0, 0, 1)
        colorramp_node.color_ramp.elements[1].position = 0.8
        colorramp_node.color_ramp.elements[1].color = (1, 1, 1, 1)
        
        links.new(noise_node.outputs['Color'], colorramp_node.inputs['Fac'])
        links.new(colorramp_node.outputs['Color'], bg_node.inputs['Color'])
        links.new(bg_node.outputs['Background'], output_node.inputs['Surface'])
        
        # Add Volume Scatter for fog
        volume_node = nodes.new(type='ShaderNodeVolumeScatter')
        volume_node.inputs['Density'].default_value = 0.0005 # Drastically weakened fog
        volume_node.inputs['Anisotropy'].default_value = 0.6 # Forward scattering for god rays
        
        links.new(volume_node.outputs['Volume'], output_node.inputs['Volume'])

    def setup_camera(self):
        # Create Camera
        bpy.ops.object.camera_add(location=(15, -15, 10), rotation=(math.radians(60), 0, math.radians(45)))
        camera = bpy.context.view_layer.objects.active
        bpy.context.scene.camera = camera
        
        # We will add a track-to constraint to the earth later.
        return camera

