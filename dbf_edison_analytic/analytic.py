# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2001-2014 Micronaet SRL (<http://www.micronaet.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os
import sys
import logging
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from dbfread import DBF
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)


class AccountAnalyticAccount(orm.Model):
    """ Model name: Analytic Account
    """
    
    _inherit = 'account.analytic.account'
    
    def schedule_dbf_edison_analytic_import(self, cr, uid, 
            verbose_log_count=100, with_address=False, log_name='cantieri.log',
            context=None):
        ''' Import analytic from external DBF
        '''
        _logger.info('Start import account')    

        # Pool used:
        partner_pool = self.pool.get('res.partner')
        company_pool = self.pool.get('res.company')

        db = company_pool.get_dbf_table(
            cr, uid, 'CANTIE.DBF', context=context)
        # Log:
        log_file = company_pool.get_dbf_logfile(
            cr, uid, log_name, context=context)
        log = company_pool.get_dbf_logevent
        log(log_file, 'Inizio importazione cantieri', mode='INFO')
            
        i = 0
        for record in db:
            i += 1
            if verbose_log_count and i % verbose_log_count == 0:
                _logger.warning('Import analytic #: %s' % i)
            
            # -----------------------------------------------------------------
            # Mapping fields (readability):
            # -----------------------------------------------------------------
            # Analytic account ref:
            code = '%s%s' % (
                '', # record['CANNCANT'] or '', # TODO remove year
                record['CNUMCANT'] or '',
                )
            name = record['CDESCANT'] or ''            
            from_date = record['DDATINLA'].strftime(DEFAULT_SERVER_DATE_FORMAT)
            
            # Partner ref.:
            partner_code = record['CCODCLIE'] or ''
                
            # Address ref.:    
            address_street = record['CINDCANT']
            address_city = record['CCOMCANT']
            address_code = '#%s' % code

            # -----------------------------------------------------------------
            # Linked partner:
            # -----------------------------------------------------------------
            partner_ids = partner_pool.search(cr, uid, [
                ('dbf_customer_code', '=', partner_code)
                ], context=context)

            partner_id = False
            if len(partner_ids) > 1:
                log(
                    log_file, 
                    'Codice partner multiplo: %s' % partner_code, 
                    mode='ERROR',
                    )
            if partner_ids:
                partner_id = partner_ids[0]

            # -----------------------------------------------------------------
            # Address partner (create):
            # -----------------------------------------------------------------
            address_id = False
            if with_address and address_street:# or address_city:
                address_ids = partner_pool.search(cr, uid, [
                    ('dbf_destination_code', '=', address_code)
                    ], context=context)
                    
                if len(address_ids) > 1:
                    log(
                        log_file, 
                        'Codice indirizzo multiplo: %s' % address_code, 
                        mode='ERROR',
                        )
                address_data = {
                    'name': name,
                    'parent_id': partner_id,
                    'street': address_street,
                    'city': address_city,
                    'is_address': True,
                    #'is_company': True,                    
                    }        

                if address_ids:
                    address_id = address_ids[0]
                    partner_pool.write(cr, uid, address_id, address_data, 
                        context=context)
                else:       
                    address_id = partner_pool.create(
                        cr, uid, address_data, context=context)

            #CDESCANT CCODCLIE CDESDECL DDATINLA DDATFILA LBLOCCA
            #CRIF1CAN CRIF2CAN CRESESTE LECONOMIA LCONTRATTO NOREVIAGGI
            #NMINVIAGGI CFILLER LSELRIGA NRIFIMAT NRIFIMAN NRIFISPE
            #NRIFIMATV NRIFIMANV NRIFISPEV CTIPCOMM CTLIARTI CFASCIA
            #CTLICOST CTLIPREZ NRICPREZ LRICNOTE LVALCOPR NRMACOST
            #NRMAPREZ LMANCOPR NRSECOST NRSEPREZ LSEXCOPR NKMPVIAGGI
            #NCOSVIAGGI NPRZVIAGGI LATTESA LRICNOST NRICMANO NRICSPEX
            #DDATAANA CCODPERS CLISCECO CSTATO NRMTCOST NSTSINCR
            #DATOPER CORAOPER CCODOPER CCODUTEN CCODRECO LVALPRZV
            #NRICPRZV CCODPRAT CCONTORI DDATCONS CCODLUPR NIMPCONT
            #NPERESEG LVALCOMP LVALTUOR CFILLER2 NPERCOST NPERPROV	
            #CCODAGEN NPERRITG NPERMUTA CCODARTI NQTAARTI NPERPRO2
            #CCODAMMI MMEMO1 MMEMOANA MMEMOANA2 MMEMOANA3

            data = {
                'dbf_import': True,
                'code': code,
                'name': name,
                'partner_id': partner_id,
                'address_id': address_id,
                'type': 'normal', 
                'use_timesheets': True,
                'from_date': from_date,
                }
                
            # Search partner code:
            analytic_ids = self.search(cr, uid, [
                ('code', '=', code),
                ], context=context)

            if len(analytic_ids) > 1:
                log(
                    log_file, 
                    'Codice commessa multiplo: %s' % code, 
                    mode='ERROR',
                    )

            if analytic_ids:
                self.write(cr, uid, analytic_ids, data, context=context)
            else:
                self.create(cr, uid, data, context=context)
        log(
            log_file, 
            'Fine importazione cantieri [Tot.: %s]\n' % i,
            mode='INFO',
            )
        try:
            log_file.close()
        except:
            return False    
        return True        
            
    _columns = {
        'dbf_import': fields.boolean('DBF import'),
        'from_date': fields.date('From Date'),
        }
   
    _defaults = {
        'from_date': lambda *x: datetime.now().strftime(
            DEFAULT_SERVER_DATE_FORMAT),
        }     
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
