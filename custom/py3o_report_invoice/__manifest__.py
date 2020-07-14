# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Py3o Report Invoice',
    'version': '1.0',
    'category': 'Report',
    'license': 'AGPL-3',
    'summary': 'Py3o Report Invoice',
    'description': """
Py3o Report Invoice
    """,
    'author': 'SK Company',
    'depends': [
        'Maintain_Collation_History',
        'Maintain_Bill_Management',
        'report_py3o',
        ],
    'data': ['report.xml'],
    'installable': True,
}
