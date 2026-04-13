# ******************************************************************************
#  Copyright © 2026 Kerry S. Martin, martin@wild-wood.net
#  Free for usage without warranty, expressed or implied; attribution required
#
#  Filename   : BOM_header.py
#  Description:
#    Bill-of-material single/dual row, pin/socket header part number generator
#
#  Created    : 04/13/2026
#  Modified   : 04/13/2026
#  Author     : Kerry S. Martin, martin@wild-wood.net
# ******************************************************************************

"""BOM capacitor part number generator"""

import re
from enum import Enum
from BOM.static_init import static_init
from BOM.numstr import numstr
from BOM.BOM_component import BOM_component
from BOM.BOM_settings import BOM_settings


# ------------------------------------------------------------------------------
# class: BOM_pin_header
# ------------------------------------------------------------------------------

@static_init
class BOM_pin_header(BOM_component):
	"""Single/dual row pin header"""

	class Format(Enum):
		GENERIC   = 0    # default if no other is specified
		ADAM_TECH = 1    # Adam Tech PH series pin header
		SULLINS   = 2    # Sullins PR series pin header


	@classmethod
	def static_init(cls):
		# public
		cls.FORMAT: BOM_pin_header.Format|None = None    # None will default to Format.GENERIC

		# private
		cls.__RE_MATCH_ADAM = re.compile(r"^ADAM(?: ?TECH)?$", re.IGNORECASE)
		cls.__RE_MATCH_SULLINS = re.compile(r"^SULLINS$", re.IGNORECASE)

		# TODO: future will have different pitches and select series by pitch
		cls.__RE_PART_ID_PATTERN = re.compile(r"^Connector:(?:Pin_)?Header_0?[12]x[0-9]{2}\[PinHeader_.+_P2\.54mm_(?:Vertical|Horizontal)\]$")
		cls.__RE_PACKAGE_PATTERN = re.compile(r"PinHeader_(.+)_(P2\.54mm)_(Vertical|Horizontal)")
		cls.__RE_PULL_DIMS = re.compile(r"^([12])x(0[1-9]|[1-3][0-9]|40)$")


	def __init__(self, id, format, *args):
		"""BOM_pin_header constructor

		Args:
			Any number of strings or lists of strings with component parameters
			package="connector package"
			format="Generic","Adam","Sullins"
		"""
		super().__init__(BOM_pin_header.__RE_PART_ID_PATTERN, id, format, *args)
		
		if self._id:
			format = BOM_pin_header.__get_format(self._format) if self._format else BOM_pin_header.FORMAT
			self.mfn, self.mpn, self.desc, self.package = BOM_pin_header.__generate_mfn_mpn(self.package, format)
		

	@classmethod
	def apply_settings(cls, settings : BOM_settings):
		if v := settings.get_setting("JPH_MFN", ""):
			cls.FORMAT = BOM_pin_header.__get_format(v)


	@staticmethod
	def __get_dims(dims:str) -> tuple[int, int]:
		if m := BOM_pin_header.__RE_PULL_DIMS.match(dims):
			return (int(m.group(1)), int(m.group(2)))
		else:
			return (0, 0)


	@staticmethod
	def __get_format(format:"BOM_pin_header.Format|str|None"):
		if isinstance(format, BOM_pin_header.Format):
			return format
		elif isinstance(format, str):
			if BOM_pin_header.__RE_MATCH_ADAM.match(format):
				return BOM_pin_header.Format.ADAM_TECH
			elif BOM_pin_header.__RE_MATCH_SULLINS.match(format):
				return BOM_pin_header.Format.SULLINS
		return BOM_pin_header.Format.GENERIC


	@staticmethod
	def __generate_mfn_mpn(package:str, format:"BOM_pin_header.Format|str|None"):

		if format is None:
			my_format = BOM_pin_header.FORMAT
		else:
			my_format = BOM_pin_header.__get_format(format)
		
		if m := BOM_pin_header.__RE_PACKAGE_PATTERN.match(package):
			my_shape = m.group(1)         # *x**
			my_pitch = m.group(2)         # *.**mm
			my_orient_long = m.group(3)   # Horizontal or Vertical
			my_orient = my_orient_long[0] # H or V
		else:
			my_shape = "?x??"
			my_pitch = "?.??mm"
			my_orient_long = "?"
			my_orient = "?"

		if my_format == BOM_pin_header.Format.ADAM_TECH:
			mfn, mpn = BOM_pin_header.__generate_Adam_Tech(my_shape, my_pitch, my_orient)
		elif my_format == BOM_pin_header.Format.SULLINS:
			mfn, mpn = BOM_pin_header.__generate_Sullins(my_shape, my_pitch, my_orient)
		else:
			mfn = "Generic"
			mpn = f"JPH_{my_shape}_P{my_pitch}_{my_orient}"

		desc = f"Pin header, {my_shape}, {my_pitch} pitch, {my_orient_long}"

		return (mfn, mpn, desc, f"{package}")


	@staticmethod
	def __generate_Adam_Tech(my_shape:str, my_pitch:str, my_orient:str):
		mfn = "Adam Tech"
		nr, nc = BOM_pin_header.__get_dims(my_shape)
		
		# TODO: pitch and orient?
		
		np = 0
		if nr == 1:
			mpn = "PH1"
			if nc in range(1, 41):
				np = nc
		elif nr == 2:
			mpn = "PH2"
			if nc in range(1, 41):
				np = 2*nc
		else:
			mpn = "PH?"

		if np > 0:
			mpn += f"-{np:02}-UA"
		else:
			mpn += "-??-UA"

		return (mfn, mpn)


	@staticmethod
	def __generate_Sullins(my_shape:str, my_pitch:str, my_orient:str):
		mfn = "Sullins"
		nr, nc = BOM_pin_header.__get_dims(my_shape)

		# TODO: pitch and orient?
		
		mpn = "PR*C"
		if not nc in range(2, 41):
			nc = 0
			
		if nc > 0:
			mpn += f"{nc:03}"
		else:
			mpn += "???"
			
		if nr == 1:
			mpn += "S"
		elif nr == 2:
			mpn += "D"
		else:
			mpn += "?"

		mpn += "**N"

		return (mfn, mpn)


# ------------------------------------------------------------------------------
# class: BOM_socket_header
# ------------------------------------------------------------------------------

@static_init
class BOM_socket_header(BOM_component):
	"""Single/dual row socket header"""

	class Format(Enum):
		GENERIC   = 0    # default if no other is specified
		ADAM_TECH = 1    # Adam Tech RS series pin header
		SULLINS   = 2    # Sullins female pin header


	@classmethod
	def static_init(cls):
		# public
		cls.FORMAT: BOM_socket_header.Format|None = None    # None will default to Format.GENERIC

		# private
		cls.__RE_MATCH_ADAM = re.compile(r"^ADAM(?: ?TECH)?$", re.IGNORECASE)
		cls.__RE_MATCH_SULLINS = re.compile(r"^SULLINS$", re.IGNORECASE)

		# TODO: future will have different pitches and select series by pitch
		cls.__RE_PART_ID_PATTERN = re.compile(r"^Connector:(?:Socket_)?Header_0?[12]x[0-9]{2}\[SocketHeader_.+_P2\.54mm_(?:Vertical|Horizontal)\]$")
		cls.__RE_PACKAGE_PATTERN = re.compile(r"SocketHeader_(.+)_P(2\.54mm)_(Vertical|Horizontal)")
		cls.__RE_PULL_DIMS = re.compile(r"^([12])x(0[1-9]|[1-3][0-9]|40)$")


	def __init__(self, id, format, *args):
		"""BOM_socket_header constructor

		Args:
			Any number of strings or lists of strings with component parameters
			package="connector package"
			format="Generic","Adam","Sullins"
		"""
		super().__init__(BOM_socket_header.__RE_PART_ID_PATTERN, id, format, *args)
		
		if self._id:
			format = BOM_socket_header.__get_format(self._format) if self._format else BOM_socket_header.FORMAT
			self.mfn, self.mpn, self.desc, self.package = BOM_socket_header.__generate_mfn_mpn(self.package, format)
		

	@classmethod
	def apply_settings(cls, settings : BOM_settings):
		if v := settings.get_setting("JSH_MFN", ""):
			cls.FORMAT = BOM_socket_header.__get_format(v)


	@staticmethod
	def __get_dims(dims:str) -> tuple[int, int]:
		if m := BOM_socket_header.__RE_PULL_DIMS.match(dims):
			return (int(m.group(1)), int(m.group(2)))
		else:
			return (0, 0)


	@staticmethod
	def __get_format(format:"BOM_socket_header.Format|str|None"):
		if isinstance(format, BOM_socket_header.Format):
			return format
		elif isinstance(format, str):
			if BOM_socket_header.__RE_MATCH_ADAM.match(format):
				return BOM_socket_header.Format.ADAM_TECH
			elif BOM_socket_header.__RE_MATCH_SULLINS.match(format):
				return BOM_socket_header.Format.SULLINS
		return BOM_socket_header.Format.GENERIC


	@staticmethod
	def __generate_mfn_mpn(package:str, format:"BOM_socket_header.Format|str|None"):

		if format is None:
			my_format = BOM_socket_header.FORMAT
		else:
			my_format = BOM_socket_header.__get_format(format)
		
		if m := BOM_socket_header.__RE_PACKAGE_PATTERN.match(package):
			my_shape = m.group(1)         # *x**
			my_pitch = m.group(2)         # *.**mm
			my_orient_long = m.group(3)   # Horizontal or Vertical
			my_orient = my_orient_long[0] # H or V
		else:
			my_shape = "?x??"
			my_pitch = "?.??mm"
			my_orient_long = "?"
			my_orient = "?"

		if my_format == BOM_socket_header.Format.ADAM_TECH:
			mfn, mpn = BOM_socket_header.__generate_Adam_Tech(my_shape, my_pitch, my_orient)
		elif my_format == BOM_socket_header.Format.SULLINS:
			mfn, mpn = BOM_socket_header.__generate_Sullins(my_shape, my_pitch, my_orient)
		else:
			mfn = "Generic"
			mpn = f"JSH_{my_shape}_P{my_pitch}_{my_orient}"

		desc = f"Socket header, {my_shape}, {my_pitch} pitch, {my_orient_long}"

		return (mfn, mpn, desc, f"{package}")


	@staticmethod
	def __generate_Adam_Tech(my_shape:str, my_pitch:str, my_orient:str):
		mfn = "Adam Tech"
		nr, nc = BOM_socket_header.__get_dims(my_shape)
		
		# TODO: pitch and orient?
		
		np = 0
		if nr == 1:
			mpn = "RS1"
			if nc in range(1, 41):
				np = nc
		elif nr == 2:
			mpn = "RS2"
			if nc in range(1, 41):
				np = 2*nc
		else:
			mpn = "RS?"

		if np > 0:
			mpn += f"-{np:02}-G"
		else:
			mpn += "-??-G"

		return (mfn, mpn)


	@staticmethod
	def __generate_Sullins(my_shape:str, my_pitch:str, my_orient:str):
		mfn = "Sullins"
		nr, nc = BOM_socket_header.__get_dims(my_shape)
		
		# TODO: pitch and orient?
		
		mpn = "PP*C"
		
		if nr == 1 or nr == 2:
			if nc in range(2, 41):
				mpn += f"{nc:02}{nr}"
			else:
				mpn += f"??{nr}"
		else:
			mpn += "???"
			
		mpn += "***N"

		return (mfn, mpn)


# ******************************************************************************
#  Copyright © 2026 Kerry S. Martin, martin@wild-wood.net
#  Free for usage without warranty, expressed or implied; attribution required
# ******************************************************************************