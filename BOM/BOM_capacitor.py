# ******************************************************************************
#  Copyright © 2026 Kerry S. Martin, martin@wild-wood.net
#  Free for usage without warranty, expressed or implied; attribution required
#
#  Filename   : BOM_capacitor.py
#  Description:
#    Bill-of-material capacitor part number generator (multi-layer ceramic chip
#    and tantalum capacitor)
#
#  Created    : 03/21/2025
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
# class: BOM_MLCC_capacitor
# ------------------------------------------------------------------------------

@static_init
class BOM_MLCC_capacitor(BOM_component):
	"""Multi-layer ceramic capacitor"""

	class Format(Enum):
		GENERIC = 0    # default if no other is specified
		KEMET = 1      # Kemet MLCC capacitor
		MURATA = 2     # Murata MLCC capacitor
		TDK = 3        # TDK MLCC capacitor
		SEI = 4        # Stackpole/SEI capacitor


	@classmethod
	def static_init(cls):
		# public
		cls.FORMAT: BOM_MLCC_capacitor.Format|None = None    # None will default to Format.GENERIC
		cls.DEFAULT_TOL = "M"   # ±20%
		cls.DEFAULT_TCC_LOW = "C0G"
		cls.DEFAULT_TCC_MID = "X7R"
		cls.DEFAULT_VRATING = "50V"
		cls.VALUE_LOW_MID_BREAK = 1000.0e-12  # LOW <= 1000pF; MID > 1000pF

		# private
		cls.__RE_MATCH_KEMET = re.compile(r"^(?:KEMET)$", re.IGNORECASE)
		cls.__RE_MATCH_MURATA = re.compile(r"^(?:GRM|MURATA)$", re.IGNORECASE)
		cls.__RE_MATCH_TDK = re.compile(r"^(?:TDK)$", re.IGNORECASE)
		cls.__RE_MATCH_SEI = re.compile(r"^(?:CML|SEI|Stackpole)$", re.IGNORECASE)
		
		cls.__RE_PART_ID_PATTERN = re.compile(r"^Passive:C(?:[0-9]{4,6})?\[C_(?:0402|0603|0805|1206|1210)\]$")


	def __init__(self, id, format, *args):
		"""BOM_MLCC_capacitor constructor

		Args:
			Any number of strings or lists of strings with component parameters
			package="capacitor package"
			format="Generic","Kemet","Murata","TDK"
		"""
		super().__init__(BOM_MLCC_capacitor.__RE_PART_ID_PATTERN, id, format, *args)
		
		if self._id:
			self.value = self.params["VALUE"] if "VALUE" in self.params else None
			self.tol = self.params["TOL"] if "TOL" in self.params else BOM_MLCC_capacitor.DEFAULT_TOL
			self.tcc = self.params["TCC"] if "TCC" in self.params else None
			if self.tcc is None:
				if not self.value:
					self.tcc = BOM_MLCC_capacitor.DEFAULT_TCC_MID
				elif float(self.value) <= BOM_MLCC_capacitor.VALUE_LOW_MID_BREAK:
					self.tcc = BOM_MLCC_capacitor.DEFAULT_TCC_LOW
				else:
					self.tcc = BOM_MLCC_capacitor.DEFAULT_TCC_MID
			self.Vrating = self.params["VRATING"] if "VRATING" in self.params else BOM_MLCC_capacitor.DEFAULT_VRATING
			format = BOM_MLCC_capacitor.__get_format(self._format) if self._format else BOM_MLCC_capacitor.FORMAT

			self.mfn, self.mpn, self.desc, self.package = BOM_MLCC_capacitor.__generate_mfn_mpn(self.package, self.value, self.tol, self.tcc, self.Vrating, format)


	@classmethod
	def apply_settings(cls, settings : BOM_settings):
		if v := settings.get_setting("MLCC_MFN", ""):
			cls.FORMAT = BOM_MLCC_capacitor.__get_format(v)
		if v := settings.get_setting("MLCC_TOL", ""):
			code = BOM_component._tol_decode(v)
			if code:
				cls.DEFAULT_TOL = code
		if v := settings.get_setting("MLCC_VRATING", ""):
			if not v[-1].upper() == 'V':
				v = v + "V"
			cls.DEFAULT_VRATING = v


	@staticmethod
	def __get_format(format:"BOM_MLCC_capacitor.Format|str|None"):
		if isinstance(format, BOM_MLCC_capacitor.Format):
			return format
		elif isinstance(format, str):
			if BOM_MLCC_capacitor.__RE_MATCH_KEMET.match(format):
				return BOM_MLCC_capacitor.Format.KEMET
			elif BOM_MLCC_capacitor.__RE_MATCH_MURATA.match(format):
				return BOM_MLCC_capacitor.Format.MURATA
			elif BOM_MLCC_capacitor.__RE_MATCH_TDK.match(format):
				return BOM_MLCC_capacitor.Format.TDK
			elif BOM_MLCC_capacitor.__RE_MATCH_SEI.match(format):
				return BOM_MLCC_capacitor.Format.SEI
		return BOM_MLCC_capacitor.Format.GENERIC


	@staticmethod
	def __get_code_pF(value:numstr):
		# all capacitors use 3-digit code, so pass tol="J" to get it as 3 digit
		return value.code(tol="J", scale=1.0e12)   # 3 digit code in pF


	@staticmethod
	def __generate_mfn_mpn(package:str|None, value:numstr|None, tol:str|None, tcc:str|None, Vrating:numstr|None, format:"BOM_MLCC_capacitor.Format|str|None"):

		# determine format
		if format is None:
			my_format = BOM_MLCC_capacitor.FORMAT
		else:
			my_format = BOM_MLCC_capacitor.__get_format(format)

		# preprocess package
		my_package = BOM_component._extract_package_digits(package) if package is not None else "?"

		my_tcc = "X7R" if tcc is None else tcc
		my_value = numstr(value)
		my_tol = "" if tol is None else tol
		my_Vrating = numstr(Vrating)

		if my_format == BOM_MLCC_capacitor.Format.KEMET:
			mfn, mpn = BOM_MLCC_capacitor.__generate_Kemet(my_package, my_value, my_tol, my_tcc, my_Vrating)
		elif my_format == BOM_MLCC_capacitor.Format.MURATA:
			mfn, mpn = BOM_MLCC_capacitor.__generate_Murata(my_package, my_value, my_tol, my_tcc, my_Vrating)
		elif my_format == BOM_MLCC_capacitor.Format.TDK:
			mfn, mpn = BOM_MLCC_capacitor.__generate_TDK(my_package, my_value, my_tol, my_tcc, my_Vrating)
		elif my_format == BOM_MLCC_capacitor.Format.SEI:
			mfn, mpn = BOM_MLCC_capacitor.__generate_SEI(my_package, my_value, my_tol, my_tcc, my_Vrating)
		else:
			mfn = "Generic"
			mpn = f"C{my_package}_"
			if my_value:
				mpn += f"{my_value.unitless}"
			if my_tol:
				mpn += f"_{BOM_component._tol_expr(my_tol)}"
			if my_Vrating:
				mpn += f"_{my_Vrating}"
			if my_tcc and my_tcc != "?":
				mpn += f"_{my_tcc}"

		desc = f"Capacitor, MLCC, {my_package}"
		if my_value:
			desc += f", {my_value.pretty}"
			if my_tol:
				desc += f" {BOM_component._tol_expr(my_tol)}"
			if my_Vrating:
				desc += f" {my_Vrating}"
			if my_tcc:
				desc += f" {my_tcc}"

		return (mfn, mpn, desc, f"{my_package}")


	@staticmethod
	def __generate_Kemet(package:str, value:numstr, tol:str, tcc:str, Vrating:numstr):
		mfn = "Kemet"
		if package in ("0402", "0603", "0805", "1206", "1210", "1812", "2220"):
			mpn = f"C{package}C"
		else:
			mpn = "C????C"
		code = BOM_MLCC_capacitor.__get_code_pF(value)
		mpn += f"{code}{tol}"

		match Vrating.value:
			case 6.3:
				vcode = "9"
			case 10.0:
				vcode = "8"
			case 16.0:
				vcode = "4"
			case 25.0:
				vcode = "3"
			case 50.0:
				vcode = "5"
			case 100.0:
				vcode = "1"
			case 200.0:
				vcode = "2"
			case _:
				vcode = "?"
		mpn += vcode

		match tcc:
			case "C0G" | "NP0":
				tcc_code = "G"
			case "X5R":
				tcc_code = "P"
			case "X7R":
				tcc_code = "R"
			case _:
				tcc_code = "?"
		mpn += f"{tcc_code}AC"

		return (mfn, mpn)


	@staticmethod
	def __generate_Murata(package:str, value:numstr, tol:str, tcc:str, Vrating:numstr):
		mfn = "Murata"
		mpn = "GRM"
		match package: # and thickness code (multiple = *)
			case "0402":
				pkg = "15*"
			case "0603":
				pkg = "18*"
			case "0805":
				pkg = "21*"
			case "1206":
				pkg = "31*"
			case "1210":
				pkg = "32*"
			case "1812":
				pkg = "43*"
			case "2220":
				pkg = "55*"
			case _:
				pkg = "???"
		mpn += pkg

		match tcc:
			case "C0G" | "NP0":
				tcode = "5C"
			case "X5R":
				tcode = "R6"
			case "X7R":
				tcode = "R7"
			case _:
				tcode = "??"
		mpn += tcode

		match Vrating.value:
			case 6.3:
				vcode = "0J"
			case 10.0:
				vcode = "1A"
			case 16.0:
				vcode = "1C"
			case 25.0:
				vcode = "1E"
			case 50.0:
				vcode = "1H"
			case 100.0:
				vcode = "2A"
			case 200.0:
				vcode = "2D"
			case _:
				vcode = "??"
		mpn += f"{vcode}"

		code = BOM_MLCC_capacitor.__get_code_pF(value)
		mpn += f"{code}{tol}"

		return (mfn, mpn)


	@staticmethod
	def __generate_TDK(package:str, value:numstr, tol:str, tcc:str, Vrating:numstr):
		mfn = "TDK"
		mpn = "C"
		match package:  # TDK uses metric case codes
			case "0402":
				pcode = "1005"
			case "0603":
				pcode = "1608"
			case "0805":
				pcode = "2012"
			case "1206":
				pcode = "3216"
			case "1210":
				pcode = "3225"
			case "1812":
				pcode = "4532"
			case "2220":
				pcode = "5750"
			case _:
				pcode = "????"
		mpn += pcode + tcc

		match Vrating.value:
			case 6.3:
				vcode = "0J"
			case 10.0:
				vcode = "1A"
			case 16.0:
				vcode = "1C"
			case 25.0:
				vcode = "1E"
			case 35.0:
				vcode = "1V"
			case 50.0:
				vcode = "1H"
			case _:
				vcode = "??"
		mpn += vcode

		code = BOM_MLCC_capacitor.__get_code_pF(value)
		mpn += f"{code}{tol}***"

		return (mfn, mpn)


	@staticmethod
	def __generate_SEI(package:str, value:numstr, tol:str, tcc:str, Vrating:numstr):
		mfn = "SEI"
		if package in ("0402", "0603", "0805", "1206", "1210", "1812"):
			mpn = f"CML{package}"
		else:
			mpn = "CML????"
			
		match tcc:
			case "C0G" | "NP0":
				tcc_code = "C0G"
			case "X5R":
				tcc_code = "X5R"
			case "X7R":
				tcc_code = "X7R"
			case _:
				tcc_code = "???"
		mpn += tcc_code
				
		code = BOM_MLCC_capacitor.__get_code_pF(value)
		mpn += f"{code}{tol}T"  # value, tolerance, packaging

		match Vrating.value:
			case 10.0:
				vcode = "10V"
			case 16.0:
				vcode = "16V"
			case 25.0:
				vcode = "25V"
			case 50.0:
				vcode = "50V"
			case 100.0:
				vcode = "100V"
			case _:
				vcode = "??V"
		mpn += vcode

		return (mfn, mpn)


# ------------------------------------------------------------------------------
# class: BOM_tantalum_capacitor
# ------------------------------------------------------------------------------

@static_init
class BOM_tantalum_capacitor(BOM_component):
	"""Tantalum capacitor"""

	class Format(Enum):
		GENERIC = 0    # default if no other is specified
		KEMET = 1      # Kemet tantalum capacitor
		AVX = 2        # AVX tantalum capacitor


	@classmethod
	def static_init(cls):
		# public
		cls.FORMAT: BOM_tantalum_capacitor.Format|None = None    # None will default to Format.GENERIC
		cls.DEFAULT_TOL = "M"   # ±20%
		cls.DEFAULT_VRATING = "16V"

		# private
		cls.__RE_MATCH_KEMET = re.compile(r"^(?:T491|KEMET)$", re.IGNORECASE)
		cls.__RE_MATCH_AVX = re.compile(r"^(?:TAJ|.*AVX.*|.*KYOCERA.*)$", re.IGNORECASE)

		cls.__RE_PART_ID_PATTERN = re.compile(r"^Passive:CP(?:_tan_[0-9]{4}-[0-9]{2})?\[CP_(?:3216-1[28]|3528-(?:12|21)|6032-(?:15|28)|7343-(?:20|31|43)|7360-38)\]$")


	def __init__(self, id, format, *args):
		"""BOM_tantalum_capacitor constructor

		Args:
			Any number of strings or lists of strings with component parameters
			package="capacitor package"
			format="Generic","Kemet","AVX"
		"""
		super().__init__(BOM_tantalum_capacitor.__RE_PART_ID_PATTERN, id, format, *args)
		
		if self._id:
			self.value = self.params["VALUE"] if "VALUE" in self.params else None
			self.tol = self.params["TOL"] if "TOL" in self.params else BOM_tantalum_capacitor.DEFAULT_TOL
			self.Vrating = self.params["VRATING"] if "VRATING" in self.params else BOM_tantalum_capacitor.DEFAULT_VRATING

			format = BOM_tantalum_capacitor.__get_format(self._format) if self._format else BOM_tantalum_capacitor.FORMAT
			
			self.mfn, self.mpn, self.desc, self.package = BOM_tantalum_capacitor.__generate_mfn_mpn(self.package, self.value, self.tol, self.Vrating, format)


	@classmethod
	def apply_settings(cls, settings : BOM_settings):
		if v := settings.get_setting("CTAN_MFN", ""):
			cls.FORMAT = BOM_tantalum_capacitor.__get_format(v)
		if v := settings.get_setting("CTAN_TOL", ""):
			code = BOM_component._tol_decode(v)
			if code:
				cls.DEFAULT_TOL = code
		if v := settings.get_setting("CTAN_VRATING", ""):
			if not v[-1].upper() == 'V':
				v = v + "V"
			cls.DEFAULT_VRATING = v
		
		
	@staticmethod
	def __get_format(format:"BOM_tantalum_capacitor.Format|str|None"):
		if isinstance(format, BOM_tantalum_capacitor.Format):
			return format
		elif isinstance(format, str):
			if BOM_tantalum_capacitor.__RE_MATCH_KEMET.match(format):
				return BOM_tantalum_capacitor.Format.KEMET
			elif BOM_tantalum_capacitor.__RE_MATCH_AVX.match(format):
				return BOM_tantalum_capacitor.Format.AVX
		return BOM_tantalum_capacitor.Format.GENERIC


	@staticmethod
	def __get_code_pF(value:numstr):
		# all capacitors use 3-digit code, so pass tol="J" to get it as 3 digit
		return value.code(tol="J", scale=1.0e12)   # 3 digit code in pF


	@staticmethod
	def __generate_mfn_mpn(package:str|None, value:numstr|None, tol:str|None, Vrating:numstr|None, format:"BOM_tantalum_capacitor.Format|str|None"):

		# determine format
		if package is None:
			my_format = BOM_tantalum_capacitor.FORMAT
		else:
			my_format = BOM_tantalum_capacitor.__get_format(format)

		# preprocess package
		my_package = BOM_component._extract_package_digits(package) if package is not None else "?"

		my_value = numstr(value)
		my_tol = "" if tol is None else tol
		my_Vrating = numstr(Vrating)

		if my_format == BOM_tantalum_capacitor.Format.KEMET:
			mfn, mpn = BOM_tantalum_capacitor.__generate_Kemet(my_package, my_value, my_tol, my_Vrating)
		elif my_format == BOM_tantalum_capacitor.Format.AVX:
			mfn, mpn = BOM_tantalum_capacitor.__generate_AVX(my_package, my_value, my_tol, my_Vrating)
		else:
			mfn = "Generic"
			mpn = f"CTAN_{my_package}_"
			if my_value:
				mpn += f"{my_value.unitless}"
			if my_tol:
				mpn += f"_{BOM_component._tol_expr(my_tol)}"
			if my_Vrating:
				mpn += f"_{my_Vrating}"

		desc = f"Capacitor, tantalum, {my_package}"
		if my_value:
			desc += f", {my_value.pretty}"
			if my_tol:
				desc += f" {BOM_component._tol_expr(my_tol)}"
			if my_Vrating:
				desc += f" {my_Vrating}"

		return (mfn, mpn, desc, f"{my_package}")


	@staticmethod
	def __generate_Kemet(package:str, value:numstr, tol:str, Vrating:numstr):
		mfn = "Kemet"
		package_codes = \
		{	"3216-18":"A", "3528-21":"B", "6032-28":"C", "7343-31":"D",
			"7360-38":"E", "3216-12":"S", "3528-12":"T",
			"6032-15":"U", "7343-20":"V", "7343-43":"X"
		}
		if package in package_codes.keys():
			mpn = f"T491{package_codes[package]}"
		else:
			mpn = "T491?"
		code = BOM_tantalum_capacitor.__get_code_pF(value)
		mpn += f"{code}{tol}"

		match Vrating.value:
			case 2.5:
				vcode = "2R5"
			case 3.0:
				vcode = "003"
			case 4.0:
				vcode = "004"
			case 6.3:
				vcode = "006"
			case 10.0:
				vcode = "010"
			case 16.0:
				vcode = "016"
			case 20.0:
				vcode = "020"
			case 25.0:
				vcode = "025"
			case 35.0:
				vcode = "035"
			case 50.0:
				vcode = "050"
			case _:
				vcode = "???"
		mpn += vcode

		return (mfn, mpn)


	@staticmethod
	def __generate_AVX(package:str, value:numstr, tol:str, Vrating:numstr):
		mfn = "Kyocera AVX"
		package_codes = \
		{	"3216-18":"A", "3528-21":"B", "6032-28":"C", "7343-31":"D",
			"7343-43":"E", "7360-43":"U", "7360-38":"V"
		}
		if package in package_codes.keys():
			mpn = f"TAJ{package_codes[package]}"
		else:
			mpn = "TAJ?"
		code = BOM_tantalum_capacitor.__get_code_pF(value)
		mpn += f"{code}{tol}"

		match Vrating.value:
			case 2.5:
				vcode = "002"
			case 3.0:
				vcode = "003"
			case 4.0:
				vcode = "004"
			case 6.3:
				vcode = "006"
			case 10.0:
				vcode = "010"
			case 16.0:
				vcode = "016"
			case 20.0:
				vcode = "020"
			case 25.0:
				vcode = "025"
			case 35.0:
				vcode = "035"
			case 50.0:
				vcode = "050"
			case _:
				vcode = "???"
		mpn += vcode

		return (mfn, mpn)


# ******************************************************************************
#  Copyright © 2026 Kerry S. Martin, martin@wild-wood.net
#  Free for usage without warranty, expressed or implied; attribution required
# ******************************************************************************