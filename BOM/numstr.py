# ******************************************************************************
#  Copyright © 2026 Kerry S. Martin, martin@wild-wood.net
#  Free for usage without warranty, expressed or implied; attribution required
#
#  Filename   : numstr.py
#  Description:
#    Numerical engineering syntax strings
#
#    numstr format specification
#
#      0, 10, 10.5          (decimal)
#      1.0e-3, 2.5e5        (exponential/scientific)
#      100k, 10.0k, 0R      (suffix)
#      1k00, 2R5            (infix)
#      value may be preceded by a - or + to denote sign
#      value may be proceded by a unit [_a-zA-ZΩ]+
#      recognized case-sensitive suffix/index:
#         [TGMKkRrmunpf]|MEG
#
#  Created    : 03/14/2025
#  Modified   : 04/07/2026
#  Author     : Kerry S. Martin, martin@wild-wood.net
# ******************************************************************************

# TODO: numstr: if value was exponential format, estimate digits of precision

"""numstr: numerical engineering syntax strings"""

import re
import math
from copy import copy
from BOM.static_init import static_init


# ------------------------------------------------------------------------------
# class: numstr
# ------------------------------------------------------------------------------

@static_init
class numstr:
	"""class numstr: numeric engineering syntax strings

	Methods:
		numstr(raw, unit:str=None)      constructor
		bool(obj)                       returns True if valid, False otherwise
		float(obj)                      returns equivalent float value
		str(obj)                        returns "pretty" str representation
		obj.code(tol, scale)            returns "###E" code num + exponent
		obj.RKM(tol)                    returns RKM code ex/ 10K0, 3R32
		is_numstr(obj)                  check if obj can be expressed as numstr
	"""

	@classmethod
	def static_init(cls):
		# public
		cls.IS_VERBOSE : bool = False   # is __str__ verbose (True) or succinct (False)?

		# protected
		cls._REFG_UNIT = r"[_a-zA-ZΩ]*?"             # regex fragment for unit
		cls._REFG_SUFFIX = r"[TGMKkRrmunpf]|MEG"     # regex fragment for suffix/infix
		cls._RE_INFIX = re.compile(r"^([-+]?)(\d*(" + cls._REFG_SUFFIX + r")\d+)(" + cls._REFG_UNIT + r")$")
		cls._RE_SUFFIX = re.compile(r"^([-+]?)(\d+|\d*\.\d+|\d+\.)(" + cls._REFG_SUFFIX + r")(" + cls._REFG_UNIT + r")$")
		cls._RE_DECIMAL = re.compile(r"^([-+]?)((?:\d+|\d+\.\d*|\d*\.\d+)(?:[eE][-+]?\d{1,3})?)(" + cls._REFG_UNIT + r")$")


	def __init__(self, raw:"str|float|numstr|None"=None, unit:str|None=None):
		"""numstr constructor

		Args:
			raw: str or float to convert to raw string
			unit: optional unit associated wit the value. Defaults to None.
		"""
		if isinstance(raw, numstr):
			# copy the numstr (copy.copy did not work here for some reason)
			self.raw = raw.raw
			self.value = raw.value
			self.unit = raw.unit
			self.unitless = raw.unitless
			self.pretty = raw.pretty
		elif isinstance(raw, str):
			# convert string to numstr
			value, raw_unit, raw, ndigits, has_sign = numstr.__process_raw(raw)
			self.raw = raw
			self.value = value
			if value is not None:
				self.unit = unit if unit is not None else raw_unit
				self.unitless = numstr.__make_pretty(value, ndigits, None, has_sign)
				self.pretty = self.unitless if self.unit is None else f"{self.unitless}{self.unit}"
			else:
				self.unit = None
				self.unitless = None
				self.pretty = None
		elif isinstance(raw, float):
			# convert float to numstr
			self.raw = raw
			self.value = raw
			self.unit = "" if unit is None else unit
			self.unitless = numstr.__make_pretty(raw, None, None, False)
			self.pretty = self.unitless if self.unit is None else f"{self.unitless}{self.unit}"
		else:
			self.raw = None
			self.value = None
			self.unit = None
			self.unitless = None
			self.pretty = None


	def __bool__(self) -> bool:
		"""Test if numstr is defined
		
		Returns:
			True if numstr is defined; False if numstr is not defined
		"""
		return True if self.value is not None else False


	def __float__(self) -> float:
		"""Convert numstr to float

		Returns:
			float value of numstr
		"""
		if self.value is None:
			raise numstr.FloatConversionInvalid
		return self.value


	def __str__(self) -> str:
		"""Convert numstr to str

		Returns:
			if IS_VERBOSE==False, pretty version of numstr
			if IS_VERBOSE==True,  full numstr info
		"""
		pretty = self.pretty

		if numstr.IS_VERBOSE:
			if isinstance(self.raw, str):
				s = f'numstr<raw:\"{self.raw}\", pretty:\"{pretty}\", value:{self.value}, unit:\"{self.unit}\">'
			else:
				s = f'numstr<raw:{self.raw}, pretty:\"{pretty}\", value:{self.value}, unit:\"{self.unit}\">'
			return s
		elif pretty is not None:
			return pretty
		else:
			return ""


	def code(self, tol:str|None=None, scale:float|None=None) -> str:
		"""Generate 3 or 4 digit value code (##E or ###E)

		Args:
			tol: Tolerance letter code. Defaults to None.

		Returns:
			str: 3 or 4 digit value code
		"""
		value = self.value
		if tol is None or tol=="F" or tol=="Z":
			digits = 4
		else:
			digits = 3

		if value is None:
			return "?"*digits

		else:
			value = abs(value)

			if scale is not None and scale!=1.0:
				value = value*scale

			if digits == 4:
				if value<1.0:
					return "0R00"
				else:
					e = math.floor(math.log10(value))-2
					m = math.floor(value/math.pow(10.0, e))
					s = f"{m:03.0f}"
					if e >= 0:
						return f"{s}{e:01.0f}"
					elif e == -1:
						return f"{s[0:2]}R{s[2]}"
					elif e == -2:
						return f"{s[0]}R{s[1:3]}"
					elif e == -3:
						return f"R{s}"
					else:
						return "????"
			else:
				if value<1.0:
					return "0R0"
				else:
					e = math.floor(math.log10(value))-1
					m = math.floor(value/math.pow(10.0, e))
					s = f"{m:02.0f}"
					if e >= 0:
						return f"{m:02.0f}{e:01.0f}"
					elif e == -1:
						return f"{s[0]}R{s[1]}"
					elif e == -2:
						return f"R{s}"
					else:
						return "???"


	def RKM(self, tol:str|None=None) -> str:
		"""Convert numstr to str in RKM-infix format

		Args:
			tol: Tolerance letter code. Defaults to None.

		Returns:
			value expressed in RKM-infix format (ex/ 10R0, 4K7, 1M00)
		"""

		if tol is None or tol=="F" or tol=="Z":
			digits = 4
		else:
			digits = 3

		value = self.value
		if value is None:
			return "?"*digits

		else:
			value = abs(value)  # RKM only valid for non-negative

			if digits==4:
				if value<1.0:
					# all values below 1 ohm will be treated as 0 ohm jumper in RKM-infix format
					return "0000"
				elif value >= 1.0e6:
					value /= 1.0e6
					if value >= 100.0:
						return f"{value:0.0f}M"
					elif value >= 10.0:
						return f"{value:0.1f}".replace(".","M")
					else:
						return f"{value:0.2f}".replace(".","M")
					return value
				elif value >= 1.0e3:
					value /= 1.0e3
					if value >= 100.0:
						return f"{value:0.0f}K"
					elif value >= 10.0:
						return f"{value:0.1f}".replace(".","K")
					else:
						return f"{value:0.2f}".replace(".","K")
				else: # 1.0e3 > value >= 1.0
					if value >= 100.0:
						return f"{value:0.0f}R"
					elif value >= 10.0:
						return f"{value:0.1f}".replace(".","R")
					else:
						return f"{value:0.2f}".replace(".","R")
			else:
				return "?"*digits


	@staticmethod
	def is_numstr(value) -> bool:
		"""Test to see if value can be converted to a valid numstr.

		Args:
			value: any object

		Returns:
			True if value can be converted to numstr, False otherwise
		"""
		if isinstance(value, numstr):
			return bool(value)
		elif isinstance(value, float):
			return True
		elif isinstance(value, str):
			return (numstr._RE_INFIX.match(value) is not None) \
				or (numstr._RE_SUFFIX.match(value) is not None) \
				or (numstr._RE_DECIMAL.match(value) is not None)
		else:
			return False


	@staticmethod
	def __process_raw(raw:str) -> tuple: # [float|None,str,str,int,bool]
		raw = raw.strip()
		ndigits = None
		value = None
		unit = None
		sign = None
		pol = 1       # polarity +:1   -:-1
		while True: # one-pass break loop
			
			if m := numstr._RE_INFIX.match(raw):
				sign = m.group(1)
				pol = -1 if sign=='-' else 1
				num = m.group(2)
				infix = m.group(3)
				num = num.replace(infix, '.')
				ndigits = numstr.__count_digits(num)
				_, e, r = numstr.__norm_suffix(infix)
				value = pol*float(num)*pow(10.0, e+r)
				unit = m.group(4)
				break

			
			if m := numstr._RE_SUFFIX.match(raw):
				sign = m.group(1)
				pol = -1 if sign=='-' else 1
				num = m.group(2)
				ndigits = numstr.__count_digits(num)
				suffix = m.group(3)
				_, e, r = numstr.__norm_suffix(suffix)
				value = pol*float(num)*pow(10.0, e+r)
				unit = m.group(4)
				break

			
			if m := numstr._RE_DECIMAL.match(raw):
				sign = m.group(1)
				pol = -1 if sign=='-' else 1
				num = m.group(2)
				ndigits = numstr.__count_digits(num)
				value = pol*float(num)
				unit = m.group(3)
				break

			# unrecognized string, leave value==None to signal error
			break

		if value is not None:
			has_sign = False if sign=='' else True
		else:
			has_sign = None

		return (value, unit, raw, ndigits, has_sign)


	@staticmethod
	def __make_pretty(value:float, ndigits:int|None=None, unit:str|None=None, has_sign:bool=False) -> str:
		pretty = ""
		unit = "" if unit is None else unit
		if value==0.0:
			if ndigits is None or ndigits<=0:
				pretty = f"0{unit}"
			else:
				pretty = f"{0:.0{ndigits}f}{unit}"
		else:
			mag = abs(value)
			sign = '-' if value<0.0 else '+' if has_sign else ''
			suffix, n, _ = numstr.__norm_suffix(mag)
			mag = mag/pow(10.0,n)
			if ndigits is None:
				pretty = f"{sign}{mag}{suffix}{unit}"
			else:
				if mag>=100.0:
					n1 = 3
				elif mag>= 10.0:
					n1 = 2
				else:
					n1 = 1
				n2 = ndigits-n1 if ndigits>n1 else 0
				if n2>0:
					pretty = f"{sign}{mag:.{n2}f}{suffix}{unit}"
				else:
					pretty = f"{sign}{mag:.0f}{suffix}{unit}"

		return pretty


	@staticmethod
	def __norm_suffix(s:str|float|int) -> tuple:
		"""Analyze and normalize a suffix/infix

		Args:
			s: suffix       (as str)
			s: exponent     (as int)
			s: value        (as float)

		Returns:
			(eng_suffix, eng_exponent, res_exponent)
			where eng_suffix is the normalized suffix
				  eng_exponent is the engineering (power of 3) exponent value
				  res_exponent is the residual exponent such that:
					  eng_exponent + res_exponent = value exponent
		"""
		if isinstance(s, str):
			# convert engineering suffix to engineering exponent
			if s=='f':
				eng_exponent = -15
			elif s=='p':
				eng_exponent = -12
			elif s=='n':
				eng_exponent = -9
			elif s=='u':
				eng_exponent = -6
			elif s=='m':
				eng_exponent = -3
			elif s=='R' or s=='r' or s=='':
				eng_exponent = 0
			elif s=='K' or s=='k':
				eng_exponent = 3
			elif s=='M' or s=='MEG':
				eng_exponent = 6
			elif s=='G':
				eng_exponent = 9
			elif s=='T':
				eng_exponent = 12
			else:
				eng_exponent = None # Error

			# no remainder with this branch
			res_exponent = 0

		elif isinstance(s, (float,int)):
			# convert multiplier (float) or exponent (int) to suffix and residual exponent
			if isinstance(s, float):
				if float != 0.0:
					n1 = math.log10(abs(s))
				else:
					n1 = 0
			else:
				n1 = s

			# calculate engineering exponent and remaining exponent
			eng_exponent = 3*int(math.floor(n1/3))
			res_exponent = int(math.floor(n1-eng_exponent))

		else:
			eng_exponent = None
			res_exponent = 0

		if eng_exponent is not None:
			# normlize s to the preferred suffix
			if eng_exponent==-15:
				s = 'f'
			elif eng_exponent==-12:
				s = 'p'
			elif eng_exponent==-9:
				s = 'n'
			elif eng_exponent==-6:
				s = 'u'
			elif eng_exponent==-3:
				s = 'm'
			elif eng_exponent==0:
				s = ''
			elif eng_exponent==3:
				s = 'k'
			elif eng_exponent==6:
				s = 'M'
			elif eng_exponent==9:
				s = 'G'
			elif eng_exponent==12:
				s = 'T'
			else:
				s = '?'

			return (s, eng_exponent, res_exponent)

		else:
			return (None, None, None)


	@staticmethod
	def __count_digits(s:str) -> int:
		# count the number of significant digits in a numeric string
		# rules:
		#   cease counting at the end of the string or at the first character [^.0-9]
		#   do not count leading zeros
		n = 0
		had_lead_in = False
		for c in s:
			if c=='.':
				had_lead_in = True
			elif c=='0':
				if had_lead_in:
					n += 1
			elif c.isdigit():
				had_lead_in = True
				n += 1
			else:
				# stop counting at first non-numeric character
				break

		return n
		
		
	class FloatConversionInvalid(Exception):
		"""Attempted to convert undefined numstr into a float"""
		...


# ******************************************************************************
#  Copyright © 2026 Kerry S. Martin, martin@wild-wood.net
#  Free for usage without warranty, expressed or implied; attribution required
# ******************************************************************************