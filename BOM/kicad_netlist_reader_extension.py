# ******************************************************************************
#  Copyright © 2026 Kerry S. Martin, martin@wild-wood.net
#  Free for usage without warranty, expressed or implied; attribution required
#
#  Filename   : kicad_netlist_reader_extension.py
#  Description:
#    Extension to kicad_netlist_reader.py that adds the ability to read variant
#    values from components.
#
#    This adds a class comp_variants that is derived from the base class comp.
#    comp_variants adds two additional methods:
#      has_variant   does the comp have the given variant?
#      getValue()    overload: gets the value for the given variant
#      getField()    overload: gets the field for the given variant
#
#  This work is derived directly from kicad_netlist_reader.py
#
#  Created    : 04/12/2026
#  Modified   : 04/12/2026
#  Author     : Kerry S. Martin, martin@wild-wood.net
# ******************************************************************************

from BOM.kicad_netlist_reader import netlist, comp


class comp_variants(comp):
	"""extension of kicad_netlist_reader comp to handle variant values
	"""

	def __init__(self, xml_element, variant:str):
		"""comp_variants constructor

		Args:
			xml_element: [xmlElement] XML element used to initialize
			             [comp]       comp object being extended with variants
			variant:     [str]        name of the target variant
		"""
		if isinstance(xml_element, comp):
			super().__init__(xml_element.element)
		else:
			super().__init__(xml_element)
		self.variant_tag = variant
		self.variant = None
		if (variants := self.element.getChild("variants")) is not None:
			variants_children = variants.getChildren()
			for my_variant in variants_children:
				if my_variant.get('variant', 'name') == self.variant_tag:
					self.variant = my_variant
					break

	@property
	def has_variant(self) -> bool:
		"""check if the target variant exists for this comp

		Returns:
			True if the target variant is defined for comp; False otherwise
		"""
		return (self.variant is not None)


	def getValue(self):
		"""gets the value for the target variant

		Returns:
			If the target variant is defined for comp, returns its value
			Otherwise, returns the default value for the comp
		"""
		value = super().getValue()
		if self.variant is not None:
			if (fields := self.variant.getChild("fields")) is not None:
				for field in fields.getChildren():
					if field.get('field', 'name') == 'Value':
						value = field.get('field', 'name', 'Value')
						break
		return value
		
		
	def getField(self, name, aLibraryToo = True):
		"""gets the value of a field for the target variant
		
		Returns:
			If the target variant is defined for comp, returns the field value
			Otherwise, returns the default field value for the comp
		"""
		value = super().getField(name, aLibraryToo)
		if self.variant is not None:
			if (fields := self.variant.getChild("fields")) is not None:
				for field in fields.getChildren():
					if field.get('field', 'name') == name:
						value = field.get('field', 'name', name)
						break

		return value
		
	
	def _getProperty(self, name):
		value = ""
		if self.variant is not None:
			props = self.variant.getChildren('property')
			for prop in props:
				try:
					if prop.attributes['name'] == name:
						prop_value = prop.attributes['value']
						value = prop_value
						break
					
				except KeyError:
					continue

		return value		


	def getDNP(self):
		"""gets the state of DNP for the target variant
		
		Returns:
			True  if the target variant is defined for comp and is marked DNP
			False otherwise
		"""
		result = super().getDNP()
		if self.variant is not None:
			if dnp := self._getProperty("dnp"):
				result = (dnp == "1")
		return result


	def getDNPString(self):
		"""gets the state of DNP for the target variant as a string "DNP" or ""
		
		Returns:
			"DNP" if the target variant is defined for comp and is marked DNP
			""     otherwise
		"""
		return "DNP" if self.getDNP() else ""


	@staticmethod
	def get_variant_names(target) -> set[str]:
		"""gets the names of all variants found in the target

		Args:
			target: [xmlElement]
			        [comp]
			        [netlist]

		Returns:
			list of variant names or empty l
		"""
		result = set()
		if isinstance(target, comp):
			my_element = target.element
		elif isinstance(target, netlist):
			my_comps = target.getInterestingComponents(excludeBOM=False)
			for my_comp in my_comps:
				result.update(comp_variants.get_variant_names(my_comp))
			my_element = None
		else:
			my_element = target

		if my_element:
			if (variants := my_element.getChild("variants")) is not None:
				for variant in variants.getChildren():
					name = variant.get('variant', 'name')
					if name:
						result.add(name)

		return result


# ******************************************************************************
#  Copyright © 2026 Kerry S. Martin, martin@wild-wood.net
#  Free for usage without warranty, expressed or implied; attribution required
# ******************************************************************************