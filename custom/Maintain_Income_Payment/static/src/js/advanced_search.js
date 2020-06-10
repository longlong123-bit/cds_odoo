odoo.define('Income_Payment.Advanced_Search', function(require){
    var FilterMenu = require('web.FilterMenu_free');

    FilterMenu.include({
        advancedSearch: _.extend({}, FilterMenu.prototype.advancedSearch || {}, {
            'account.payment': {
                template: 'Income_Payment.advanced_search'
            }
        })
    });
});
