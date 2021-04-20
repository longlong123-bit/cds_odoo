odoo.define('Invoice.Search', function(require){
    var FilterMenu = require('web.FilterMenu_free');

    FilterMenu.include({
        advancedSearch: _.extend({}, FilterMenu.prototype.advancedSearch || {}, {
            'account.move': {
                template: 'invoice.advanced_search'
            },
            'account.move.line': {
                'account.move.line.search': {template: 'invoice_line.advanced_search'},
                'invoice.history.tree': {template: 'invoice_history.advanced_search'}
            }
        })
    });
});
