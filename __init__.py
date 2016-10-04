#----------------------------------------------------------
# File __init__.py
#----------------------------------------------------------

bl_info = {
"name": "Omni-Tools",
"author": "Highstaker a.k.a. Omni H. Sable",
"version": (1, 1, 8),
"blender": (2, 74, 0),
"location": "View3D > Tool Shelf > Omni-Tools Tab",
"description": "A set of my tools to boost the workflow",
"warning": "Still a work in progress. Can be unstable.",
"wiki_url": "",
"category": "3D View",
}

# To support reload properly, try to access a package var,
# if it's there, reload everything
if "bpy" in locals():
	try:
		import importlib
		importlib.reload(OmniTools)
	except ImportError:
		import imp
		imp.reload(OmniTools)
	print("Reloaded multifiles")
else:
	from . import OmniTools
	print("Imported multifiles")

import bpy
from bpy.props import *

PROCESSES = 4
bpy.types.Scene.processes = IntProperty(name="Processes", description="", min=PROCESSES, )

# main class of this toolbar
class VIEW3D_PT_OmniTools(bpy.types.Panel):
	bl_category = "OmniTools"
	bl_space_type = "VIEW_3D"
	bl_region_type = "TOOLS"
	bl_label = "OmniTools"

	def draw(self, context):
		layout = self.layout
		view = context.space_data

		# col = layout.column(align=True)
		# layout.prop(data=context.scene, property='processes')

		col = layout.column(align=True)
		col.operator("view3d.unwrap_per_material",text="Unwrap per material")

		col = layout.column(align=True)
		col.operator("view3d.previous_material_select",text="Previous Material Vertices")
		col.operator("view3d.this_material_select",text="Current Material Vertices")
		col.operator("view3d.next_material_select",text="Next Material Vertices")

		col = layout.column(align=True)
		col.operator("view3d.select_half",text="Select Half")

		col = layout.column(align=True)
		col.operator("view3d.reinit_images",text="Reinitialize images")

		col = layout.column(align=True)
		col.operator("view3d.save_baked_images",text="Save baked images")

		col = layout.column(align=True)
		col.operator("view3d.fake_backup_mesh",text="Backup mesh")

		col = layout.column(align=True)
		col.operator("view3d.make_single_user",text="Make mesh single-user")

		box = layout.box()
		label = box.label(text="Export tools",translate=False)
		col = box.column(align=True)
		col.operator("view3d.dae_export_selected_per_scene",text="Export selected to Collada per scene")

		col = layout.column(align=True)
		col.operator("view3d.array_rotation_jitter",text="Jittered array")

		col = layout.column(align=True)
		col.operator("view3d.move_pivot",text="Move Pivot")

		col = layout.column(align=True)
		col.operator("view3d.mirror_weights",text="Mirror Weights")




################
### REGISTRATION
################

def register():
	bpy.utils.register_module(__name__)

def unregister():
	bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
	register()