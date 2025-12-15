from odoo import models, fields, api
import json
import requests
import logging

_logger = logging.getLogger(__name__)


class Tramite(models.Model):
    _inherit = 'api_tramites_servicios_17.servicios'  # Asegurando herencia para métodos adicionales si aplica

    @api.model
    def execute_cron_ficha(self):
        """Método llamado por el cron. Obtiene el token y realiza la solicitud con la homoclave del modelo `servicios`."""
        _logger.info("*********************INICIANDO PROCESAMIENTO DE FICHAS (20 EN 20)**************************")
        
        try:
            token = self.obtain_token_ficha()
            _logger.info(token)
            if not token:
                _logger.error("Error: No se obtuvo el token.")
                return False
            
            # Buscar servicios que NO tienen ficha, limitado a 20
            servicios_sin_ficha = self.env['api_tramites_servicios_17.servicios'].search([
                ('ficha', '=', False),
                ('homoclave', '!=', False)
            ], limit=20, order='id')  # Ordenar por ID para consistencia
            
            _logger.info(f"Encontrados {len(servicios_sin_ficha)} servicios sin ficha para procesar")
            
            if servicios_sin_ficha:
                servicios_procesados = 0
                servicios_con_error = 0
                
                for servicio in servicios_sin_ficha:
                    try:
                        _logger.info(f"Procesando ficha para servicio: {servicio.nombre} (Homoclave: {servicio.homoclave})")
                        self.call_single_page_ficha(token, servicio.homoclave)
                        servicios_procesados += 1
                        
                        # Delay entre requests para evitar sobrecarga
                        import time
                        time.sleep(1)  # 1 segundo entre requests
                        
                    except Exception as e:
                        _logger.error(f"Error procesando ficha para servicio {servicio.nombre}: {str(e)}")
                        servicios_con_error += 1
                        continue
                
                _logger.info(f"Fichas procesadas: {servicios_procesados} exitosos, {servicios_con_error} con errores")
                
                # Verificar si quedan más servicios sin ficha
                servicios_restantes = self.env['api_tramites_servicios_17.servicios'].search_count([
                    ('ficha', '=', False),
                    ('homoclave', '!=', False)
                ])
                
                _logger.info(f"Servicios sin ficha restantes: {servicios_restantes}")
                
                # Si no quedan más servicios sin ficha, desactivar el cron
                if servicios_restantes == 0:
                    cron = self.env.ref('api_tramites_servicios_17.ir_cron_execute_api_calls_ficha', raise_if_not_found=False)
                    if cron:
                        cron.sudo().write({'active': False})
                        _logger.info("Cron desactivado: no quedan servicios sin ficha")
                else:
                    _logger.info(f"Próxima ejecución procesará otros {min(20, servicios_restantes)} servicios")
                
                return True
            else:
                _logger.info("No hay servicios sin ficha para procesar")
                return False
                
        except Exception as e:
            _logger.error(f"Error en execute_cron_ficha: {str(e)}")
            import traceback
            _logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def obtain_token_ficha(self):
        """Realiza la solicitud para obtener el token."""
        url_token = "https://www.catalogonacional.gob.mx/sujetosobligados/api/Login"
        payload_token = json.dumps({
            "Usuario": "api.veracruz.xalapa",
            "Password": "D1*yR7jM4vQ2nX9sA+kT6pWf8",
            "Tipo": "Correo",
            "Ip": "0.0.0.0"
        })
        headers_token = {
            'Content-Type': 'application/json'
        }

        try:
            response_token = requests.post(url_token, headers=headers_token, data=payload_token)
            if response_token.status_code == 200:
                token_data = response_token.json()
                return token_data.get("token")
            else:
                _logger.info(f"Error al obtener el token en obtain_token_ficha: {response_token.status_code}")
        except Exception as e:
            _logger.info(f"Exception occurred: {str(e)}")
        return None

    def call_single_page_ficha(self, token, homoclave):
        """Realiza la consulta para una homoclave específica y almacena la data en los modelos correspondientes."""
        headers = {
            'Authorization': f'Bearer {token}'
        }
        url_consulta = f"https://www.catalogonacional.gob.mx/sujetosobligados/api/Tramites/ficha/publica/actual/{homoclave}"

        try:
            response = requests.get(url_consulta, headers=headers)
            if response.status_code == 200:
                data = response.json()
                self.create_tramite_record_ficha(data)
            else:
                _logger.info(f"Error al realizar la consulta en la homoclave: {response.status_code}")
        except Exception as e:
            _logger.info(f"Exception occurred while calling API: {str(e)}")

    def create_tramite_record_ficha(self, data):
        """Crea o actualiza el registro de `tramite` con la data obtenida."""
        tramite_vals = {
            'id': data.get('id'),
            'dependencia': data.get('dependencia'),
            'unidadAdministrativa': data.get('unidadAdministrativa'),
            'acronimoDependencia': data.get('acronimoDependencia'),
            'tipo': data.get('tipo'),
            'homoclave': data.get('homoclave'),
            'nombre': data.get('nombre'),
            'descripcionCiudadana': data.get('descripcionCiudadana'),
            'descripcion': data.get('descripcion'),
            'modalidad': data.get('modalidad'),
            'traResolucionesFavorables': data.get('traResolucionesFavorables'),
            'tramiteServicio': data.get('tramiteServicio'),
            'traquienSolicita_Otro': data.get('traquienSolicita_Otro'),
            'traConsultasChatLinea': data.get('traConsultasChatLinea'),
            'numeroRequFormato': data.get('numeroRequFormato'),
            'numeroRequNoFormato': data.get('numeroRequNoFormato'),
            'requiereConservarInfo': data.get('requiereConservarInfo'),
            'acreditacion': data.get('acreditacion'),
            'acreditacionEspecifique': data.get('acreditacionEspecifique'),
            'verificacion': data.get('verificacion'),
            'verificacionEspecifique': data.get('verificacionEspecifique'),
            'inspeccion': data.get('inspeccion'),
            'inspeccionEspecifique': data.get('inspeccionEspecifique'),
            'conservarOtros': data.get('conservarOtros'),
            'conservarOtrosEspecifique': data.get('conservarOtrosEspecifique'),
            'suficienteCumplirRequisitos': data.get('suficienteCumplirRequisitos'),
            'metodologiaResolucion': data.get('metodologiaResolucion'),
            'metodologiaAdjuntarArchivo': data.get('metodologiaAdjuntarArchivo'),
            'tramiteRequiereInspeccion': data.get('tramiteRequiereInspeccion'),
            'objetivoInspeccion': data.get('objetivoInspeccion'),
            'traResolucionesFav': data.get('traResolucionesFav'),
            'traVolumenAnual': data.get('traVolumenAnual'),
            'traComentariosRespecto': data.get('traComentariosRespecto'),
            'traConsultasChatLineaLigas': data.get('traConsultasChatLineaLigas'),
            'fechaActualizacion': data.get('fechaActualizacion'),
        }

        tramite = self.env['api_tramites_servicios_17.tramite'].search([('homoclave', '=', tramite_vals['homoclave'])], limit=1)
        if tramite:
            tramite.sudo().write(tramite_vals)
        else:
            tramite = self.env['api_tramites_servicios_17.tramite'].sudo().create(tramite_vals)

        self.create_related_records_ficha(tramite, data)

        # Actualizar el campo `ficha_id` en `servicios` usando `homoclave`
        servicio = self.env['api_tramites_servicios_17.servicios'].search([('homoclave', '=', tramite.homoclave)], limit=1)
        if servicio:
            servicio.ficha_id = tramite.id
            servicio.ficha = True

    def create_related_records_ficha(self, tramite, data):
        """Crea registros relacionados para `costos`, `opcionesRealizarTramite`, y otros."""

        # Crear registros en `costos`
        self.env['tramite.costo'].search([('tramite_id', '=', tramite.id)]).sudo().unlink()
        for costo in data.get('costos', []):
            self.env['tramite.costo'].sudo().create({
                'tramite_id': tramite.id,
                'monto': costo.get('monto'),
                'moneda': costo.get('moneda'),
                'tipoCosto': costo.get('tipoCosto'),
                'momentoRealizarPago': costo.get('momentoRealizarPago'),
                'formula': costo.get('formula'),
                'dondeRealizarPago': costo.get('dondeRealizarPago'),
                'descripcionMedioPago': costo.get('descripcionMedioPago'),
                'rangoMontoInicial': costo.get('rangoMontoInicial'),
                'rangoMontoFinal': costo.get('rangoMontoFinal'),
                'montoOficinas': costo.get('montoOficinas'),
                'montoOficinasEspecifique': costo.get('montoOficinasEspecifique'),
                'montoBanco': costo.get('montoBanco'),
                'montoBancoReferencias': costo.get('montoBancoReferencias'),
                'montoEnLinea': costo.get('montoEnLinea'),
                'montoEnLineaReferencias': costo.get('montoEnLineaReferencias'),
                'montoTiendas': costo.get('montoTiendas'),
                'montoTiendasReferncias': costo.get('montoTiendasReferncias'),
                'montosOtros': costo.get('montosOtros'),
                'montosOtrosEspecifique': costo.get('montosOtrosEspecifique'),
                'montoOtroDesc': costo.get('montoOtroDesc')
            })

        # Crear registros en `opcionesRealizarTramite`
        self.env['tramite.opcion'].search([('tramite_id', '=', tramite.id)]).sudo().unlink()
        for opcion in data.get('opcionesRealizarTramite', []):
            l = self.env['tramite.opcion'].sudo().create({
                'tramite_id': tramite.id,
                'opcionRealizarTramite': opcion.get('opcionRealizarTramite'),
                'permiteAgendarCita': opcion.get('permiteAgendarCita'),
                'agendarCitaEnLinea': opcion.get('agendarCitaEnLinea'),
                'ligaCitaEnLinea': opcion.get('ligaCitaEnLinea'),
                'canalAtencionId': opcion.get('canalAtencionId'),
                'existeAppTramite': opcion.get('existeAppTramite'),
                'accionesApp': opcion.get('accionesApp'),
                'existeWebTramite': opcion.get('existeWebTramite'),
                'ligaWeb': opcion.get('ligaWeb'),
                'accionesWeb': opcion.get('accionesWeb'),
                'viaTelefonica': opcion.get('viaTelefonica'),
                'telefono': opcion.get('telefono'),
                'accionesTelefono': opcion.get('accionesTelefono'),
                'viaSMS': opcion.get('viaSMS'),
                'codigoSMS': opcion.get('codigoSMS'),
                'viaKiosko': opcion.get('viaKiosko'),
                'accionesKiosko': opcion.get('accionesKiosko'),
                'accionesSMS': opcion.get('accionesSMS'),
                'otro': opcion.get('otro'),
                'especifiqueOtro': opcion.get('especifiqueOtro'),
                'accionesOtro': opcion.get('accionesOtro')
            })
            for horario in opcion.get('accionesPresenciallst', []):
                self.env['tramite.accionpresencial'].sudo().create({
                    'opcion_id': l.id,
                    'accion': horario.get('accion'),
                    'orden': horario.get('orden'),
                })


        # Crear registros en `oficinasAtencion`
        self.env['tramite.oficina'].search([('tramite_id', '=', tramite.id)]).sudo().unlink()
        for oficina in data.get('oﬁcinasAtencion', []):
            oficina_record = self.env['tramite.oficina'].sudo().create({
                'tramite_id': tramite.id,
                'id': oficina.get('id'),
                'nombre': oficina.get('nombre'),
                'direccion': oficina.get('direccion'),
                'telefono': oficina.get('telefono'),
                'extension': oficina.get('extension')
            })
            for horario in oficina.get('horarios', []):
                self.env['tramite.horario'].sudo().create({
                    'oficina_id': oficina_record.id,
                    'dia': horario.get('dia'),
                    'apertura': horario.get('apertura'),
                    'cierre': horario.get('cierre')
                })

        # Crear registros en `contactos`
        self.env['tramite.contacto'].search([('tramite_id', '=', tramite.id)]).sudo().unlink()
        for contacto in data.get('contactos', []):
            self.env['tramite.contacto'].sudo().create({
                'tramite_id': tramite.id,
                'nombre': contacto.get('nombre'),
                'apellidoP': contacto.get('apellidoP'),
                'apellidoM': contacto.get('apellidoM'),
                'telefono': contacto.get('telefono'),
                'extension': contacto.get('extension'),
                'cargo': contacto.get('cargo'),
                'correo': contacto.get('correo'),
                'tipoContacto': contacto.get('tipoContacto'),
                'rolFuncionario': contacto.get('rolFuncionario')
            })

        # Crear registros en `requisitos`
        self.env['tramite.requisito'].search([('tramite_id', '=', tramite.id)]).sudo().unlink()
        for requisito in data.get('requisitos', []):
            self.env['tramite.requisito'].sudo().create({
                'tramite_id': tramite.id,
                'nombre': requisito.get('nombre'),
                'descripcion': requisito.get('descripcion'),
                'original': requisito.get('original'),
                'copias': requisito.get('copias'),
                'copiasCerificadas': requisito.get('copiasCerificadas'),
                'naturalezaDelRequisito': requisito.get('naturalezaDelRequisito'),
                'esNecesarioFirma': requisito.get('esNecesarioFirma'),
                'tipoRevisionTercero_CatId': requisito.get('tipoRevisionTercero_CatId'),
                'tipoRevisionTercero_CatIdNom': requisito.get('tipoRevisionTercero_CatIdNom'),
                'otroTipoRevisionTercero': requisito.get('otroTipoRevisionTercero'),
                'empresaEmiteRevision_CatId': requisito.get('empresaEmiteRevision_CatId'),
                'empresaEmiteRevision_CatIdNom': requisito.get('empresaEmiteRevision_CatIdNom'),
                'otraEmpresaEmiteRevision': requisito.get('otraEmpresaEmiteRevision'),
                'requisitoEsTramite': requisito.get('requisitoEsTramite'),
                'institucionEmite': requisito.get('institucionEmite'),
                'nombreTramiteRequisito': requisito.get('nombreTramiteRequisito'),
                'requisitoId': requisito.get('requisitoId'),
                'requisitoParteFormato': requisito.get('requisitoParteFormato'),
                'tiempoDias': requisito.get('tiempoDias'),
                'tiempoHoras': requisito.get('tiempoHoras'),
                'tiempoMinutos': requisito.get('tiempoMinutos'),
                'requisitoTramite': requisito.get('requisitoTramite')
            })

        # Crear registros en `formatos`
        self.env['tramite.formato'].search([('tramite_id', '=', tramite.id)]).sudo().unlink()
        for formato in data.get('formatos', []):
            self.env['tramite.formato'].sudo().create({
                'tramite_id': tramite.id,
                'nombre': formato.get('nombre'),
                'identificador': formato.get('identificador'),
                'url': formato.get('url'),
                'llenarLinea': formato.get('llenarLinea'),
                'ligaLlenar': formato.get('ligaLlenar'),
                'enviarFormatos': formato.get('enviarFormatos'),
                'ligaEnvioFormatos': formato.get('ligaEnvioFormatos'),
                'ligaDOF': formato.get('ligaDOF'),
                'formatoId': formato.get('formatoId'),
                'fechaPublicacionFormato': formato.get('fechaPublicacionFormato')
            })

        # Crear registros en `fundamento`
        self.env['tramite.fundamento'].search([('tramite_id', '=', tramite.id)]).sudo().unlink()
        for fundamento in data.get('fundamento', []):
            self.env['tramite.fundamento'].sudo().create({
                'tramite_id': tramite.id,
                'tramiteId': fundamento.get('tramiteId'),
                'tipo': fundamento.get('tipo'),
                'requisitoId': fundamento.get('requisitoId'),
                'canalAtencionId': fundamento.get('canalAtencionId'),
                'formatoId': fundamento.get('formatoId'),
                'plazoPrevencionId': fundamento.get('plazoPrevencionId'),
                'plazoInterezadoId': fundamento.get('plazoInterezadoId'),
                'plazoMaximoId': fundamento.get('plazoMaximoId'),
                'ordenGobierno': fundamento.get('ordenGobierno'),
                'tipoOrdenamiento': fundamento.get('tipoOrdenamiento'),
                'nombreOrdenamiento': fundamento.get('nombreOrdenamiento'),
                'articulo': fundamento.get('articulo'),
                'fraccion': fundamento.get('fraccion'),
                'inciso': fundamento.get('inciso'),
                'parrafo': fundamento.get('parrafo'),
                'numero': fundamento.get('numero'),
                'letra': fundamento.get('letra'),
                'otro': fundamento.get('otro')
            })

        # Crear registros en `plazos`
        self.env['tramite.plazo'].search([('tramite_id', '=', tramite.id)]).sudo().unlink()
        for plazo in data.get('plazos', []):
            self.env['tramite.plazo'].sudo().create({
                'tramite_id': tramite.id,
                'nombrePlazo': plazo.get('nombrePlazo'),
                'respuestaResolver': plazo.get('respuestaResolver'),
                'paraPrevenir': plazo.get('paraPrevenir'),
                'responderlaPrevencion': plazo.get('responderlaPrevencion'),
                'respuestaDependencia': plazo.get('respuestaDependencia')
            })

        # Crear registros en `vigencia`
        self.env['tramite.vigencia'].search([('tramite_id', '=', tramite.id)]).sudo().unlink()
        for vigencia in data.get('vigencia', []):
            self.env['tramite.vigencia'].sudo().create({
                'tramite_id': tramite.id,
                'vigenciaTramite': vigencia.get('vigenciaTramite')
            })

        # Crear registros en `solicita`
        self.env['tramite.solicita'].search([('tramite_id', '=', tramite.id)]).sudo().unlink()
        for solicita in data.get('solicita', []):
            self.env['tramite.solicita'].sudo().create({
                'tramite_id': tramite.id,
                'quienSolicita': solicita.get('quienSolicita'),
                'casoRealizaTramite': solicita.get('casoRealizaTramite'),
                'descripcionVinculada': solicita.get('descripcionVinculada'),
                'descripcionRequisitoOtroTramite': solicita.get('descripcionRequisitoOtroTramite')
            })

        # Crear registros en `conservarInformacion`
        self.env['tramite.conservar_informacion'].search([('tramite_id', '=', tramite.id)]).sudo().unlink()
        for conservar_info in data.get('conservarInformacion', []):
            self.env['tramite.conservar_informacion'].sudo().create({
                'tramite_id': tramite.id,
                'requiereConservar': conservar_info.get('requiereConservar'),
                'finesParaConservar': conservar_info.get('finesParaConservar'),
                'descripcion': conservar_info.get('descripcion')
            })

        # Crear registros en `solicitudes`
        self.env['tramite.solicitud'].search([('tramite_id', '=', tramite.id)]).sudo().unlink()
        for solicitud in data.get('solicitudes', []):
            self.env['tramite.solicitud'].sudo().create({
                'tramite_id': tramite.id,
            })

class Tramite(models.Model):
    _name = 'api_tramites_servicios_17.tramite'
    _description = 'Trámite'

    id = fields.Char(string='ID')
    dependencia = fields.Char(string='dependencia')
    unidadAdministrativa = fields.Char(string='unidadAdministrativa')
    acronimoDependencia = fields.Char(string='acronimoDependencia')
    tipo = fields.Char(string='tipo')
    homoclave = fields.Char(string='homoclave')
    nombre = fields.Char(string='nombre')
    descripcionCiudadana = fields.Char(string='descripcionCiudadana')
    descripcion = fields.Char(string='descripcion')
    modalidad = fields.Char(string='modalidad')
    traResolucionesFavorables = fields.Char(string='traResolucionesFavorables')
    tramiteServicio = fields.Char(string='tramiteServicio')
    traquienSolicita_Otro = fields.Char(string='traquienSolicita_Otro')
    traConsultasChatLinea = fields.Char(string='traConsultasChatLinea')
    numeroRequFormato = fields.Char(string='numeroRequFormato')
    numeroRequNoFormato = fields.Char(string='numeroRequNoFormato')
    requiereConservarInfo = fields.Char(string='requiereConservarInfo')
    acreditacion = fields.Char(string='acreditacion')
    acreditacionEspecifique = fields.Char(string='acreditacionEspecifique')
    verificacion = fields.Char(string='verificacion')
    verificacionEspecifique = fields.Char(string='verificacionEspecifique')
    inspeccion = fields.Char(string='inspeccion')
    inspeccionEspecifique = fields.Char(string='inspeccionEspecifique')
    conservarOtros = fields.Char(string='conservarOtros')
    conservarOtrosEspecifique = fields.Char(string='conservarOtrosEspecifique')
    suficienteCumplirRequisitos = fields.Char(string='suficienteCumplirRequisitos')
    metodologiaResolucion = fields.Char(string='metodologiaResolucion')
    metodologiaAdjuntarArchivo = fields.Char(string='metodologiaAdjuntarArchivo')
    tramiteRequiereInspeccion = fields.Char(string='tramiteRequiereInspeccion')
    objetivoInspeccion = fields.Char(string='objetivoInspeccion')
    traResolucionesFav = fields.Char(string='traResolucionesFav')
    traVolumenAnual = fields.Char(string='traVolumenAnual')
    traComentariosRespecto = fields.Char(string='traComentariosRespecto')
    traConsultasChatLineaLigas = fields.Char(string='traConsultasChatLineaLigas')
    criteriosresolucion = fields.One2many('tramite.criterioresolucion', 'tramite_id', string='criteriosresolucion')
    costos = fields.One2many('tramite.costo', 'tramite_id', string='costos')
    fechaActualizacion = fields.Char(string='fechaActualizacion')
    opcionesRealizarTramite = fields.One2many('tramite.opcion', 'tramite_id', string='opcionesRealizarTramite')
    oficinasAtencion = fields.One2many('tramite.oficina', 'tramite_id', string='oficinasAtencion')
    contactos = fields.One2many('tramite.contacto', 'tramite_id', string='contactos')
    requisitos = fields.One2many('tramite.requisito', 'tramite_id', string='requisitos')
    formatos = fields.One2many('tramite.formato', 'tramite_id', string='formatos')
    fundamento = fields.One2many('tramite.fundamento', 'tramite_id', string='fundamento')
    plazos = fields.One2many('tramite.plazo', 'tramite_id', string='plazos')
    vigencia = fields.One2many('tramite.vigencia', 'tramite_id', string='vigencia')
    solicita = fields.One2many('tramite.solicita', 'tramite_id', string='solicita')
    conservarInformacion = fields.One2many('tramite.conservar_informacion', 'tramite_id', string='conservarInformacion')
    solicitudes = fields.One2many('tramite.solicitud', 'tramite_id', string='solicitudes')



class TramiteCriterioResolucion(models.Model):
    _name = 'tramite.criterioresolucion'
    _description = 'Criterio de Resolución'

    tramite_id = fields.Many2one('api_tramites_servicios_17.tramite', string='Trámite')


class TramiteCosto(models.Model):
    _name = 'tramite.costo'
    _description = 'Costos del Trámite'

    tramite_id = fields.Many2one('api_tramites_servicios_17.tramite', string='Trámite')
    monto = fields.Char(string='monto')
    moneda = fields.Char(string='moneda')
    tipoCosto = fields.Char(string='tipoCosto')
    momentoRealizarPago = fields.Char(string='momentoRealizarPago')
    formula = fields.Char(string='formula')
    dondeRealizarPago = fields.Char(string='dondeRealizarPago')
    descripcionMedioPago = fields.Char(string='descripcionMedioPago')
    rangoMontoInicial = fields.Char(string='rangoMontoInicial')
    rangoMontoFinal = fields.Char(string='rangoMontoFinal')
    montoOficinas = fields.Char(string='montoOficinas')
    montoOficinasEspecifique = fields.Char(string='montoOficinasEspecifique')
    montoBanco = fields.Char(string='montoBanco')
    montoBancoReferencias = fields.Char(string='montoBancoReferencias')
    montoEnLinea = fields.Char(string='montoEnLinea')
    montoEnLineaReferencias = fields.Char(string='montoEnLineaReferencias')
    montoTiendas = fields.Char(string='montoTiendas')
    montoTiendasReferncias = fields.Char(string='montoTiendasReferncias')
    montosOtros = fields.Char(string='montosOtros')
    montosOtrosEspecifique = fields.Char(string='montosOtrosEspecifique')
    montoOtroDesc = fields.Char(string='montoOtroDesc')


class TramiteOpcion(models.Model):
    _name = 'tramite.opcion'
    _description = 'Opciones para Realizar Trámite'

    tramite_id = fields.Many2one('api_tramites_servicios_17.tramite', string='Trámite')
    opcionRealizarTramite = fields.Char(string='opcionRealizarTramite')
    permiteAgendarCita = fields.Char(string='permiteAgendarCita')
    agendarCitaEnLinea = fields.Char(string='agendarCitaEnLinea')
    ligaCitaEnLinea = fields.Char(string='ligaCitaEnLinea')
    canalAtencionId = fields.Char(string='canalAtencionId')
    existeAppTramite = fields.Char(string='existeAppTramite')
    accionesApp = fields.Char(string='accionesApp')
    existeWebTramite = fields.Char(string='existeWebTramite')
    ligaWeb = fields.Char(string='ligaWeb')
    accionesWeb = fields.Char(string='accionesWeb')
    viaTelefonica = fields.Char(string='viaTelefonica')
    telefono = fields.Char(string='telefono')
    accionesTelefono = fields.Char(string='accionesTelefono')
    viaSMS = fields.Char(string='viaSMS')
    codigoSMS = fields.Char(string='codigoSMS')
    viaKiosko = fields.Char(string='viaKiosko')
    accionesKiosko = fields.Char(string='accionesKiosko')
    accionesSMS = fields.Char(string='accionesSMS')
    otro = fields.Char(string='otro')
    especifiqueOtro = fields.Char(string='especifiqueOtro')
    accionesOtro = fields.Char(string='accionesOtro')
    #accionesApplst = fields.One2many('tramite.accionapp', 'opcion_id', string='accionesApplst')
    #accionesKioskolst = fields.One2many('tramite.accionkiosko', 'opcion_id', string='accionesKioskolst')
    #accionesOtrolst = fields.One2many('tramite.accionotro', 'opcion_id', string='accionesOtrolst')
    accionesPresenciallst = fields.One2many('tramite.accionpresencial', 'opcion_id', string='accionesPresenciallst')


class TramiteAccionPresencial(models.Model):
    _name = 'tramite.accionpresencial'
    _description = 'Acciones Presenciales'

    opcion_id = fields.Many2one('tramite.opcion', string='Opción')
    accion = fields.Char(string='accion')
    orden = fields.Char(string='orden')


class TramiteOficina(models.Model):
    _name = 'tramite.oficina'
    _description = 'Oficinas de Atención para Trámite'

    tramite_id = fields.Many2one('api_tramites_servicios_17.tramite', string='Trámite')
    id = fields.Char(string='ID')
    nombre = fields.Char(string='nombre')
    direccion = fields.Char(string='direccion')
    telefono = fields.Char(string='telefono')
    extension = fields.Char(string='extension')
    horarios = fields.One2many('tramite.horario', 'oficina_id', string='horarios')


class TramiteHorario(models.Model):
    _name = 'tramite.horario'
    _description = 'Horarios de Atención'

    oficina_id = fields.Many2one('tramite.oficina', string='Oficina')
    dia = fields.Char(string='dia')
    apertura = fields.Char(string='apertura')
    cierre = fields.Char(string='cierre')


class TramiteContacto(models.Model):
    _name = 'tramite.contacto'
    _description = 'Contactos para Trámite'

    tramite_id = fields.Many2one('api_tramites_servicios_17.tramite', string='Trámite')
    nombre = fields.Char(string='nombre')
    apellidoP = fields.Char(string='apellidoP')
    apellidoM = fields.Char(string='apellidoM')
    telefono = fields.Char(string='telefono')
    extension = fields.Char(string='extension')
    cargo = fields.Char(string='cargo')
    correo = fields.Char(string='correo')
    tipoContacto = fields.Char(string='tipoContacto')
    rolFuncionario = fields.Char(string='rolFuncionario')


class TramiteRequisito(models.Model):
    _name = 'tramite.requisito'
    _description = 'Requisitos del Trámite'

    tramite_id = fields.Many2one('api_tramites_servicios_17.tramite', string='Trámite')
    nombre = fields.Char(string='nombre')
    descripcion = fields.Char(string='descripcion')
    original = fields.Char(string='original')
    copias = fields.Char(string='copias')
    copiasCerificadas = fields.Char(string='copiasCerificadas')
    naturalezaDelRequisito = fields.Char(string='naturalezaDelRequisito')
    esNecesarioFirma = fields.Char(string='esNecesarioFirma')
    tipoRevisionTercero_CatId = fields.Char(string='tipoRevisionTercero_CatId')
    tipoRevisionTercero_CatIdNom = fields.Char(string='tipoRevisionTercero_CatIdNom')
    otroTipoRevisionTercero = fields.Char(string='otroTipoRevisionTercero')
    empresaEmiteRevision_CatId = fields.Char(string='empresaEmiteRevision_CatId')
    empresaEmiteRevision_CatIdNom = fields.Char(string='empresaEmiteRevision_CatIdNom')
    otraEmpresaEmiteRevision = fields.Char(string='otraEmpresaEmiteRevision')
    requisitoEsTramite = fields.Char(string='requisitoEsTramite')
    institucionEmite = fields.Char(string='institucionEmite')
    nombreTramiteRequisito = fields.Char(string='nombreTramiteRequisito')
    requisitoId = fields.Char(string='requisitoId')
    requisitoParteFormato = fields.Char(string='requisitoParteFormato')
    tiempoDias = fields.Char(string='tiempoDias')
    tiempoHoras = fields.Char(string='tiempoHoras')
    tiempoMinutos = fields.Char(string='tiempoMinutos')
    requisitoTramite = fields.Char(string='requisitoTramite')


class TramiteFormato(models.Model):
    _name = 'tramite.formato'
    _description = 'Formatos del Trámite'

    tramite_id = fields.Many2one('api_tramites_servicios_17.tramite', string='Trámite')
    nombre = fields.Char(string='nombre')
    identificador = fields.Char(string='identificador')
    url = fields.Char(string='url')
    llenarLinea = fields.Char(string='llenarLinea')
    ligaLlenar = fields.Char(string='ligaLlenar')
    enviarFormatos = fields.Char(string='enviarFormatos')
    ligaEnvioFormatos = fields.Char(string='ligaEnvioFormatos')
    ligaDOF = fields.Char(string='ligaDOF')
    formatoId = fields.Char(string='formatoId')
    fechaPublicacionFormato = fields.Char(string='fechaPublicacionFormato')


class TramiteFundamento(models.Model):
    _name = 'tramite.fundamento'
    _description = 'Fundamento del Trámite'

    tramite_id = fields.Many2one('api_tramites_servicios_17.tramite', string='Trámite')
    tramiteId = fields.Char(string='tramiteId')
    tipo = fields.Char(string='tipo')
    requisitoId = fields.Char(string='requisitoId')
    canalAtencionId = fields.Char(string='canalAtencionId')
    formatoId = fields.Char(string='formatoId')
    plazoPrevencionId = fields.Char(string='plazoPrevencionId')
    plazoInterezadoId = fields.Char(string='plazoInterezadoId')
    plazoMaximoId = fields.Char(string='plazoMaximoId')
    ordenGobierno = fields.Char(string='ordenGobierno')
    tipoOrdenamiento = fields.Char(string='tipoOrdenamiento')
    nombreOrdenamiento = fields.Char(string='nombreOrdenamiento')
    articulo = fields.Char(string='articulo')
    fraccion = fields.Char(string='fraccion')
    inciso = fields.Char(string='inciso')
    parrafo = fields.Char(string='parrafo')
    numero = fields.Char(string='numero')
    letra = fields.Char(string='letra')
    otro = fields.Char(string='otro')


class TramitePlazo(models.Model):
    _name = 'tramite.plazo'
    _description = 'Plazos del Trámite'

    tramite_id = fields.Many2one('api_tramites_servicios_17.tramite', string='Trámite')
    nombrePlazo = fields.Char(string='nombrePlazo')
    respuestaResolver = fields.Char(string='respuestaResolver')
    paraPrevenir = fields.Char(string='paraPrevenir')
    responderlaPrevencion = fields.Char(string='responderlaPrevencion')
    respuestaDependencia = fields.Char(string='respuestaDependencia')


class TramiteVigencia(models.Model):
    _name = 'tramite.vigencia'
    _description = 'Vigencia del Trámite'

    tramite_id = fields.Many2one('api_tramites_servicios_17.tramite', string='Trámite')
    vigenciaTramite = fields.Char(string='vigenciaTramite')


class TramiteSolicita(models.Model):
    _name = 'tramite.solicita'
    _description = 'Solicitante del Trámite'

    tramite_id = fields.Many2one('api_tramites_servicios_17.tramite', string='Trámite')
    quienSolicita = fields.Char(string='quienSolicita')
    casoRealizaTramite = fields.Char(string='casoRealizaTramite')
    descripcionVinculada = fields.Char(string='descripcionVinculada')
    descripcionRequisitoOtroTramite = fields.Char(string='descripcionRequisitoOtroTramite')


class TramiteConservarInformacion(models.Model):
    _name = 'tramite.conservar_informacion'
    _description = 'Conservar Información del Trámite'

    tramite_id = fields.Many2one('api_tramites_servicios_17.tramite', string='Trámite')
    requiereConservar = fields.Char(string='requiereConservar')
    finesParaConservar = fields.Char(string='finesParaConservar')
    descripcion = fields.Char(string='descripcion')


class TramiteSolicitud(models.Model):
    _name = 'tramite.solicitud'
    _description = 'Solicitudes del Trámite'

    tramite_id = fields.Many2one('api_tramites_servicios_17.tramite', string='Trámite')


##############################################################################
class tramiteaccionapp(models.Model):
    _name = 'tramite.accionapp'

class tramiteaccionkiosko(models.Model):
    _name = 'tramite.accionkiosko'

class TramiteSolicitud(models.Model):
    _name = 'tramite.accionotro'

