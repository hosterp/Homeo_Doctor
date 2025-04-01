from odoo import api, fields, models, _




class LabResultPage(models.Model):
    _name='lab.result.page'
    _rec_name = 'bill_number'

    bill_number=fields.Many2one('doctor.lab.report',string='Bill Number', domain=[('status', '=', 'paid')])
    patient_id=fields.Many2one(related='bill_number.user_ide',string='UHID')
    patient_name = fields.Char(related='bill_number.patient_name')
    doctor=fields.Many2one('doctor.profile',string='Doctor')
    sample_collected=fields.Datetime(string='Sample collection On')
    lab_collection=fields.Datetime(string='Lab Collection On')
    test_on=fields.Datetime(string='Test On')
    internal_doctor = fields.Many2one('internal.doctor',string='Select Internal Doctor')
    lab_incharge =fields.Many2one('lab.incharge',string='Select Lab In-charge')
    lab_technician = fields.Many2one('lab.technician',string='Select Lab Technician')
    lab_line_ids = fields.One2many('lab.scan.line', 'lab_result_id', string='Lab Result')
    staff=fields.Char(string='staff')
    @api.onchange('bill_number')
    def _onchange_bill_number(self):
        self.patient_id = False
        self.patient_name = False
        self.doctor = False
        self.sample_collected = False
        self.lab_collection = False
        self.test_on = False
        self.internal_doctor = False
        self.lab_incharge = False
        self.lab_technician = False
        self.lab_line_ids = [(5, 0, 0)]

        if self.bill_number:

            lab_report = self.bill_number


            self.patient_id = lab_report.user_ide.id
            self.patient_name = lab_report.patient_name
            self.doctor = lab_report.doctor_id.id
            self.sample_collected = lab_report.date


            lab_lines = []
            for lab_line in lab_report.lab_line_ids:
                lab_lines.append((0, 0, {
                    'lab_result_id': self.id,
                    'lab_test_name': lab_line.lab_test_name,
                    'lab_result': lab_line.lab_result,
                }))


            if lab_lines:
                self.lab_line_ids = lab_lines


class InternalDoctor(models.Model):
    _name = 'internal.doctor'
    _rec_name = 'internal_doctor'


    internal_doctor = fields.Char(string='Internal Doctor')


class labIncharge(models.Model):
    _name = 'lab.incharge'
    _rec_name = 'lab_incharge_name'


    lab_incharge_name=fields.Char(string='Lab Incharge')


class LabTechnician(models.Model):
    _name = 'lab.technician'



    lab_tecnician_name = fields.Char(string='Lab Technician')