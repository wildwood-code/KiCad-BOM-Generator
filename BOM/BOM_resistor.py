# ******************************************************************************
#  Copyright © 2026 Kerry S. Martin, martin@wild-wood.net
#  Free for usage without warranty, expressed or implied; attribution required
#
#  Filename   : BOM_resistor.py
#  Description:
#    Bill-of-material resistor part number generator
#    class BOM_SMT_resistor => thick-film SMT resistors
#    class BOM_THT_resistor => carbon-film THT resistors
#    class BOM_RMF_resistor => metal-film SMT MELF resistors
#
#  Created    : 03/21/2025
#  Modified   : 04/13/2026
#  Author     : Kerry S. Martin, martin@wild-wood.net
# ******************************************************************************

"""BOM resistor part number generator"""

import re
from enum import Enum
from BOM.static_init import static_init
from BOM.numstr import numstr
from BOM.BOM_component import BOM_component
from BOM.BOM_settings import BOM_settings


# ------------------------------------------------------------------------------
# class: BOM_SMT_resistor
# ------------------------------------------------------------------------------

@static_init
class BOM_SMT_resistor(BOM_component):
	"""Thick-film SMT resistors"""

	class Format(Enum):
		GENERIC = 0    # default if no other is specified
		CRCW = 1       # Vishay Dale thick-film resistors
		RMCF = 2       # Stackpole/SEI thick-film resistors
		RK73 = 3       # KOA Speer thick-film resistors


	@classmethod
	def static_init(cls):
		# public
		cls.FORMAT : BOM_SMT_resistor.Format|None = None
		cls.DEFAULT_TOL = "J"  # 5%
		cls.DEFAULT_TCR = "±200ppm/K"

		# private
		cls.__RE_MATCH_CRCW = re.compile(r"^(?:CRCW|.*DALE.*|.*VISHAY.*)$", re.IGNORECASE)
		cls.__RE_MATCH_RMCF = re.compile(r"^(?:RMCF|SEI)$", re.IGNORECASE)
		cls.__RE_MATCH_RK73 = re.compile(r"^(?:RK73|.*KOA.*|.*SPEER.*)$", re.IGNORECASE)

		cls.__RE_PART_ID_PATTERN = re.compile(r"^Passive:R(?:[0-9]{4,6})?\[R_(?:0402|0603|0805|1206|1210|2010)\]$")


	@classmethod
	def apply_settings(cls, settings : BOM_settings):
		if v := settings.get_setting("RTF_MFN", ""):
			cls.FORMAT = BOM_SMT_resistor.__get_format(v)
		if v := settings.get_setting("RTF_TOL", ""):
			code = BOM_component._tol_decode(v)
			if code:
				cls.DEFAULT_TOL = code
		if v := settings.get_setting("RTF_TCR", ""):
			tcr = BOM_component._tcr_decode(v)
			if tcr:
				cls.DEFAULT_TCR = tcr
				

	def __init__(self, id, format, *args):
		"""BOM_SMT_resistor constructor

		Args:
			Any number of strings or lists of strings with component parameters
			package="resistor package"
			format="Generic","CRCW","Vishay","Dale","RMCF","SEI","RK73","KOA"
		"""
		super().__init__(BOM_SMT_resistor.__RE_PART_ID_PATTERN, id, format, *args)
		
		if self._id:
			self.value = self.params["VALUE"] if "VALUE" in self.params else None
			self.tol = self.params["TOL"] if "TOL" in self.params else BOM_SMT_resistor.DEFAULT_TOL
			self.tcr = self.params["TCR"] if "TCR" in self.params else BOM_SMT_resistor.DEFAULT_TCR
			self.Prating = self.params["PRATING"] if "PRATING" in self.params else None
			
			format = BOM_SMT_resistor.__get_format(self._format) if self._format else BOM_SMT_resistor.FORMAT

			self.mfn, self.mpn, self.desc, self.package = BOM_SMT_resistor.__generate_mfn_mpn(self.package, self.value, self.tol, self.tcr, format)
		

	@staticmethod
	def __get_format(format:"BOM_SMT_resistor.Format|str|None") -> "BOM_SMT_resistor.Format":
		if isinstance(format, BOM_SMT_resistor.Format):
			return format
		elif isinstance(format, str):
			if BOM_SMT_resistor.__RE_MATCH_CRCW.match(format):
				return BOM_SMT_resistor.Format.CRCW
			elif BOM_SMT_resistor.__RE_MATCH_RMCF.match(format):
				return BOM_SMT_resistor.Format.RMCF
			elif BOM_SMT_resistor.__RE_MATCH_RK73.match(format):
				return BOM_SMT_resistor.Format.RK73
		return BOM_SMT_resistor.Format.GENERIC


	@staticmethod
	def __generate_mfn_mpn(package:str|None, value:numstr|None, tol:str|None, tcr:str|None, format:"BOM_SMT_resistor.Format|str|None"):

		# determine format
		if format is None:
			my_format = BOM_SMT_resistor.FORMAT
		else:
			my_format = BOM_SMT_resistor.__get_format(format)

		# preprocess package
		my_package = BOM_component._extract_package_digits(package) if package is not None else "?"
		
		my_value = numstr(value)
		my_tol = BOM_component._tol_expr(tol) if tol is None else tol
		my_tcr = "?" if tcr is None else tcr

		if my_format == BOM_SMT_resistor.Format.CRCW:
			mfn, mpn = BOM_SMT_resistor.__generate_CRCW(my_package, my_value, my_tol, my_tcr)
		elif my_format == BOM_SMT_resistor.Format.RMCF:
			mfn, mpn = BOM_SMT_resistor.__generate_RMCF(my_package, my_value, my_tol, my_tcr)
		elif my_format == BOM_SMT_resistor.Format.RK73:
			mfn, mpn = BOM_SMT_resistor.__generate_RK73(my_package, my_value, my_tol, my_tcr)
		else:
			mfn = "Generic"
			mpn = f"R{my_package}"
			if my_value:
				mpn += f"_{my_value.unitless}"
			if tol is not None:
				mpn += f"_{my_tol}"
			if tcr is not None:
				mpn += f"_{my_tcr}"

		desc = f"Resistor, thick-film, {my_package}"
		if my_value:
			desc += f", {my_value.pretty}"
			if my_tol:
				desc += f" {BOM_component._tol_expr(my_tol)}"
			if my_tcr and my_tcr != "?":
				desc += f" {my_tcr}"

		return (mfn, mpn, desc, f"{my_package}")


	@staticmethod
	def __generate_RK73(package:str, value:numstr, tol:str, tcr:str):
		mfn = "KOA Speer"

		if not value or float(value) == 0.0:
			series = "Z"
			tol = ""
		elif tol is not None:
			if tol == "D" or tol == "F":
				series = "H"
			elif tol == "G" or tol == "J":
				series = "B"
			else:
				series = "?"
		else:
			tol = ""
			series = "?"

		match package:
			case "01005":
				package = "1F"
			case "0201":
				package = "1H"
			case "0402":
				package = "1E"
			case "0603":
				package = "1J"
			case "0805":
				package = "2A"
			case "1206":
				package = "2B"
			case "1210":
				package = "2E"
			case "2010":
				package = "2H"
			case "2512":
				package = "3A"
			case _:
				package = "??"

		if not value or float(value)>0.0:
			code = value.code(tol)
			mpn = f"RK73{series}{package}T_{code}{tol}"
		else:
			mpn = f"RK73{series}{package}T"

		return (mfn, mpn)


	@staticmethod
	def __generate_CRCW(package:str, value:numstr, tol:str, tcr:str):
		mfn = "Vishay Dale"
		match package:
			case "0402"|"0603"|"0805"|"1206"|"1210"|"1218"|"2010"|"2512":
				mpn = f"CRCW{package}"
			case _:
				mpn = "CRCW????"
		mpn = mpn + value.RKM()
		if not value or float(value)==0.0:
			tol = "Z"
		if tol is not None and tol in ("F", "J", "Z"):
			mpn = mpn + tol
		else:
			mpn = mpn + "_"

		if not value or float(value)==0.0:
			mpn = mpn + "S"
		elif tcr == "±100ppm/K":
			mpn = mpn + "K"
		elif tcr == "±200ppm/K":
			mpn = mpn + "N"
		else:
			mpn = mpn + "?"

		return (mfn, mpn)


	@staticmethod
	def __generate_RMCF(package:str, value:numstr, tol:str, tcr:str):
		mfn = "Stackpole SEI"
		match package:
			case "01005"|"0201"|"0402"|"0603"|"0805"|"1206"|"1210"|"2010"|"2512":
				mpn = f"RMCF{package}"
			case _:
				mpn = f"RMCF????"
		if not value or float(value)==0.0:
			tol = "Z"
		if tol is not None and tol in ("F", "J", "Z"):
			mpn = mpn + tol
		else:
			mpn = mpn + "?"
		mpn = mpn + "_"  # packaging
		if not value or float(value)==0.0:
			mpn = mpn + "0R00"
		else:
			mpn = mpn + value.RKM()
		return (mfn, mpn)


# ------------------------------------------------------------------------------
# class: BOM_THT_resistor
# ------------------------------------------------------------------------------

@static_init
class BOM_THT_resistor(BOM_component):
	"""Carbon film THT resistors"""

	class Format(Enum):
		GENERIC = 0    # default if no other is specified
		CF = 1         # Stackpole/SEI CF series carbon film THT resistors
		CFR = 2        # Yageo CFR series carbon film THT resistors


	@classmethod
	def static_init(cls):
		# public
		cls.FORMAT : BOM_THT_resistor.Format|None = None
		cls.DEFAULT_TOL = "J"  # 5%

		# private
		cls.__RE_MATCH_CF = re.compile(r"^(?:CF|SEI)$", re.IGNORECASE)
		cls.__RE_MATCH_CFR = re.compile(r"^(?:CFR|YAGEO)$", re.IGNORECASE)

		cls.__RE_PART_ID_PATTERN = re.compile(r"^Passive:(?:R|R_THT_(?:[0-9]{4}))?\[R_Axial_(?:0207|0309|0414)(?:_[HV])?\]$")
		
		
	def __init__(self, id, format, *args):
		"""BOM_THT_resistor constructor

		Args:
			Any number of strings or lists of strings with component parameters
			package="resistor package"
			format="Generic","CF","SEI","CFR","Yageo"
		"""
		super().__init__(BOM_THT_resistor.__RE_PART_ID_PATTERN, id, format, *args)
		
		if self._id:
			self.value = self.params["VALUE"] if "VALUE" in self.params else None
			self.tol = self.params["TOL"] if "TOL" in self.params else BOM_THT_resistor.DEFAULT_TOL
			self.Prating = self.params["PRATING"] if "PRATING" in self.params else None

			format = BOM_THT_resistor.__get_format(self._format) if self._format else BOM_THT_resistor.FORMAT
			
			self.mfn, self.mpn, self.desc, self.package = BOM_THT_resistor.__generate_mfn_mpn(self.package, self.value, self.tol, format)
		

	@classmethod
	def apply_settings(cls, settings : BOM_settings):
		if v := settings.get_setting("RCF_MFN", ""):
			cls.FORMAT = BOM_THT_resistor.__get_format(v)
		if v := settings.get_setting("RCF_TOL", ""):
			code = BOM_component._tol_decode(v)
			if code:
				cls.DEFAULT_TOL = code
		

	@staticmethod
	def __get_format(format:"BOM_THT_resistor.Format|str|None") -> "BOM_THT_resistor.Format":
		if isinstance(format, BOM_THT_resistor.Format):
			return format
		elif isinstance(format, str):
			if BOM_THT_resistor.__RE_MATCH_CF.match(format):
				return BOM_THT_resistor.Format.CF
			elif BOM_THT_resistor.__RE_MATCH_CFR.match(format):
				return BOM_THT_resistor.Format.CFR
		return BOM_THT_resistor.Format.GENERIC


	@staticmethod
	def __generate_mfn_mpn(package:str|None, value:numstr|None, tol:str|None, format:"BOM_THT_resistor.Format|str|None"):

		# determine format
		if format is None:
			my_format = BOM_THT_resistor.FORMAT
		else:
			my_format = BOM_THT_resistor.__get_format(format)

		# preprocess package
		my_package = BOM_component._extract_package_digits(package) if package is not None else "?"
		
		my_value = numstr(value)
		my_tol = BOM_component._tol_expr(tol) if tol is None else tol

		if my_format == BOM_THT_resistor.Format.CF:
			mfn, mpn = BOM_THT_resistor.__generate_CF(my_package, my_value, my_tol)
		elif my_format == BOM_THT_resistor.Format.CFR:
			mfn, mpn = BOM_THT_resistor.__generate_CFR(my_package, my_value, my_tol)
		else:
			mfn = "Generic"
			mpn = f"R{my_package}"
			if my_value:
				mpn += f"_{my_value.unitless}"
			if tol is not None:
				mpn += f"_{my_tol}"

		desc = f"Resistor, carbon-film, THT {my_package}"
		if my_value:
			desc += f", {my_value.pretty}"
			if my_tol:
				desc += f" {BOM_component._tol_expr(my_tol)}"

		return (mfn, mpn, desc, f"{my_package}")


	@staticmethod
	def __generate_CF(package:str, value:numstr, tol:str):
		mfn = "Stackpole SEI"

		if not tol in ('G', 'J'):
			tol = '?'

		match package:
			case "0207":
				series = "14"
			case "0309":
				series = "12"
			case "0414":
				series = "1"
			case _:
				series = "?"

		mpn = f"CF{series}{tol}{value.RKM()}"

		return (mfn, mpn)


	@staticmethod
	def __generate_CFR(package:str, value:numstr, tol:str):
		mfn = "Yageo"
		
		if not tol in ('G', 'J'):
			tol = '?'

		match package:
			case "0207":
				series = "-25"
				form = "-52"
			case "0309":
				series = "-50"
				form = "-52"
			case "0414":
				series = "100"
				form = "-73"
			case _:
				series = "?"
				form = "-?"
				
		mpn = f"CFR{series}{tol}T{form}{value.RKM()}"

		return (mfn, mpn)


# ------------------------------------------------------------------------------
# class: BOM_RMF_resistor
# ------------------------------------------------------------------------------

@static_init
class BOM_RMF_resistor(BOM_component):
	"""Metal-film SMT MELF resistors"""

	class Format(Enum):
		GENERIC = 0    # default if no other is specified
		MMF = 1        # Yageo MMF series thick-film MELF resistors
		MLFA = 2       # Stackpole/SEI MLFA series thick-film MELF resistors


	@classmethod
	def static_init(cls):
		# public
		cls.FORMAT : BOM_RMF_resistor.Format|None = None
		cls.DEFAULT_TOL = "F"  # 1%
		cls.DEFAULT_TCR = "±100ppm/K"

		# private
		#cls.__RE_PACKAGE = re.compile(r"^(?:[A-Z_]+?:)?(?:R_MELF_)?([0-9]{4,6})$", re.IGNORECASE)
		cls.__RE_MATCH_MLFA = re.compile(r"^(?:MLFA|SEI)$", re.IGNORECASE)
		cls.__RE_MATCH_MMF = re.compile(r"^(?:MMF|YAGEO)$", re.IGNORECASE)

		cls.__RE_PART_ID_PATTERN = re.compile(r"^Passive:(?:R|R_MELF_[0-9]{4})\[R_MELF_(?:0102|0204|0207)\]$")
		
		
	def __init__(self, id, format, *args):
		"""BOM_RMF_resistor constructor

		Args:
			Any number of strings or lists of strings with component parameters
			package="resistor package"
			format="Generic","CRCW","Vishay","Dale","RMCF","SEI","RK73","KOA"
		"""
		super().__init__(BOM_RMF_resistor.__RE_PART_ID_PATTERN, id, format, *args)
		
		if self._id:
			self.value = self.params["VALUE"] if "VALUE" in self.params else None
			self.tol = self.params["TOL"] if "TOL" in self.params else BOM_RMF_resistor.DEFAULT_TOL
			self.tcr = self.params["TCR"] if "TCR" in self.params else BOM_RMF_resistor.DEFAULT_TCR
			self.Prating = self.params["PRATING"] if "PRATING" in self.params else None

			format = BOM_RMF_resistor.__get_format(self._format) if self._format else BOM_RMF_resistor.FORMAT

			self.mfn, self.mpn, self.desc, self.package = BOM_RMF_resistor.__generate_mfn_mpn(self.package, self.value, self.tol, self.tcr, format)


	@classmethod
	def apply_settings(cls, settings : BOM_settings):
		if v := settings.get_setting("RMF_MFN", ""):
			cls.FORMAT = BOM_RMF_resistor.__get_format(v)
		if v := settings.get_setting("RMF_TOL", ""):
			code = BOM_component._tol_decode(v)
			if code:
				cls.DEFAULT_TOL = code
		if v := settings.get_setting("RMF_TCR", ""):
			tcr = BOM_component._tcr_decode(v)
			if tcr:
				cls.DEFAULT_TCR = tcr
		

	@staticmethod
	def __get_format(format:"BOM_RMF_resistor.Format|str|None") -> "BOM_RMF_resistor.Format":
		if isinstance(format, BOM_RMF_resistor.Format):
			return format
		elif isinstance(format, str):
			if BOM_RMF_resistor.__RE_MATCH_MLFA.match(format):
				return BOM_RMF_resistor.Format.MLFA
			elif BOM_RMF_resistor.__RE_MATCH_MMF.match(format):
				return BOM_RMF_resistor.Format.MMF
		return BOM_RMF_resistor.Format.GENERIC


	@staticmethod
	def __generate_mfn_mpn(package:str|None, value:numstr|None, tol:str|None, tcr:str|None, format:"BOM_RMF_resistor.Format|str|None"):

		# determine format
		if format is None:
			my_format = BOM_RMF_resistor.FORMAT
		else:
			my_format = BOM_RMF_resistor.__get_format(format)

		# preprocess package
		my_package = BOM_component._extract_package_digits(package) if package is not None else "?"
		
		my_value = numstr(value)
		my_tol = BOM_component._tol_expr(tol) if tol is None else tol
		my_tcr = "?" if tcr is None else tcr

		if my_format == BOM_RMF_resistor.Format.MLFA:
			mfn, mpn = BOM_RMF_resistor.__generate_MLFA(my_package, my_value, my_tol, my_tcr)
		elif my_format == BOM_RMF_resistor.Format.MMF:
			mfn, mpn = BOM_RMF_resistor.__generate_MMF(my_package, my_value, my_tol, my_tcr)
		else:
			mfn = "Generic"
			mpn = f"R_MELF{my_package}"
			if my_value:
				mpn += f"_{my_value.unitless}"
			if tol is not None:
				mpn += f"_{my_tol}"
			if tcr is not None:
				mpn += f"_{my_tcr}"

		desc = f"Resistor, metal-film, MELF {my_package}"
		if my_value:
			desc += f", {my_value.pretty}"
			if my_tol:
				desc += f" {BOM_component._tol_expr(my_tol)}"
			if my_tcr and my_tcr != "?":
				desc += f" {my_tcr}"

		return (mfn, mpn, desc, f"MELF_{my_package}")


	@staticmethod
	def __generate_MLFA(package:str, value:numstr, tol:str, tcr:str):
		mfn = "Stackpole SEI"
		match package:
			case "0102":
				series = "13"
			case "0204":
				series = "25"
			case "0207":
				series = "1"
			case _:
				series = "?"
		
		# SEI does not use the standard tolerance codes for all tolerances
		match tol:
			case "E5": # ±0.1% has no standard tolerance code, E5=>E/5=>0.1%
				tol = "B"
			case "E": # ±0.5%
				tol = "D"
			case "F": # ±1%
				tol = "F"
			case "J": # ±5%
				tol = "J"
			case "ZERO": # zero-ohm jumper, no standard tolerance code
				tol = "Z"
			case _:
				tol = "?"

		match tcr:
			case "±5ppm/K":
				tcr = "Y"
			case "±15ppm/K":
				tcr = "S"
			case "±25ppm/K":
				tcr = "E"
			case "±50ppm/K":
				tcr = "C"
			case "±100ppm/K":
				tcr = "D"
			case _:
				tcr = "?"
				
		if not value or float(value) == 0.0:
			mpn = f"MLFA{series}ZTZ0R00"
		else:
			mpn = f"MLFA{series}{tol}T{tcr}{value.RKM()}"
		
		return (mfn, mpn)


	@staticmethod
	def __generate_MMF(package:str, value:numstr, tol:str, tcr:str):
		mfn = "Yageo"
		match package:
			case "0102":
				series = "?"
			case "0204":
				series = "-12"
			case "0207":
				series = "-25"
			case _:
				series = "?"
	
		# SEI does not use the standard tolerance codes for all tolerances
		match tol:
			case "E5": # ±0.1% has no standard tolerance code, E5=>E/5=>0.1%
				tol = "B"
			case "E2": # ±0.25% has no standard tolerance code, E2=>E/2=>0.25%
				tol = "C"
			case "E": # ±0.5%
				tol = "D"
			case "F": # ±1%
				tol = "F"
			case "G": # ±2%
				tol = "G"
			case "J": # ±5%
				tol = "J"
			case _:
				tol = "?"
			
		match tcr:
			case "±15ppm/K":
				tcr = "C"
			case "±25ppm/K":
				tcr = "D"
			case "±50ppm/K":
				tcr = "E"
			case "±100ppm/K":
				tcr = "F"
			case "±200ppm/K":
				tcr = "G"
			case _:
				tcr = "?"
			
		if not value or float(value) == 0.0:
			mpn = f"MMF{series}ZTZ0R00"
		else:
			mpn = f"MMF{series}{tol}R{tcr}{value.RKM()}"
		
		return (mfn, mpn)


# ******************************************************************************
#  Copyright © 2026 Kerry S. Martin, martin@wild-wood.net
#  Free for usage without warranty, expressed or implied; attribution required
# ******************************************************************************