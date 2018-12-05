##############################################################################
#
#    GNU Condo: The Free Management Condominium System
#    Copyright (C) 2016- M. Alonso <port02.server@gmail.com>
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from trytond.pool import Pool
from trytond.report import Report

import logging

__all__ = ['AddressList']


class AddressList(Report):
    __name__ = 'condo.address_list'

    @classmethod
    def get_context(cls, records, data):
        report_context = super(AddressList, cls).get_context(records, data)

        #records:
        #[Pool().get('company.company')(4), Pool().get('company.company')(6)]
        #data:
        #{u'model': u'company.company', u'action_id': 69, u'ids': [4, 6], u'id': 4}

        pool = Pool()
        CondoParty = pool.get('condo.party')
        CondoUnit = pool.get('condo.unit')

        units = CondoUnit.search_read([
                    'OR', [
                            ('company', 'in', data['ids']),
                        ],[
                            ('company.parent', 'child_of', data['ids']),
                        ],
                ], fields_names=['id'])

        condoparties = CondoParty.search([
                ('unit', 'in', [ x['id'] for x in units ]),
                ('address', '!=', None),
                ], order=[('unit.company', 'ASC'), ('unit.name', 'ASC')])

        report = []
        crossreferences = {}
        for condoparty in condoparties:
            item = {
                'party': condoparty.party,
                'address': condoparty.address
                }

            #tuple (party, address) already in report: repeated item detected so next loop
            if item in report:
                continue

            #condoparty.address.name exist and is not empty
            if condoparty.address.name and condoparty.address.name.strip():
                #condoparty.address.name already used as another condoparty.party.full_name
                if (condoparty.address.name in crossreferences) and \
                    (crossreferences[condoparty.address.name]==condoparty.party.full_name):
                        repeated_item = next(filter(lambda f:f['party'].full_name==condoparty.address.name and f['address'].name==condoparty.party.full_name, report),None)
                        if repeated_item:
                            r =  repeated_item['address']
                            #if all fields of address are same the repeated item is detected
                            if r.street==condoparty.address.street and \
                                r.zip==condoparty.address.zip and \
                                r.city==condoparty.address.city and \
                                r.subdivision==condoparty.address.subdivision and \
                                r.country==condoparty.address.country:
                                logging.warning('Repeated record: {0} {1} {2} {3} {4} {5} {6}',
                                                                                  condoparty.party.full_name,
                                                                                  condoparty.address.name,
                                                                                  r.street,
                                                                                  r.zip,
                                                                                  r.city,
                                                                                  r.subdivision.name,
                                                                                  r.country.name)
                                continue
                else:
                    crossreferences[condoparty.party.full_name]=condoparty.address.name.strip()

            report.append(item)

        report_context['records'] = report

        return report_context
