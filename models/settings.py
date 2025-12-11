# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class Settings(models.Model):
    _name = 'api_tramites_servicios_17.settings'
    _description = 'Settings'

    usuario = fields.Char('usuario')
    password = fields.Char('Password')
    tipo = fields.Char('Tipo')
    ip = fields.Char('Ip')
    page = fields.Char('Pagina')
