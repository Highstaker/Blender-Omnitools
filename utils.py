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

