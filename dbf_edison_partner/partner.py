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
            verbose_log_count=100, context=None):
        ''' Import partner from external DBF
        '''
        # ---------------------------------------------------------------------
        #                      COMMON PART: Get parameter
        # ---------------------------------------------------------------------
        # Browse company: 
        company_pool = self.pool.get('res.company')
        company_ids = company_pool.search(cr, uid, [], context=context)
        company_proxy = company_pool.browse(
            cr, uid, company_ids, context=context)[0]
        
        # Read parameter:    
        dbf_root_path = os.path.expanduser(company_proxy.dbf_root_path)
        dbf_ignorecase = company_proxy.dbf_ignorecase
        dbf_memofile = company_proxy.dbf_memofile
        dbf_encoding = company_proxy.dbf_encoding

        # ---------------------------------------------------------------------
        #                             CUSTOMER
        # ---------------------------------------------------------------------
        filename = os.path.join(dbf_root_path, 'TBCLIE.DBF')
        db = DBF(
            filename, 
            ignorecase=dbf_ignorecase,
            ignore_missing_memofile=dbf_memofile,
            encoding=dbf_encoding,
            )
            
        i = 0
        #XXX db.field_names
        for record in db:
            i += 1
            if verbose_log_count and i % verbose_log_count == 0:
                _logger.warning('Import customer #: %s' % i)
            
            # Mapping fields:
            ref = record['CCODCLIE']
            name = '%s%s' % (
                record['CDESCLIE'] or '',
                record['CDE2CLIE'] or '',
                )
            vat = record['CPARTIVA']
            if vat and vat[:1].isdigit():
                vat = 'IT%s' % vat
                
            data = {
                'customer': True,
                'dbf_import': True,
                'dbf_customer_code': ref, 
                'ref': ref,
                'name': name,
                'street': record['CINDIR'],
                'city': record['CCOMUNE'],
                'zip': record['CCAP'],
                'fiscalcode': record['CCODFISC'],
                'vat': vat,
                'phone': record['CTEACLIE'],
                'mobile': record['CTECCLIE'],
                'email': record['CEMAIL'], 
                'website': record['CSITOWEB'],
                #'prov': record['CDPROV']
                #'codefascia': record['CFASCIA'],
                #'codecopa': record['CCODCOPA'],
                #'codebanca': record['CCODBANC'],
                #'codeiva': record['CCODCIVA'],               
                #'desdescr': record['CDESDESCR'],
                #'desindir': record['CDESINDIR'],
                #'descitta':  record['CDESCITTA'], 
                #'phone2': record['CTEUCLIE'], 
                #'telrif': record['CTELRIF'],
                #'mesiman': record['CMESIMAN'],
                #'costoman': record['NCOSTMAN'],
                #'dataman': record['DDATAMAN'], 
                #'ctipcli': record['CTIPCLIE'],
                #'codzona': record['CCODZONA'],
                #'ctliarse': record['CTLIARSE'],
                #'ctliarco': record['CTLIARCO'],
                #'nazione': record['CNAZIONE'],  
                #'lflagcee': record['LFLAGCEE'], 
                #'codagen': record['CCODAGEN'],
                #'scintex': record['NSCONTEX'],
                #'codvett': record['CCODVETT'],
                #'codvalu': record['CCODVALU'], 
                #'codlist': record['CCODLIST'],
                #'contori': record['CCONTORI'],
                #'cstato': record['CSTATO'], 
                #'contocorr': record['CCONTCORR'],
                #'nspesein': record['NSPESEIN'],
                #'nspeseboll': record['NSPEBOLL'],
                #'nspesetras': record['NSPETRAS'],
                #'numdic': record['CNUMDIC'], 
                #'datdic': record['DDATDIC'],
                #'numreg': record['CNUMREG'],
                #'datareg': record['DDATREG'],
                #'leffrate': record['LEFFRATE'],
                #'cfiller': record['CFILLER'], 
                #'nqualif': record['NQUALIFI'],
                #'datanse': record['DDATINSE'],
                #'criferm': record['CRIFERIM'],
                #'contratt': record['CCORTATT'],
                #'lspesein': record['LSPESEIN'], 
                #'lspeseboll': record['LSPEBOLL'],
                #'lnoexpco': record['LNOEXPCO'],
                #'nspefiss': record['NSPEFISS'],
                #'codcinn': record['CCODCINN'],
                #'codcine': record['CCODCINE'], 
                #'nscofatt': record['NSCOFATT'],
                #'nscoarfa': record['NSCOARFA'],
                #'nstsincr': record['NSTSINCR'],
                #'ddatoper': record['DDATOPER'],
                #'coraoper': record['CORAOPER'], 
                #'ccodoper': record['CCODOPER'],
                #'ccoduten': record['CCODUTEN'],
                #'nricmano': record['NRICMANO'],
                #'nricspex': record['NRICSPEX'],
                #'lpersona': record['LPERSONA'], 
                #'cfiller1': record['CFILLER1'],
                #'ctec2cli': record['CTEC2CLI'],
                #'ctelrif2': record['CTELRIF2'],
                #'codammi': record['CCODAMMI'],
                #'codport': record['CCODPORT'], 
                #'tipsogg': record['CTIPSOGG'],
                #'nqualif2': record['NQUALIF2'],
                #'nqualif3': record['NQUALIF3'],
                #'lcalcrit': record['LCALCRIT'],
                #'lfrzprzv': record['LFRZPRZV'], 
                #'lfrznprz': record['LFRZNPRZ'],
                #'cemail2': record['CEMAIL2'],
                #'cpec': record['CPEC'],
                #'mzona': record['MZONA'],
                #'mnote': record['MNOTE'],
                }
                
            # Search partner code:
            if vat: 
                domain = [
                    '|', '|', 
                    ('dbf_customer_code', '=', ref),
                    ('name', '=', name),
                    ('vat', '=', vat),
                    ]
            else: 
                domain = [
                    '|', 
                    ('dbf_customer_code', '=', ref),
                    ('name', '=', name),
                    ]
                    
            partner_ids = self.search(cr, uid, domain, context=context)
            # TODO manage error (also for vat)
            # len(partner_ids) > 1 TODO WARNING
            if partner_ids:
                self.write(cr, uid, partner_ids, data, context=context)
            else:
                self.create(cr, uid, data, context=context)

        # ---------------------------------------------------------------------
        #                             SUPPLIER
        # ---------------------------------------------------------------------
        filename = os.path.join(dbf_root_path, 'TBFORN.DBF')
        db = DBF(
            filename, 
            ignorecase=dbf_ignorecase,
            ignore_missing_memofile=dbf_memofile,
            encoding=dbf_encoding,
            )
            
        i = 0
        #XXX db.field_names
        for record in db:
            i += 1
            if verbose_log_count and i % verbose_log_count == 0:
                _logger.warning('Import supplier #: %s' % i)
            
            # Mapping fields:
            ref = record['CCODFORN']
            name = '%s%s' % (
                record['CDESFORN'] or '',
                record['CDE2FORN'] or '',
                )
            vat = record['CPARTIVA']
            if vat and vat[:1].isdigit():
                vat = 'IT%s' % vat
            data = {
                'supplier': True,
                'dbf_import': True,
                'dbf_supplier_code': ref, 
                #'ref': ref,
                'name': name,
                'street': record['CINDIR'],
                'city': record['CCOMUNE'],
                'zip': record['CCAP'],
                'fiscalcode': record['CCODFISC'],
                'vat': vat,
                'phone': record['CTEAFORN'],
                'mobile': record['CTECFORN'],
                'email': record['CEMAIL'], 
                'website': record['CSITOWEB'],
                }
                #'cprov': record['CPROV'], 
                #'ccodaggi': record[CCODAGGI],
                #'ddatulag': record[DDATULAG],
                #'cfilelis': record[CFILELIS],
                #'cesclcar': record[CESCLCAR],	
                #'cteuforn': record[CTEUFORN], 
                #'ctelrif': record[CTELRIF],	
                #'ccodprag': record[CCODPRAG],
                #'lflagages': record[LFLAGAGES],
                #'nflagages': record[NFLAGAGES],
                #'ccodbanc': record[CCODBANC],
                #'ccodciva': record[CCODCIVA]	
                #'ccodcopa': record[CCODCOPA],	
                #'nscontex': record[NSCONTEX],	
                #'ccontori': record[CCONTORI],
                #'cstato': record[CSTATO],
                #'ccontcorr': record[CCONTCORR],
                #'nqualifi': record[NQUALIFI],
                #'ccodcate': record[CCODCATE],	
                #'ddatinse': record[DDATINSE],
                #'criferim': record[CRIFERIM],
                #'ccortatt': record[CCORTATT],
                #'cversaggln': record[CVERSAGGLN],	
                #'cfilepro': record[CFILEPRO],
                #'cfilebar': record[CFILEBAR],
                #'cfilefas': record[CFILEFAS],
                #'cfilecav': record[CFILECAV],	
                #'ccodagen': record[CCODAGEN],
                #'lnoexpco': record[LNOEXPCO],
                #'cnazione': record[CNAZIONE],
                #'ccodcinn': record[CCODCINN],
                #'ccodcine': record[CCODCINE],
                #'nstsincr': record[NSTSINCR],
                #'ddatoper': record[DDATOPER],
                #'coraoper': record[CORAOPER],
                #'ccodoper': record[CCODOPER],
                #'ccoduten': record[CCODUTEN],
                #'lpersona': record[LPERSONA]	
                #'nqualif2': record[NQUALIF2],
                #'nqualif3': record[NQUALIF3],
               	#'cspediz': record[CSPEDIZ],	
                #'ccodport': record[CCODPORT],
                #'ccodzona': record[CCODZONA],
                #'cemail2': record[CEMAIL2],
                #'cpec': record[CPEC],	
                #'mzona': record[MZONA],
               	#'mnote': record[MNOTE],
               	#'mnoteord': record[MNOTEORD],
               	#'mprodser': record[MPRODSER],
               	#'mvalanno': record[MVALANNO],	
                #'mstrateg': record[MSTRATEG],
               	#'mesitrif': record[MESITRIF],
               	#'mrivalut': record[MRIVALUT],

            # Search partner code:
            if vat: 
                domain = [
                    '|', '|', 
                    ('dbf_supplier_code', '=', ref),
                    ('name', '=', name),
                    ('vat', '=', vat),
                    ]
            else: 
                domain = [
                    '|', 
                    ('dbf_supplier_code', '=', ref),
                    ('name', '=', name),
                    ]
                    
            partner_ids = self.search(cr, uid, domain, context=context)
            # len(partner_ids) > 1 TODO WARNING
            if partner_ids:
                self.write(cr, uid, partner_ids, data, context=context)
            else:
                self.create(cr, uid, data, context=context)                
        return True        
            
    _columns = {
        'dbf_import': fields.boolean('DBF import'),
        'dbf_customer_code': fields.char('DBF customer code', size=10),
        'dbf_supplier_code': fields.char('DBF supplier code', size=10),
        'dbf_destination_code': fields.char('DBF destination code', size=10),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
