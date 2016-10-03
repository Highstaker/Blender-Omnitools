import bpy
from mathutils import Vector


def vectorMultiply(a,b):
	"""
	Multiplies elements of `a` with the respective elements of `b`
	"""
	return Vector(x * y for x, y in zip(a, b))


def getSelectedMeshObjects():
	"""
	Returns a list of selected mesh objects
	"""
	return [i for i in bpy.context.scene.objects if i.select and i.type == 'MESH']


def selectActiveMaterialOnly():
	"""
	Selects the verts belonging to active material, deselecting all others.
	:return:
	"""
	bpy.ops.mesh.select_all(action='DESELECT')
	bpy.ops.object.material_slot_select()


def selectNeighbourMaterial(context, forward=True):
	"""
	Selects vertices belonging to the next (if forward is True) or previous (if False) material in the stack,
	deselecting all others.
	:param context:
	:param forward:
	:return:
	"""
	bpy.ops.object.mode_set(mode="EDIT")
	context.tool_settings.mesh_select_mode = (False, False, True)  # vert, edge, face
	obj = context.object

	am = len(obj.material_slots)  # amount of materials
	cur_i = obj.active_material_index
	cur_i = (cur_i + (1 if forward else -1)) % am
	obj.active_material_index = cur_i
	selectActiveMaterialOnly()
