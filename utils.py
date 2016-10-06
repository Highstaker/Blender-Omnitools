import bpy
from mathutils import Vector
import math


def vectorMultiply(a,b):
	"""
	Multiplies elements of `a` with the respective elements of `b`
	"""
	return Vector(x * y for x, y in zip(a, b))


def vectorLength(vert1, vert2, return_square=False):
	"""
	Returns the length of a vector from (0,0,0) to the given vertex (position vector)
	:param return_square: If true, doesn't calculate root, returns a square of vector length. Obviously makes it faster.
	:param vert: coordinates, as Vector or sequence of (x,y,z)
	:return: length of position vector
	"""
	result = (vert2[0]-vert1[0])**2 + (vert2[1]-vert1[1])**2 + (vert2[2]-vert1[2])**2
	if not return_square:
		result = math.sqrt(result)
	return result


def radiusVectorLength(vert, return_square=False):
	"""
	Returns the length of a vector from (0,0,0) to the given vertex (position vector)
	:param return_square: If true, doesn't calculate root, returns a square of vector length. Obviously makes it faster.
	:param vert: coordinates, as Vector or sequence of (x,y,z)
	:return: length of position vector
	"""
	result = vert[0]*vert[0] + vert[1]*vert[1] + vert[2]*vert[2]
	if not return_square:
		result = math.sqrt(result)
	return result


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
