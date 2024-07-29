import re
import os
import sys
import inspect
import builtins
from typing import get_args, get_origin
from typing import Literal, Union, Sequence, Mapping, Callable, IO

# === INTERNAL TYPES ===
_OpenDirection = Literal['r', 'w', 'x', 'a']
_OpenEncoding = Literal['b', 't']
_OpenModifier = Literal['+', '']
_open_modes = tuple(
		[x + z for x in get_args(_OpenDirection) for z in get_args(_OpenModifier)]
		+
		[x + y + z for x in get_args(_OpenDirection) for y in get_args(_OpenEncoding) for z in get_args(_OpenModifier)]
	)

# === PUBLIC TYPES ===

IntLike = Union[int, str]

PathLike = Union[str, os.PathLike]

Destination = Union[IO, PathLike]

PatternLike = Union[str, re.Pattern]

LineIdentifier = Union[int, PatternLike]

RegexFlag = Union[int, re.RegexFlag]

YesNo = Literal['y','n', True, False]

StringList = Sequence[str]

Receiver = tuple[Callable, Sequence, Mapping]

# noinspection PyTypeHints
OpenMode = Literal[_open_modes]

class Placeholder:
	""" Throwaway class used to mark an intended variable injection into an :py:class:`Unpack` (*args or **kwargs). """
	pass


# === TYPING HELPERS ===

def get_parent_class(__obj):
	""" Return the parent class of an object or function. """
	if hasattr(__obj, '__module__') and __obj.__module__ is not None:
		module = sys.modules[__obj.__module__]
		class_name = __obj.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0]
		return getattr(module, class_name)
	elif hasattr(__obj, '__qualname__') and __obj.__qualname__ is not None:
		module = sys.modules['builtins']
		class_name = __obj.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0]
		return getattr(module, class_name)
	else:
		return __obj.__class__


def extend_class(cls:Union[type,str], *mixins:type, attrs:dict = None) -> type:
	""" Dynamically extend a class with the specified mixins and attributes.

	Parameters:
		cls: The class to extend.
		*mixins: Additional base-classes to include in the new class.
			The `cls` class is appended to this list when generating the new subclass.
		attrs: Additional attribute and method definitions for the class.
			See the `Python docs <https://docs.python.org/3.9/library/functions.html#type>`_
			for more information on the :py:class:`type` function.
	"""

	# classes currently available in the runtime
	classes_in_frame = { name: obj for name, obj in inspect.getmembers(sys.modules[__name__]) if inspect.isclass(obj) }

	if isinstance(cls, str): cls = classes_in_frame[cls]

	if issubclass(cls, mixins): return cls  # return if already extended

	# generate a name for the new class, to avoid collisions
	mixin_names = [ mixin.__name__.title() for mixin in mixins ]
	extension_name = ''.join(mixin_names) + cls.__name__.title()

	# generate the extended class
	if extension_name in classes_in_frame:
		# the desired subclass already exists...
		return classes_in_frame[extension_name]
	else:
		# otherwise we create the new subclass and return it
		extended_class = type(extension_name, (*mixins, cls), attrs or {})
		return extended_class


def wrap_object(__obj, *mixins:type, **attrs):
	""" Cast the object such that it includes the specified mixins.

	Parameters:
		__obj: The object to wrap.
		*mixins: Additional base-classes to include in the new class.
			The `cls` class is appended to this list when generating the new subclass.
		attrs: Additional attribute and method definitions for the class.
			See the `Python docs <https://docs.python.org/3.9/library/functions.html#type>`_
			for more information on the :py:class:`type` function.
	"""

	cls = get_parent_class(__obj)
	return extend_class(cls, *mixins, **attrs)(__obj)



# noinspection PyShadowingBuiltins
def isinstance(obj, typ):
	""" Like isinstance(), but allows subscripted types or type-tuples. """

	if builtins.isinstance(typ, list) or builtins.isinstance(typ, tuple):
		return any(builtins.isinstance(obj, _type) for _type in typ)
	elif get_origin(typ) is Union:
		return any(builtins.isinstance(obj, _type) for _type in get_args(typ))
	elif get_origin(typ) is None:
		return builtins.isinstance(obj, typ)
	else:
		return builtins.isinstance(obj, get_origin(typ)) and all(builtins.isinstance(arg, typ_arg) for arg, typ_arg in zip(obj, get_args(typ)))


def class_path(__obj):
	cls = __obj.__class__

	if hasattr(cls, '__module__'):
		module = cls.__module__
		if module not in ('builtins', '__builtin__', '__main__'):
			return module + '.' + cls.__name__

	return cls.__name__ # avoid outputs like '__builtin__.str'