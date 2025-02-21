# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Homeo_Doctor1',
    'version': '1.0',
    'category': 'Sales/Sales',
    'summary': 'Hospital Management Software',

    'depends': [
        'product','hr','account',
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
        "views/patient_appointments.xml",
        "views/doctor_department.xml",
        # "views/hr_module_custom.xml",
        "report/patient_report.xml",
        "report/patient_registion_report.xml",
        "report/admitted_patient_report.xml",
        "views/patient.xml",
        "views/ct_scan.xml",
        "views/mri_scan.xml",
        "views/x_ray_scan.xml",
        "views/patient_appointments.xml",
        "views/audiology.xml",
        "views/templates.xml",
        "report/ct_invoice_template.xml",
        "report/ct_reports.xml",
        "report/mri_invoice_template.xml",
        "report/mri_reports.xml",
        "report/x_ray_invoice_template.xml",
        "report/x_ray_reports.xml",
        "report/audiology_invoice_template.xml",
        "report/audiology_reports.xml",
        "report/lab_report.xml",
        "report/lab_report.xml",
        "report/Lab_report_report.xml",
        "views/custom_title.xml",
        "views/account_move_view.xml",

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
