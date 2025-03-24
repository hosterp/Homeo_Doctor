from odoo import api, fields, models, _



class LabDepartment(models.Model):
    _name = 'lab.department'
    _rec_name = 'department_name'


    department_name=fields.Char(string='Department Name')
    order_no=fields.Integer(string='Order Number')


class LabInvestigation(models.Model):
    _name = 'lab.investigation'
    _rec_name = 'investigation_name'



    lab_department=fields.Many2one('lab.department',string='Lab Department')
    investigation_name= fields.Char(string = 'Investigation Name')
    bill_code = fields.Char(string = 'Bill Code')
    rate= fields.Char(string='Rate')