from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

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

