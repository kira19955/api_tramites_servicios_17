from odoo import fields, models, api
import json
import requests
import logging
import time
import traceback
from datetime import datetime

_logger = logging.getLogger(__name__)


class CronJobs(models.AbstractModel):
    _name = 'api_tramites_servicios_17.cron'
    _description = 'Funciones para crons'

    @api.model
    def execute_cron_service(self):
        """Método que será llamado por el cron. Obtiene el token y realiza la solicitud de la página correspondiente."""

        token = self.obtain_token()

        if token:
            self.call_single_page(token)
            _logger.info("Token obtenido correctamente: %s", token)

        else:
            _logger.info("Error: No se obtuvo el token.")

    #FUNCIONES DEL CRON PARA LA PRIMERA EJECUCION QUE TRAE
    # LOS SERVICIOS CON SUS ORDENAMIENTOS SOLICITANDO UN TOKEN
    #
    def obtain_token(self):
        """Realiza la solicitud para obtener el token desde los datos almacenados en el modelo api_tramites_servicios_17.settings."""

        settings = self.env['api_tramites_servicios_17.settings'].search([], limit=1)

        if not settings:
            _logger.info("No se encontraron configuraciones para obtener el token.")
            return None

        payload_token = json.dumps({
            "Usuario": settings.usuario,
            "Password": settings.password,
            "Tipo": settings.tipo,
            "Ip": settings.ip
        })

        headers_token = {
            'Content-Type': 'application/json'
        }

        url_token = "https://www.catalogonacional.gob.mx/sujetosobligados/api/Login"

        try:
            response_token = requests.post(url_token, headers=headers_token, data=payload_token)
            if response_token.status_code == 200:
                token_data = response_token.json()
                token = token_data.get("token")
                return token
            else:
                _logger.info(f"Error al obtener el token: {response_token.status_code}")
                return None
        except Exception as e:
            _logger.info(f"Exception occurred: {str(e)}")
            return None

    def call_single_page(self, token):
        """Consulta una página de la API usando el token, y procesa los servicios recibidos."""

        headers_consulta = {
            'Authorization': f'Bearer {token}'
        }

        settings = self.env['api_tramites_servicios_17.settings'].search([], limit=1)

        # Si no hay registro de configuración, lo creamos con página 1
        if not settings:
            settings = self.env['api_tramites_servicios_17.settings'].create({
                'page': 1,
            })

        page_number = settings.page or 1  # Asegura que siempre sea al menos 1

        url_consulta = f"https://www.catalogonacional.gob.mx/sujetosobligados/api/ConsultaTramites/Id_nom_cat_dep_hom/all/{page_number}"

        try:
            response = requests.get(url_consulta, headers=headers_consulta)
            _logger.info(f"Response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json().get('data', [])

                # Detectar fin de paginación
                if not data:
                    _logger.info(f"La página {page_number} no contiene datos. Reiniciando página y deteniendo cron.")
                    settings.page = 1

                    try:

                        cron_id_ficha = self.env.ref('api_tramites_servicios_17.ir_cron_execute_api_calls_ficha',
                                               raise_if_not_found=False)

                        if cron_id_ficha:
                            self.reset_all_fichas()
                            cron_id_ficha.sudo().write({'active': True})
                            _logger.info("El cron fue activado automáticamente (fin de los servicios)")
                    except Exception as e:
                        _logger.error(f"No se pudo desactivar el cron automáticamente: {str(e)}")

                    return  # Salimos de la función para no seguir

                _logger.info(f"Procesando {len(data)} servicios de la página {page_number}")

                servicios_procesados = 0
                servicios_con_error = 0

                for index, item in enumerate(data):
                    try:
                        _logger.info(f"Procesando servicio {index + 1}/{len(data)}: {item.get('nombre', 'Sin nombre')}")
                        servicio = self.create_or_update_service(item)
                        _logger.info(f"Servicio creado/actualizado: ID {servicio.id}, Nombre: {servicio.nombre}")

                        # Crear o actualizar ordenamientos
                        ordenamientos_data = item.get('ordenamientos', [])
                        for ordenamiento in ordenamientos_data:
                            try:
                                ordenamiento_id = ordenamiento.get('id')

                                # Buscar si ya existe este ordenamiento para el servicio
                                existing = self.env['api_tramites_servicios_17.ordenamientos'].search([
                                    ('id_ordenamiento', '=', ordenamiento_id),
                                    ('service_id', '=', servicio.id)
                                ], limit=1)

                                valores_ordenamiento = {
                                    'nombre': ordenamiento.get('nombre'),
                                    'articulo': ordenamiento.get('articulo'),
                                    'fraccion': ordenamiento.get('fraccion'),
                                    'insiso': ordenamiento.get('insiso'),
                                    'parrafo': ordenamiento.get('parrafo'),
                                    'numero': ordenamiento.get('numero'),
                                    'letra': ordenamiento.get('letra'),
                                    'otro': ordenamiento.get('otro'),
                                    'service_id': servicio.id
                                }

                                if existing:
                                    existing.write(valores_ordenamiento)
                                    _logger.info(f"Ordenamiento actualizado: {existing.id}")
                                else:
                                    self.env['api_tramites_servicios_17.ordenamientos'].create({
                                        'id_ordenamiento': ordenamiento_id,
                                        **valores_ordenamiento
                                    })
                                    _logger.info(f"Ordenamiento creado: {ordenamiento_id}")

                            except Exception as e:
                                _logger.error(f"Error creando/actualizando ordenamiento para servicio {servicio.id}: {e}")

                        servicios_procesados += 1

                    except Exception as e:
                        _logger.error(f"Error procesando servicio {index + 1}: {e}")
                        servicios_con_error += 1
                        continue

                _logger.info(
                    f"Página {page_number} procesada: {servicios_procesados} exitosos, {servicios_con_error} con errores")

                if servicios_procesados > 0:
                    settings.page += 1
                    _logger.info(f"Página incrementada a: {settings.page}")
                else:
                    _logger.warning("No se procesaron servicios exitosamente, la página no se incrementa.")

            else:
                _logger.error(f"Error HTTP al consultar página {page_number}: {response.status_code}")
                _logger.error(f"Contenido de respuesta: {response.text}")

        except Exception as e:
            _logger.error(f"Error de red o parseo al procesar página {page_number}: {e}")
            _logger.error(f"Traceback: {traceback.format_exc()}")

    def create_or_update_service(self, data):
        """Crea o actualiza un registro del modelo servicios basado en la data de la API."""
        try:
            # Validar datos requeridos
            if not data.get('id'):
                raise ValueError("ID del servicio es requerido")

            servicio = self.env['api_tramites_servicios_17.servicios'].search([('id_servicios', '=', data.get('id'))], limit=1)

            # Procesar fecha de modificación
            fecha_modificacion = None
            if data.get('traFechaModificacion'):
                try:
                    # Convertir fecha ISO a formato Odoo

                    fecha_str = data.get('traFechaModificacion')
                    # Parsear fecha ISO: 2025-03-07T00:00:00
                    fecha_modificacion = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
                    _logger.info(f"Fecha parseada correctamente: {fecha_modificacion}")
                except Exception as fecha_error:
                    _logger.warning(f"Error parseando fecha {data.get('traFechaModificacion')}: {str(fecha_error)}")
                    fecha_modificacion = None

            servicio_data = {
                'id_servicios': data.get('id'),
                'nombre': data.get('nombre', 'Sin nombre'),
                'homoclave': data.get('homoclave', ''),
                'categoria': data.get('categoria', ''),
                'modalidad': data.get('modalidad', ''),
                'sujetoObligado': data.get('sujetoObligado', ''),
                'descripcionCiudadana': data.get('descripcionCiudadana', ''),
                'traFechaModificacion': fecha_modificacion
            }

            if not servicio:
                _logger.info(f"Creando nuevo servicio: {servicio_data['nombre']} (ID: {servicio_data['id_servicios']})")
                Servicios = self.env['api_tramites_servicios_17.servicios']
                servicio = Servicios.create(servicio_data)
                _logger.info(f"Servicio creado exitosamente: {servicio.id}")
            else:
                _logger.info(f"Actualizando servicio existente: {servicio.nombre} (ID: {servicio.id})")
                servicio.write(servicio_data)
                _logger.info(f"Servicio actualizado exitosamente: {servicio.id}")

            return servicio

        except Exception as e:
            _logger.error(f"Error en create_or_update_service: {str(e)}")
            _logger.error(f"Datos del servicio: {data}")
            raise




        ###################################################################################################################################

    def reset_all_fichas(self):
        self.env['api_tramites_servicios_17.servicios'].search([]).write({'ficha': False})
        _logger.info("Todas las fichas fueron reseteadas a False.")

    @api.model
    def execute_cron_ficha(self):
        """Método llamado por el cron. Obtiene el token y realiza la solicitud con la homoclave del modelo `servicios`."""
        _logger.info("*********************INICIANDO PROCESAMIENTO DE FICHAS (20 EN 20)**************************")

        try:
            cron_id = self.env.ref('api_tramites_servicios_17.ir_cron_execute_api_calls_services',
                                   raise_if_not_found=False)

            if cron_id:
                cron_id.sudo().write({'active': False})
                _logger.info("El cron fue desactivado automáticamente (fin de la paginación)")

            token = self.obtain_token()
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
                        _logger.info(
                            f"Procesando ficha para servicio: {servicio.nombre} (Homoclave: {servicio.homoclave})")
                        self.call_single_page_ficha(token, servicio.homoclave)
                        servicios_procesados += 1

                        # Delay entre requests para evitar sobrecarga

                        time.sleep(1)  # 1 segundo entre requests

                    except Exception as e:
                        _logger.error(f"Error procesando ficha para servicio {servicio.nombre}: {str(e)}")
                        servicios_con_error += 1
                        continue

                _logger.info(
                    f"Fichas procesadas: {servicios_procesados} exitosos, {servicios_con_error} con errores")

                # Verificar si quedan más servicios sin ficha
                servicios_restantes = self.env['api_tramites_servicios_17.servicios'].search_count([
                    ('ficha', '=', False),
                    ('homoclave', '!=', False)
                ])

                _logger.info(f"Servicios sin ficha restantes: {servicios_restantes}")

                # Si no quedan más servicios sin ficha, desactivar el cron
                if servicios_restantes == 0:
                    cron = self.env.ref('api_tramites_servicios_17.ir_cron_execute_api_calls_ficha',
                                        raise_if_not_found=False)
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
            _logger.error(f"Traceback: {traceback.format_exc()}")
            return False


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

        tramite = self.env['api_tramites_servicios_17.tramite'].search(
            [('homoclave', '=', tramite_vals['homoclave'])], limit=1)
        if tramite:
            tramite.sudo().write(tramite_vals)
        else:
            tramite = self.env['api_tramites_servicios_17.tramite'].sudo().create(tramite_vals)

        self.create_related_records_ficha(tramite, data)

        # Actualizar el campo `ficha_id` en `servicios` usando `homoclave`
        servicio = self.env['api_tramites_servicios_17.servicios'].search([('homoclave', '=', tramite.homoclave)],
                                                                          limit=1)
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



#########################################################################################################################################
    @api.model
    def activate_cron(self):
        """Activa el cron para ejecutar las llamadas a la API si está desactivado."""
        cron_id = self.env.ref('api_tramites_servicios_17.ir_cron_execute_api_calls_services', raise_if_not_found=False)
        if cron_id and not cron_id.active:
            cron_id.sudo().write({'active': True})
            _logger.info("El cron 'ir_cron_execute_api_calls' ha sido activado.")
        else:
            _logger.info("El cron 'ir_cron_execute_api_calls' ya está activo o no se encontró.")