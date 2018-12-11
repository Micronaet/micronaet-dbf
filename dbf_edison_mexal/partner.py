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
    
    def schedule_dbf_edison_partner_mx_import(self, cr, uid, 
            verbose_log_count=100, customer='customer.csv', 
            supplier='supplier.csv', context=None):
        ''' Import partner from external DBF
        '''
        # ---------------------------------------------------------------------
        #                      COMMON PART: Get parameter
        # ---------------------------------------------------------------------
        eol = '\n\r'
        
        # Browse company: 
        company_pool = self.pool.get('res.company')
        
        # Log:
        log = company_pool.get_dbf_logevent
        log(log_file, 'Inizio extract partner', mode='INFO')

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
                }, customer),
            ('supplier', 'TBFORN.DBF', {
                'ref': 'CCODFORN',
                'name1': 'CDESFORN',
                'name2': 'CDE2FORN',
                'phone': 'CTEAFORN',
                'mobile': 'CTECFORN',
                }, supplier),
            ]
        
        i = c = s = 0 # counters (total read, customer, supplier)
        mask = '%-8s%-70s%-30s%-90s%-30s%-29s%-24s%-17s%-52s%-5s%-26s%-20s' + \
            '%-25s%-10s%-16s%-30s%-37s%s'
        import pdb; pdb.set_trace()
        for mode, db_name, mapping, csv_name in mapping_db:
            db = company_pool.get_dbf_table(
                cr, uid, db_name, context=context)
            f_export = open(csv_name, 'w')    
            for record in db:
                i += 1
                if verbose_log_count and i % verbose_log_count == 0:
                    _logger.info('Extract customer #: %s' % i)
                
                # Mapping fields:
                ref = record[mapping['ref']]
                name = '%s%s' % (
                    record[mapping['name1']] or '',
                    record[mapping['name2']] or '',
                    )
                vat = record['CPARTIVA']
                if vat and vat[:1].isdigit():
                    vat = 'IT%s' % vat
                
                row = mask % (
                    ref,
                    name[:70],
                    record[mapping['phone']], # phone
                    record['CEMAIL'], # email
                    '', # TODO fax
                    '', # TODO reference
                    vat, # vat
                    record['CCODFISC'], # fiscalcode
                    record['CINDIR'], # street
                    record['CCAP'], # zip
                    record['CCOMUNE'], # city
                    record['CDPROV'], # prov.

                    '', #record['CDPROV'], # payment
                    record['CCODAGEN'], # agent code
                    '', #record['NSCOFATT'], # discount
                    record['CCODBANC'], # cod. bank
                    '', #record['CDPROV'], # IBAN
                                        
                    
                    #'mobile': record[mapping['mobile']], # mobile
                    #'website': record['CSITOWEB'], # website                    
                    #CFASCIA CCODCOPA CCODCIVA CDESDESCR 
                    #CDESINDIR CDESCITTA 2CTEUCLIE CTELRIF CMESIMAN NCOSTMAN 
                    #DDATAMAN CTIPCLIE CCODZONA CTLIARSE CTLIARCO CNAZIONE
                    #LFLAGCEE NSCONTEX CCODVETT CCODVALU
                    #CCODLIST CCONTORI CSTATO
                    #CCONTCORR NSPESEIN NSPEBOLL NSPETRAS CNUMDIC
                    #DDATDIC CNUMREG DDATREG LEFFRATE CFILLER
                    #NQUALIFI DDATINSE CRIFERIM CCORTATT LSPESEIN
                    #LSPEBOLL LNOEXPCO NSPEFISS CCODCINN CCODCINE
                    # NSCOARFA NSTSINCR DDATOPER CORAOPER
                    #CCODOPER CCODUTEN NRICMANO NRICSPEX LPERSONA
                    #CFILLER1 CTEC2CLI CTELRIF2 CCODAMMI CCODPORT
                    #CTIPSOGG NQUALIF2 3NQUALIF3 LCALCRIT LFRZPRZV
                    #LFRZNPRZ CEMAIL2 CPEC MZONA MNOTE
                    eol,
                    )

                #clean row    
                f_export.write(row)
            f_export.close()    
        return True        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
