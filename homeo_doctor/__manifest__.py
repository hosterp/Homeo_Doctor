# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Homeo_Doctor',
    'version': '1.0',
    'category': 'Sales/Sales',
    'summary': 'Hospital Management Software',

    'depends': [
        'product'
    ],
    'data': [
        "views/patient_reg.xml",
        "views/menu.xml",
        "views/medicine_entry.xml",
        "views/product_product_inherit.xml",

    ],
    'demo': [

    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
