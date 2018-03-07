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


class is_bureau(models.Model):
    _name = "is.bureau"
    _description = "Bureau"
    _order='name'

    name            = fields.Char('Bureau', required=True)
    commentaire     = fields.Text('Commentaire')


class is_type_ordinateur(models.Model):
    _name = "is.type.ordinateur"
    _description = "Type d'ordinateur"
    _order='name'

    name            = fields.Char("Type d'ordinateur", required=True)
    commentaire     = fields.Text('Commentaire')


class is_ordinateur(models.Model):
    _name = "is.ordinateur"
    _description = "Ordinateurs"
    _order='name'

    site_id            = fields.Many2one('is.site', 'Site', required=True)
    name               = fields.Char('Nom du poste', required=True)
    type_ordinateur_id = fields.Many2one('is.type.ordinateur', "Type d'ordinateur")
    bureau_id          = fields.Many2one('is.bureau', 'Bureau')
    service_id         = fields.Many2one('is.service', 'Service')
    utilisateur_id     = fields.Many2one('is.utilisateur', 'Utilisateur')
    date_debut         = fields.Date('Date de mise en service')
    partage_ids        = fields.Many2many('is.partage' , 'is_ordinateur_partage_rel' , 'ordinateur_id','partage_id' , string="Partages", help=u"Ce champ est utilisé par le programme de sauvegarde des messageries" )
    commentaire        = fields.Text('Commentaire')
    action_ids         = fields.One2many('is.action', 'ordinateur_id', u'Actions', readonly=True)
    sauvegarde_ids     = fields.One2many('is.save.mozilla', 'ordinateur_id', u'Sauvegardes', readonly=True)
    active             = fields.Boolean('Actif', default=True)

    glpi_name              = fields.Char('Nom du poste' , readonly=True)
    glpi_contact           = fields.Char('Utilisateur'  , readonly=True)
    glpi_serial            = fields.Char('N°série'      , readonly=True)
    glpi_os_license_number = fields.Char('Licence OS'   , readonly=True)
    glpi_os_licenseid      = fields.Char('Licence OS id', readonly=True)
    glpi_date_mod          = fields.Datetime('Date GLPI', readonly=True)
    glpi_operatingsystems  = fields.Char('Système'      , readonly=True)

    glpi_bios_date         = fields.Date('Date du bios', readonly=True)
    glpi_installationdate  = fields.Date("Date d'installation", readonly=True)
    glpi_remote_addr       = fields.Char('Adresse IP'   , readonly=True)
    glpi_winowner          = fields.Char('Administrateur'  , readonly=True)



#winowner 	wincompany 	last_fusioninventory_update 	remote_addr 	plugin_fusioninventory_computerarchs_id 	serialized_inventory 	is_entitylocked 	oscomment
#	8 	8 	2014-12-18 00:00:00 	A10 	  	1 	2015-02-18 16:17:53 	utilisateur 	Microsoft 	2018-03-02 13:55:10 	192.0.0.206 	1 	[BLOB - 11,6Kio]	0 	NULL
# localhost - glpi - glpi_plugin_fusioninventory_inventorycomputercomputers 



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
                    ossp.name,
                    f.bios_date,
                    f.operatingsystem_installationdate,
                    f.remote_addr,
                    f.winowner
                FROM glpi_computers c left outer join glpi_operatingsystems os on c.operatingsystems_id=os.id
                                      left outer join glpi_operatingsystemservicepacks ossp on c.operatingsystemversions_id=ossp.id
                                      left outer join glpi_plugin_fusioninventory_inventorycomputercomputers f on f.computers_id=c.id
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
                if row[8]:
                    obj.glpi_bios_date     = row[8].strftime('%Y-%m-%d')  
                if row[9]:
                    obj.glpi_installationdate = row[9].strftime('%Y-%m-%d')  
                obj.glpi_remote_addr       = row[10]
                obj.glpi_winowner          = row[11]

    def actualiser_glpi_scheduler_action(self, cr, uid, use_new_cursor=False, company_id = False, context=None):
        self.actualiser_glpi_scheduler(cr, uid, context)


    @api.multi
    def actualiser_glpi_scheduler(self):
        _logger.info("## Actualisation depuis GLPI - Début")
        ordinateurs=self.env['is.ordinateur'].search([])
        ordinateurs.actualiser_glpi_action()
        _logger.info("## Actualisation depuis GLPI - Fin")



