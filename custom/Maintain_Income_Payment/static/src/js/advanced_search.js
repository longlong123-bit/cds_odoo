odoo.define('Income_Payment.Advanced_Search', function(require){
    var FilterMenu = require('web.FilterMenu_free');

    FilterMenu.include({
        advancedSearch: _.extend({}, FilterMenu.prototype.advancedSearch || {}, {
            'account.payment': {
                'account.payment.custom.tree.in.payment': {template: 'Income_Payment.advanced_search'},
                template: 'dialog.advanced_search',
            },
            'many.payment': {
                template: 'many_payment.advanced_search'
            },
            'account.payment.line': {
                template: 'payment_line.advanced_search'
            }
        })
    });
});
