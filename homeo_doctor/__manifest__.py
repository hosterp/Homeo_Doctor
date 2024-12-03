# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Homeo_Doctor1',
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
        "views/patient.xml",
        "views/doctor_profile_views.xml",
        "views/doctor_lab_report_views.xml",
        "views/product_product_inherit.xml",
        "views/pharmacy.xml",
        "views/admitted_patient_details.xml",
        "views/ot_management.xml",
        "views/patient_insurance.xml",
        "report/patient_report.xml",
        "report/patient_registion_report.xml",
        "report/admitted_patient_report.xml",

    ],
    'assets': {
        'web.assets_backend': [
            'homeo_doctor/static/src/js/custom_filter.js',
        ],
    },
    'demo': [

    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
