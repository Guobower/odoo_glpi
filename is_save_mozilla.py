# -*- coding: utf-8 -*-
import datetime
import pytz
from openerp import models,fields,api
from openerp.tools.translate import _
from openerp.exceptions import Warning
import logging
_logger = logging.getLogger(__name__)


class is_save_mozilla(models.Model):
    _name = "is.save.mozilla"
    _description = "Sauvegarde Mozilla"
    _order='heure_debut desc'

    date            = fields.Date('Date sauvegarde')
    site_id         = fields.Many2one('is.site', 'Site')
    service_id      = fields.Many2one('is.service', 'Service')
    utilisateur_id  = fields.Many2one('is.utilisateur', 'Utilisateur')
    ordinateur_id   = fields.Many2one('is.ordinateur', 'Ordinateur')
    partage         = fields.Char('Partage')
    mail            = fields.Char('Mail')
    taille          = fields.Integer('Taille (Mo)')
    nb_modifs       = fields.Integer('Nb modifs')
    heure_debut     = fields.Datetime('Heure début')
    heure_fin       = fields.Datetime('Heure fin')
    temps           = fields.Integer('Temps (s)')
    resultat        = fields.Text('Résultat')


    def name_get(self, cr, uid, ids, context=None):
        res = []
        for obj in self.browse(cr, uid, ids, context=context):
            name=str(obj.heure_debut)+" "+obj.ordinateur_id.name
            res.append((obj.id,name))
        return res





    @api.multi
    def mail_anomalie_sauvegarde_action(self):
        for obj in self:
            filtre=[
                ('date','=',datetime.date.today()),
                ('utilisateur_id.site_id.name','=','Gray'),
                ('partage','=','Thunderbird'),
                ('resultat','=','OK'),
                ('nb_modifs','>',0),
            ]
            filtre=[
                ('date','=',datetime.date.today()),
                ('partage','=','Thunderbird'),
            ]
            rows  = self.env['is.save.mozilla'].search(filtre, order='heure_debut')
            html=u"""
                <table style="">
                    <thead>
                        <tr>
                            <th>Utilisateur</th>
                            <th>Début</th>
                            <th>Fin</th>
                            <th>Durée (mn)</th>
                            <th>Taille (go)</th>
                            <th>Nb modifs</th>
                            <th>Résultat</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            for row in rows:
                nb_modifs_color='white'
                if row.nb_modifs==0:
                    nb_modifs_color='orange'
                temps_color='white'
                if row.temps>=600:
                    temps_color='orange'

                resultat_color='white'
                if row.resultat=="OK" and row.nb_modifs>0 and row.temps<600:
                    resultat_color='green'

                html+=u"""
                    <tr>
                        <td style="text-align:left">"""+row.utilisateur_id.name+"""</td>
                        <td style="text-align:center">"""+utc2local(row.heure_debut)+"""</td>
                        <td style="text-align:center">"""+utc2local(row.heure_fin)+"""</td>
                        <td style="text-align:right;background-color:"""+temps_color+"""">"""+"{:10.1f}".format(row.temps/60.0)+"""</td>
                        <td style="text-align:right">"""+"{:10.2f}".format(row.taille/1024.0)+"""</td>
                        <td style="text-align:right;background-color:"""+nb_modifs_color+"""">"""+str(row.nb_modifs)+"""</td>
                        <td style="text-align:left;width:50%;background-color:"""+resultat_color+"""">"""+row.resultat+"""</td>
                    </tr>
                """
            html+="</tbody></table>"
            user  = self.env['res.users'].browse(self._uid)
            email_to=[]
            email_to.append(user.name+u' <'+user.email+u'>')
            subject=u"Anomalies sauvegarde Thunderbird du "+str(obj.date)
            body_html=u"""
                <html>
                    <head>
                        <meta content="text/html; charset=UTF-8" http-equiv="Content-Type">
                        <style>
                            table {
                                border:1px solid black;
                                width:100%;
                                border-collapse:collapse;
                            }
                            td,th { 
                                border:1px solid black;
                                padding:0.5em;
                                margin:0.5em;
                            }
                        </style>
                    </head>
                    <body>
                        <h2>"""+subject+"""</h2>
                        """+html+"""
                    </body>
                </html>
            """
            email_vals={
                'subject'       : subject,
                'email_to'      : ';'.join(email_to), 
                'email_cc'      : "",
                'email_from'    : "robot@plastigray.com", 
                'body_html'     : body_html.encode('utf-8'), 
            }
            email_id=self.env['mail.mail'].create(email_vals)
            self.env['mail.mail'].send(email_id)
            _logger.info(subject)


def utc2local(date):
    # Timezone en UTC
    utc = pytz.utc
    # DateTime à partir d'une string avec ajout de la timezone
    utc_dt  = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S').replace(tzinfo=utc)
    # Timezone Europe/Paris
    europe = pytz.timezone('Europe/Paris')
    # Convertion de la datetime utc en datetime localisée
    loc_dt = utc_dt.astimezone(europe)
    # Retour de la datetime localisée en string
    #return loc_dt.strftime('%d/%m/%Y %H:%M')
    return loc_dt.strftime('%H:%M')





