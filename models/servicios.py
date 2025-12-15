from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)

class Servicios(models.Model):
    _name = 'api_tramites_servicios_17.servicios'

    id_servicios = fields.Char(string='Id')
    nombre = fields.Char(string='Nombre')
    homoclave = fields.Char(string='Homoclave')
    categoria = fields.Char(string='Categoria')
    modalidad = fields.Char(string='Modalidad')
    sujetoObligado = fields.Char(string='Sujeto Obligado')
    descripcionCiudadana = fields.Text(string='Descripcion ciudadana')
    traFechaModificacion = fields.Datetime(string='traFechaModificacion')

    ordenamientos_ids = fields.One2many(
        'api_tramites_servicios_17.ordenamientos',
        'service_id',
        string='Ordenamientos'
    )

    ficha_id = fields.Many2one('api_tramites_servicios_17.tramite', string='Ficha')
    ficha = fields.Boolean(string="Tiene Ficha", default= False)