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


class ResPartner(orm.Model):
    """ Model name: ResPartner
    """
    
    _inherit = 'res.partner'
    
    def schedule_dbf_edison_partner_import(self, cr, uid, 
            verbose_log_count=100, log_name='partner.log',
            context=None):
        ''' Import partner from external DBF
        '''
        # ---------------------------------------------------------------------
        #                      COMMON PART: Get parameter
        # ---------------------------------------------------------------------
        # Browse company: 
        company_pool = self.pool.get('res.company')
        
        # Log:
        log_file = company_pool.get_dbf_logfile(
            cr, uid, log_name, context=context)
        log = company_pool.get_dbf_logevent
        log(log_file, 'Inizio importazione partner', mode='INFO')

        # ---------------------------------------------------------------------
        # Mapping:
        # ---------------------------------------------------------------------
        mapping_db = [ # DB and mapping fields:
            ('customer', 'TBCLIE.DBF', {
                'ref': 'CCODCLIE',
                'name1': 'CDESCLIE',
                'name2': 'CDE2CLIE',
                'phone': 'CTEACLIE',
                'mobile': 'CTECCLIE',                
                }),
            ('supplier', 'TBFORN.DBF', {
                'ref': 'CCODFORN',
                'name1': 'CDESFORN',
                'name2': 'CDE2FORN',
                'phone': 'CTEAFORN',
                'mobile': 'CTECFORN',
                }),
            ]
        
        i = c = s = 0 # counters (total read, customer, supplier)
        for mode, db_name, mapping in mapping_db:
            db = company_pool.get_dbf_table(
                cr, uid, db_name, context=context)
            for record in db:
                i += 1
                if verbose_log_count and i % verbose_log_count == 0:
                    _logger.info('Import customer #: %s' % i)
                
                # Mapping fields:
                ref = record[mapping['ref']]
                name = '%s%s' % (
                    record[mapping['name1']] or '',
                    record[mapping['name2']] or '',
                    )
                vat = record['CPARTIVA']
                if vat and vat[:1].isdigit():
                    vat = 'IT%s' % vat
                    
                data = {
                    'is_company': True,
                    'dbf_import': True,
                    'name': name,
                    'street': record['CINDIR'],
                    'city': record['CCOMUNE'],
                    'zip': record['CCAP'],
                    'fiscalcode': record['CCODFISC'],
                    'vat': vat,
                    'phone': record[mapping['phone']],
                    'mobile': record[mapping['mobile']],
                    'email': record['CEMAIL'], 
                    'website': record['CSITOWEB'],
                    #CDPROV CFASCIA CCODCOPA CCODBANC CCODCIVA CDESDESCR 
                    #CDESINDIR CDESCITTA 2CTEUCLIE CTELRIF CMESIMAN NCOSTMAN 
                    #DDATAMAN CTIPCLIE CCODZONA CTLIARSE CTLIARCO CNAZIONE
                    #LFLAGCEE CCODAGEN NSCONTEX CCODVETT CCODVALU
                    #CCODLIST CCONTORI CSTATO
                    #CCONTCORR NSPESEIN NSPEBOLL NSPETRAS CNUMDIC
                    #DDATDIC CNUMREG DDATREG LEFFRATE CFILLER
                    #NQUALIFI DDATINSE CRIFERIM CCORTATT LSPESEIN
                    #LSPEBOLL LNOEXPCO NSPEFISS CCODCINN CCODCINE
                    #NSCOFATT NSCOARFA NSTSINCR DDATOPER CORAOPER
                    #CCODOPER CCODUTEN NRICMANO NRICSPEX LPERSONA
                    #CFILLER1 CTEC2CLI CTELRIF2 CCODAMMI CCODPORT
                    #CTIPSOGG NQUALIF2 3NQUALIF3 LCALCRIT LFRZPRZV
                    #LFRZNPRZ CEMAIL2 CPEC MZONA MNOTE
                    }
                if mode == 'supplier':
                    dbf_code = 'dbf_supplier_code'
                    data['supplier'] = True
                    s += 1                    
                else: # customer
                    dbf_code = 'dbf_customer_code'
                    data['customer'] = True
                    data['ref'] = ref
                    c += 1
                data[dbf_code] = ref
                
                # Search partner code:
                if vat: 
                    domain = ['|', '|', 
                        (dbf_code, '=', ref), ('name', '=', name),
                        ('vat', '=', vat),
                        ]
                else: 
                    domain = ['|', 
                        (dbf_code, '=', ref), ('name', '=', name),
                        ]
                        
                partner_ids = self.search(cr, uid, domain, context=context)                
                if len(partner_ids) > 1:
                    log(
                        log_file, 
                        'Errore partner multipli: %s (usato primo)' % name, 
                        mode='ERROR',
                        )
                    partner_ids = [partner_ids[0]]
                    
                if partner_ids:
                    try:
                        self.write(cr, uid, partner_ids, data, context=context)
                    except: # Try removing vat
                        log(
                            log_file, 
                            'Rimossa P. IVA non valida: %s [ref: %s]' % (
                                data['vat'], ref),
                            mode='WARNING',
                            )
                        del(data['vat'])
                        try:
                            self.write(
                                cr, uid, partner_ids, data, context=context)
                        except:
                            _logger.error('Error data: %s' % data)
                            log(
                                log_file, 
                                'Errore nell''inserimento dati, rif: %s' % ref,
                                mode='ERROR',
                                )
                else:
                    try:
                        self.create(cr, uid, data, context=context)                
                    except: # Try removing vat
                        log(
                            log_file, 
                            'Rimossa P. IVA non valida: %s [ref: %s]' % (
                                data['vat'], ref),
                            mode='WARNING',
                            )
                        del(data['vat'])
                        try:
                            self.create(cr, uid, data, context=context)                
                        except:
                            log(
                                log_file, 
                                'Errore nell''inserimento dati, rif: %s' % ref,
                                mode='ERROR',
                                )
        log(
            log_file, 
            'Fine importazione [Tot: %s (clienti: %s, fornitori: %s)]\n' % (
                i, c, s),
            mode='INFO',
            )
        try:
            log_file.close()
        except:
            return False    
        return True        
            
    _columns = {
        'dbf_import': fields.boolean('DBF import'),
        'dbf_customer_code': fields.char('DBF customer code', size=10),
        'dbf_supplier_code': fields.char('DBF supplier code', size=10),
        'dbf_destination_code': fields.char('DBF destination code', size=10),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
