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
        def clean(value, length=False):
            if not value:
                return ''
                
            res = ''
            for c in value:
                if ord(c) < 127:
                    res += c
                else:
                    res += '#'
            if length:
                return res[:length]        
            return res
        
        def clean_excel_line(record):
            res = []
            for item in record.values():
                res.append(u'%s' % (item or ''))
            return res
                    
        # ---------------------------------------------------------------------
        #                      COMMON PART: Get parameter
        # ---------------------------------------------------------------------
        eol = '\n\r'
        
        payment_db = {
            }
        vat_db = {
            #'21': '20',
            #'23': 
            }
        
        # Browse company: 
        company_pool = self.pool.get('res.company')
        excel_pool = self.pool.get('excel.writer')

        # ---------------------------------------------------------------------
        # Mapping:
        # ---------------------------------------------------------------------
        mapping_db = [ # DB and mapping fields:
            ('customer', 'TBCLIE.DBF', {
                'ref': 'CCODCLIE',
                'name1': 'CDESCLIE',
                'name2': 'CDE2CLIE',
                'phone': 'CTEUCLIE',
                'mobile': 'CTEACLIE',                
                }, customer),
            ('supplier', 'TBFORN.DBF', {
                'ref': 'CCODFORN',
                'name1': 'CDESFORN',
                'name2': 'CDE2FORN',
                'phone': 'CTEUFORN',
                'mobile': 'CTEAFORN',
                }, supplier),
            ]
        
        i = c = s = 0 # counters (total read, customer, supplier)
        mask = '%-8s%-70s%-30s%-90s%-30s%-29s%-24s%-17s%-52s%-5s%-26s%-20s' + \
            '%-25s%-10s%-16s%-30s%-4s%-2s%-20s%-80s%-6s%-1s%-2s%s'

        for mode, db_name, mapping, csv_name in mapping_db:
            db = company_pool.get_dbf_table(
                cr, uid, db_name, context=context)
            f_export = open(csv_name, 'w')    

            excel_row = 0
            ws_name = mode
            excel_pool.create_worksheet(ws_name)
            for record in db:
                # -------------------------------------------------------------
                # Excel extract
                # -------------------------------------------------------------
                # Write header:
                if not excel_row:                    
                    excel_pool.write_xls_line(
                        ws_name, excel_row, record.keys())
                    excel_row += 1
                # Write line:                
                excel_pool.write_xls_line(
                    ws_name, excel_row, clean_excel_line(record))
                excel_row += 1
                    
                i += 1
                if verbose_log_count and i % verbose_log_count == 0:
                    _logger.info('Extract customer #: %s' % i)
                
                # Mapping fields:
                ref = record[mapping['ref']]
                name = '%s%s' % (
                    record[mapping['name1']] or '',
                    record[mapping['name2']] or '',
                    )

                row = mask % (
                    clean(ref, 8),
                    clean(name, 70),
                    clean(record[mapping['phone']], 30), # phone
                    clean(record['CEMAIL'], 90), # email
                    clean('', 30), # TODO fax
                    clean('CRIFERIM', 29), # TODO reference
                    clean(record['CPARTIVA'], 24), # vat
                    clean(record['CCODFISC'], 17), # fiscalcode
                    clean(record['CINDIR'], 52), # street
                    clean(record['CCAP'], 5), # zip
                    clean(record['CCOMUNE'], 26), # city
                    clean(record['CPROV'], 20), # prov.

                    clean(payment_db.get(
                        '', ''), 25), #record['CDPROV'], # payment
                    clean(record['CCODAGEN'], 10), # agent code
                    clean('', 16), #record['NSCOFATT'], # discount
                    clean(record['CCODBANC'], 30), # cod. bank
                    clean(vat_db.get(
                        record['CCODCIVA'], ''), 4), # IVA ID
                    clean(record['CNAZIONE'], 2), # Country
                    clean(record['CCONTCORR'], 20), # CC
                    clean(record['CSITOWEB'], 80), # Web
                    clean(record['NSPESEIN'], 6), # Expense
                    clean(record['CCODCINN'], 1), # Cinn
                    clean(record['CCODCINE'], 2), # Cine
                    eol,
                    )
                f_export.write(row)
            f_export.close()    
        excel_filename = os.path.expanduser('~/partner.xlsx')    
        excel_pool.save_file_as(excel_filename)
        return True        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
