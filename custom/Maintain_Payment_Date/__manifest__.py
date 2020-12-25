{
    'name': 'Payment Date',
    'version': '13.0',
    'author': 'TrongHuy',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'description': """
""",
    'depends': [
        'base_setup', 'Maintain_Client', 'Maintain_Organization'
    ],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'views/payment_date_view.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}