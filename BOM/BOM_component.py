# ******************************************************************************
#  Copyright © 2026 Kerry S. Martin, martin@wild-wood.net
#  Free for usage without warranty, expressed or implied; attribution required
#
#  Filename   : BOM_component.py
#  Description:
#    Bill-of-material component representations allowing the auto-generation of
#    part numbers from common manufacturers.
#    BOM_component is the base class, providing utilities to derived classes
#
#  Guidelines for MFN and MPN
#    When converted to a str, a BOM_component produces the MFN and MPN
#    in the form: "MFN:MPN" with MFN and MPN separated by a colon (:)
#    In the MPN, there are symbols with special meaning:
#      * = multiple possibilities (ex/ capacitor thickness code)
#      _ = non-functional code (ex/ tape and reel)
#      ? = unable to determine code (ex/ unrecognized package)
#    Non-functional codes at the end of the MPN shall be omitted.
#    MFN and MPN shall not contain :
#    MFN and MPN may contain spaces
#
#    The MPN is, in general, an auto-generated value based upon the component
#    parameters and values. It may or may not be a valid, orderable part number
#
#  Created    : 03/05/2025
#  Modified   : 04/08/2026
#  Author     : Kerry S. Martin, martin@wild-wood.net
# ******************************************************************************

"""BOM component classes: BOM_resistor and BOM_capacitor"""

import re
from enum import Enum
from abc import ABC, abstractmethod
from BOM.static_init import static_init
from BOM.numstr import numstr
from BOM.BOM_settings import BOM_settings


# ------------------------------------------------------------------------------
# class: BOM_component - base class for BOM_resistor and BOM_capacitor
# BOM_component provides static methods and utilities for derived components
# ------------------------------------------------------------------------------

@static_init
class BOM_component(ABC):
	"""BOM_component: base class for bill-of-material components"""

	@classmethod
	def static_init(cls):
		# public
		cls.IS_VERBOSE : bool = False   # is __str__ verbose (True) or succinct (False)?

		# private
		cls.__RE_TOL = re.compile(r"^([-+±]?)(?:(\d+|0\.5))(?:%?\/([-+]?)(?:(\d+)))?%$")
		cls.__RE_TOL_AE = re.compile(r"^±(0?\.05|0?\.10?|0?\.25|0?\.50?|1(?:\.0)?|2(?:\.0)?)_?pF$", re.IGNORECASE)
		cls.__RE_TCC = re.compile(r"^([CBLAMPRSTVU][0-8][GHJKLMN]|[XYZ][4-9][PRSTUV])$", re.IGNORECASE)
		cls.__RE_TCR = re.compile(r"^±?(\d+)_?ppm(?:\/K)$", re.IGNORECASE)
		cls.__RE_EXTRACT_ID = re.compile(r"^([^:]+):([^:]+)\[(.+)\]$")
		cls.__RE_EXTRACT_PKG_DIGITS = re.compile(r"^[A-Za-z_]+([0-9][-_0-9]+)$")
		cls.__RE_EXTRACT_PKG_DIGITS = re.compile(r"^[A-Za-z_]+([0-9][-_0-9]+)(?:_[HV])?$")


	def __init__(self, pattern, id, format, *args):
		"""BOM_component constructor

		Args:
			Any number of strings or lists of strings with component parameters
		"""
		self.params = BOM_component._parse_params(*args)
		self.mfn = None
		self.mpn = None
		self.desc = None
		self.package = None
		self._library = None
		self._symbol = None
		self._format = format
		self._pattern = pattern
		self._id = id
		
		# now, check to see if the part ID matches the pattern for this component
		if self._id:
			if re_part_id_pattern := self._pattern:
				if match := re_part_id_pattern.match(self._id):
					(self._library, self._symbol, self.package) = \
						BOM_component.extract_part_id(self._id)
				else:
					self._id = None
			else:
				self._id = None


	@staticmethod
	@abstractmethod
	def apply_settings(cls, settings : BOM_settings):
		...


	@staticmethod
	def extract_part_id(part_id:str) -> tuple[str,str,str]:
		if match := BOM_component.__RE_EXTRACT_ID.match(part_id):
			return (match.group(1), match.group(2), match.group(3))
		else:
			return ("", "", "")
		

	def __bool__(self) -> bool:
		"""Test if BOM_component successfully generated a part number
		
		Returns:
			True if part number is defined; False otherwise
		"""
		return True if self.mpn else False
	

	def __str__(self):
		"""BOM_component conversion to str

		Returns:
			str representation of BOM_component: "MFN:MPN"
		"""
		return f"{self.mfn}:{self.mpn}"


	@staticmethod
	def _parse_params(*args) -> dict:
		"""Parse values from component fields

		Returns:
			dict with one or more of the following keys:
			  "VALUE":
			  "TOL":
			  "VRATING":
			  "PRATING":
			  "TCR":
			  "TCC":
		"""
		unknown = 0
		parse = {}
		for arg in reversed(args):
			if isinstance(arg,str):
				items = arg.split()
				for item in reversed(items):
					# TCR, TOL, TCC
					if mat := BOM_component.__RE_TCR.match(item):
						parse['TCR'] = "±" + str(int(mat.group(1))) + 'ppm/K'
						continue
					if mat := BOM_component.__RE_TOL.match(item):
						(parse['TOL'], _) = BOM_component._tol_code(mat.group(1), mat.group(2), mat.group(3), mat.group(4))
						continue
					if mat := BOM_component.__RE_TOL_AE.match(item):
						(parse['TOL'], _) = BOM_component._tol_code('pF', mat.group(1))
						continue
					if mat := BOM_component.__RE_TCC.match(item):
						parse['TCC'] = mat.group(1).upper()
						continue
					# VRATING, PRATING, VALUE
					if num := numstr(item):
						if unit := num.unit:
							unit = unit.upper()
						else:
							unit = ""
						# VRATING, PRATING, VALUE
						if unit=='V':
							parse['VRATING'] = num
							continue
						elif unit=='W':
							parse['PRATING'] = num
							continue
						else:
							parse['VALUE'] = num
							continue
					# unknown item
					unknown += 1
					parse[f'UNKNOWN{unknown}'] = item
					continue

		return parse


	@staticmethod
	def _tol_expr(tol:str|None, is_pF:bool=False) -> str:
		
		if tol is None:
			return "?"
			
		if is_pF:
			match tol:
				case "A":
					return "±0.05pF"
				case "B":
					return "±0.1pF"
				case "C":
					return "±0.25pF"
				case "D":
					return "±0.5pF"
				case "F":
					return "±1.0pF"
				case "G":
					return "±2.0pF"

		match tol:
			case 'A': # note W is also 0.05%
				return "±0.05%"
			case 'B':
				return "±0.1%"
			case 'C':
				return "±0.25%"
			case 'D':
				return "±0.5%"
			case 'F':
				return "±1%"
			case 'G':
				return "±2%"
			case 'H':
				return "±3%"
			case 'J':
				return "±5%"
			case 'K':
				return "±10%"
			case 'L':
				return "±0.01%"
			case 'M':
				return "±20%"
			case 'N':
				return "±30%"
			case 'P':
				return "+0.02%"
			case 'Q':
				return "-10%/+30%"
			case 'S':
				return "-20%/+50%"
			case 'T':
				return "-10%/+50%"
			case 'W': # note A is also 0.05%
				return "±0.05%"
			case 'Z':
				return "-20%/+80%"
			case _:
				return "?"


	@staticmethod
	def _tol_code(sign1:str, val1:str|None, sign2:str|None = None, val2:str|None = None):
		"""Determine tolerance code from parsed sign and tol fields

		Args:
			sign1: sign '', '+', '-', '±", or 'pF' for first value
			val1: first value
			sign2: sign '', '+', or '-' for second value
			val2: second value

		Notes:
			For the special case where sign1 == 'pF', the tolerance is a fixed
			tolerance in pF. This produces codes A-D.
			The string val1 in this case is the tolerance following the decimal
			point. For instance, "±0.10pF" would produce sign1=='pF' val1=="10"

		Returns:
			EIA tolerance code in set [ABCDEFGHJKLMNPSWXZ] or None
			None is produced if no valid tolerance code was indicated
			tuple: (code, is_pF)  when a valid tolerance code is found
			       (None, False)  when no valid tolerance code is found
				   code is a single letter in the set [ABCDEFGHJKLMNPSWXZ]
		"""

		if sign1=='pF':
			# codes A-D: symmetrical pF
			if val1=='.05' or val1=='0.05':
				return ('A', True)
			elif val1=='.1' or val1=='.10' or val1=='0.1' or val1=='0.10':
				return ('B', True)
			elif val1=='.25' or val1=='0.25':
				return ('C', True)
			elif val1=='.5' or val1=='.50' or val1=='0.5' or val1=='0.50':
				return ('D', True)
			elif val1=='1' or val1=='1.0':
				return ('F', True)
			elif val1=='2' or val1=='2.0':
				return ('G', True)
			else:
				return (None, True)

		my_val1 = float(val1) if val1 else -1.0
		my_val2 = float(val2) if val2 else -1.0
		sign1 = sign1 if sign1 is not None else ''
		sign2 = sign2 if sign2 is not None else ''

		if sign1=='±' or sign1=='':
			# codes E-N: symmetrical percentage
			if sign2!='' or my_val2>=0.0:
				return (None, False)  # ± allowed only for single tolerance spec
			elif my_val1==0.005:
				return ('E', False)
			elif my_val1==0.01:
				return ('L', False)
			elif my_val1==0.02:
				return ('P', False)
			elif my_val1==0.05:
				return ('W', False)
			elif my_val1==0.1:
				return ('B', False)
			elif my_val1==0.25:
				return ('C', False)
			elif my_val1==0.5:
				return ('D', False)
			elif my_val1==1.0:
				return ('F', False)
			elif my_val1==2.0:
				return ('G', False)
			elif my_val1==3.0:
				return ('H', False)
			elif my_val1==5.0:
				return ('J', False)
			elif my_val1==10.0:
				return ('K', False)
			elif my_val1==15.0:
				return ('L', False)
			elif my_val1==20.0:
				return ('M', False)
			elif my_val1==30.0:
				return ('N', False)
			else:
				# catch-all for unknown codes
				return (None, False)

		if sign1=='+' and sign2=='':
			# not allowed
			return (None, False)

		if sign1=='+' and sign2=='-':
			# swap them - with + and -, - should appear first
			sign1, my_val1, sign2, my_val2 = sign2, my_val2, sign1, my_val1

		if sign1=='-' and sign2=='+':
			# codes S, X, and Z: unbalanced percentage
			if my_val1==10.0 and my_val2==30.0:
				return ('Q', False)
			elif my_val1==20.0 and my_val2==50.0:
				return ('S', False)
			elif my_val1==10.0 and my_val2==50.0:
				return ('T', False)
			elif my_val1==20.0 and my_val2==80.0:
				return ('Z', False)
			else:
				return (None, False)

		else:
			# everything else is invalid
			return (None, False)


	@staticmethod
	def _tol_decode(tol:str):
		if mat := BOM_component.__RE_TOL.match(tol):
			(code, _) = BOM_component._tol_code(mat.group(1), mat.group(2), mat.group(3), mat.group(4))
		else:
			code = ""
		return code


	@staticmethod
	def _tcr_decode(tcr:str):
		if mat := BOM_component.__RE_TCR.match(item):
			tcr = "±" + str(int(mat.group(1))) + 'ppm/K'
		else:
			tcr = ""
		return tcr


	def _extract_package_digits(package:str) -> str:
		my_package = ""
		if package:
			if match := BOM_component.__RE_EXTRACT_PKG_DIGITS.match(package):
				my_package = match.group(1)
		return my_package


	def _extract_package_digits_hv(package:str) -> str:
		my_package = ""
		if package:
			if match := BOM_component.__RE_EXTRACT_PKG_DIGITS_HV.match(package):
				my_package = match.group(1)
		return my_package	


# ******************************************************************************
#  Copyright © 2026 Kerry S. Martin, martin@wild-wood.net
#  Free for usage without warranty, expressed or implied; attribution required
# ******************************************************************************