# -*- coding: utf-8 -*-
import datetime
from openerp import models,fields,api
from openerp.tools.translate import _
from openerp.exceptions import Warning
import MySQLdb
import logging
_logger = logging.getLogger(__name__)


class is_partage(models.Model):
    _name = "is.partage"
    _description = "Partages Windows"
    _order='name'

    name = fields.Char('Partage', required=True)


class is_ordinateur(models.Model):
    _name = "is.ordinateur"
    _description = "Ordinateurs"
    _order='name'

    site_id        = fields.Many2one('is.site', 'Site', required=True)
    name           = fields.Char('Nom du poste', required=True)
    service_id     = fields.Many2one('is.service', 'Service')
    utilisateur_id = fields.Many2one('is.utilisateur', 'Utilisateur')
    date_debut     = fields.Date('Date de mise en service')
    partage_ids    = fields.Many2many('is.partage' , 'is_ordinateur_partage_rel' , 'ordinateur_id','partage_id' , string="Partages", help=u"Ce champ est utilisé par le programme de sauvegarde des messageries" )
    commentaire    = fields.Text('Commentaire')
    action_ids     = fields.One2many('is.action', 'ordinateur_id', u'Actions', readonly=True)
    active         = fields.Boolean('Actif', default=True)

    glpi_name              = fields.Char('Nom du poste' , readonly=True)
    glpi_contact           = fields.Char('Utilisateur'  , readonly=True)
    glpi_serial            = fields.Char('N°série'      , readonly=True)
    glpi_os_license_number = fields.Char('Licence OS'   , readonly=True)
    glpi_os_licenseid      = fields.Char('Licence OS id', readonly=True)
    glpi_date_mod          = fields.Datetime('Date GLPI', readonly=True)
    glpi_operatingsystems  = fields.Char('Système'      , readonly=True)


    @api.multi
    def actualiser_glpi_action(self):
        uid=self._uid
        user=self.env['res.users'].browse(uid)
        glpi_host   = user.company_id.is_glpi_host
        glpi_user   = user.company_id.is_glpi_user
        glpi_passwd = user.company_id.is_glpi_passwd
        glpi_db     = user.company_id.is_glpi_db
        try:
            db = MySQLdb.connect(host=glpi_host, user=glpi_user, passwd=glpi_passwd, db=glpi_db)
        except MySQLdb.OperationalError, msg:
            raise Warning(u"La connexion à GLPI a échouée ! \n"+str(msg[1]))
        cur = db.cursor()
        nb=len(self)
        ct=0
        for obj in self:
            ct=ct+1
            _logger.info(str(ct)+'/'+str(nb)+u' : Mise à jour GLPI '+str(obj.name))
            SQL="""
                SELECT 
                    c.name,
                    c.contact,
                    c.serial,
                    c.os_license_number,
                    c.os_licenseid,
                    c.date_mod,
                    os.name,
                    ossp.name
                FROM glpi_computers c left outer join glpi_operatingsystems os on c.operatingsystems_id=os.id
                                      left outer join glpi_operatingsystemservicepacks ossp on c.operatingsystemversions_id=ossp.id
                WHERE c.name='"""+obj.name+"""'
            """
            cur.execute(SQL)
            for row in cur.fetchall():
                obj.glpi_name              = row[0]
                obj.glpi_contact           = row[1]
                obj.glpi_serial            = row[2]
                obj.glpi_os_license_number = row[3]
                obj.glpi_os_licenseid      = row[4]
                obj.glpi_date_mod          = row[5]
                obj.glpi_operatingsystems  = (row[6] or '')+' '+(row[7] or '')


    def actualiser_glpi_scheduler_action(self, cr, uid, use_new_cursor=False, company_id = False, context=None):
        self.actualiser_glpi_scheduler(cr, uid, context)


    @api.multi
    def actualiser_glpi_scheduler(self):
        _logger.info("## Actualisation depuis GLPI - Début")
        ordinateurs=self.env['is.ordinateur'].search([])
        ordinateurs.actualiser_glpi_action()
        _logger.info("## Actualisation depuis GLPI - Fin")



