import bpy
import os
import random
import itertools
from time import time

from mathutils import Vector

from .utils import vectorMultiply, vectorLength, getSelectedMeshObjects, selectActiveMaterialOnly, selectNeighbourMaterial

#works
#TODO: Add more unwrap modes and options
class VIEW3D_OT_unwrap(bpy.types.Operator):
	bl_label = "Unwrap Materials Separately"
	bl_idname = "view3d.unwrap_per_material"
	bl_description = "Selects each material one by one and makes a UV-unwrap on per-material basis"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		bpy.ops.object.mode_set(mode="EDIT")
		bpy.context.tool_settings.mesh_select_mode = (False, False, True)  # vert, edge, face
		for i in range(len(bpy.context.object.material_slots)):
			bpy.context.object.active_material_index = i
			bpy.ops.object.material_slot_select()
			bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
			bpy.ops.mesh.select_all(action='DESELECT')

		return {'FINISHED'}

#works
class VIEW3D_OT_next_material_select(bpy.types.Operator):
	bl_label = "Next Material Select"
	bl_idname = "view3d.next_material_select"
	bl_description = "Selects all faces with the material that is next in the stack," \
					 " deselecting faces not belonging to this material."
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		selectNeighbourMaterial(context, forward=True)

		return {'FINISHED'}

#works
class VIEW3D_OT_previous_material_select(bpy.types.Operator):
	bl_label = "Previous Material Select"
	bl_idname = "view3d.previous_material_select"
	bl_description = "Selects all faces with the material that is previous in the stack," \
					 " deselecting faces not belonging to this material."
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		selectNeighbourMaterial(context, forward=False)

		return {'FINISHED'}

#works
class VIEW3D_OT_this_material_select(bpy.types.Operator):
	bl_label = "This Material Select"
	bl_idname = "view3d.this_material_select"
	bl_description = 'Selects all faces with the material that is currently selected, ' \
					 'deselecting faces not belonging to this material.'
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		bpy.ops.object.mode_set(mode="EDIT")
		bpy.context.tool_settings.mesh_select_mode = (False, False, True)  # vert, edge, face
		selectActiveMaterialOnly()

		return {'FINISHED'}

class VIEW3D_OT_mirror_weights(bpy.types.Operator):
	bl_label = "Mirror weights"
	bl_idname = "view3d.mirror_weights"
	bl_description = "Mirror weights from one half to another"
	bl_options = {'REGISTER', 'UNDO'}

	axes_menu_items = (("x", "X", "", 0), ("y", "Y", "", 1), ("z", "Z", "", 2),)
	# algorithms_menu_items = (("perebor", "Perebor", "", 0), ("vector_grouper", "Vector-grouper", "", 1),)

	# algorithm = bpy.props.EnumProperty(items=algorithms_menu_items, name="Algorithm", description="")
	resolution = bpy.props.IntProperty(name="Resolution",description="", min=1, default=14, max=30)
	axis = bpy.props.EnumProperty(items=axes_menu_items, name="Axis", description="Axis of symmetry")
	negative = bpy.props.BoolProperty(name="Negative", subtype="NONE",
									  description="Copy from negative to positive side if checked. If unchecked - from positive to negative")
	margin = bpy.props.FloatProperty(name="Margin", unit="LENGTH", subtype="NONE", soft_min=0, step=0.00001 * 100,
									 description="The coordinate of a vertex will be checked in the interval with width of 2*margin. Needed to avoid precision problems. Should be left at default value most of the time.", default=0.00001, precision=6)

	def execute(self, context):
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

		def perebor_algorithm():
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

		def vector_grouper_algorithm():
			def assignWeight(a,b):
				"""
				Assigns a weight from a to b. If a has no weight data, assigns 0 to b.
				:param a:
				:param b:
				:return:
				"""
				try:
					vert_weight = vertex_group.weight(a)
					vertex_group.add((b,), vert_weight, "REPLACE")
				except RuntimeError:
					vertex_group.add((b,), 0, "REPLACE")

			def searcher(A, B):
				"""
				Looks for symmetical vertices in A and B and assigns weight from 
				a vertex in A to a corresponding vertex in B.
				"""
				for a in A:
					coord_a = data.vertices[a].co.to_tuple()
					for b in B:
						coord_b = data.vertices[b].co.to_tuple()
						if symmetricals(coord_a, coord_b):
							assignWeight(a,b)

			def getPivotOffset(preset=None):
				axes = tuple(i for i in range(3) if i != axis_index)
				if not preset:
					max_a = -float("inf")
					max_b = -float("inf")
					for vert in data.vertices:
						vert_coords = vert.co
						if vert_coords[axes[0]] > max_a:
							max_a = vert_coords[axes[0]]
						if vert_coords[axes[1]] > max_b:
							max_b = vert_coords[axes[1]]

					result = [max_a, max_b]
					result.insert(axis_index, 0)

					return Vector(result)
				else:
					preset[axis_index] = 0
					return preset

			pivot_offset = getPivotOffset()

			verts = data.vertices
			verts_len = len(verts)
			verts_len_old = float("inf")
			res = 2**self.resolution  # resolution
			print("len(verts)",len(tuple(verts)))#debug


			while verts_len and verts_len < verts_len_old:
				print("pivot_offset",pivot_offset)#debug
				# grouping by position vector lengths
				vec_distrib = dict()
				for vert in verts:
					vert_coords = vert.co.to_tuple()
					l = vectorLength(vert.co, pivot_offset, return_square=True)
					# key = round(l/vector_step)
					key = round(l*res)
					group_index = 0 if vert_coords[axis_index] < 0 else 1  # positive or negative
					# print(vert_coords[axis_index], group_index)#debug
					vec_distrib.setdefault(key, ([], []))[group_index].append(vert.index)

				temp = vec_distrib.copy()#debug

				for i, v in vec_distrib.copy().items():
					negatives = v[0]
					positives = v[1]

					# perfectly distributed!
					if len(negatives) == len(positives) == 1:
						if self.negative:
							assignWeight(negatives[0], positives[0])
						else:
							assignWeight(positives[0], negatives[0])

						del vec_distrib[i]

					# it is either a vertex with x==0, or a vertex that accidentally fell out.
					elif (len(negatives) == 1 and len(positives) == 0) or (len(negatives) == 0 and len(positives) == 1):
						# a vert in 0
						if abs(data.vertices[(negatives + positives)[0]].co[axis_index]) < self.margin:
							# just skip it
							pass
							del vec_distrib[i]

					# elif negatives and positives:
					# 	if self.negative:
					# 		searcher(negatives, positives)
					# 	else:
					# 		searcher(positives, negatives)
					#
					# 	del vec_distrib[i]
				pass
				verts = tuple(data.vertices[i] for i in itertools.chain.from_iterable(itertools.chain.from_iterable(vec_distrib.values())))
				verts_len_old = verts_len
				verts_len = len(verts)
				try:
					pivot_offset = getPivotOffset(preset=verts[0].co)
				except IndexError:
					# end. All verts are arranged!
					pass
				print("verts_len", verts_len)#debug

				# print("vec_distrib",vec_distrib)#debug
				# print(set((len(vec_distrib[i][0]), len(vec_distrib[i][1]),) for i in vec_distrib))#debug
				# print("old size:", len(temp), "new size:", len(vec_distrib))#debug
				# print(list(itertools.chain.from_iterable(itertools.chain.from_iterable(vec_distrib.values()))))#debug

		start_time = time()
		if vertex_group:
			if context.scene.weight_mirror_algorithm == "perebor":
			# if False:
				perebor_algorithm()
			elif context.scene.weight_mirror_algorithm == "vector_grouper":
				vector_grouper_algorithm()
		else:
			print("Object has no vertex groups!")
			self.report({'ERROR'}, 'Object has no vertex groups!')

		print("Time elapsed:", time()-start_time)

		return {'FINISHED'}

#works
class VIEW3D_OT_select_half(bpy.types.Operator):
	bl_label = "Select Half"
	bl_idname = "view3d.select_half"
	bl_description = "Selects the verticies that are to one side of pivot point."
	bl_options = {'REGISTER', 'UNDO'}

	axes_menu_items = (("x", "X", "", 0), ("y", "Y", "", 1), ("z", "Z", "", 2),)

	margin = bpy.props.FloatProperty(name="Margin", unit="LENGTH", subtype="NONE",
									 min=0.00001, step=0.001, precision=6,
									description=" The coordinate of a vertex will be checked in the interval with width of 2*margin. Needed to avoid precision problems. Should be left at default value most of the time. ")
	axis = bpy.props.EnumProperty(items=axes_menu_items, name="Axis", description="Axis of symmetry")
	negative = bpy.props.BoolProperty(name="Negative", subtype="NONE", description="Select vertices on negative side of symmetry axis. If unchecked - on positive.")
	deselect = bpy.props.BoolProperty(name="Deselect", subtype="NONE", description="If checked, deselects all previously selected vertices. If unchecked, appends selection.")

	def execute(self, context):
		active_obj = context.active_object
		data = active_obj.data
		axis_index = "xyz".index(self.axis)

		bpy.ops.object.mode_set(mode="EDIT")
		if self.deselect:
			bpy.ops.mesh.select_all(action="DESELECT")
		context.tool_settings.mesh_select_mode = (True, False, False)  # vert, edge, face
		bpy.ops.object.mode_set(mode="OBJECT")  # or else it won't update

		for vert in data.vertices:
			sym_coord = vert.co[axis_index]
			compare_me = sym_coord.__lt__ if self.negative else sym_coord.__gt__
			if compare_me(0.0 + self.margin * (-1 if self.negative else 1)):
				vert.select = True

		bpy.ops.object.mode_set(mode="EDIT")

		return {'FINISHED'}

#works
class VIEW3D_OT_reinit_images(bpy.types.Operator):
	bl_label = "Re-initialize images"
	bl_idname = "view3d.reinit_images"
	bl_description = "Regenerates images that correspond to selected image texture nodes in every material of the object. Useful when the images use external files and these files get deleted."

	def execute(self, context):
		for slot in context.active_object.material_slots:
			mat = slot.material
			imag = mat.node_tree.nodes.active.image
			imag.source = 'GENERATED'

		return {'FINISHED'}

#works
class VIEW3D_OT_save_baked_images(bpy.types.Operator):
	bl_label = "Save baked images"
	bl_idname = "view3d.save_baked_images"
	bl_description = "Saves all the baked images in active object."

	directory = bpy.props.StringProperty(subtype="DIR_PATH")

	def execute(self, context):
		for slot in bpy.context.active_object.material_slots:
			mat = slot.material

			imag = mat.node_tree.nodes.active.image

			# filepath_raw doesn't erase image data, unlike filepath
			imag.filepath_raw = os.path.join(self.directory, imag.name + ".png")

			imag.file_format = 'PNG'

			imag.save()

		return {'FINISHED'}

	def invoke(self, context, event):
		wm = context.window_manager
		wm.fileselect_add(self)
		return {'RUNNING_MODAL'}

#works
class VIEW3D_OT_fake_backup_mesh(bpy.types.Operator):
	bl_label = "Backup mesh"
	bl_idname = "view3d.fake_backup_mesh"
	bl_description = "Backups mesh, creating a fake user."

	def execute(self, context):
		cur_mode = context.active_object.mode

		bpy.ops.object.mode_set(mode="OBJECT")

		orig_mesh = bpy.context.active_object.data

		NAME = orig_mesh.name

		bak_mesh = orig_mesh.copy()
		bak_mesh.name = NAME + "_old"

		bak_mesh.use_fake_user = True

		bpy.ops.object.mode_set(mode=cur_mode)

		return {'FINISHED'}

#works
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


#works
class VIEW3D_OT_dae_export_selected_per_scene(bpy.types.Operator):
	bl_label = "Collada export selected per scene"
	bl_idname = "view3d.dae_export_selected_per_scene"
	bl_description = "Iterates over all scenes and exports meshes from each into a separate .dae file."

	directory = bpy.props.StringProperty(subtype="DIR_PATH")

	def execute(self, context):
		for scene in bpy.data.scenes:
			context.screen.scene = scene
			filepath = os.path.join(self.directory,
					   os.path.splitext(bpy.path.basename(bpy.context.blend_data.filepath))[
						   0] + "_" + scene.name + ".dae")
			bpy.ops.wm.collada_export(filepath=filepath, apply_modifiers=True, selected=True)

		return {'FINISHED'}

	def invoke(self, context, event):
		wm = context.window_manager
		wm.fileselect_add(self)
		return {'RUNNING_MODAL'}

#works
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

#works. Offset values are relative to object scale, not world
class VIEW3D_OT_move_pivot(bpy.types.Operator):
	bl_idname = "view3d.move_pivot"  # unique identifier for buttons and menu items to reference.
	bl_label = "Move Pivot"  # display name in the interface.
	bl_description = "Moves the pivot point (origin) according to input. Values are relative to object sizes, not world."
	bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

	pivot_offset = bpy.props.FloatVectorProperty(name="Pivot Offset",
												 unit="LENGTH", subtype="TRANSLATION")

	def execute(self, context):  # execute() is called by blender when running the operator.
		scene = context.scene
		obj = scene.objects.active
		mesh = bpy.context.active_object.data

		bpy.ops.object.mode_set(mode="OBJECT")  # it doesn't work in EDIT mode!

		for vertex in mesh.vertices:
			vertex.co -= self.pivot_offset

		obj.location += vectorMultiply(self.pivot_offset, obj.scale)

		return {'FINISHED'}  # this lets blender know the operator finished successfully.
