# ******************************************************************************
#  Copyright © 2026 Kerry S. Martin, martin@wild-wood.net
#  Free for usage without warranty, expressed or implied; attribution required
#
#  Filename   : BOM_settings.py
#  Description:
#    Class to hold global BOM generator settings as obtained from the fields of
#    the optional BOM_GENERATOR symbol on the schematic.
#
#  Created    : 04/08/2026
#  Modified   : 04/11/2026
#  Author     : Kerry S. Martin, martin@wild-wood.net
# ******************************************************************************


class BOM_settings:
	"""Class for holding named settings, retrieved from the BOM_GENERATOR symbol
	"""
	
	def __init__(self):
		"""BOM_settings constructor: create an empty BOM_settings object
		"""
		self._settings = dict()


	def add_setting(self, name:str, value:str):
		"""Add a named setting and value
		
		Args:
			name  = [string] case-sensitive name of the setting
			value = [string] value to assign to the setting
		"""
		self._settings[name] = value


	def get_setting(self, name:str, default:str) -> str:
		"""Retrieve a named setting or default value
		
		Args:
			name    = [string] case-sensitive name of the setting
			default = [string] value returned if setting is not defined or blank
			
		"""
		if name in self._settings:
			if self._settings[name]:
				return self._settings[name]
			else:
				return default
		else:
			return default


# ******************************************************************************
#  Copyright © 2026 Kerry S. Martin, martin@wild-wood.net
#  Free for usage without warranty, expressed or implied; attribution required
# ******************************************************************************	