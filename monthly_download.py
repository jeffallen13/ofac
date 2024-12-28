'''
Downloads and processes OFAC sanctions data at the end of each month
'''

from ofac import OFACProcessor

processor = OFACProcessor()

ofac_list = processor.update_ofac_list()

ofac_panel = processor.create_panel(ofac_list)

