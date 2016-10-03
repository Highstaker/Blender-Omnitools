import bpy
import os
import random
from mathutils import Vector

from .utils import vectorMultiply, getSelectedMeshObjects


class VIEW3D_OT_unwrap(bpy.types.Operator):
	bl_label = "Unwrap Materials Separately"
	bl_idname = "view3d.unwrap_per_material"
	bl_description = "Selects each material one by one and makes a UV-unwrap on per-material basis"

	def execute(self, context):
		bpy.ops.object.mode_set(mode="EDIT")
		bpy.context.tool_settings.mesh_select_mode = (False, False, True)  # vert, edge, face
		for i in range(len(bpy.context.object.material_slots)):
			bpy.context.object.active_material_index = i
			bpy.ops.object.material_slot_select()
			bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
			bpy.ops.mesh.select_all(action='DESELECT')

		return {'FINISHED'}


class VIEW3D_OT_next_material_select(bpy.types.Operator):
	bl_label = "Next Material Select"
	bl_idname = "view3d.next_material_select"
	bl_description = "Selects all faces with the material that is next in the stack, deselecting faces not belonging to thos material."

	def execute(self, context):
		bpy.ops.object.mode_set(mode="EDIT")
		bpy.context.tool_settings.mesh_select_mode = (False, False, True)  # vert, edge, face

		am = len(bpy.context.object.material_slots)

		cur_i = bpy.context.object.active_material_index

		cur_i = (cur_i + 1) % am

		bpy.context.object.active_material_index = cur_i

		bpy.ops.mesh.select_all(action='DESELECT')
		bpy.ops.object.material_slot_select()

		return {'FINISHED'}


class VIEW3D_OT_previous_material_select(bpy.types.Operator):
	bl_label = "Previous Material Select"
	bl_idname = "view3d.previous_material_select"
	bl_description = "Selects all faces with the material that is previous in the stack, deselecting faces not belonging to thos material."

	def execute(self, context):
		bpy.ops.object.mode_set(mode="EDIT")
		bpy.context.tool_settings.mesh_select_mode = (False, False, True)  # vert, edge, face

		am = len(bpy.context.object.material_slots)

		cur_i = bpy.context.object.active_material_index

		cur_i = (cur_i - 1) % am

		bpy.context.object.active_material_index = cur_i

		bpy.ops.mesh.select_all(action='DESELECT')
		bpy.ops.object.material_slot_select()

		return {'FINISHED'}


class VIEW3D_OT_this_material_select(bpy.types.Operator):
	bl_label = "This Material Select"
	bl_idname = "view3d.this_material_select"
	bl_description = "Selects all faces with the material that is currently selected, deselecting faces not belonging to thos material."

	def execute(self, context):
		bpy.ops.object.mode_set(mode="EDIT")
		bpy.context.tool_settings.mesh_select_mode = (False, False, True)  # vert, edge, face

		bpy.ops.mesh.select_all(action='DESELECT')
		bpy.ops.object.material_slot_select()

		return {'FINISHED'}


class VIEW3D_OT_mirror_weights(bpy.types.Operator):
	bl_label = "Select Half"
	bl_idname = "view3d.mirror_weights"
	bl_description = "Mirror weights from one half to another"
	bl_options = {'REGISTER', 'UNDO'}

	axes_menu_items = (("x", "X", "", 0), ("y", "Y", "", 1), ("z", "Z", "", 2),)

	axis = bpy.props.EnumProperty(items=axes_menu_items, name="Axis", description="")
	negative = bpy.props.BoolProperty(name="Negative", subtype="NONE",
									  description="Copy from negative to positive side if checked. If unchecked - from positive to negative")
	margin = bpy.props.FloatProperty(name="Margin", unit="LENGTH", subtype="NONE", soft_min=0, step=0.00001 * 100,
									 description="", default=0.00001, precision=6)

	def execute(self, context):
		print("context.scene.processes", context.scene.processes)  # debug
		active_obj = context.active_object
		data = active_obj.data
		axis_index = "xyz".index(self.axis)

		# get active vertex group
		vertex_group = active_obj.vertex_groups.active

		def symmetricals(a, b):
			"""
			Checks whether the vertices are symmetrical along given axis or not.
			"""
			result = []
			for ax in range(3):
				if ax == axis_index:
					result.append(abs(a[ax] + b[ax]) < self.margin)
				else:
					result.append(abs(a[ax] - b[ax]) < self.margin)

			return all(result)

		positives = []
		negatives = []

		for vert in data.vertices:
			vert_coords = vert.co.to_tuple()
			if self.negative:
				# negative (from -X to +X)
				if vert_coords[axis_index] < 0:
					# weights are copied FROM these
					try:
						vert_weight = vertex_group.weight(vert.index)
					except RuntimeError:
						continue
					# look for symmetrical vertex among saved ones
					for n, other_vert_index in enumerate(positives):
						other_vert_coords = data.vertices[other_vert_index].co.to_tuple()
						if symmetricals(other_vert_coords, vert_coords):
							vertex_group.add((other_vert_index,), vert_weight, "REPLACE")
							positives.pop(n)
							break
					else:
						negatives.append(vert.index)
				elif vert_coords[axis_index] > 0:
					# weights are copied TO these
					for n, other_vert_index in enumerate(negatives):
						other_vert_coords = data.vertices[other_vert_index].co.to_tuple()
						if symmetricals(other_vert_coords, vert_coords):
							vert_weight = vertex_group.weight(other_vert_index)
							vertex_group.add((vert.index,), vert_weight, "REPLACE")
							negatives.pop(n)
							break
					else:
						vertex_group.add((vert.index,), 0.0, "REPLACE")
						positives.append(vert.index)
			else:
				# positive (from +X to -X)
				if vert_coords[axis_index] > 0:
					# weights are copied FROM these
					try:
						vert_weight = vertex_group.weight(vert.index)
					except RuntimeError:
						continue
					# look for symmetrical vertex among saved ones
					for n, other_vert_index in enumerate(negatives):
						other_vert_coords = data.vertices[other_vert_index].co.to_tuple()
						if symmetricals(other_vert_coords, vert_coords):
							vertex_group.add((other_vert_index,), vert_weight, "REPLACE")
							negatives.pop(n)
							break
					else:
						positives.append(vert.index)
				elif vert_coords[axis_index] < 0:
					# weights are copied TO these
					for n, other_vert_index in enumerate(positives):
						other_vert_coords = data.vertices[other_vert_index].co.to_tuple()
						if symmetricals(other_vert_coords, vert_coords):
							vert_weight = vertex_group.weight(other_vert_index)
							vertex_group.add((vert.index,), vert_weight, "REPLACE")
							positives.pop(n)
							break
					else:
						vertex_group.add((vert.index,), 0.0, "REPLACE")
						negatives.append(vert.index)

		return {'FINISHED'}


class VIEW3D_OT_select_half(bpy.types.Operator):
	# TO-DO: add negatives per axis,
	# add props descriptions
	bl_label = "Select Half"
	bl_idname = "view3d.select_half"
	bl_description = "Selects the verticies that are to one side of pivot point."
	bl_options = {'REGISTER', 'UNDO'}

	margin = bpy.props.FloatProperty(name="Margin", unit="LENGTH", subtype="NONE", soft_min=0, step=0.01,
									 description="")
	axis = bpy.props.BoolVectorProperty(name="Axis", subtype="XYZ", description="", default=(True, False, False))
	negative = bpy.props.BoolProperty(name="Negative", subtype="NONE", description="")

	def execute(self, context):

		data = bpy.context.scene.objects.active.data
		bpy.ops.object.mode_set(mode="EDIT")
		bpy.ops.mesh.select_all(action="DESELECT")
		bpy.context.tool_settings.mesh_select_mode = (True, False, False)  # vert, edge, face
		bpy.ops.object.mode_set(mode="OBJECT")

		if True not in self.axis:
			# there must be an axis to operate on. If none is chosen, choose X
			self.axis = (True, False, False)

		# iterate over all axises
		for i in range(3):
			for vert in data.vertices:
				if self.axis[i]:
					if not ((vert.co[i] < (0.0 - (2 * int(self.negative) - 1) * self.margin)) ^ self.negative):
						vert.select = True

		bpy.ops.object.mode_set(mode="EDIT")

		return {'FINISHED'}


class VIEW3D_OT_reinit_images(bpy.types.Operator):
	bl_label = "Re-initialize images"
	bl_idname = "view3d.reinit_images"
	bl_description = "Regenerates images that correspond to selected image texture nodes in every material of the object. Useful when the images use external files and these files get deleted."

	def execute(self, context):
		for slot in bpy.context.active_object.material_slots:
			mat = slot.material

			imag = mat.node_tree.nodes.active.image

			imag.source = 'GENERATED'

		return {'FINISHED'}


class VIEW3D_OT_save_baked_images(bpy.types.Operator):
	bl_label = "Save baked images"
	bl_idname = "view3d.save_baked_images"
	bl_description = "Saves all the baked images in active object."

	def execute(self, context):
		for slot in bpy.context.active_object.material_slots:
			mat = slot.material

			imag = mat.node_tree.nodes.active.image

			# filepath_raw doesn't erase image data, unlike filepath
			imag.filepath_raw = "//textures/" + imag.name + ".png"

			imag.file_format = 'PNG'

			imag.save()

		return {'FINISHED'}


class VIEW3D_OT_fake_backup_mesh(bpy.types.Operator):
	bl_label = "Backup mesh"
	bl_idname = "view3d.fake_backup_mesh"
	bl_description = "Backups mesh, creating a fake user."

	def execute(self, context):
		cur_mode = bpy.context.active_object.mode

		bpy.ops.object.mode_set(mode="OBJECT")

		orig_mesh = bpy.context.active_object.data

		NAME = orig_mesh.name

		bak_mesh = orig_mesh.copy()
		bak_mesh.name = NAME + "_old"

		bak_mesh.use_fake_user = True

		bpy.ops.object.mode_set(mode=cur_mode)

		return {'FINISHED'}


class VIEW3D_OT_make_single_user(bpy.types.Operator):
	bl_label = "Make mesh single-user"
	bl_idname = "view3d.make_single_user"
	bl_description = "Creates a new mesh with the same name and assigns the object to it, effectively making it single-user. The old mesh is backed up with '_multi' postfix. Useful when you need to apply modifiers to multi-user data."

	def execute(self, context):
		bpy.ops.object.mode_set(mode="OBJECT")
		active_obj = bpy.context.scene.objects.active
		orig_mesh = active_obj.data
		NAME = orig_mesh.name
		copy_mesh = orig_mesh.copy()
		orig_mesh.name = NAME + "_multi"
		active_obj.data = copy_mesh
		copy_mesh.name = NAME

		return {'FINISHED'}


class VIEW3D_OT_replace_data_by_active(bpy.types.Operator):
	bl_label = "Replace data by active"
	bl_idname = "view3d.replace_data_by_active"
	bl_description = "Replaces the data in the objects that contain the data specified in the menu with the data in active object. Useful for applying changes to other meshes after using 'Make mesh single-user' and applying modifiers."
	bl_options = {"REGISTER", "UNDO"}

	def item_cb(self, context):
		return [(ob.name, ob.name, ob.name) for ob in bpy.data.meshes]

	mesh_name = bpy.props.EnumProperty(items=item_cb, name="Mesh Data", description="Mesh data to be replaced")

	def execute(self, context):

		mesh = self.mesh_name

		print("Menu ", mesh)

		scenes = bpy.data.scenes

		for scene in scenes:
			objects = scene.objects
			for obj in objects:
				if obj.data.name == mesh:
					obj.data = bpy.context.scene.objects.active.data

		bpy.ops.object.mode_set(mode="EDIT")
		bpy.ops.object.mode_set(mode="OBJECT")

		return {'FINISHED'}


class VIEW3D_OT_dae_export_selected_per_scene(bpy.types.Operator):
	bl_label = "Collada export selected per scene"
	bl_idname = "view3d.dae_export_selected_per_scene"
	bl_description = "Iterates over all scenes and exports meshes from each into a separate .dae file."

	def execute(self, context):
		EXPORT_FOLDER = 'dae_exports'

		for scene in bpy.data.scenes:
			bpy.context.screen.scene = scene
			filepath = os.path.dirname(bpy.data.filepath) + "/" + EXPORT_FOLDER + "/" + \
					   os.path.splitext(bpy.path.basename(bpy.context.blend_data.filepath))[
						   0] + "_" + scene.name + ".dae"
			bpy.ops.wm.collada_export(filepath=filepath, apply_modifiers=True, selected=True)

		return {'FINISHED'}


class VIEW3D_OT_array_rotation_jitter(bpy.types.Operator):
	bl_idname = "view3d.array_rotation_jitter"
	bl_label = "Array with Rotation Jitter"
	bl_description = "Creates an array of randomly rotated and shifted objects"
	bl_options = {'REGISTER', 'UNDO'}

	# changeable parameters

	total = bpy.props.IntProperty(name="Amount of instances", default=2, min=1, max=1000)
	offsets = bpy.props.FloatVectorProperty(name="Fixed Offsets", unit="LENGTH", subtype="TRANSLATION")
	max_rotations = bpy.props.FloatVectorProperty(name="Maximum rotations", unit="ROTATION"
												  , subtype="EULER", min=0)
	max_random_offsets = bpy.props.FloatVectorProperty(name="Max Offset Jitter",
													   unit="LENGTH", subtype="TRANSLATION", min=0)
	scale_jitter = bpy.props.FloatVectorProperty(name="Scale Jitter", unit="LENGTH"
												 , subtype="DIRECTION", min=0)

	def execute(self, context):
		scene = context.scene
		cursor = scene.cursor_location
		obj = scene.objects.active

		for i in range(self.total):
			obj_new = obj.copy()  # copy current object
			scene.objects.link(obj_new)  # add object to scene

			# offset
			cur_position_jitter = [random.random() for i in range(3)]
			obj_new.location = [a + b * (i + 1) + (2 * d - 1) * c for a, b, c, d in
								zip(obj.location, self.offsets, self.max_random_offsets, cur_position_jitter)]

			# scale randomness
			cur_scale_jitter = [random.random() for i in range(3)]
			obj_new.scale = [a + b * (2 * c - 1) for a, b, c in
							 zip(obj.scale, self.scale_jitter, cur_scale_jitter)]

			# apply rotation randomness
			cur_rotation_jitter = [random.random() for i in range(3)]
			obj_new.rotation_euler = [a + b * (2 * c - 1) for a, b, c in
									  zip(obj.rotation_euler, self.max_rotations, cur_rotation_jitter)]

		return {'FINISHED'}


class VIEW3D_OT_move_pivot(bpy.types.Operator):
	bl_idname = "view3d.move_pivot"  # unique identifier for buttons and menu items to reference.
	bl_label = "Move Pivot"  # display name in the interface.
	bl_description = "Moves the pivot point (origin) according to input"
	bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

	pivot_offset = bpy.props.FloatVectorProperty(name="Pivot Offset",
												 unit="LENGTH", subtype="TRANSLATION")

	def execute(self, context):  # execute() is called by blender when running the operator.
		scene = context.scene
		cursor = scene.cursor_location
		obj = scene.objects.active
		mesh = bpy.context.active_object.data

		bpy.ops.object.mode_set(mode="OBJECT")  # it doesn't work in EDIT mode!

		for vertex in mesh.vertices:
			vertex.co -= self.pivot_offset

		obj.location += vectorMultiply(self.pivot_offset, obj.scale)

		return {'FINISHED'}  # this lets blender know the operator finished successfully.
