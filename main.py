import bpy
import os
import sys
import math

# Ensure current directory is in sys.path to import local modules
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from scene_manager import SceneManager
from celestial_body import CelestialBody

def main():
    frames = 500
    output_dir = os.path.join(current_dir, "frames")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_prefix = os.path.join(output_dir, "frame_")
    
    # 1. Setup Scene Manager
    manager = SceneManager()
    manager.clear_scene()
    manager.setup_render_engine(output_prefix, frames=frames)
    manager.setup_world_background()
    camera = manager.setup_camera()
    
    # 2. Setup Celestial Bodies
    sun = CelestialBody("Sun", radius=4.0, location=(0, 0, 0))
    sun.set_emission(color=(1.0, 0.5, 0.1, 1.0), strength=8.0)
    
    mercury = CelestialBody("Mercury", radius=0.4)
    mercury.set_procedural_texture(planet_type='rocky', color_palette=[(0.0, (0.4, 0.4, 0.4, 1.0)), (1.0, (0.6, 0.5, 0.5, 1.0))])
    
    venus = CelestialBody("Venus", radius=0.9)
    venus.set_procedural_texture(planet_type='rocky', color_palette=[(0.0, (0.8, 0.4, 0.1, 1.0)), (1.0, (0.9, 0.7, 0.3, 1.0))])
    
    earth = CelestialBody("Earth", radius=1.0)
    earth.set_procedural_texture(planet_type='rocky', color_palette=[(0.2, (0.1, 0.3, 0.8, 1.0)), (0.6, (0.2, 0.6, 0.2, 1.0)), (1.0, (1.0, 1.0, 1.0, 1.0))])
    
    moon = CelestialBody("Moon", radius=0.3)
    moon.set_procedural_texture(planet_type='rocky', color_palette=[(0.0, (0.3, 0.3, 0.3, 1.0)), (1.0, (0.7, 0.7, 0.7, 1.0))])
    
    mars = CelestialBody("Mars", radius=0.6)
    mars.set_procedural_texture(planet_type='rocky', color_palette=[(0.0, (0.8, 0.2, 0.1, 1.0)), (1.0, (0.5, 0.1, 0.05, 1.0))])
    
    jupiter = CelestialBody("Jupiter", radius=2.5)
    jupiter.set_procedural_texture(planet_type='gas', color_palette=[(0.0, (0.7, 0.5, 0.3, 1.0)), (0.3, (0.8, 0.7, 0.5, 1.0)), (0.6, (0.6, 0.3, 0.1, 1.0)), (1.0, (0.9, 0.8, 0.7, 1.0))])
    
    # 3. Animate Orbits
    mercury_pivot = mercury.animate_orbit(sun.obj, distance=7.0, speed=4.0, frames=frames)
    venus_pivot = venus.animate_orbit(sun.obj, distance=11.0, speed=2.0, frames=frames)
    earth_pivot = earth.animate_orbit(sun.obj, distance=16.0, speed=1.0, frames=frames)
    mars_pivot = mars.animate_orbit(sun.obj, distance=21.0, speed=0.5, frames=frames)
    jupiter_pivot = jupiter.animate_orbit(sun.obj, distance=32.0, speed=0.2, frames=frames)
    
    # Moon orbits Earth
    moon_pivot = moon.animate_orbit(earth.obj, distance=2.5, speed=5.0, frames=frames)
    moon_pivot.parent = earth.obj
    moon_pivot.location = (0, 0, 0)
    
    # 4. Set Camera Tracking
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
    
    # We will build a dynamic sweeping camera by parenting it to a pivot and animating both location/rotation
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    camera_pivot = bpy.context.view_layer.objects.active
    camera.parent = camera_pivot
    
    # Static offset relative to the pivot
    camera.location = (60, -60, 40)
    
    # Dynamically rotate the pivot around the sun across 500 frames
    camera_pivot.rotation_euler = (0, 0, 0)
    camera_pivot.keyframe_insert(data_path="rotation_euler", frame=1)
    
    camera_pivot.rotation_euler = (math.radians(15), math.radians(-5), math.radians(120))
    camera_pivot.keyframe_insert(data_path="rotation_euler", frame=frames)
    
    # Also push the camera closer over time by animating its focal length or local position
    camera.location = (60, -60, 40)
    camera.keyframe_insert(data_path="location", frame=1)
    
    camera.location = (20, -20, 15)
    camera.keyframe_insert(data_path="location", frame=frames)

    # Add track to constraint so it always looks at the Sun while sweeping
    track = camera.constraints.new(type='TRACK_TO')
    track.target = sun.obj
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'
    
    # 5. Render
    print(f"Rendering animation to {output_prefix}...")
    bpy.ops.render.render(animation=True)
    print("Render complete! You can compile these frames using FFmpeg: ffmpeg -y -framerate 30 -i frames/frame_%04d.png -c:v libx264 -pix_fmt yuv420p orbital_scene.mp4")

if __name__ == "__main__":
    main()
